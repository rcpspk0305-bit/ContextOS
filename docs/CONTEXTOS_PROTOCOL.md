# ContextOS — Universal Envelope & Interoperability Protocol Specification

**Specification Version:** 1.0.0-RFC  
**MIME Type:** `application/vnd.contextos.envelope+json`  

---

## 1. Scope & Objective

The ContextOS Protocol defines standardized, interoperable data contracts for AI agent lifecycle events, state checkpoints, token-partitioned context bundles, and human-in-the-loop approvals.

---

## 2. Event Envelope Schema (`EventEnvelope`)

All state transitions, tool invocations, and agent actions publish normalized event envelopes over the WebSocket bus (`/ws/events`) and persist into SQLite:

```json
{
  "id": "evt_491a0c7b2e",
  "agent_id": "ag_coder_01",
  "session_id": "session_alpha",
  "type": "tool.approval_required",
  "timestamp": "2026-09-20T10:00:00.000000Z",
  "payload": {
    "tool_name": "TerminalTool",
    "command": "git push origin main",
    "risk_level": "CRITICAL",
    "approval_id": "appr_7f9b2d01"
  }
}
```

### Standard Event Types
- `agent.started` / `agent.paused` / `agent.resumed` / `agent.stopped`
- `tool.requested` / `tool.approval_required` / `tool.completed` / `tool.failed`
- `context.generated`
- `memory.remembered` / `decision.recorded`
- `checkpoint.created` / `session.resumed`

---

## 3. Session Checkpoint Schema (`Checkpoint`)

State snapshots serialize execution context to enable resumption across sessions and models without raw turn replays:

```json
{
  "id": "chk_e62eed03b2d3",
  "project_id": "contextos",
  "session_id": "session_alpha",
  "agent_id": "ag_coder_01",
  "timestamp": "2026-09-20T10:15:30.000000Z",
  "state_summary": "Implemented database connection pooling with WAL mode and jitter backoff retry decorator.",
  "active_task": "Implement database connection pooling & retry decorator",
  "modified_files": [
    "server/contextos/storage/db.py",
    "server/contextos/storage/pool.py"
  ],
  "open_decisions": [
    "adr_6f2e0f8d20"
  ],
  "context_tokens_used": 4350,
  "metadata": {
    "git_branch": "main",
    "tests_status": "PASSING"
  }
}
```

---

## 4. Architecture Decision Record Schema (`DecisionRecord`)

```json
{
  "id": "adr_6f2e0f8d20",
  "project_id": "contextos",
  "session_id": "session_alpha",
  "title": "ADR-004: Database Connection Pool Exponential Backoff",
  "context": "High concurrent agent writes caused SQLite database locked contention.",
  "decision": "Use exponential jitter backoff with max 5 retries and WAL journal mode.",
  "consequences": "Eliminates database locked errors during parallel fleet execution.",
  "status": "accepted",
  "alternatives_considered": [
    "Synchronous mutex",
    "In-memory mock database"
  ],
  "created_at": "2026-09-20T10:10:00.000000Z"
}
```

---

## 5. Token-Budgeted Context Bundle Schema (`ContextBundle`)

```json
{
  "id": "ctx_bundle_3910ab",
  "intent": "Verify modified files and validate ADR-004 compliance",
  "active_task": "Implement database connection pooling & retry decorator",
  "session_id": "session_beta",
  "budget": 8000,
  "total_tokens": 4075,
  "candidate_tokens": 129725,
  "tokens_avoided": 125650,
  "reduction_ratio": 96.86,
  "tiers": {
    "system_instructions": 120,
    "active_task": 185,
    "memory_and_decisions": 650,
    "source_files": 3120,
    "buffer": 3925
  },
  "source_files": [
    {
      "path": "server/contextos/storage/pool.py",
      "tokens": 420,
      "is_ast_compressed": true,
      "relevance_score": 0.98
    }
  ],
  "decisions": ["adr_6f2e0f8d20"],
  "memories": ["mem_16a2b9dd24fb"]
}
```

---

## 6. Human Approval Request & Decision Schema

```json
{
  "id": "appr_7f9b2d01",
  "agent_id": "ag_coder_01",
  "session_id": "session_alpha",
  "action_type": "shell_command",
  "action_name": "TerminalTool",
  "command": "git push origin main",
  "arguments": { "command": "git push origin main" },
  "risk_level": "CRITICAL",
  "affected_resource": "git:main",
  "reason": "Pushing unreviewed code to remote main branch.",
  "timestamp": "2026-09-20T10:00:00.000000Z",
  "status": "PENDING"
}
```

Resolutions are posted via `POST /api/approvals/{id}/resolve` with:
```json
{
  "decision": "APPROVE_ONCE" // "APPROVE_ONCE" | "APPROVE_SESSION" | "REJECT"
}
```
