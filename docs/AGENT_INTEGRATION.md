# ContextOS — Agent Fleet Integration Guide

This guide details how external AI agents and IDEs integrate with ContextOS via the Model Context Protocol (MCP) v2, the REST/WebSocket daemon, and the Universal Session Continuity layer.

---

## 1. Supported Client Ecosystem

ContextOS is designed to operate seamlessly with:
1. **Google Antigravity (AGY)**
2. **OpenAI Codex**
3. **Cursor & VS Code**
4. **Claude Desktop**
5. **Custom CLI / Daemon Agents**

---

## 2. Integration via Model Context Protocol (MCP)

The most direct way for any agent to leverage ContextOS is by configuring ContextOS as a standard MCP server.

### 2.1 Google Antigravity (AGY) Integration
In your AGY agent configuration (`.gemini/mcp_config.json` or project MCP config):

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": ["-m", "contextos.main", "--mcp-stdio"],
      "cwd": "C:/Users/rc821/OneDrive/Desktop/ContextOS/server"
    }
  }
}
```

### 2.2 Cursor / VS Code Integration
In `.cursor/mcp.json` or VS Code MCP settings:

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": ["-m", "contextos.main", "--mcp-stdio"],
      "cwd": "C:/Users/rc821/OneDrive/Desktop/ContextOS/server"
    }
  }
}
```

### 2.3 Claude Desktop Integration
In `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": ["-m", "contextos.main", "--mcp-stdio"],
      "cwd": "C:/Users/rc821/OneDrive/Desktop/ContextOS/server"
    }
  }
}
```

---

## 3. Core MCP Tools Available to Agents

Once connected, external agents gain access to 17 specialized ContextOS tools:

```text
context_build       -> Generates a 4-tier token-budgeted context bundle with AST compression.
context_search      -> Searches files and extracted AST symbol definitions.
memory_search       -> Queries long-term semantic, episodic, and decision records using FTS5 BM25.
memory_remember     -> Stores a persistent memory item with tags and importance scoring.
memory_decision_add -> Records an Architectural Decision Record (ADR).
session_checkpoint  -> Serializes state summary, modified files, and open decisions.
session_resume      -> Reconstitutes execution state without replaying raw conversation turns.
project_status      -> Inspects uncommitted files, git branch, and active fleet count.
git_diff_summary    -> Summarizes staged and unstaged changes for quick context assembly.
token_metrics       -> Queries cumulative tokens avoided, reduction percentages, and savings.
```

---

## 4. Universal Session Continuity & Cross-Agent Handoff

ContextOS normalizes diverse proprietary session turn formats into a **Universal Session Envelope**:

```python
class UniversalSessionEnvelope(BaseModel):
    id: str
    session_id: str
    source_agent: str         # "codex", "agy", "generic"
    title: str
    summary: str
    turns: List[UniversalTurn]
    artifacts: List[str]
    decisions: List[str]
    created_at: datetime
```

### 4.1 Cross-Agent Handoff Pattern (Codex $\to$ AGY)
1. **Agent A (Codex):** Executes coding task, modifies files, records decisions via `memory_decision_add`, and commits a checkpoint using `session_checkpoint`.
2. **Session Termination:** Agent A stops execution.
3. **Agent B (AGY):** Starts with a clean prompt buffer. Calls `session_resume(checkpoint_id)`.
4. **Context Reconstitution:** ContextOS provides:
   - Resumed task description and goal.
   - List of modified files and recent AST signatures.
   - Associated Architecture Decision Records (ADRs).
   - Relevant semantic memories.
   - **ZERO conversation turns are replayed**, reducing token overhead by over 90% while preventing context window pollution.

---

## 5. Implementing a Custom Agent Adapter

To support a new external AI agent format, subclass `BaseSessionAdapter`:

```python
from contextos.memory.adapters import BaseSessionAdapter
from contextos.models.memory import UniversalSessionEnvelope, UniversalTurn

class CustomAgentAdapter(BaseSessionAdapter):
    def to_universal(self, external_data: dict) -> UniversalSessionEnvelope:
        turns = [
            UniversalTurn(
                turn_id=t["id"],
                role=t["speaker"],
                content=t["text"],
                tool_calls=t.get("tools", []),
            )
            for t in external_data.get("messages", [])
        ]
        return UniversalSessionEnvelope(
            session_id=external_data["session_id"],
            source_agent="custom",
            title=external_data.get("title", "Custom Session"),
            summary=external_data.get("summary", ""),
            turns=turns,
            artifacts=external_data.get("files", []),
            decisions=[],
        )
```
