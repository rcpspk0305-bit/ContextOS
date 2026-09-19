# AIOS Context Engine API & Interface Specification

## 1. REST API (FastAPI Daemon)
Base URL: `http://localhost:8000/api/v1`

### Projects & Workspaces
- `GET /projects` — List registered local projects.
- `POST /projects` — Register a new local project workspace (`{ name, root_path }`).
- `GET /projects/{project_id}` — Get project metadata, active branch, and statistics.

### Tasks
- `GET /tasks?project_id={id}&status={status}` — List tasks with optional filtering.
- `POST /tasks` — Create a development task (`{ project_id, title, description, acceptance_criteria }`).
- `GET /tasks/{task_id}` — Get detailed task spec and execution history.
- `PATCH /tasks/{task_id}` — Update task details or mark complete.

### Agent Runs & Lifecycle Supervision
- `POST /agents/runs` — Start an agent run on a task (`{ task_id, agent_name, provider_name, config }`).
- `GET /agents/runs/{run_id}` — Get run status, current state, token metrics, and active checkpoint.
- `POST /agents/runs/{run_id}/pause` — Pause execution. If `supports_pause == False`, triggers `AWAITING_CHECKPOINT` sequence.
- `POST /agents/runs/{run_id}/resume` — Resume a paused run.
- `POST /agents/runs/{run_id}/cancel` — Cancel run with `SIGTERM`/`SIGKILL` to process group.
- `GET /agents/runs/{run_id}/events` — Fetch historical execution events and logs.

### Context & Code Intelligence
- `POST /context/packet` — Generate a 4-Tier ContextPacket (`{ task_id, token_ceiling, target_files }`).
- `GET /symbols/search?project_id={id}&query={q}` — Search Tree-sitter indexed symbols and signatures.

### Sessions & Checkpoints
- `GET /sessions/{session_id}/checkpoints` — List saved checkpoints for a session.
- `POST /sessions/{session_id}/checkpoints` — Create a manual checkpoint (`{ notes }`).
- `POST /sessions/checkpoints/{checkpoint_id}/resume` — Generate a Universal Handoff Envelope to resume in target provider.

### Analytics & Token Metrics
- `GET /analytics/tokens?project_id={id}&range={range}` — Fetch aggregated token usage, tokens avoided, and efficiency ratios.

---

## 2. WebSocket Realtime Event Bus
URL: `ws://localhost:8000/ws/v1/events`

### Client Subscription Message
```json
{
  "action": "subscribe",
  "project_id": "proj_123",
  "run_id": "run_456"
}
```

### Server Event Message Schema
```json
{
  "event_id": "evt_789",
  "timestamp": "2026-09-19T22:25:00Z",
  "run_id": "run_456",
  "type": "LOG" | "STATE_CHANGE" | "TOKEN_USAGE" | "TOOL_CALL" | "CHECKPOINT_SAVED" | "ERROR",
  "payload": {
    "state": "RUNNING",
    "stdout": "Running pytest tests/...",
    "prompt_tokens": 1200,
    "completion_tokens": 350
  }
}
```

---

## 3. Model Context Protocol (MCP) Server

AIOS runs a local MCP server over stdio or SSE (`http://localhost:8000/mcp/sse`), allowing external agents (Antigravity, Claude Code, Cursor, Codex) to query AIOS.

### MCP Resources
- `context://current` — Active 4-tier minimal context packet for the assigned task.
- `tasks://active` — Current active task specification, description, and acceptance criteria.
- `memory://project` — Project architectural constraints, rules, and known gotchas.
- `decisions://log` — Chronological log of recorded ADRs and micro-decisions.

### MCP Tools

#### `aios_get_context`
Retrieve the minimal 4-tier context packet for a task or query.
```json
{
  "name": "aios_get_context",
  "description": "Fetch minimal 4-tier context packet (task, target code, signatures, decisions) bounded by token budget.",
  "parameters": {
    "type": "object",
    "properties": {
      "task_id": { "type": "string" },
      "target_files": { "type": "array", "items": { "type": "string" } },
      "token_budget": { "type": "integer", "default": 4000 }
    }
  }
}
```

#### `aios_record_decision`
Record an architectural decision or technical learning into persistent memory.
```json
{
  "name": "aios_record_decision",
  "description": "Record an architectural decision or key insight to persistent project memory.",
  "parameters": {
    "type": "object",
    "properties": {
      "title": { "type": "string" },
      "rationale": { "type": "string" },
      "impacted_files": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["title", "rationale"]
  }
}
```

#### `aios_checkpoint_session`
Checkpoint the current working state and diff.
```json
{
  "name": "aios_checkpoint_session",
  "description": "Save an atomic session checkpoint with active uncommitted git diff and task progress.",
  "parameters": {
    "type": "object",
    "properties": {
      "notes": { "type": "string" },
      "completed_items": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["notes"]
  }
}
```

#### `aios_log_tokens`
Report token usage from external agent completions.
```json
{
  "name": "aios_log_tokens",
  "description": "Log prompt and completion token counts for auditable analytics.",
  "parameters": {
    "type": "object",
    "properties": {
      "prompt_tokens": { "type": "integer" },
      "completion_tokens": { "type": "integer" },
      "model": { "type": "string" }
    },
    "required": ["prompt_tokens", "completion_tokens"]
  }
}
```

---

## 4. Typer CLI (`aios`)

```bash
# Daemon & System Control
aios start                     # Start FastAPI daemon and MCP server in background
aios status                    # Show daemon status and running agents
aios stop                      # Stop daemon safely

# Project & Workspace
aios project init [PATH]       # Register current directory as an AIOS project
aios project list              # List registered projects

# Tasks & Runs
aios task create --title "..." # Create a development task
aios run <task-id> --agent codex # Execute task under supervision
aios pause <run-id>            # Gracefully pause or auto-checkpoint run
aios resume <run-id>           # Resume paused run
aios cancel <run-id>           # Terminate run and process group immediately

# Context & Memory
aios context inspect <task-id> # Display 4-tier context packet and token breakdown
aios memory list               # Display persistent project decisions and rules
aios checkpoint create         # Create manual snapshot of current git state
```
