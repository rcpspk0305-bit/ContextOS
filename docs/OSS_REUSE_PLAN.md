# ContextOS — Open-Source Software (OSS) Reuse Plan

**Date:** 2026-09-20  
**Architect:** Antigravity (AGY)  
**Status:** Approved Architectural Plan

---

## 1. Governance & Reuse Principles

To achieve maximum reliability, eliminate unnecessary custom code, and respect intellectual property:
1. **Never reinvent mature wheels:** When a production-tested package exists with a permissive license (MIT/Apache-2.0), prefer importing it over writing custom code.
2. **Minimal copy/adapt:** If only a specific schema, converter, or component is needed, copy only that isolated function/module, maintaining full copyright attribution and change notes in `THIRD_PARTY_REUSE.md`.
3. **No Enterprise/Proprietary code:** Strictly audit repositories for `ee/`, `enterprise/`, or non-permissive dual licenses (e.g., BSL, SSPL, AGPL) and exclude them completely.
4. **Local-first execution:** Avoid cloud-only dependencies, multi-service message queues (Kafka, Celery), or external database servers for V1. Run on local SQLite and in-process WebSocket/HTTP transports.

---

## 2. Comprehensive Candidate Matrix

| Candidate Repository | Capability / Component | Decision | License | Integration / Architecture Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **`mem0ai/mem0`** | Persistent semantic memory, user/session memory, entity extraction | **USE AS PACKAGE** | Apache 2.0 | Install `mem0ai` as the underlying semantic memory engine. Use local SQLite / sqlite-vec or Chroma for zero-cloud embeddings and storage. |
| **`mem0ai/openmemory`** | Cross-platform session discovery, conversion, import/export format | **COPY/ADAPT SMALL MODULE** | Apache 2.0 | Extract the normalized session representation and conversion logic into `contextos.adapters.sessions`. Avoid importing the entire application stack. |
| **`assistant-ui/assistant-ui`** | Chat primitives, thread history, streaming markdown, thread composer | **USE AS PACKAGE** | MIT | Install `@assistant-ui/react` and `@assistant-ui/react-markdown` in `web/` to power the agent conversation screen. |
| **`assistant-ui/tool-ui`** | Tool call visualization, approval cards, argument rendering | **USE AS PACKAGE / ADAPT** | MIT | Use `tool-ui` components for rendering live tool requests, approval triggers, diff displays, and action execution cards. |
| **`CopilotKit/CopilotKit`** | Real-time state synchronization, human-in-the-loop generative UI | **REFERENCE ARCHITECTURE ONLY** | MIT | Adopt CopilotKit's clean state synchronization and action subscription paradigm (`useCopilotAction`), but implement it via native typed WebSocket events to avoid pulling in heavy CoAgent / LangGraph backend proxies. |
| **`OpenHands/software-agent-sdk`** | Agent, Conversation, Workspace, TerminalTool, FileEditorTool, TaskTrackerTool | **COPY/ADAPT SMALL MODULE** | MIT | Adapt the clean, lightweight abstractions for `Agent`, `Conversation`, `TerminalTool`, and `FileEditorTool` into `contextos.agents` and `contextos.workspace`. Provides path jailing and process management without pulling the entire OpenHands system. |
| **`modelcontextprotocol/python-sdk`** | MCP Server v2, Streamable HTTP and Stdio transports, Tool/Resource registration | **USE AS PACKAGE** | MIT | Install `mcp` (v2 official SDK) directly. Implement FastMCP or standard `Server` with Streamable HTTP endpoints mounted into FastAPI. Expose ContextOS tools directly over MCP. |
| **`shadcn-ui/ui`** | Accessible dashboard primitives (Sidebar, Card, Dialog, Tabs, Table, Badge, ScrollArea) | **USE AS PACKAGE / CLI INSTALL** | MIT | Install `@shadcn/ui` components in `web/` using Tailwind CSS and Radix UI primitives. |
| **`langchain-ai/langgraph`** | Graph-based multi-agent state orchestration | **DO NOT USE** | MIT | ContextOS agent lifecycles follow a strict, auditable 8-state machine (`IDLE` $\to$ `STARTING` $\to$ `RUNNING` $\to$ `WAITING_APPROVAL` $\to$ `PAUSED` $\to$ `COMPLETED`/`FAILED`/`STOPPED`). Introducing LangGraph adds unnecessary cyclic abstraction, heavy LangChain dependencies, and debugging complexity. |
| **`langfuse/langfuse`** | LLM observability, tracing, and cost dashboard | **DO NOT USE (V1) / REFERENCE ONLY** | MIT / FSL (Enterprise) | For V1, local SQLite event logging and our dedicated token budgeting math provide auditable telemetry with zero external infrastructure. Avoid Langfuse's complex multi-container Postgres/ClickHouse architecture and proprietary enterprise directories. |

---

## 3. Detailed Component Analysis & Strategy

### 3.1 Session Portability: `mem0ai/openmemory`
- **What it provides:** Normalization logic that discovers, converts, and formats coding agent sessions across disparate providers into a portable format.
- **Reuse Plan:** Adapt the session schema and normalization converter into `server/contextos/adapters/sessions/`. This allows importing sessions from Codex, AGY, and generic JSON formats into a single canonical `SessionCheckpoint`.

### 3.2 Persistent Memory: `mem0ai/mem0`
- **What it provides:** Layered memory (semantic, episodic, entity-relationship) with vector search and memory update/forget operations.
- **Reuse Plan:** Install `mem0ai` as a backend dependency. Wrap it in a clean `MemoryEngine` interface with ContextOS domain types (`DecisionRecord`, `FailureRecord`, `TaskMemory`, `CodeReferenceMemory`).

### 3.3 Agent Chat & Tool UI: `assistant-ui` and `assistant-ui/tool-ui`
- **What it provides:** Production-grade React streaming chat components that handle markdown, syntax highlighting, thread history, and rich tool-result rendering.
- **Reuse Plan:** Embed `@assistant-ui/react` directly inside the AIOS Control Center's central workspace (`/agents/[id]`). Use tool-ui patterns to render our `ApprovalCard` for risky actions (shell execution, file deletion, git push).

### 3.4 Agent Supervision & Tools: `OpenHands/software-agent-sdk`
- **What it provides:** Standardized tool contracts (`TerminalTool`, `FileEditorTool`) and event model (`Action`, `Observation`).
- **Reuse Plan:** Extract and adapt the core tool interfaces and path verification logic into `server/contextos/workspace/`. This gives ContextOS production-tested filesystem boundaries and shell execution controls while preserving an isolated, lightweight local architecture.

### 3.5 Model Context Protocol: `modelcontextprotocol/python-sdk`
- **What it provides:** Official MCP v2 protocol implementation supporting tools, resources, prompts, and Streamable HTTP / Stdio transports.
- **Reuse Plan:** Directly install `mcp>=1.2.0`. Expose ContextOS services (`context_build`, `memory_search`, `session_checkpoint`, `agent_status`) directly as MCP tools so AGY, Codex, and Claude Code can consume them natively.
