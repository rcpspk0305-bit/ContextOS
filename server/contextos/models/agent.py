from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class AgentRole(str, Enum):
    PLANNER = "PLANNER"
    CODER = "CODER"
    REVIEWER = "REVIEWER"
    RESEARCHER = "RESEARCHER"
    TESTER = "TESTER"

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

class AgentPermissions(BaseModel):
    can_execute_shell: bool = False
    can_edit_files: bool = True
    can_git_commit: bool = False
    can_network: bool = False

class TokenUsage(BaseModel):
    candidate_tokens: int = 0
    selected_tokens: int = 0
    excluded_tokens: int = 0
    estimated_tokens_avoided: int = 0
    cache_hits: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    reused_cached_tokens: int = 0

class Agent(BaseModel):
    id: str
    name: str
    role: AgentRole
    provider: str
    model: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: str = ""
    project_id: str = "contextos"
    session_id: str = "default_session"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context_budget: int = 8000
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    permissions: AgentPermissions = Field(default_factory=AgentPermissions)
    runtime_seconds: int = 0
