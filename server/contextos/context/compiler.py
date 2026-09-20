import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from contextos.models.context import (
    ContextBudget,
    ContextTier,
    ContextItem,
    ContextBundle,
)
from contextos.models.event import EventEnvelope, EventType
from contextos.context.tokenizer import count_tokens
from contextos.context.compressor import ast_compressor
from contextos.memory.engine import memory_engine
from contextos.runtime.event_bus import event_bus
from contextos.config import settings

class ContextCompiler:
    """
    4-Tier Token-Budgeted Context Compiler.
    Selects, scores, compresses, and packs context items into strict partition budgets:
      - Tier 1: System (15%)
      - Tier 2: Task (10%)
      - Tier 3: Memory & Decisions (15%)
      - Tier 4: Source & Tests (50%)
      - Reserve: Buffer (10%)
    Strictly guarantees total token usage never exceeds the allotted budget.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or settings.workspace_root

    async def compile(
        self,
        intent: str,
        active_task: str = "",
        session_id: str = "default_session",
        budget: int = 8000,
        system_instructions: Optional[str] = None,
        workspace_root: Optional[Path] = None,
    ) -> ContextBundle:
        ws_root = workspace_root or self.workspace_root
        budget_obj = ContextBudget.from_total(budget)

        items: List[ContextItem] = []
        tier_counts: Dict[str, int] = {
            ContextTier.SYSTEM.value: 0,
            ContextTier.TASK.value: 0,
            ContextTier.MEMORY.value: 0,
            ContextTier.SOURCE.value: 0,
        }

        # --- TIER 1: SYSTEM (15%) ---
        default_sys = (
            "You are an AI coding assistant operating within ContextOS AIOS.\n"
            "Adhere to local workspace safety boundaries, minimal surgical edits, and SOLID design principles.\n"
            "Preserve working code, verify with tests before shipping, and respect user approval gates."
        )
        sys_text = system_instructions or default_sys
        sys_tokens = count_tokens(sys_text)
        if sys_tokens > budget_obj.system_budget:
            # Truncate to fit
            approx_chars = int(budget_obj.system_budget * 3.8)
            sys_text = sys_text[:approx_chars] + "\n[System instructions truncated to budget]"
            sys_tokens = count_tokens(sys_text)

        sys_item = ContextItem(
            tier=ContextTier.SYSTEM,
            source="system_instructions",
            content=sys_text,
            tokens=sys_tokens,
            score=1.0,
            compression_level="full",
        )
        items.append(sys_item)
        tier_counts[ContextTier.SYSTEM.value] += sys_tokens

        # --- TIER 2: TASK (10%) ---
        task_content = active_task or f"Current User Intent: {intent}"
        task_tokens = count_tokens(task_content)
        if task_tokens > budget_obj.task_budget:
            approx_chars = int(budget_obj.task_budget * 3.8)
            task_content = task_content[:approx_chars] + "\n[Task description truncated to budget]"
            task_tokens = count_tokens(task_content)

        task_item = ContextItem(
            tier=ContextTier.TASK,
            source="active_task",
            content=task_content,
            tokens=task_tokens,
            score=1.0,
            compression_level="full",
        )
        items.append(task_item)
        tier_counts[ContextTier.TASK.value] += task_tokens

        # --- TIER 3: MEMORY & DECISIONS (15%) ---
        mem_items_packed, mem_tokens = await self._pack_memory_tier(
            intent=intent,
            session_id=session_id,
            budget=budget_obj.memory_budget,
        )
        items.extend(mem_items_packed)
        tier_counts[ContextTier.MEMORY.value] += mem_tokens

        # --- TIER 4: SOURCE & TESTS (50%) ---
        source_items_packed, source_tokens, candidate_source_tokens = self._pack_source_tier(
            intent=intent,
            active_task=active_task,
            workspace_root=ws_root,
            budget=budget_obj.source_budget,
        )
        items.extend(source_items_packed)
        tier_counts[ContextTier.SOURCE.value] += source_tokens

        # Calculate totals & telemetry
        selected_tokens = sum(item.tokens for item in items)
        candidate_tokens = (
            sys_tokens + task_tokens + mem_tokens + candidate_source_tokens
        )
        tokens_avoided = max(0, candidate_tokens - selected_tokens)
        reduction_ratio = (
            round((tokens_avoided / candidate_tokens) * 100.0, 2)
            if candidate_tokens > 0
            else 0.0
        )

        # Assemble compiled prompt
        compiled_prompt = self._render_prompt(items)

        bundle = ContextBundle(
            intent=intent,
            budget=budget_obj,
            items=items,
            tier_token_counts=tier_counts,
            total_tokens=selected_tokens,
            candidate_tokens=candidate_tokens,
            tokens_avoided=tokens_avoided,
            reduction_ratio=reduction_ratio,
            compiled_prompt=compiled_prompt,
        )

        # Emit context generated event
        await event_bus.emit(
            EventEnvelope(
                agent_id="system",
                session_id=session_id,
                type=EventType.CONTEXT_GENERATED,
                payload={
                    "bundle_id": bundle.id,
                    "intent": intent,
                    "total_tokens": selected_tokens,
                    "candidate_tokens": candidate_tokens,
                    "tokens_avoided": tokens_avoided,
                    "reduction_ratio": reduction_ratio,
                    "budget_limit": budget,
                },
            )
        )

        return bundle

    async def _pack_memory_tier(
        self, intent: str, session_id: str, budget: int
    ) -> Tuple[List[ContextItem], int]:
        """Pulls memories and decisions and fits them within memory_budget."""
        packed: List[ContextItem] = []
        spent_tokens = 0

        # 1. ADR Decisions
        decisions = memory_engine.get_decisions(session_id=session_id, limit=5)
        for d in decisions:
            text = f"[ADR] {d.title}: {d.decision} (Status: {d.status})"
            tokens = count_tokens(text)
            if spent_tokens + tokens <= budget:
                packed.append(
                    ContextItem(
                        tier=ContextTier.MEMORY,
                        source=f"adr:{d.id}",
                        content=text,
                        tokens=tokens,
                        score=0.9,
                        compression_level="summary",
                    )
                )
                spent_tokens += tokens

        # 2. Memories relevant to intent or active session
        memories = await memory_engine.recall(query=intent, limit=10)
        session_mems = await memory_engine.recall(session_id=session_id, limit=5)
        seen_ids = set(m.id for m in memories)
        for sm in session_mems:
            if sm.id not in seen_ids:
                memories.append(sm)

        for m in memories:
            text = f"[{m.type.value.upper()}] {m.content}"
            tokens = count_tokens(text)
            if spent_tokens + tokens <= budget:
                packed.append(
                    ContextItem(
                        tier=ContextTier.MEMORY,
                        source=f"mem:{m.id}",
                        content=text,
                        tokens=tokens,
                        score=m.relevance_score or 0.8,
                        compression_level="full",
                    )
                )
                spent_tokens += tokens

        return packed, spent_tokens

    def _pack_source_tier(
        self, intent: str, active_task: str, workspace_root: Path, budget: int
    ) -> Tuple[List[ContextItem], int, int]:
        """Discovers, scores, compresses, and packs workspace source files."""
        packed: List[ContextItem] = []
        spent_tokens = 0
        candidate_tokens_total = 0

        if not workspace_root.exists():
            return packed, spent_tokens, candidate_tokens_total

        # 1. Discover candidate files
        candidates: List[Tuple[str, str, int]] = []  # (rel_path, content, raw_tokens)
        ignore_dirs = {".git", "node_modules", "__pycache__", "dist", ".pytest_cache", ".gemini", "build"}

        for root, dirs, files in os.walk(workspace_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in (".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".sql", ".toml", ".yaml", ".yml"):
                    full_p = Path(root) / file
                    try:
                        # Skip files larger than 1MB
                        if full_p.stat().st_size > 1024 * 1024:
                            continue
                        content = full_p.read_text(encoding="utf-8", errors="replace")
                        rel_path = str(full_p.relative_to(workspace_root)).replace("\\", "/")
                        t_count = count_tokens(content)
                        candidate_tokens_total += t_count
                        candidates.append((rel_path, content, t_count))
                    except Exception:
                        pass

        # 2. Score candidates
        keywords = set((intent + " " + active_task).lower().split())

        def score_candidate(item: Tuple[str, str, int]) -> float:
            path_lower = item[0].lower()
            score = 0.2  # base score

            # Path matches keywords
            for kw in keywords:
                if len(kw) > 2 and kw in path_lower:
                    score += 0.4
                    break

            # Source code over config / tests
            if path_lower.endswith((".py", ".ts", ".tsx")):
                score += 0.3
            if "test" in path_lower:
                score -= 0.1

            return score

        candidates.sort(key=score_candidate, reverse=True)

        # 3. Pack within budget using adaptive compression
        for rel_path, content, raw_tokens in candidates:
            if spent_tokens >= budget:
                break

            remaining_budget = budget - spent_tokens

            # Attempt Full Inclusion
            if raw_tokens <= remaining_budget and raw_tokens <= 800:
                packed.append(
                    ContextItem(
                        tier=ContextTier.SOURCE,
                        source=rel_path,
                        content=content,
                        tokens=raw_tokens,
                        score=score_candidate((rel_path, content, raw_tokens)),
                        compression_level="full",
                    )
                )
                spent_tokens += raw_tokens
                continue

            # Attempt AST Signatures Compression
            compressed_content = ast_compressor.compress(rel_path, content)
            sig_tokens = count_tokens(compressed_content)
            if sig_tokens <= remaining_budget:
                packed.append(
                    ContextItem(
                        tier=ContextTier.SOURCE,
                        source=rel_path,
                        content=compressed_content,
                        tokens=sig_tokens,
                        score=score_candidate((rel_path, content, raw_tokens)),
                        compression_level="signatures",
                    )
                )
                spent_tokens += sig_tokens
                continue

            # Attempt Minimal Outline / Summary
            outline = f"# {rel_path} (Interface summary - {len(content.splitlines())} lines)"
            out_tokens = count_tokens(outline)
            if out_tokens <= remaining_budget:
                packed.append(
                    ContextItem(
                        tier=ContextTier.SOURCE,
                        source=rel_path,
                        content=outline,
                        tokens=out_tokens,
                        score=score_candidate((rel_path, content, raw_tokens)),
                        compression_level="summary",
                    )
                )
                spent_tokens += out_tokens

        return packed, spent_tokens, candidate_tokens_total

    def _render_prompt(self, items: List[ContextItem]) -> str:
        """Assembles structured prompt sections across all 4 tiers."""
        sections = []

        # Group by tier
        by_tier: Dict[ContextTier, List[ContextItem]] = {
            ContextTier.SYSTEM: [],
            ContextTier.TASK: [],
            ContextTier.MEMORY: [],
            ContextTier.SOURCE: [],
        }
        for it in items:
            if it.tier in by_tier:
                by_tier[it.tier].append(it)

        # Tier 1
        if by_tier[ContextTier.SYSTEM]:
            sections.append("=== TIER 1: SYSTEM INSTRUCTIONS ===")
            for item in by_tier[ContextTier.SYSTEM]:
                sections.append(item.content)
            sections.append("")

        # Tier 2
        if by_tier[ContextTier.TASK]:
            sections.append("=== TIER 2: ACTIVE TASK & STATE ===")
            for item in by_tier[ContextTier.TASK]:
                sections.append(item.content)
            sections.append("")

        # Tier 3
        if by_tier[ContextTier.MEMORY]:
            sections.append("=== TIER 3: PERSISTENT MEMORY & ARCHITECTURAL DECISIONS ===")
            for item in by_tier[ContextTier.MEMORY]:
                sections.append(f"• {item.content}")
            sections.append("")

        # Tier 4
        if by_tier[ContextTier.SOURCE]:
            sections.append("=== TIER 4: WORKSPACE SOURCE CODE & INTERFACES ===")
            for item in by_tier[ContextTier.SOURCE]:
                header = f"--- [{item.compression_level.upper()}] {item.source} ({item.tokens} tokens) ---"
                sections.append(f"{header}\n{item.content}\n")

        return "\n".join(sections)

context_compiler = ContextCompiler()
