# ContextOS Model Context Protocol (MCP) Setup Guide

ContextOS includes a high-performance **FastMCP v2** server exposing 17 specialized tools for 4-tier context compilation, persistent memory, Architecture Decision Records (ADRs), cross-agent session continuity, fleet supervision, and token telemetry.

---

## 1. FastMCP Server Overview

The server can run in two distinct modes:
1. **Stdio Mode (Local CLI & IDEs)**: Recommended for Cursor, Antigravity, VS Code, Claude Desktop, and CLI agent wrappers.
2. **Streamable HTTP / SSE Mode (Web & Remote)**: Mounted under the FastAPI daemon at `http://127.0.0.1:8000`.

### Command-Line Invocation
```powershell
# From ContextOS/server directory:
python -m contextos.main --mcp
```

---

## 2. Integration Guides

### A. Google Antigravity (AGY) Integration
Add ContextOS to your Antigravity user or workspace MCP configuration (`~/.gemini/antigravity-ide/mcp_config.json` or `.agents/mcp_config.json`):

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": [
        "-m",
        "contextos.main",
        "--mcp"
      ],
      "cwd": "c:/Users/rc821/OneDrive/Desktop/ContextOS/server",
      "env": {
        "PYTHONPATH": "c:/Users/rc821/OneDrive/Desktop/ContextOS/server"
      }
    }
  }
}
```

### B. Cursor & VS Code Integration
Add to `.cursor/mcp.json` or VS Code MCP configuration:

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": [
        "-m",
        "contextos.main",
        "--mcp"
      ],
      "cwd": "c:\\Users\\rc821\\OneDrive\\Desktop\\ContextOS\\server",
      "env": {
        "PYTHONPATH": "c:\\Users\\rc821\\OneDrive\\Desktop\\ContextOS\\server"
      }
    }
  }
}
```

### C. Claude Desktop Integration
Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": [
        "-m",
        "contextos.main",
        "--mcp"
      ],
      "cwd": "c:/Users/rc821/OneDrive/Desktop/ContextOS/server"
    }
  }
}
```

---

## 3. Registered MCP Tools (17 Core Tools)

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| **`project_get`** | `project_id?: str` | Retrieve workspace root, db location, and configuration limits. |
| **`project_status`** | `project_id?: str` | Get active git branch, modified files count, and active agent metrics. |
| **`context_build`** | `intent: str, active_task?: str, budget?: int, session_id?: str` | Run 4-tier token-budgeted compiler; returns structured prompt & telemetry. |
| **`context_search`** | `query: str, limit?: int` | Search codebase files and AST signatures with relevance score. |
| **`memory_search`** | `query: str, memory_type?: str, limit?: int` | Search semantic, episodic, task, and failure memories. |
| **`memory_remember`** | `content: str, memory_type?: str, tags?: list` | Persist learned concepts, bug patterns, or repo facts. |
| **`memory_decision_add`**| `title: str, context: str, decision: str, consequences?: str, alternatives?: list` | Record an Architecture Decision Record (ADR). |
| **`session_checkpoint`** | `session_id: str, agent_id: str, state_summary: str, active_task?: str, modified_files?: list` | Freeze session state into a checkpoint. |
| **`session_resume`** | `checkpoint_id_or_session_id: str` | Reconstitute execution context without turn replay. |
| **`session_import`** | `source_agent: str, session_data: dict` | Convert Codex / AGY conversation formats into Universal Envelopes. |
| **`agent_list`** | None | List all fleet agents and their lifecycle statuses. |
| **`agent_status`** | `agent_id: str` | Retrieve status, task, token usage, and metrics for an agent. |
| **`agent_delegate`** | `from_agent_id: str, to_role: str, task: str` | Delegate a subtask to a specialized sub-agent. |
| **`task_get`** | `agent_id: str` | Get task progress summary and checklist items. |
| **`task_update`** | `agent_id: str, item_id: str, completed?: bool` | Mark acceptance criteria milestone as completed. |
| **`git_diff_summary`** | None | Summarize unstaged and staged workspace changes. |
| **`token_metrics`** | None | Return token savings metrics and context reduction ratio. |
