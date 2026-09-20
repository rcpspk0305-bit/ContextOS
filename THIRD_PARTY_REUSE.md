# Third-Party Open Source Software (OSS) Reuse Register

This file maintains an immutable, auditable record of all external open-source code, modules, schemas, or components copied or adapted into ContextOS, in strict compliance with project policies and upstream licenses.

---

## Reuse Policy & Checklist
- [x] Only permissively licensed repositories (MIT, Apache-2.0, BSD) are utilized.
- [x] No enterprise, commercial-only, or `ee/` directories are ever copied or referenced.
- [x] Original copyright notices, license texts, and author attributions are preserved in destination source files.
- [x] Every reused file or code snippet is documented in the table below before merging.

---

## Third-Party Reuse Ledger

| Repository | Source URL | Commit SHA / Version | Original File | Destination File | License | What Was Reused | Modifications Made |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`OpenHands/software-agent-sdk`** | https://github.com/OpenHands/software-agent-sdk | `main` (Latest tag / SDK v1) | `agent/tool/terminal.py` | `server/contextos/workspace/terminal_tool.py` | MIT | Terminal execution logic, process timeout handling, and stdout buffering | Adapted to local Windows/POSIX process groups; added strict path jailing; stripped remote Docker dependencies. |
| **`OpenHands/software-agent-sdk`** | https://github.com/OpenHands/software-agent-sdk | `main` (Latest tag / SDK v1) | `agent/tool/file_editor.py` | `server/contextos/workspace/file_editor_tool.py` | MIT | File reading, surgical chunk replacement, and line viewing interfaces | Enforced local workspace root validation (`os.path.commonpath`); removed sandbox VM remote calls. |
| **`OpenHands/software-agent-sdk`** | https://github.com/OpenHands/software-agent-sdk | `main` (Latest tag / SDK v1) | `agent/tool/task_tracker.py` | `server/contextos/workspace/task_tracker_tool.py` | MIT | Task checklist and acceptance criteria progression tracker | Refactored with Pydantic v2 data models and in-memory progress summaries. |
| **`mem0ai/openmemory`** | https://github.com/mem0ai/openmemory | `main` (Latest) | `src/models/session.py` | `server/contextos/adapters/sessions/normalized.py` | Apache-2.0 | Normalized session and conversation schema models | Simplified to lightweight Pydantic v2 schemas; aligned with ContextOS universal handoff envelopes. |
| **`assistant-ui/tool-ui`** | https://github.com/assistant-ui/tool-ui | `@assistant-ui/react` (Latest npm) | `packages/react/src/components/ToolCall.tsx` | `web/src/components/approval/ApprovalCard.tsx` | MIT | Tool-call and argument rendering card pattern | Embedded human-in-the-loop approval actions (`Approve once`, `Approve for session`, `Reject`); styled with `shadcn/ui` tokens. |
| **`shadcn-ui/ui`** | https://github.com/shadcn-ui/ui | Latest CLI templates | Various primitives (button, card, dialog, tabs, sheet, badge) | `web/src/components/ui/*` | MIT | Tailwind CSS + Radix UI accessible dashboard component primitives | Styled using custom neutral slate / zinc tokens; dark/light mode optimized. |

---

## Package Dependencies (Installed via Package Managers)

The following mature open-source packages are installed as standard dependencies (not copied):
1. **`mcp` (`modelcontextprotocol`)** — Official Model Context Protocol SDK v2 (MIT License).
2. **`mem0ai`** — Core persistent memory vector layer (Apache-2.0 License).
3. **`@assistant-ui/react` & `@assistant-ui/react-markdown`** — React streaming conversation UI components (MIT License).
4. **`fastapi`, `uvicorn`, `pydantic`** — High-performance asynchronous API daemon (MIT License).
5. **`tree-sitter`** — AST-level signature extraction for Tier 1 context assembly (MIT License).
