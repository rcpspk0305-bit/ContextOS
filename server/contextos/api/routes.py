from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from contextos.models.agent import Agent, AgentRole, AgentPermissions
from contextos.models.approval import ApprovalRequest, ApprovalDecision
from contextos.models.event import EventEnvelope, EventType
from contextos.models.memory import (
    MemoryType,
    MemoryItem,
    DecisionRecord,
    Checkpoint,
    UniversalSessionEnvelope,
)
from contextos.models.context import ContextBundle
from contextos.runtime.supervisor import agent_runtime
from contextos.memory.engine import memory_engine
from contextos.memory.adapters import (
    CodexSessionAdapter,
    AGYSessionAdapter,
    GenericJsonSessionAdapter,
)
from contextos.context.compiler import context_compiler
from contextos.models.analytics import (
    TokenRecord,
    AnalyticsSummary,
    BreakdownItem,
    ComparisonSeries,
)
from contextos.analytics.engine import analytics_engine
import contextos.storage.db as db_mod

router = APIRouter(prefix="/api")

class CreateAgentRequest(BaseModel):
    name: str
    type: AgentRole = AgentRole.CODER
    provider: str = "OpenAI / Codex"
    model: str = "gpt-4o"
    task: str = ""
    context_budget: int = 8000

class MessageRequest(BaseModel):
    content: str

class ResolveApprovalRequest(BaseModel):
    decision: ApprovalDecision

# Health
@router.get("/health")
def get_health():
    with db_mod.db.get_connection() as conn:
        ts = conn.execute("SELECT datetime('now')").fetchone()[0]
    return {
        "status": "healthy",
        "service": "ContextOS Local Daemon",
        "version": "0.1.0",
        "timestamp": ts,
    }

# Agent Fleet Endpoints
@router.get("/agents", response_model=List[Agent])
def list_agents():
    return agent_runtime.list_agents()

@router.post("/agents", response_model=Agent)
def create_agent(req: CreateAgentRequest):
    return agent_runtime.create_agent(
        name=req.name,
        role=req.type,
        provider=req.provider,
        model=req.model,
        current_task=req.task,
        context_budget=req.context_budget,
    )

@router.get("/agents/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    agent = agent_runtime.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/agents/{agent_id}/start", response_model=Agent)
async def start_agent(agent_id: str):
    try:
        return await agent_runtime.start_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{agent_id}/pause", response_model=Agent)
async def pause_agent(agent_id: str):
    try:
        return await agent_runtime.pause_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{agent_id}/resume", response_model=Agent)
async def resume_agent(agent_id: str):
    try:
        return await agent_runtime.resume_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{agent_id}/stop", response_model=Agent)
async def stop_agent(agent_id: str):
    try:
        return await agent_runtime.stop_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{agent_id}/message")
async def send_agent_message(agent_id: str, req: MessageRequest):
    try:
        return await agent_runtime.send_message(agent_id, req.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/agents/{agent_id}/events", response_model=List[EventEnvelope])
def get_agent_events(agent_id: str, limit: int = Query(default=100, le=500)):
    return agent_runtime.get_events(agent_id=agent_id, limit=limit)

@router.get("/agents/{agent_id}/metrics")
def get_agent_metrics(agent_id: str):
    try:
        return agent_runtime.get_metrics(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Human-in-the-Loop Approvals Endpoints
@router.get("/approvals", response_model=List[ApprovalRequest])
def list_approvals(status: Optional[str] = None):
    return db_mod.db.list_approvals(status=status)

@router.post("/approvals/{approval_id}/resolve")
async def resolve_approval(approval_id: str, req: ResolveApprovalRequest):
    if req.decision == ApprovalDecision.REJECT:
        return await agent_runtime.reject_tool(approval_id)
    else:
        return await agent_runtime.approve_tool(approval_id, req.decision)

# Memory Engine Endpoints
class CreateMemoryRequest(BaseModel):
    content: str
    type: MemoryType = MemoryType.SEMANTIC
    project_id: str = "contextos"
    session_id: str = "default_session"
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class CreateDecisionRequest(BaseModel):
    title: str
    context: str
    decision: str
    consequences: str = ""
    status: str = "accepted"
    alternatives_considered: List[str] = []
    project_id: str = "contextos"
    session_id: str = "default_session"

class CreateCheckpointRequest(BaseModel):
    session_id: str
    agent_id: str
    state_summary: str
    active_task: str = ""
    modified_files: List[str] = []
    open_decisions: List[str] = []
    context_tokens_used: int = 0
    project_id: str = "contextos"
    metadata: Dict[str, Any] = {}

class ImportSessionRequest(BaseModel):
    source_agent: str  # codex, agy, generic
    data: Dict[str, Any]

@router.get("/memories", response_model=List[MemoryItem])
async def search_memories(
    query: Optional[str] = None,
    type: Optional[MemoryType] = None,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    return await memory_engine.recall(
        query=query,
        memory_type=type,
        project_id=project_id,
        session_id=session_id,
        tags=tags,
        limit=limit,
    )

@router.post("/memories", response_model=MemoryItem)
async def create_memory(req: CreateMemoryRequest):
    return await memory_engine.remember(
        content=req.content,
        memory_type=req.type,
        project_id=req.project_id,
        session_id=req.session_id,
        tags=req.tags,
        metadata=req.metadata,
    )

@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: str):
    success = memory_engine.forget(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "memory_id": memory_id}

@router.get("/decisions", response_model=List[DecisionRecord])
def list_decisions(
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    return memory_engine.get_decisions(project_id=project_id, session_id=session_id, limit=limit)

@router.post("/decisions", response_model=DecisionRecord)
def create_decision(req: CreateDecisionRequest):
    return memory_engine.record_decision(
        title=req.title,
        context=req.context,
        decision=req.decision,
        consequences=req.consequences,
        status=req.status,
        alternatives_considered=req.alternatives_considered,
        project_id=req.project_id,
        session_id=req.session_id,
    )

@router.post("/checkpoints", response_model=Checkpoint)
def create_checkpoint(req: CreateCheckpointRequest):
    return memory_engine.checkpoint(
        session_id=req.session_id,
        agent_id=req.agent_id,
        state_summary=req.state_summary,
        active_task=req.active_task,
        modified_files=req.modified_files,
        open_decisions=req.open_decisions,
        context_tokens_used=req.context_tokens_used,
        project_id=req.project_id,
        metadata=req.metadata,
    )

@router.get("/checkpoints/{checkpoint_id}", response_model=Checkpoint)
def get_checkpoint(checkpoint_id: str):
    chk = db_mod.db.get_checkpoint(checkpoint_id)
    if not chk:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return chk

@router.get("/checkpoints", response_model=List[Checkpoint])
def list_checkpoints(
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    return db_mod.db.list_checkpoints(project_id=project_id, session_id=session_id, limit=limit)

@router.post("/checkpoints/{checkpoint_id}/resume")
def resume_from_checkpoint(checkpoint_id: str):
    try:
        return memory_engine.resume(checkpoint_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/import", response_model=UniversalSessionEnvelope)
def import_session(req: ImportSessionRequest):
    source = req.source_agent.lower()
    if source == "codex":
        adapter = CodexSessionAdapter()
    elif source == "agy":
        adapter = AGYSessionAdapter()
    else:
        adapter = GenericJsonSessionAdapter()

    envelope = adapter.to_universal(req.data)
    db_mod.db.save_session_envelope(envelope)
    return envelope

@router.get("/sessions/{session_id}/envelope", response_model=UniversalSessionEnvelope)
def get_session_envelope(session_id: str):
    envelope = db_mod.db.get_session_envelope(session_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Session envelope not found")
    return envelope

# Context Engine Endpoints
class CompileContextRequest(BaseModel):
    intent: str
    active_task: str = ""
    session_id: str = "default_session"
    budget: int = 8000
    system_instructions: Optional[str] = None

@router.post("/context/compile", response_model=ContextBundle)
async def compile_context(req: CompileContextRequest):
    return await context_compiler.compile(
        intent=req.intent,
        active_task=req.active_task,
        session_id=req.session_id,
        budget=req.budget,
        system_instructions=req.system_instructions,
    )

@router.get("/context/metrics")
def get_context_metrics():
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

# Analytics & Token Telemetry Endpoints
class RecordTokenRequest(BaseModel):
    project_id: str = "contextos"
    session_id: str = "default_session"
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    provider: str = "OpenAI"
    model: str = "gpt-4o"
    candidate_tokens: int = 0
    selected_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    estimated: bool = True
    metadata: Dict[str, Any] = {}

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    return analytics_engine.get_summary(project_id=project_id, session_id=session_id)

@router.get("/analytics/breakdown", response_model=List[BreakdownItem])
def get_analytics_breakdown(
    by: str = Query(default="provider", pattern="^(provider|model|agent|project|session)$"),
    project_id: Optional[str] = None,
):
    return analytics_engine.get_breakdown(dimension=by, project_id=project_id)

@router.get("/analytics/comparison", response_model=ComparisonSeries)
def get_analytics_comparison(
    project_id: Optional[str] = None,
    limit: int = Query(default=15, le=100),
):
    return analytics_engine.get_comparison(project_id=project_id, limit=limit)

@router.post("/analytics/record", response_model=TokenRecord)
def record_token_event(req: RecordTokenRequest):
    return analytics_engine.record_event(
        project_id=req.project_id,
        session_id=req.session_id,
        agent_id=req.agent_id,
        task_id=req.task_id,
        provider=req.provider,
        model=req.model,
        candidate_tokens=req.candidate_tokens,
        selected_tokens=req.selected_tokens,
        output_tokens=req.output_tokens,
        cache_hit_tokens=req.cache_hit_tokens,
        estimated=req.estimated,
        metadata=req.metadata,
    )


