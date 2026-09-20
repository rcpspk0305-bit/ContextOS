from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class TokenRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"tok_{uuid.uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    project_id: str = "contextos"
    session_id: str = "default_session"
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    provider: str = "OpenAI"
    model: str = "gpt-4o"
    candidate_tokens: int = 0
    selected_tokens: int = 0
    output_tokens: int = 0
    tokens_avoided: int = 0
    cache_hit_tokens: int = 0
    cost_without_usd: float = 0.0
    cost_with_usd: float = 0.0
    cost_saved_usd: float = 0.0
    bytes_avoided: int = 0
    estimated: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AnalyticsSummary(BaseModel):
    total_events: int = 0
    total_candidate_tokens: int = 0
    total_selected_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens_avoided: int = 0
    overall_reduction_ratio: float = 0.0
    bytes_not_transmitted: int = 0
    total_cost_without_usd: float = 0.0
    total_cost_with_usd: float = 0.0
    cost_saved_usd: float = 0.0
    cache_hits: int = 0
    estimated_percentage: float = 100.0
    provider_reported_events: int = 0
    estimated_events: int = 0

class BreakdownItem(BaseModel):
    dimension: str
    key: str
    count: int = 0
    candidate_tokens: int = 0
    selected_tokens: int = 0
    output_tokens: int = 0
    tokens_avoided: int = 0
    reduction_ratio: float = 0.0
    cost_without_usd: float = 0.0
    cost_with_usd: float = 0.0
    cost_saved_usd: float = 0.0

class ComparisonDataPoint(BaseModel):
    label: str
    timestamp: Optional[str] = None
    candidate_tokens: int = 0
    selected_tokens: int = 0
    tokens_avoided: int = 0
    cost_without_usd: float = 0.0
    cost_with_usd: float = 0.0
    cost_saved_usd: float = 0.0
    reduction_ratio: float = 0.0

class ComparisonSeries(BaseModel):
    data_points: List[ComparisonDataPoint] = Field(default_factory=list)
    cumulative_candidate_tokens: int = 0
    cumulative_selected_tokens: int = 0
    cumulative_tokens_avoided: int = 0
    cumulative_cost_without_usd: float = 0.0
    cumulative_cost_with_usd: float = 0.0
    cumulative_cost_saved_usd: float = 0.0
    overall_reduction_ratio: float = 0.0
    bytes_not_transmitted: int = 0
