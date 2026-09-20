# ContextOS — Local Installation & Operator Runbook

This guide covers bootstrapping the ContextOS AI operating daemon, running automated test suites, launching the Model Context Protocol (MCP) server, and mounting the Web Control Center.

---

## 1. Prerequisites

- **Python:** 3.10 or higher (Tested and certified on Python 3.14).
- **Node.js:** v18.0.0 or higher (Tested on Node.js v24.19.0).
- **Package Managers:** `pip` and `npm`.
- **Operating System:** Windows 10/11, macOS, or Linux.

---

## 2. Repository Layout

```text
ContextOS/
├── server/                 # Python Backend (Daemon, MCP Server, Runtime, Memory)
│   ├── contextos/          # Core package
│   │   ├── api/            # FastAPI REST & WebSocket endpoints
│   │   ├── approval/       # Human-in-the-loop risk policy engine
│   │   ├── context/        # 4-tier token budgeted context compiler & AST compressor
│   │   ├── mcp/            # FastMCP server exposing 17 core tools
│   │   ├── memory/         # Persistent memory engine with SQLite FTS5 BM25
│   │   ├── models/         # Pydantic v2 schemas
│   │   ├── runtime/        # Process supervisor and event bus
│   │   └── storage/        # Database manager & migrations
│   ├── tests/              # 35 automated pytest unit & integration tests
│   └── scripts/            # Cross-agent simulation and bench tools
├── web/                    # Desktop-first React 19 + Vite Web Control Center
│   ├── src/                # UI components, pages, hooks, and types
│   └── scripts/            # Playwright screenshot automation
├── docs/                   # Architecture, Security, Protocol, and Setup specs
├── reports/                # Handoff verification and performance reports
└── artifacts/              # E2E test screenshots and run artifacts
```

---

## 3. Backend Daemon Setup

### 3.1 Install Python Dependencies
```bash
cd server
pip install fastapi uvicorn pydantic mcp pytest pytest-cov httpx
```

### 3.2 Launch the Local AIOS Daemon
```bash
# Starts REST API on :8000 and WebSocket on ws://127.0.0.1:8000/ws/events
python -m uvicorn contextos.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 3.3 Launch MCP Server in Stdio Mode (For IDEs)
```bash
python -m contextos.main --mcp-stdio
```

### 3.4 Run Automated Backend Tests
```bash
python -m pytest tests -v --cov=contextos
```

---

## 4. Web Control Center Setup

### 4.1 Install Node Dependencies
```bash
cd web
npm install
```

### 4.2 Start Development Server
```bash
npm run dev
# Server mounts at http://127.0.0.1:3000
```

### 4.3 Build for Production & Preview
```bash
npm run build
npm run preview -- --port 3000 --host 127.0.0.1
```

---

## 5. Running Cross-Agent Handoff Verification

To run the end-to-end simulation testing cross-agent handoff between Codex (Session A) and Antigravity (Session B) with zero turn replay:

```bash
cd server
python -m scripts.run_handoff_test
```
Reports and token telemetry will be generated in `reports/handoff-test/`.
