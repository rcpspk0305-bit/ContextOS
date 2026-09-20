# ContextOS — Final Architecture & System Design

**Version:** 1.0.0-GA  
**Status:** Production-Ready / Fully Verified  
**Operating Mode:** Local-First AI Operating Layer & Agent Fleet Supervisor  

---

## 1. System Topology & Architecture Overview

ContextOS operates as a unified, local-first operating layer between AI coding agents (Google Antigravity/AGY, OpenAI Codex, Cursor, Claude Desktop) and the underlying host operating system and filesystem.

```text
+-------------------------------------------------------------------------------+
|                       AI Clients & Interfaces                                 |
|   +-------------------+    +--------------------+    +--------------------+   |
|   | Google Antigravity|    |    OpenAI Codex    |    |   Cursor / VS Code |   |
|   +---------+---------+    +---------+----------+    +---------+----------+   |
|             |                        |                         |              |
|             +-------------------+----+-------------------------+              |
|                                 |                                             |
|                         [MCP v2 / Stdio & SSE]                                |
|                                 v                                             |
+---------------------------------+---------------------------------------------+
|                      ContextOS Core System Layer                              |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |                       FastAPI API & Daemon                            |   |
|   |   - REST Endpoints (/api/agents, /api/context, /api/analytics, etc.)  |   |
|   |   - WebSocket Normalized Event Bus (/ws/events)                       |   |
|   |   - Model Context Protocol Server (17 FastMCP Tools)                  |   |
|   +-----------------------------------------------------------------------+   |
|                                                                               |
|   +-------------------+  +---------------------+  +-----------------------+   |
|   |   Agent Runtime   |  |   Context Engine    |  |    Memory Engine      |   |
|   | - Process Groups  |  | - 4-Tier Budgeting  |  | - SQLite FTS5 (BM25)  |   |
|   | - 8-State Machine |  | - AST Compressor    |  | - 6 Memory Types      |   |
|   | - Risk Gatekeeper |  | - Candidate Scorer  |  | - ADR Architecture    |   |
|   +-------------------+  +---------------------+  +-----------------------+   |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |                   Auditable Analytics & Pricing Engine                |   |
|   |   - Provider/Model Cost Savings  - Context Bytes Avoided Tracking     |   |
|   |   - Side-by-Side Comparison      - Provider Reported vs Estimated     |   |
|   +-----------------------------------------------------------------------+   |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |                     SQLite Local Persistence Layer                    |   |
|   |   - agents, events, approvals, memories, decisions, checkpoints       |   |
|   |   - token_records, session_envelopes, memories_fts (FTS5 virtual)     |   |
|   +-----------------------------------------------------------------------+   |
|                                                                               |
+---------------------------------+---------------------------------------------+
|                                 v                                             |
|                  Host Workspace & Filesystem Sandbox                          |
|         - Enforced Path Jailing (`os.path.commonpath`)                        |
|         - Subprocess Process Groups & Secret Pattern Redaction                |
+-------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### 2.1 Agent Runtime & Process Supervision
- **Workspace Containment:** All file and directory reads/writes validate boundary containment using `os.path.commonpath([workspace_root, target_path]) == workspace_root`. Path traversals (`../`) or absolute jumps outside the workspace raise immediate `PermissionError`.
- **Subprocess Isolation:** Terminal commands execute under dedicated OS process groups (`creationflags=CREATE_NEW_PROCESS_GROUP` on Windows; `preexec_fn=os.setsid` on POSIX) with configurable wall-clock timeouts and 100KB stdout/stderr truncation buffers to prevent daemon out-of-memory lockups.
- **Human-in-the-Loop Risk Policy:** Dangerous operations (`git_push`, `delete_file`, `overwrite_file`, `shell_command` with high-risk patterns) trigger mandatory human approval cards before execution proceeds.

### 2.2 Token-Aware Context Engine
- **4-Tier Budgeting Partition:**
  - **Tier 1 (System Instructions):** 15% budget cap. Core role prompts, safety rules.
  - **Tier 2 (Active Task & Acceptance Criteria):** 10% budget cap. Current checklist items.
  - **Tier 3 (Persistent Memory & ADRs):** 15% budget cap. Relevant decisions and semantic records.
  - **Tier 4 (Source Code & Tests):** 50% budget cap. Prioritizes modified files, AST signatures, and targeted snippets.
  - **Tier 5 (Safety Buffer):** 10% reserved for model generation and reasoning overhead.
- **AST Compressor:** Parses Python (`ast.parse`) and TypeScript/JavaScript to strip implementation bodies, preserving clean function/class signatures, docstrings, type annotations, and exported interfaces, cutting token payloads by 70%–92%.
- **Deterministic Token Budget Invariant:** The compiler guarantees `total_tokens <= budget` under all repository loads, pruning low-relevance files when budgets are saturated.

### 2.3 ContextOS Memory Engine
- **6 Memory Types:** `semantic`, `episodic`, `decision`, `task`, `failure`, `code_reference`.
- **FTS5 BM25 Search:** SQLite full-text search index across memory content and tags with sanitized multi-word OR-prefixed matching.
- **Architecture Decision Records (ADRs):** Structured decision tracking (`title`, `context`, `decision`, `consequences`, `status`, `alternatives_considered`).
- **Universal Session Envelopes & Checkpoints:** Captures longitudinal state snapshots allowing cross-session resumption with **zero raw conversation turn replay**.

### 2.4 Model Context Protocol (MCP) Server v2
- Implemented using official `FastMCP` exposing 17 tools:
  - Project tools: `project_get`, `project_status`
  - Context tools: `context_build`, `context_search`
  - Memory tools: `memory_search`, `memory_remember`, `memory_decision_add`
  - Session continuity tools: `session_checkpoint`, `session_resume`, `session_import`
  - Agent fleet tools: `agent_list`, `agent_status`, `agent_delegate`
  - Task tools: `task_get`, `task_update`
  - Diagnostics: `git_diff_summary`, `token_metrics`
- Supported transports:
  - **Stdio Transport:** Standard input/output for IDEs like Cursor, AGY, VS Code.
  - **SSE Transport:** Server-Sent Events over HTTP for browser clients.

### 2.5 Analytics & Defensible Savings Engine
- Tracks token consumption and savings categorized by provider, model, agent, project, and session.
- Pre-configured verified pricing models for Anthropic, OpenAI, Google, and Local/Ollama models.
- Side-by-side comparative telemetry ("Without ContextOS" vs "With ContextOS").
- Strictly adheres to the **Zero Speculative Carbon** policy: only mathematically provable token counts, context bytes, and verified pricing rates are reported.
