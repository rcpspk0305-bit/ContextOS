---
title: AIOS Context Engine System Blueprint - Plan
type: feat
date: 2026-09-19
topic: aios-context-engine-blueprint
artifact_contract: ce-unified-plan/v1
artifact_readiness: requirements-only
product_contract_source: ce-brainstorm
execution: code
---

## Goal Capsule

- **Objective:** Provide a local-first AI operating and context-control layer that supervises software-development agent lifecycles, assembles minimal 4-tier context to eliminate redundant whole-repository token dumps, tracks auditable token avoidance metrics, and enables seamless session checkpoint resumption across heterogeneous agent providers without proprietary account circumvention.
- **Means:** A modular monolith in `aios/` combining a Python FastAPI supervisor daemon, local Model Context Protocol (MCP) server, SQLite database, Tree-sitter code indexing, and a Next.js App Router web console.
- **Product Authority:** The architecture and requirements specified herein govern the full six-milestone roadmap of AIOS Context Engine; Milestone 1 owns the foundation, domain models, schemas, lifecycle state machine, and core documentation baseline. Surrounding downstream milestone implementations remain contextual candidates governed by this contract.
- **Execution Profile:** Local developer workstation (Windows/Linux/macOS), standalone daemon, local-first SQLite persistence, no mandatory cloud dependencies, no Docker containers required for basic operations.
- **Open Blockers:** None. Settled decisions from architectural dialogue are incorporated with exact governance links.

---

<!-- ce-section: work-relationships -->
## How This Work Fits Together

This blueprint defines the global product architecture across six planned development milestones, with active execution initially focused on Milestone 1:

- **Milestone 1: Monolith Foundation & Core Domain Architecture (Active Focus)**
  - Sets up modular monolith directory layout (`aios/apps/*`, `aios/packages/*`, `data/`, `tests/`, `docs/`).
  - Implements core domain models in SQLAlchemy 2 and Pydantic v2 with Alembic migrations and SQLite.
  - Defines the 8-state Agent lifecycle state machine and provider capability contract.
  - Establishes project baseline documentation (`docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/API.md`, `docs/PROGRESS.md`).
- **Milestone 2: Agent Runtime & Provider Adapters**
  - *Depends on:* Milestone 1 domain models and state machine.
  - *Enables:* Supervised OS child process execution with `setpgid`/job-object process grouping, workspace path jailing (`os.path.commonpath`), graceful cancellation (`AWAITING_CHECKPOINT`), and adapters for Ollama, Codex, and Antigravity-compatible workflows.
- **Milestone 3: Context Engine & Code Intelligence**
  - *Depends on:* Milestone 1 domain models (`CodeSymbol`, `ContextPacket`, `TokenMetric`).
  - *Enables:* Tree-sitter AST parsing, signature stub extraction, sqlite-vec embeddings, strict 4-tier context packet generation, and auditable token calculation.
- **Milestone 4: Persistent Memory & Cross-Agent Checkpoints**
  - *Depends on:* Milestone 2 agent runs and Milestone 3 context packets.
  - *Enables:* Project memory store, decision ADR logs, Git patch working-state capture, and Universal Handoff Envelopes across different agent providers.
- **Milestone 5: MCP Server & Agent Direct Bridge**
  - *Depends on:* Milestones 2, 3, and 4.
  - *Enables:* Native Model Context Protocol server exposing AIOS tools (`aios_get_context`, `aios_record_decision`, `aios_checkpoint_session`) directly to external agents (Antigravity, Claude Code, Cursor, Codex).
- **Milestone 6: Web Control Console & Analytics Dashboard**
  - *Depends on:* Milestones 1 through 5.
  - *Enables:* Next.js App Router UI with real-time WebSocket agent console, task assignment board, context visualizer, and Recharts token avoidance analytics.

---

## Product Contract

### Summary
AIOS Context Engine is a local-first supervisor daemon and context broker that manages coding agents across their complete lifecycle, assembles 4-tier minimal AST/semantic context packets instead of dumping full repositories, persists project decisions and working state across sessions via Universal Handoff Envelopes, and tracks auditable token avoidance metrics.

### Problem Frame
Developers using AI coding agents currently face three acute compounding problems:
1. **Context Bloat & Token Waste:** Agents repeatedly ingest entire repositories, file trees, or sprawling chat transcripts, causing high token costs, degraded LLM attention, and context window exhaustion.
2. **Fragile Agent Supervision:** External CLI tools run as unmanaged bare subprocesses that leave orphaned background processes on exit, lack uniform lifecycle controls (pause/resume/cancel), and risk filesystem path escapes.
3. **Session Amnesia & Vendor Lock-in:** Switching between agents (e.g. from Codex to Antigravity or a local Ollama model) results in a total loss of working context, active decisions, uncommitted diffs, and architectural guardrails.

AIOS resolves this by acting as the local control layer, indexing ASTs with Tree-sitter to serve signature stubs alongside target code bodies, jailing agent subprocesses cleanly, and storing persistent project decisions that serialize into universal handoff artifacts.

### Key Decisions
- **KD1. Supervisor & Context Broker Daemon Topology** (session-settled: user-directed — chosen over embedded-only library and autonomous runner: centralizes lifecycle supervision, real-time WebSocket telemetry, and MCP context serving across heterogeneous CLI and API agents). Governs R1, R2, R3, R4.
- **KD2. Sandboxed Subprocess Execution with Process Groups and Path Jailing** (session-settled: user-directed — chosen over bare subprocesses and heavy Docker virtualization: enforces OS process group management via `setpgid`/job-objects and `os.path.commonpath` verification to eliminate orphaned children and directory traversal without VM overhead). Governs R5, R6.
- **KD3. Strict 4-Tier Context Hierarchy** (session-settled: user-directed — chosen over unranked chunk RAG and full call-graph DAGs: codifies Tier 0 task/diff, Tier 1 signature stubs, Tier 2 target bodies, and Tier 3 semantic past decisions/failures to eliminate signature hallucination while respecting token budgets). Governs R7, R8, R9, R10.
- **KD4. Graceful Cancellation & Auto-Checkpoint for Non-Pausable Providers** (session-settled: user-directed — chosen over stalling in unachievable PAUSED states: automatically transitions pause actions to `AWAITING_CHECKPOINT` or graceful cancellation with an immediate working state capture when `supports_pause: false`). Governs R11, R12.
- **KD5. Universal Handoff Envelope for Cross-Agent Resumption** (session-settled: user-directed — chosen over conversation transpilation and Git worktree branching: packages Git patch/diff, active task checklist, decisions made, and minimal context into a standardized markdown/JSON envelope that any subsequent agent can ingest). Governs R13, R14.
- **KD6. Auditable Grounded Token Metrics** (session-settled: user-directed — chosen over estimated heuristics: computes tokens avoided via exact difference between baseline candidate tokens and actual dispatched tokens). Governs R15, R16.
- **KD7. Modular Monolith Architecture** (session-settled: user-approved — chosen over microservices: packages core domains in `aios/packages/*` and applications in `aios/apps/*` to ensure single-command local development and maintainability). Governs R17, R18.

### Actors
- A1. **Developer:** Initiates tasks, inspects context packets, monitors live agent runs, approves checkpoints, and tracks token savings from the Web UI or Typer CLI.
- A2. **AI Coding Agent:** An external or local model process (Codex CLI, Antigravity workflow, Ollama local model) executing a development task under AIOS supervision.
- A3. **AIOS Supervisor Daemon:** The central local FastAPI process orchestrating subprocesses, managing state transitions, serving MCP endpoints, generating context packets, and persisting database records.

### Requirements

#### Monolith Structure & Domain Foundation
- R1. AIOS must be structured as a modular monolith in `aios/` with distinct application directories (`apps/web`, `apps/api`, `apps/cli`, `apps/mcp`) and modular domain packages (`packages/core`, `packages/agents`, `packages/context`, `packages/memory`, `packages/indexing`, `packages/tasks`, `packages/analytics`, `packages/providers`, `packages/git`).
- R2. The core domain model must define first-class typed entities for: Project, Agent, AgentProvider, AgentRun, Task, Session, Checkpoint, Memory, Decision, CodeSymbol, ContextPacket, TokenMetric, Event, and PermissionPolicy.
- R3. SQLite with SQLAlchemy 2 (async) and Alembic migrations must serve as the primary local persistence engine, storing all domain entities, event logs, and checkpoints.
- R4. Foundational architecture documentation (`docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/API.md`, and `docs/PROGRESS.md`) must be maintained and updated after every development milestone.

#### Agent Lifecycle & Process Supervision
- R5. The agent process supervisor must enforce OS process group management (`setpgid` on POSIX systems, Windows Job Objects on Windows) so that `SIGTERM` or `SIGKILL` cleanly terminates all child and descendant processes without leaving orphaned background workers.
- R6. The supervisor must enforce strict working-directory jailing via `os.path.commonpath` validation, rejecting any tool call or process configuration that attempts to execute outside the authorized project root.
- R7. The agent lifecycle must strictly enforce 8 discrete states: `IDLE`, `STARTING`, `RUNNING`, `PAUSED`, `WAITING`, `COMPLETED`, `FAILED`, and `CANCELLED`.
- R8. Provider adapters must declare truthful capabilities via a typed `ProviderCapabilities` schema (`supports_pause`, `supports_resume`, `supports_streaming`, `supports_checkpoints`, `supports_mcp_injection`); provider capabilities must never be faked.
- R9. When a user requests a pause on an agent whose provider reports `supports_pause: false`, the supervisor must transition the run to `AWAITING_CHECKPOINT` and initiate a graceful termination sequence with an automatic checkpoint rather than entering an unachievable `PAUSED` state.
- R10. All stdout/stderr lines, state changes, and token telemetry from running agents must be ingested as normalized `Event` records and broadcast in real time via WebSockets.

#### Context Engine & 4-Tier Hierarchy
- R11. The context assembly engine must construct `ContextPacket` artifacts using a strict 4-tier hierarchy:
  - *Tier 0 (Task & Worktree):* Active Task requirements, acceptance criteria, and uncommitted Git working-tree diff.
  - *Tier 1 (Signatures & Stubs):* Tree-sitter extracted signatures, interfaces, and exported types for all imported or dependency symbols (omitting implementation bodies).
  - *Tier 2 (Target Bodies):* Complete source code bodies for the specific files or symbols targeted for inspection or editing.
  - *Tier 3 (Semantic History & Decisions):* sqlite-vec indexed project decisions, architectural constraints, past bug resolutions, and failure modes relevant to the active task.
- R12. Context packets must be bounded by a user-configured token ceiling, prioritizing Tier 0 and Tier 2 before allocating remaining budget to Tier 1 and Tier 3.
- R13. The indexing engine must utilize Tree-sitter parsers to extract `CodeSymbol` definitions (functions, classes, interfaces, method signatures) across TypeScript/JavaScript, Python, Go, and Rust.

#### Checkpoints & Universal Handoff
- R14. Checkpoints must capture the complete working state: active branch, dirty worktree diff/patch, touched files, completed checklist items, and recorded decisions.
- R15. Resuming a session with a different agent or model must utilize a `Universal Handoff Envelope` containing the captured Git patch, active task checklist, session briefing, and a freshly generated minimal ContextPacket.

#### Analytics & Auditable Token Metrics
- R16. Every context generation and agent run must record an auditable `TokenMetric` entry calculating exact token consumption using model-specific tokenizers (e.g. tiktoken).
- R17. Token avoidance must be calculated strictly using:
  $$\text{Tokens Avoided} = \text{Candidate Tokens} - \text{Dispatched Tokens}$$
  where $\text{Candidate Tokens}$ is the total token count of a naive baseline (full repository files and untruncated transcript history) and $\text{Dispatched Tokens}$ is the actual token count of the minimal `ContextPacket`.
- R18. The system must track and expose the `Token Efficiency Ratio`:
  $$\text{Efficiency Ratio} = \left(\frac{\text{Tokens Avoided}}{\text{Candidate Tokens}}\right) \times 100\%$$

#### MCP Server & Integration Interface
- R19. AIOS must expose an embedded local Model Context Protocol (MCP) server providing standard resources (`context://current`, `tasks://active`, `memory://project`) and tools (`aios_get_context`, `aios_record_decision`, `aios_checkpoint_session`, `aios_log_tokens`).
- R20. External agent workflows (Codex, Antigravity, Claude Code, Cursor) must be capable of connecting to AIOS directly through MCP without custom binary modifications.

### Key Flows

- F1. Supervised Agent Execution
  - **Trigger:** Developer assigns a Task to an Agent via Web UI or CLI (`aios run <task-id> --agent codex`).
  - **Actors:** A1, A3, A2
  - **Steps:**
    1. Supervisor validates workspace path with `os.path.commonpath`.
    2. Context Engine compiles a 4-Tier ContextPacket for the task.
    3. Supervisor spawns agent in a new OS process group (`setpgid`).
    4. Provider adapter streams stdout/stderr and token events over WebSockets.
    5. On completion or error, supervisor transitions state and cleans up process tree.
  - **Outcome:** Agent completes task with real-time logs visible in Web UI and zero orphaned processes.
  - **Covered by:** R5, R6, R7, R10, R11.

- F2. Graceful Pause & Checkpoint for Non-Pausable Agent
  - **Trigger:** Developer issues pause command on an Antigravity or CLI agent with `supports_pause: false`.
  - **Actors:** A1, A3, A2
  - **Steps:**
    1. Supervisor checks provider capabilities and detects no native pause hook.
    2. Supervisor transitions AgentRun state to `AWAITING_CHECKPOINT`.
    3. Supervisor requests current uncommitted Git diff via `packages/git`.
    4. Supervisor serializes working state into a Checkpoint record.
    5. Supervisor issues graceful `SIGTERM` to the process group.
    6. AgentRun transitions to `PAUSED` with checkpoint ID attached.
  - **Outcome:** Execution halts cleanly without corrupting state or hanging in unachievable loop.
  - **Covered by:** R5, R7, R8, R9, R14.

- F3. Cross-Agent Handoff Resumption
  - **Trigger:** Developer resumes a paused or failed session using a different agent provider (e.g. Ollama local model).
  - **Actors:** A1, A3, A2
  - **Steps:**
    1. Developer selects Checkpoint and chooses target agent provider.
    2. AIOS generates a Universal Handoff Envelope (Git patch + task progress briefing + Tier 0-3 context).
    3. Provider adapter initializes target agent session, injecting the handoff envelope as the initial prompt context.
    4. Target agent resumes development with full awareness of prior decisions and uncommitted changes.
  - **Outcome:** Seamless continuation of work across models without lost context or manual repo re-briefing.
  - **Covered by:** R11, R14, R15.

### Acceptance Examples

- AE1. Orphaned Process Cleanup
  - **Covers R5, R7.**
  - **Given:** An agent subprocess running a nested build command (`npm run build` spawning Node workers).
  - **When:** Developer clicks Cancel in Web UI or supervisor issues `SIGTERM`/`SIGKILL`.
  - **Then:** The supervisor signals the entire process group (`-pgid`), terminating both parent and all child workers, leaving zero orphaned node processes.

- AE2. Path Traversal Rejection
  - **Covers R6.**
  - **Given:** A misconfigured or malicious agent task configured with working directory `../../sensitive_dir`.
  - **When:** Supervisor initializes the run environment.
  - **Then:** `os.path.commonpath([workspace_root, target_dir])` detects escape, aborts with `PermissionPolicyViolationError`, and marks run `FAILED`.

- AE3. Strict 4-Tier Context Assembly
  - **Covers R11, R12, R17.**
  - **Given:** A project of 500,000 baseline candidate tokens and a task targeting `auth_service.py`.
  - **When:** Context Engine generates a ContextPacket with a 4,000 token ceiling.
  - **Then:** Tier 0 holds task spec and active diff (500 tokens), Tier 2 holds full `auth_service.py` (1,500 tokens), Tier 1 holds Tree-sitter interface stubs of imported models (1,200 tokens), Tier 3 holds 2 relevant past decisions (400 tokens), Dispatched Tokens equals 3,600, and Tokens Avoided equals 496,400 (99.28% efficiency).

- AE4. Non-Pausable Agent Transition
  - **Covers R8, R9.**
  - **Given:** An active AgentRun with provider `AntigravityAdapter` where `supports_pause == False`.
  - **When:** User triggers a pause action via CLI or Web UI.
  - **Then:** Run state transitions immediately to `AWAITING_CHECKPOINT`, persists Git patch and session memory into a new Checkpoint, cleanly stops the process group, and sets state to `PAUSED`.

### Success Criteria
- **Zero Orphaned Processes:** 100% of tested termination and cancellation signals cleanly kill child process trees across POSIX and Windows test suites.
- **Context Reduction:** Context packets achieve a minimum 80% measured $\text{Efficiency Ratio}$ compared to whole-repository baselines on standard reference repositories.
- **Zero Provider Faking:** 100% of provider adapter methods truthfully report unsupported operations with typed exceptions (`UnsupportedOperationError`).
- **Clean Cross-Agent Resumption:** Resuming from a Universal Handoff Envelope preserves uncommitted git changes and decision history without requiring manual user re-entry.

### Scope Boundaries
- **Deferred for Later (Post-V1 Milestones):**
  - Distributed multi-node supervisor clusters.
  - Remote cloud workspace synchronization (GCS / S3 state backends).
  - Fine-tuning or local model weight management.
- **Outside This Product's Identity (Positioning Guardrails):**
  - No browser automation, account switching, or credit circumvention under any circumstances.
  - No proprietary API reverse-engineering or undocumented protocol scraping.
  - No container-mandatory orchestration (remains strictly lightweight and local-first).

### Dependencies / Assumptions
- Python 3.12+ runtime installed locally with SQLite 3.38+ (supporting JSON and vector extensions).
- Tree-sitter language libraries available for target programming languages.
- Git CLI (version 2.30+) available on system `PATH`.
- Node.js 18+ for running Next.js App Router in development or production.

### Outstanding Questions
- None blocking planning. Downstream implementation specifics (exact Tree-sitter grammar binary bundling, SQLite-vec build flags per OS) are deferred to Milestone 3 planning.
