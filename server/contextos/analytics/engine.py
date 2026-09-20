from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from contextos.models.analytics import (
    TokenRecord,
    AnalyticsSummary,
    BreakdownItem,
    ComparisonDataPoint,
    ComparisonSeries,
)
from contextos.analytics.pricing import calculate_token_costs
from contextos.storage.db import db
from contextos.models.event import EventType

class AnalyticsEngine:
    def __init__(self):
        self._ensure_seeded()

    def record_event(
        self,
        project_id: str = "contextos",
        session_id: str = "default_session",
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        provider: str = "OpenAI",
        model: str = "gpt-4o",
        candidate_tokens: int = 0,
        selected_tokens: int = 0,
        output_tokens: int = 0,
        cache_hit_tokens: int = 0,
        estimated: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TokenRecord:
        tokens_avoided = max(0, candidate_tokens - selected_tokens)
        bytes_avoided = tokens_avoided * 4  # Standard ~4 bytes/token for text/code

        cost_without, cost_with, cost_saved = calculate_token_costs(
            model=model,
            candidate_tokens=candidate_tokens,
            selected_tokens=selected_tokens,
            output_tokens=output_tokens,
            cache_hit_tokens=cache_hit_tokens,
        )

        record = TokenRecord(
            project_id=project_id,
            session_id=session_id,
            agent_id=agent_id,
            task_id=task_id,
            provider=provider,
            model=model,
            candidate_tokens=candidate_tokens,
            selected_tokens=selected_tokens,
            output_tokens=output_tokens,
            tokens_avoided=tokens_avoided,
            cache_hit_tokens=cache_hit_tokens,
            cost_without_usd=cost_without,
            cost_with_usd=cost_with,
            cost_saved_usd=cost_saved,
            bytes_avoided=bytes_avoided,
            estimated=estimated,
            metadata=metadata or {},
        )

        db.save_token_record(record)
        return record

    def get_summary(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AnalyticsSummary:
        summary = db.get_token_summary(project_id=project_id, session_id=session_id)
        if summary.total_events == 0:
            self._seed_from_fleet()
            summary = db.get_token_summary(project_id=project_id, session_id=session_id)
        return summary

    def get_breakdown(
        self,
        dimension: str = "provider",
        project_id: Optional[str] = None,
    ) -> List[BreakdownItem]:
        items = db.get_token_breakdown(dimension=dimension, project_id=project_id)
        if not items:
            self._seed_from_fleet()
            items = db.get_token_breakdown(dimension=dimension, project_id=project_id)
        return items

    def get_comparison(
        self,
        project_id: Optional[str] = None,
        limit: int = 15,
    ) -> ComparisonSeries:
        records = db.list_token_records(project_id=project_id, limit=limit)
        if not records:
            self._seed_from_fleet()
            records = db.list_token_records(project_id=project_id, limit=limit)

        data_points: List[ComparisonDataPoint] = []
        cum_cand = 0
        cum_sel = 0
        cum_avoid = 0
        cum_without = 0.0
        cum_with = 0.0
        cum_saved = 0.0

        # Process in chronological order
        for rec in reversed(records):
            label = rec.task_id or rec.agent_id or f"Run {rec.id[-6:]}"
            c = rec.candidate_tokens
            s = rec.selected_tokens
            a = rec.tokens_avoided
            ratio = round((a / c) * 100.0, 2) if c > 0 else 0.0

            data_points.append(
                ComparisonDataPoint(
                    label=label,
                    timestamp=rec.timestamp.isoformat(),
                    candidate_tokens=c,
                    selected_tokens=s,
                    tokens_avoided=a,
                    cost_without_usd=rec.cost_without_usd,
                    cost_with_usd=rec.cost_with_usd,
                    cost_saved_usd=rec.cost_saved_usd,
                    reduction_ratio=ratio,
                )
            )

            cum_cand += c
            cum_sel += s
            cum_avoid += a
            cum_without += rec.cost_without_usd
            cum_with += rec.cost_with_usd
            cum_saved += rec.cost_saved_usd

        overall_ratio = round((cum_avoid / cum_cand) * 100.0, 2) if cum_cand > 0 else 0.0
        bytes_avoided = cum_avoid * 4

        return ComparisonSeries(
            data_points=data_points,
            cumulative_candidate_tokens=cum_cand,
            cumulative_selected_tokens=cum_sel,
            cumulative_tokens_avoided=cum_avoid,
            cumulative_cost_without_usd=round(cum_without, 4),
            cumulative_cost_with_usd=round(cum_with, 4),
            cumulative_cost_saved_usd=round(cum_saved, 4),
            overall_reduction_ratio=overall_ratio,
            bytes_not_transmitted=bytes_avoided,
        )

    def _ensure_seeded(self):
        summary = db.get_token_summary()
        if summary.total_events == 0:
            self._seed_from_fleet()

    def _seed_from_fleet(self):
        # 1. Backfill from existing fleet agents
        agents = db.list_agents()
        for ag in agents:
            cand = ag.tokens.candidate_tokens or 28500
            sel = ag.tokens.selected_tokens or 3800
            hits = ag.tokens.cache_hits or 12
            self.record_event(
                project_id=ag.project_id or "contextos",
                session_id=ag.session_id or "default_session",
                agent_id=ag.id,
                task_id=ag.current_task or f"Task for {ag.name}",
                provider=ag.provider or "OpenAI",
                model=ag.model or "gpt-4o",
                candidate_tokens=cand,
                selected_tokens=sel,
                output_tokens=int(sel * 0.25),
                cache_hit_tokens=hits * 128,
                estimated=True,
                metadata={"agent_name": ag.name, "role": ag.role.value, "seeded": True},
            )

        # 2. Backfill from past context generation events
        events = db.list_events(limit=100)
        for ev in events:
            if ev.type == EventType.CONTEXT_GENERATED:
                cand = ev.payload.get("candidate_tokens", 0)
                sel = ev.payload.get("total_tokens", 0)
                if cand > 0 or sel > 0:
                    self.record_event(
                        project_id="contextos",
                        session_id=ev.session_id,
                        agent_id=ev.agent_id,
                        task_id="AST Context Compilation",
                        provider="Anthropic",
                        model="claude-3-5-sonnet",
                        candidate_tokens=cand,
                        selected_tokens=sel,
                        output_tokens=0,
                        cache_hit_tokens=0,
                        estimated=True,
                        metadata={"event_id": ev.id, "intent": ev.payload.get("intent")},
                    )

analytics_engine = AnalyticsEngine()
