import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import BaseModel, Field

class EventType(str, Enum):
    AGENT_STARTED = "agent.started"
    AGENT_THINKING = "agent.thinking"
    MESSAGE_CREATED = "message.created"
    TOOL_REQUESTED = "tool.requested"
    TOOL_APPROVAL_REQUIRED = "tool.approval_required"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    FILE_READ = "file.read"
    FILE_CHANGED = "file.changed"
    TERMINAL_STARTED = "terminal.started"
    TERMINAL_OUTPUT = "terminal.output"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    CONTEXT_GENERATED = "context.generated"
    AGENT_PAUSED = "agent.paused"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

class EventEnvelope(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    agent_id: str
    session_id: str = "default_session"
    type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
