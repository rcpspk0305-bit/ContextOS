import pytest
import json
from pathlib import Path
from contextos.models.agent import AgentRole
from contextos.models.memory import MemoryType
from contextos.runtime.supervisor import agent_runtime
from contextos.memory.engine import memory_engine
from contextos.memory.adapters import CodexSessionAdapter, AGYSessionAdapter
from contextos.context.compiler import context_compiler
from contextos.analytics.engine import analytics_engine
from contextos.storage.db import db

@pytest.mark.asyncio
async def test_end_to_end_cross_agent_handoff(tmp_path):
    """
    Test end-to-end cross-agent handoff between Codex (Session A) and AGY (Session B).
    Session B must resume execution with ZERO raw conversation turn replay,
    using only ContextOS distilled memory, ADRs, and 4-tier context packet.
    """
    # 1. Agent A (Codex Coder) initiates Session A
    agent_a = agent_runtime.create_agent(
        name="Codex Core Developer",
        role=AgentRole.CODER,
        provider="OpenAI / Codex",
        model="gpt-4o",
        current_task="Implement database connection pooling & retry decorator",
        context_budget=8000,
    )
    assert agent_a.id is not None
    session_a_id = f"session_{agent_a.id}"

    # Agent A modifies code (simulated workspace file change)
    test_file = "server/contextos/storage/pool.py"
    modified_files = [test_file]

    # Agent A records an Architecture Decision Record (ADR)
    decision = memory_engine.record_decision(
        title="ADR-004: Database Connection Pool Exponential Backoff",
        context="High concurrent agent writes caused SQLite database locked warnings.",
        decision="Use exponential jitter backoff with max 5 retries and WAL mode.",
        consequences="Eliminates database locked errors during parallel fleet execution.",
        status="accepted",
        alternatives_considered=["Synchronous mutex", "In-memory mock database"],
        project_id="contextos",
        session_id=session_a_id,
    )
    assert decision.id is not None

    # Agent A stores semantic memory caveats
    mem = await memory_engine.remember(
        content="SQLite WAL mode requires pragma journal_mode=WAL on initial connection.",
        memory_type=MemoryType.DECISION,
        project_id="contextos",
        session_id=session_a_id,
        tags=["sqlite", "wal", "concurrency", "pool"],
    )
    assert mem.id is not None

    # Agent A checkpoints session state
    checkpoint_a = memory_engine.checkpoint(
        session_id=session_a_id,
        agent_id=agent_a.id,
        state_summary="Completed connection pool retry logic. Ready for test suite and review.",
        active_task="Implement database connection pooling & retry decorator",
        modified_files=modified_files,
        open_decisions=[decision.id],
        context_tokens_used=4200,
        project_id="contextos",
    )
    assert checkpoint_a.id is not None

    # Record token telemetry for Agent A
    tok_event_a = analytics_engine.record_event(
        project_id="contextos",
        session_id=session_a_id,
        agent_id=agent_a.id,
        task_id=agent_a.current_task,
        provider="OpenAI",
        model="gpt-4o",
        candidate_tokens=48000,
        selected_tokens=4200,
        output_tokens=850,
        estimated=True,
    )
    assert tok_event_a.tokens_avoided == 43800

    # Stop Agent A (Session A terminated)
    await agent_runtime.stop_agent(agent_a.id)

    # -------------------------------------------------------------
    # HANDOFF BOUNDARY: Agent B (Google Antigravity / AGY Reviewer)
    # Agent B starts with ZERO raw turns from Agent A.
    # -------------------------------------------------------------
    agent_b = agent_runtime.create_agent(
        name="Antigravity Senior Reviewer",
        role=AgentRole.REVIEWER,
        provider="Google / AGY",
        model="gemini-1.5-pro",
        current_task="Review and verify connection pool retry logic",
        context_budget=8000,
    )
    session_b_id = f"session_{agent_b.id}"

    # Agent B resumes strictly from Checkpoint A without turn replay
    resumption = memory_engine.resume(checkpoint_a.id)
    assert resumption["checkpoint"].id == checkpoint_a.id
    assert resumption["checkpoint"].active_task == "Implement database connection pooling & retry decorator"
    assert test_file in resumption["checkpoint"].modified_files
    assert len(resumption["decisions"]) >= 1
    assert any(d.id == decision.id for d in resumption["decisions"])

    # Agent B compiles targeted 4-tier context based on resumed task
    compiled_context = await context_compiler.compile(
        intent=f"Review modified files {modified_files} and verify ADR-004 compliance",
        active_task=resumption["resumed_task"],
        session_id=session_b_id,
        budget=8000,
    )
    assert compiled_context.total_tokens <= 8000
    assert compiled_context.candidate_tokens > compiled_context.total_tokens
    assert compiled_context.tokens_avoided > 0

    # Agent B performs review milestone and commits second checkpoint
    checkpoint_b = memory_engine.checkpoint(
        session_id=session_b_id,
        agent_id=agent_b.id,
        state_summary="Reviewed connection pool implementation. ADR-004 verified and approved.",
        active_task="Connection pool implementation approved",
        modified_files=modified_files,
        open_decisions=[],
        context_tokens_used=compiled_context.total_tokens,
        project_id="contextos",
        metadata={"prior_checkpoint_id": checkpoint_a.id, "verified_by": "AGY"},
    )
    assert checkpoint_b.id is not None
    assert checkpoint_b.metadata["prior_checkpoint_id"] == checkpoint_a.id

    # Record Agent B telemetry
    tok_event_b = analytics_engine.record_event(
        project_id="contextos",
        session_id=session_b_id,
        agent_id=agent_b.id,
        task_id="Review and verify connection pool retry logic",
        provider="Google",
        model="gemini-1.5-pro",
        candidate_tokens=compiled_context.candidate_tokens,
        selected_tokens=compiled_context.total_tokens,
        output_tokens=620,
        estimated=True,
    )
    assert tok_event_b.tokens_avoided > 0

    # Verify both checkpoints exist longitudinally in DB
    all_checkpoints = db.list_checkpoints(project_id="contextos")
    chk_ids = [c.id for c in all_checkpoints]
    assert checkpoint_a.id in chk_ids
    assert checkpoint_b.id in chk_ids
