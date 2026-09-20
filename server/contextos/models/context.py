import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ContextTier(str, Enum):
    SYSTEM = "system"       # 15% System instructions & role prompt
    TASK = "task"           # 10% Current task, acceptance criteria & progress
    MEMORY = "memory"       # 15% Persistent memory items, ADRs & failure learnings
    SOURCE = "source"       # 50% Active workspace files, AST signatures & test context
    BUFFER = "buffer"       # 10% Safety reserve buffer

class ContextBudget(BaseModel):
    total_budget: int = 8000
    system_budget: int = 1200   # 15%
    task_budget: int = 800      # 10%
    memory_budget: int = 1200   # 15%
    source_budget: int = 4000   # 50%
    buffer_budget: int = 800    # 10%

    @classmethod
    def from_total(cls, total: int) -> "ContextBudget":
        system = int(total * 0.15)
        task = int(total * 0.10)
        memory = int(total * 0.15)
        source = int(total * 0.50)
        buffer = total - (system + task + memory + source)
        return cls(
            total_budget=total,
            system_budget=system,
            task_budget=task,
            memory_budget=memory,
            source_budget=source,
            buffer_budget=buffer,
        )

class ContextItem(BaseModel):
    id: str = Field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    tier: ContextTier
    source: str  # file path, memory id, prompt name
    content: str
    tokens: int
    score: float = 1.0
    compression_level: str = "full"  # full, signatures, summary
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ContextBundle(BaseModel):
    id: str = Field(default_factory=lambda: f"bundle_{uuid.uuid4().hex[:10]}")
    intent: str
    budget: ContextBudget
    items: List[ContextItem] = Field(default_factory=list)
    tier_token_counts: Dict[str, int] = Field(default_factory=dict)
    total_tokens: int = 0
    candidate_tokens: int = 0
    tokens_avoided: int = 0
    reduction_ratio: float = 0.0
    compiled_prompt: str = ""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
