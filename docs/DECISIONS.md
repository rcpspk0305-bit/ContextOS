# Architecture Decision Records (ADRs)

## ADR-001: Modular Monolith Repository Pattern
- **Status:** Accepted
- **Context:** AIOS Context Engine coordinates multiple applications (Web UI, API daemon, CLI, MCP server) and shared logic (domain entities, context assembly, memory, process supervision, indexing). Microservices would introduce severe operational complexity, distributed networking overhead, and deployment friction on a developer's local machine.
- **Decision:** Structure AIOS as a modular monolith in `aios/` with `apps/` for deployable interfaces and `packages/` for domain boundaries.
- **Consequences:** Single-command local setup, unified typing (Pydantic / TypeScript), zero network serialization overhead between internal packages, while preserving clean architectural boundaries.

---

## ADR-002: Local-First Supervisor & Context Broker Daemon Topology
- **Status:** Accepted
- **Context:** Agents need real-time supervision, WebSocket telemetry, persistent state across reboots, and on-demand context serving via MCP. An embedded library alone cannot supervise independent CLI processes or host a persistent web dashboard.
- **Decision:** Deploy AIOS as a local background daemon using FastAPI and SQLite, paired with an embedded MCP server and Next.js frontend.
- **Consequences:** Provides a single control plane for local development; enables long-running background tasks, live log streaming, and cross-session checkpoint persistence.

---

## ADR-003: Sandboxed Process Group Supervision & Path Jailing
- **Status:** Accepted
- **Context:** Spawning coding agents as bare OS subprocesses risks orphaned background processes (e.g., hanging test runners or web dev servers) when cancelled, as well as unauthorized directory traversal outside the repository. Heavy Docker containers introduce latency, volume mounting issues, and container engine prerequisites.
- **Decision:** Supervise CLI processes using OS process groups (`setpgid` on POSIX, Process Job Objects on Windows) so `SIGTERM`/`SIGKILL` cleans up all descendants. Enforce strict filesystem jailing using `os.path.commonpath([project_root, target]) == project_root`.
- **Consequences:** Eliminates zombie processes on task cancellation and guarantees agents cannot mutate files outside the authorized project root, with zero VM or container overhead.

---

## ADR-004: Strict 4-Tier Context Assembly Hierarchy
- **Status:** Accepted
- **Context:** Dumping entire files or raw unranked RAG chunks causes token waste, attention distraction, and dependency interface hallucinations.
- **Decision:** Assemble minimal ContextPackets using a strict 4-tier hierarchy:
  - Tier 0: Active Task specification and uncommitted Git diff.
  - Tier 1: Tree-sitter extracted signature stubs & interfaces for imported dependencies.
  - Tier 2: Full source bodies of target files to be edited.
  - Tier 3: sqlite-vec semantic search over past project decisions, bug resolutions, and failure modes.
- **Consequences:** Bounded token consumption, elimination of signature hallucinations, and measurable token avoidance (>80% typical efficiency).

---

## ADR-005: Truthful Provider Capabilities & Graceful Auto-Checkpointing
- **Status:** Accepted
- **Context:** Providers vary widely in capability. Some support native pause/resume, while others (such as proprietary CLI loops or external agents) do not. Faking capabilities causes system hangs and unpredictable state.
- **Decision:** Enforce truthful capability reporting via `ProviderCapabilities`. When a user requests a pause on a provider where `supports_pause == False`, AIOS transitions the run to `AWAITING_CHECKPOINT`, captures an immediate Git patch and session checkpoint, and terminates the process group gracefully to enter `PAUSED`.
- **Consequences:** Eliminates infinite waiting loops and ensures zero data loss regardless of agent provider limitations.

---

## ADR-006: Universal Handoff Envelope for Cross-Agent Session Resumption
- **Status:** Accepted
- **Context:** Developers frequently switch between models (e.g. from Codex to a local Ollama model or Antigravity). Direct conversation transpilation across proprietary schema formats is fragile and lossy.
- **Decision:** Model session handoffs as a standardized `Universal Handoff Envelope` containing the active Git diff/patch, current task progress checklist, recorded decisions, and fresh 4-tier context packet.
- **Consequences:** Seamless resumption of interrupted work across any supported agent without manual re-prompting or transcript conversion bugs.

---

## ADR-007: Grounded & Auditable Token Avoidance Mathematics
- **Status:** Accepted
- **Context:** Marketing claims of "AI token efficiency" are often vague heuristics. Users need auditable numbers to evaluate real cost and performance benefits.
- **Decision:** Codify token avoidance mathematically:
  $$\text{Tokens Avoided} = \text{Candidate Tokens} - \text{Dispatched Tokens}$$
  $$\text{Efficiency Ratio} = \left(\frac{\text{Tokens Avoided}}{\text{Candidate Tokens}}\right) \times 100\%$$
- **Consequences:** Auditable dashboard metrics, verifiable against model tokenizers (tiktoken), providing clear transparency into savings.
