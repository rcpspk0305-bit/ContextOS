import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ApprovalDecision(str, Enum):
    APPROVE_ONCE = "APPROVE_ONCE"
    APPROVE_SESSION = "APPROVE_SESSION"
    REJECT = "REJECT"

class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"appr_{uuid.uuid4().hex[:12]}")
    agent_id: str
    session_id: str = "default_session"
    action_type: str
    action_name: str
    command: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel
    affected_resource: str
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "PENDING"  # PENDING, APPROVED_ONCE, APPROVED_SESSION, REJECTED
