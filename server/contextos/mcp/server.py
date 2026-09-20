import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP

from contextos.config import settings
from contextos.models.agent import AgentRole, AgentStatus
from contextos.models.memory import MemoryType
from contextos.models.event import EventType, EventEnvelope
from contextos.context.compiler import context_compiler
from contextos.memory.engine import memory_engine
from contextos.memory.adapters import (
    CodexSessionAdapter,
    AGYSessionAdapter,
    GenericJsonSessionAdapter,
)
from contextos.runtime.supervisor import agent_runtime
from contextos.runtime.event_bus import event_bus
import contextos.storage.db as db_mod

def create_mcp_server() -> FastMCP:
    """Creates and configures the ContextOS FastMCP v2 server instance with all 17 tools."""
    mcp = FastMCP(
        "contextos",
        instructions=(
            "ContextOS AIOS MCP Server: Provides local-first context compilation, "
            "persistent memory, ADR records, session continuity, and agent fleet control."
        ),
    )

    # 1. project_get
    @mcp.tool()
    async def project_get(project_id: str = "contextos") -> Dict[str, Any]:
        """Retrieve ContextOS project configuration, root workspace boundary, and operational limits."""
        return {
            "project_id": project_id,
            "workspace_root": str(settings.workspace_root),
            "db_path": str(settings.db_path),
            "host": settings.HOST,
            "port": settings.PORT,
            "command_timeout_seconds": settings.COMMAND_TIMEOUT_SECONDS,
            "max_output_bytes": settings.MAX_OUTPUT_BYTES,
        }

    # 2. project_status
    @mcp.tool()
    async def project_status(project_id: str = "contextos") -> Dict[str, Any]:
        """Retrieve current project status including active branch, uncommitted files, agents, and memories."""
        branch = "unknown"
        modified_count = 0
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(settings.workspace_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                branch = res.stdout.strip()

            diff_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(settings.workspace_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if diff_res.returncode == 0:
                modified_count = len([l for l in diff_res.stdout.splitlines() if l.strip()])
        except Exception:
            pass

        agents = db_mod.db.list_agents()
        active_agents = len([a for a in agents if a.status == AgentStatus.RUNNING])
        memories = db_mod.db.search_memories(project_id=project_id, limit=500)
        decisions = db_mod.db.list_decisions(project_id=project_id, limit=100)

        return {
            "project_id": project_id,
            "git_branch": branch,
            "uncommitted_files_count": modified_count,
            "total_agents": len(agents),
            "active_agents": active_agents,
            "total_memories": len(memories),
            "total_decisions": len(decisions),
            "status": "healthy",
        }

    # 3. context_build
    @mcp.tool()
    async def context_build(
        intent: str,
        active_task: str = "",
        budget: int = 8000,
        session_id: str = "default_session",
    ) -> Dict[str, Any]:
        """Compile a 4-tier token-budgeted context bundle for the specified user intent and task."""
        bundle = await context_compiler.compile(
            intent=intent,
            active_task=active_task,
            budget=budget,
            session_id=session_id,
        )
        return {
            "bundle_id": bundle.id,
            "total_tokens": bundle.total_tokens,
            "candidate_tokens": bundle.candidate_tokens,
            "tokens_avoided": bundle.tokens_avoided,
            "reduction_ratio": bundle.reduction_ratio,
            "tier_token_counts": bundle.tier_token_counts,
            "compiled_prompt": bundle.compiled_prompt,
        }

    # 4. context_search
    @mcp.tool()
    async def context_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search codebase files and memory records matching the query string."""
        mem_results = await memory_engine.recall(query=query, limit=limit)
        results = [
            {
                "id": m.id,
                "type": m.type.value,
                "content": m.content,
                "tags": m.tags,
                "source": "memory",
            }
            for m in mem_results
        ]
        return results

    # 5. memory_search
    @mcp.tool()
    async def memory_search(query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search persistent semantic, episodic, task, and failure memories."""
        m_type = MemoryType(memory_type) if memory_type else None
        items = await memory_engine.recall(query=query, memory_type=m_type, limit=limit)
        return [item.model_dump(mode="json") for item in items]

    # 6. memory_remember
    @mcp.tool()
    async def memory_remember(
        content: str,
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Persist a new learning, concept, failure pattern, or repo fact to persistent memory."""
        m_type = MemoryType(memory_type) if memory_type else MemoryType.SEMANTIC
        item = await memory_engine.remember(
            content=content,
            memory_type=m_type,
            tags=tags or [],
        )
        return item.model_dump(mode="json")

    # 7. memory_decision_add
    @mcp.tool()
    async def memory_decision_add(
        title: str,
        context: str,
        decision: str,
        consequences: str = "",
        alternatives: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Record an Architecture Decision Record (ADR) into persistent project memory."""
        adr = memory_engine.record_decision(
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives_considered=alternatives or [],
        )
        return adr.model_dump(mode="json")

    # 8. session_checkpoint
    @mcp.tool()
    async def session_checkpoint(
        session_id: str,
        agent_id: str,
        state_summary: str,
        active_task: str = "",
        modified_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a state checkpoint snapshot for session continuity without conversation turn replay."""
        chk = memory_engine.checkpoint(
            session_id=session_id,
            agent_id=agent_id,
            state_summary=state_summary,
            active_task=active_task,
            modified_files=modified_files or [],
        )
        return chk.model_dump(mode="json")

    # 9. session_resume
    @mcp.tool()
    async def session_resume(checkpoint_id_or_session_id: str) -> Dict[str, Any]:
        """Reconstitute active task state, modified files, and open decisions from a checkpoint."""
        resumption = memory_engine.resume(checkpoint_id_or_session_id)
        # Convert Pydantic objects to json dicts
        resumption["checkpoint"] = resumption["checkpoint"].model_dump(mode="json")
        resumption["decisions"] = [d.model_dump(mode="json") for d in resumption["decisions"]]
        return resumption

    # 10. session_import
    @mcp.tool()
    async def session_import(source_agent: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import external conversation turn formats (Codex, AGY, or Generic) into a Universal Envelope."""
        source = source_agent.lower()
        if source == "codex":
            adapter = CodexSessionAdapter()
        elif source == "agy":
            adapter = AGYSessionAdapter()
        else:
            adapter = GenericJsonSessionAdapter()

        envelope = adapter.to_universal(session_data)
        db_mod.db.save_session_envelope(envelope)
        return envelope.model_dump(mode="json")

    # 11. agent_list
    @mcp.tool()
    async def agent_list() -> List[Dict[str, Any]]:
        """List all agents in the ContextOS fleet, their roles, models, and lifecycle statuses."""
        agents = agent_runtime.list_agents()
        return [a.model_dump(mode="json") for a in agents]

    # 12. agent_status
    @mcp.tool()
    async def agent_status(agent_id: str) -> Dict[str, Any]:
        """Retrieve detailed status, active task, token metrics, and runtime for a specific agent."""
        agent = agent_runtime.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found")
        metrics = agent_runtime.get_metrics(agent_id)
        return {
            "agent": agent.model_dump(mode="json"),
            "metrics": metrics,
        }

    # 13. agent_delegate
    @mcp.tool()
    async def agent_delegate(from_agent_id: str, to_role: str, task: str) -> Dict[str, Any]:
        """Delegate a subtask to a new specialized agent (e.g. from Coder to Reviewer or Architect)."""
        role_key = to_role.upper()
        role_enum = AgentRole[role_key] if role_key in AgentRole.__members__ else AgentRole.CODER
        sub_agent = agent_runtime.create_agent(
            name=f"Delegated {to_role.capitalize()} Agent",
            role=role_enum,
            current_task=task,
        )
        await agent_runtime.start_agent(sub_agent.id)

        # Log delegation event
        await event_bus.emit(
            EventEnvelope(
                agent_id=from_agent_id,
                session_id=sub_agent.session_id,
                type=EventType.MESSAGE_CREATED,
                payload={
                    "delegated_to": sub_agent.id,
                    "target_role": role_enum.value,
                    "task": task,
                },
            )
        )
        return {
            "delegation_status": "delegated",
            "delegated_agent_id": sub_agent.id,
            "agent": sub_agent.model_dump(mode="json"),
        }

    # 14. task_get
    @mcp.tool()
    async def task_get(agent_id: str) -> Dict[str, Any]:
        """Get the current task progress, completed milestones, and remaining checklist items."""
        tracker = agent_runtime._active_task_trackers.get(agent_id)
        if tracker:
            return tracker.get_progress_summary()
        agent = agent_runtime.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found")
        return {
            "task_description": agent.current_task,
            "total_items": 0,
            "completed_count": 0,
            "current_item": agent.current_task,
            "remaining_items": [],
            "all_done": False,
        }

    # 15. task_update
    @mcp.tool()
    async def task_update(agent_id: str, item_id: str, completed: bool = True) -> Dict[str, Any]:
        """Update checklist milestone status for an agent's active task tracker."""
        tracker = agent_runtime._active_task_trackers.get(agent_id)
        if not tracker:
            raise ValueError(f"No active task tracker found for agent '{agent_id}'")
        if completed:
            msg = tracker.mark_completed(item_id)
            return {"status": "updated", "message": msg, "progress": tracker.get_progress_summary()}
        return {"status": "unchanged", "progress": tracker.get_progress_summary()}

    # 16. git_diff_summary
    @mcp.tool()
    async def git_diff_summary() -> Dict[str, Any]:
        """Summarize unstaged and staged workspace changes using git status and diff statistics."""
        stat_output = ""
        status_output = ""
        try:
            diff_res = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=str(settings.workspace_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if diff_res.returncode == 0:
                stat_output = diff_res.stdout.strip()

            status_res = subprocess.run(
                ["git", "status", "-s"],
                cwd=str(settings.workspace_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if status_res.returncode == 0:
                status_output = status_res.stdout.strip()
        except Exception as e:
            stat_output = str(e)

        return {
            "diff_stat": stat_output,
            "status_short": status_output,
            "has_uncommitted_changes": bool(status_output),
        }

    # 17. token_metrics
    @mcp.tool()
    async def token_metrics() -> Dict[str, Any]:
        """Retrieve token savings telemetry, tokens avoided, and context reduction ratios."""
        events = db_mod.db.list_events(limit=500)
        ctx_events = [e for e in events if e.type == EventType.CONTEXT_GENERATED]
        total_candidate = sum(e.payload.get("candidate_tokens", 0) for e in ctx_events)
        total_selected = sum(e.payload.get("total_tokens", 0) for e in ctx_events)
        total_avoided = sum(e.payload.get("tokens_avoided", 0) for e in ctx_events)
        overall_ratio = round((total_avoided / total_candidate) * 100.0, 2) if total_candidate > 0 else 0.0

        return {
            "total_compilations": len(ctx_events),
            "total_candidate_tokens": total_candidate,
            "total_selected_tokens": total_selected,
            "total_tokens_avoided": total_avoided,
            "average_reduction_ratio": overall_ratio,
            "estimated": True,
        }

    return mcp

mcp_server = create_mcp_server()
