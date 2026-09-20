# ContextOS — Master Implementation Plan

**Date:** 2026-09-20  
**Status:** Approved Roadmap  
**Execution Style:** Phased, Test-Driven Development (TDD) with Human Approval Gates

---

## Roadmap Overview

```text
Phase 1: Forensics & OSS Plan (Prompt 1) [CURRENT]
   |
   v
Phase 2: AIOS Web Control Center (Prompt 2)
   |
   v
Phase 3: Agent Runtime & Control API (Prompt 3)
   |
   v
Phase 4: ContextOS Memory Engine (Prompt 4)
   |
   v
Phase 5: Token-Aware Context Engine (Prompt 5)
   |
   v
Phase 6: Model Context Protocol (MCP) Server (Prompt 6)
   |
   v
Phase 7: Analytics & Token Savings Dashboard (Prompt 7)
   |
   v
Phase 8: AGY & Codex Client Interoperability (Prompt 8)
   |
   v
Phase 9: Complete AIOS Interaction Flow (Prompt 9)
   |
   v
Phase 10: End-to-End Verification with Screenshot Proof (Prompt 10)
   |
   v
Phase 11: Final Architecture Audit & Documentation (Prompt 11)
```

---

## Detailed Phase Breakdown

### Phase 1: Forensics & OSS Reuse Blueprint (AGY)
- **Goal:** Conduct forensic workspace analysis, evaluate candidate OSS repositories, create architectural documents, and set up `.gitignore` and `THIRD_PARTY_REUSE.md`.
- **Deliverables:**
  - `docs/CURRENT_ARCHITECTURE.md`
  - `docs/OSS_REUSE_PLAN.md`
  - `docs/TARGET_ARCHITECTURE.md`
  - `docs/IMPLEMENTATION_PLAN.md`
  - `THIRD_PARTY_REUSE.md`
  - `.gitignore`
- **Verification:** Clean git status, strict license compliance verified, no scaffolding pollution.

### Phase 2: AIOS Web Control Center (CODEX / AGY)
- **Goal:** Build the desktop-first AIOS Control Center using `shadcn/ui`, `assistant-ui`, and `assistant-ui/tool-ui`.
- **Pages & Views:**
  - `/dashboard`: Running agents, active project, git branch, tokens, avoided context, MCP status.
  - `/agents`: Agent fleet cards, status indicators, start/pause/resume/stop/inspect actions.
  - `/agents/[id]`: Detail tabs (Conversation, Activity, Tools, Memory, Context, Files, Terminal, Diff, Metrics).
  - `/sessions`: Longitudinal session list and checkpoint inspection.
  - `/memory`: Semantic, episodic, decision, failure records.
  - `/context`: Candidate vs selected context inspector with token budgets.
  - `/mcp`: Connected clients, tools, and resources.
  - `/analytics`: Token metrics over time, reduction ratios, model breakdown.
  - `/settings`: Project boundary configuration, model provider keys, approval policies.
- **Verification:** Type checking (`tsc`), ESLint, responsive layout test, theme toggle.

### Phase 3: Agent Runtime & Control API (CODEX)
- **Goal:** Implement the backend `AgentRuntime`, process supervisor, and REST/WebSocket API daemon using FastAPI.
- **Components:**
  - `AgentRuntime`: `create_agent()`, `start_agent()`, `send_message()`, `pause_agent()`, `resume_agent()`, `stop_agent()`, `approve_tool()`, `reject_tool()`.
  - OpenHands-adapted tools: `TerminalTool`, `FileEditorTool`, `TaskTrackerTool`.
  - Workspace path jailing and OS process group management.
  - Normalized event bus and SQLite persistence.
- **Verification:** Unit tests and integration test: Create Agent $\to$ Assign Task $\to$ Approval Gate Triggered $\to$ Approval Accepted $\to$ Execution $\to$ Completed.

### Phase 4: ContextOS Memory Engine (CODEX)
- **Goal:** Implement persistent semantic, episodic, decision, and checkpoint memory with universal handoff envelopes.
- **Components:**
  - Memory types: `semantic`, `episodic`, `decision`, `task`, `failure`, `code_reference`.
  - `remember()`, `recall()`, `search()`, `forget()`.
  - `checkpoint()` and `resume()` without full conversation replays.
  - Adapters: `CodexSessionAdapter`, `AGYSessionAdapter`, `GenericJsonSessionAdapter`.
- **Verification:** Tests for read/write, checkpoint serialization, conflict resolution, deleted file handling.

### Phase 5: Token-Aware Context Engine (CODEX)
- **Goal:** Implement the 4-tier token-budgeted context selection engine.
- **Components:**
  - Context pipeline: Intent extraction $\to$ candidate discovery $\to$ git diff $\to$ symbol relevance $\to$ memory retrieval $\to$ deduplication $\to$ deterministic scoring $\to$ token budget allocation.
  - Strictly enforce budget partitions: System (15%), Task (10%), Memory/Decisions (15%), Source/Tests (50%), Buffer (10%).
  - Real-time token metrics: `candidate_tokens`, `selected_tokens`, `tokens_avoided`.
- **Verification:** Unit tests proving token budget cannot be exceeded.

### Phase 6: Model Context Protocol (MCP) Server (CODEX)
- **Goal:** Implement the official MCP v2 server exposing ContextOS capabilities over Streamable HTTP and Stdio.
- **Tools Exposed:** `project_get`, `project_status`, `context_build`, `context_search`, `memory_search`, `memory_remember`, `memory_decision_add`, `session_checkpoint`, `session_resume`, `session_import`, `agent_list`, `agent_status`, `agent_delegate`, `task_get`, `task_update`, `git_diff_summary`, `token_metrics`.
- **Verification:** MCP client integration test with `modelcontextprotocol` SDK client; `docs/MCP_SETUP.md`.

### Phase 7: Analytics & Token Savings Dashboard (CODEX)
- **Goal:** Provide auditable token and cost telemetry.
- **Components:**
  - Token tracking per provider, model, agent, project, session, task.
  - Clear distinction between provider-reported tokens and estimated local tokens (`estimated = true`).
  - Side-by-side comparison mode: Without ContextOS vs With ContextOS.
  - Technically defensible savings (tokens avoided, context bytes not transmitted; no fake carbon numbers).
- **Verification:** Telemetry calculation unit tests and dashboard rendering tests.

### Phase 8: AGY & Codex Client Interoperability (AGY)
- **Goal:** Validate end-to-end cross-agent handoff between Antigravity (AGY) and Codex.
- **Test:**
  - Session A (Agent A): Performs task, records decision, modifies code, checkpoints session.
  - Session B (Agent B): Fresh context, resumes via ContextOS without conversation history, answers verification queries, continues task correctly.
  - Report saved to `reports/handoff-test/`.

### Phase 9: Complete AIOS Interaction Flow (CODEX)
- **Goal:** Unify all layers into a single end-to-end interactive flow.
- **Features:**
  - Global command bar (`New Agent`, `New Task`, `Checkpoint`, `Resume`, `View Diff`, `Search Memory`, etc.).
  - Visible error surfacing with retry actions and log drawer.
  - Seamless transitions from UI action to agent execution, approval popup, diff view, and checkpoint creation.

### Phase 10: E2E Playwright Verification with Screenshot Proof (CODEX)
- **Goal:** Execute headless browser automated tests capturing screenshots at every step.
- **Deliverables:**
  - Screenshots in `artifacts/e2e/` (`01-dashboard.png` through `10-resumed-session.png`).
  - `artifacts/e2e/report.md` detailing PASS/FAIL per requirement.

### Phase 11: Final Architecture Audit & Hardening (AGY)
- **Goal:** Audit security, licenses, dead code, error handling, environment variables, and types.
- **Deliverables:**
  - `docs/FINAL_ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/LOCAL_SETUP.md`, `docs/AGENT_INTEGRATION.md`, `docs/CONTEXTOS_PROTOCOL.md`, `docs/TOKEN_METRICS.md`.
  - Complete verification suite (lint, typecheck, tests, build) all passing.
