from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from contextos.models.memory import (
    MemoryType,
    MemoryItem,
    DecisionRecord,
    Checkpoint,
    UniversalSessionEnvelope,
)
from contextos.models.event import EventEnvelope, EventType
import contextos.storage.db as db_mod
from contextos.runtime.event_bus import event_bus

class MemoryEngine:
    """
    ContextOS Memory Engine.
    Provides semantic, episodic, decision, task, failure, and code_reference memory,
    plus session checkpointing and continuity without full conversation replays.
    """

    def __init__(self):
        pass

    @property
    def db(self):
        return db_mod.db

    # 1. Remember
    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        project_id: str = "contextos",
        session_id: str = "default_session",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        item = MemoryItem(
            project_id=project_id,
            session_id=session_id,
            type=memory_type,
            content=content,
            tags=tags or [],
            metadata=metadata or {},
        )
        self.db.save_memory(item)

        # Emit memory write event
        await event_bus.emit(
            EventEnvelope(
                agent_id="system",
                session_id=session_id,
                type=EventType.MEMORY_WRITE,
                payload={
                    "memory_id": item.id,
                    "type": item.type.value,
                    "content_length": len(item.content),
                    "tags": item.tags,
                },
            )
        )
        return item

    # 2. Recall / Search
    async def recall(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[MemoryItem]:
        items = self.db.search_memories(
            query=query,
            memory_type=memory_type,
            project_id=project_id,
            session_id=session_id,
            tags=tags,
            limit=limit,
        )

        # Emit memory read event
        await event_bus.emit(
            EventEnvelope(
                agent_id="system",
                session_id=session_id or "default_session",
                type=EventType.MEMORY_READ,
                payload={
                    "query": query,
                    "type": memory_type.value if memory_type else None,
                    "results_count": len(items),
                },
            )
        )
        return items

    # 3. Forget
    def forget(self, memory_id: str) -> bool:
        return self.db.delete_memory(memory_id)

    # 4. Record Decision (ADR)
    def record_decision(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str = "",
        status: str = "accepted",
        alternatives_considered: Optional[List[str]] = None,
        project_id: str = "contextos",
        session_id: str = "default_session",
    ) -> DecisionRecord:
        record = DecisionRecord(
            project_id=project_id,
            session_id=session_id,
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            status=status,
            alternatives_considered=alternatives_considered or [],
        )
        self.db.save_decision(record)
        return record

    def get_decisions(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[DecisionRecord]:
        return self.db.list_decisions(project_id=project_id, session_id=session_id, limit=limit)

    # 5. Checkpoint & Continuity Resumption
    def checkpoint(
        self,
        session_id: str,
        agent_id: str,
        state_summary: str,
        active_task: str = "",
        modified_files: Optional[List[str]] = None,
        open_decisions: Optional[List[str]] = None,
        context_tokens_used: int = 0,
        project_id: str = "contextos",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        chk = Checkpoint(
            project_id=project_id,
            session_id=session_id,
            agent_id=agent_id,
            state_summary=state_summary,
            active_task=active_task,
            modified_files=modified_files or [],
            open_decisions=open_decisions or [],
            context_tokens_used=context_tokens_used,
            metadata=metadata or {},
        )
        self.db.save_checkpoint(chk)
        return chk

    def resume(self, checkpoint_id_or_session_id: str) -> Dict[str, Any]:
        """
        Reconstitutes active task context from a checkpoint without raw conversation replays.
        """
        # 1. Try finding directly by checkpoint ID
        chk = self.db.get_checkpoint(checkpoint_id_or_session_id)
        if not chk:
            # 2. Try finding latest checkpoint for the session
            checkpoints = self.db.list_checkpoints(session_id=checkpoint_id_or_session_id, limit=1)
            if checkpoints:
                chk = checkpoints[0]

        if not chk:
            raise ValueError(f"No checkpoint found for '{checkpoint_id_or_session_id}'")

        decisions = self.get_decisions(project_id=chk.project_id, session_id=chk.session_id)

        return {
            "checkpoint": chk,
            "decisions": decisions,
            "resumed_task": chk.active_task,
            "state_summary": chk.state_summary,
            "modified_files": chk.modified_files,
            "open_decisions": chk.open_decisions,
            "context_tokens_used": chk.context_tokens_used,
            "instructions": f"Resuming work on '{chk.active_task}'. Current state: {chk.state_summary}. Modified files: {chk.modified_files}.",
        }

    # 6. Verify File References (deleted/missing file handling)
    def verify_file_references(self, memory_items: List[MemoryItem], workspace_root: Path) -> List[Dict[str, Any]]:
        results = []
        for item in memory_items:
            file_path_str = item.metadata.get("file_path") or item.metadata.get("path")
            if not file_path_str:
                results.append({"memory_id": item.id, "has_file": False, "exists": True})
                continue

            full_path = (workspace_root / file_path_str).resolve()
            exists = full_path.exists()

            if not exists:
                item.metadata["file_exists"] = False
                item.metadata["status"] = "file_missing"
                self.db.save_memory(item)

            results.append({
                "memory_id": item.id,
                "file_path": file_path_str,
                "exists": exists,
                "status": "valid" if exists else "file_missing",
            })
        return results

memory_engine = MemoryEngine()
