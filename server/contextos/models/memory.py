import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    DECISION = "decision"
    TASK = "task"
    FAILURE = "failure"
    CODE_REFERENCE = "code_reference"

class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    project_id: str = "contextos"
    session_id: str = "default_session"
    type: MemoryType = MemoryType.SEMANTIC
    content: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    relevance_score: Optional[float] = None

class DecisionRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"adr_{uuid.uuid4().hex[:10]}")
    project_id: str = "contextos"
    session_id: str = "default_session"
    title: str
    context: str
    decision: str
    consequences: str = ""
    status: str = "accepted"  # proposed, accepted, deprecated, superseded
    alternatives_considered: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Checkpoint(BaseModel):
    id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:12]}")
    project_id: str = "contextos"
    session_id: str = "default_session"
    agent_id: str = "ag_default"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state_summary: str
    active_task: str = ""
    modified_files: List[str] = Field(default_factory=list)
    open_decisions: List[str] = Field(default_factory=list)
    context_tokens_used: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Universal Session Handoff Envelopes (adapted from mem0ai/openmemory Apache-2.0)
class UniversalTurn(BaseModel):
    id: str = Field(default_factory=lambda: f"turn_{uuid.uuid4().hex[:8]}")
    role: str  # user, assistant, system, tool
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    tokens: Optional[int] = None

class UniversalSessionEnvelope(BaseModel):
    id: str = Field(default_factory=lambda: f"env_{uuid.uuid4().hex[:12]}")
    session_id: str
    source_agent: str  # codex, agy, claude, generic
    title: str = "ContextOS Session Snapshot"
    summary: str = ""
    turns: List[UniversalTurn] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
