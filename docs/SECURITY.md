# ContextOS — Security Model & Hardening Guide

**Classification:** High-Assurance Technical Specification  
**Scope:** Agent Process Isolation, Workspace Containment, Secret Protection & Human Governance  

---

## 1. Security Tenets

1. **Strict Local Containment:** ContextOS agents operate strictly inside the designated project root. No operations may read, modify, or delete files outside this boundary.
2. **Deterministic Risk Gating:** High-risk actions require explicit human operator approval before execution. No autonomous agent may override an approval block.
3. **Defense-in-Depth Secret Redaction:** API keys, certificates, and private credentials are automatically masked from event streams, terminal outputs, and persistent memory.
4. **Resilient Process Isolation:** Commands executed by agents run inside detached OS process groups with enforce wall-clock deadlines and bounded stream buffers.

---

## 2. Workspace Path Jailing

All file system operations conducted by the `FileEditorTool` and `TerminalTool` enforce canonical path containment:

```python
def validate_path(self, target_path: Path) -> Path:
    resolved_target = target_path.resolve()
    resolved_root = self.workspace_root.resolve()
    try:
        common = os.path.commonpath([resolved_root, resolved_target])
        if common != str(resolved_root):
            raise PermissionError(f"Access Denied: Path '{target_path}' lies outside workspace root '{self.workspace_root}'.")
    except ValueError:
        raise PermissionError(f"Access Denied: Path '{target_path}' is on a different drive than workspace root.")
    return resolved_target
```

### Threat Vectors Mitigated
- **Path Traversal Attacks (`../../`):** Canonical path resolution flattens relative hops prior to the common path check.
- **Cross-Drive Traversal (Windows `C:\` $\to$ `D:\`):** `ValueError` triggered by `os.path.commonpath` across differing drives is caught and converts into a strict `PermissionError`.
- **Symlink Hijacking:** `Path.resolve()` evaluates symbolic links to their real filesystem destinations before validation.

---

## 3. Subprocess & OS Process Group Isolation

When agents invoke terminal commands via `TerminalTool`:
1. **OS Process Groups:** Commands execute within an isolated process group (`creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` on Windows; `preexec_fn=os.setsid` on POSIX). This guarantees that terminating the supervisor cancels all spawned child forks and daemons.
2. **Wall-Clock Timeouts:** Every command has a strict timeout (default: 60 seconds). Overrunning commands are forcefully terminated via SIGTERM/SIGKILL tree walks.
3. **Bounded Stream Buffering:** Output streams are capped at 100KB per execution. Excess characters are truncated with an explicit `[OUTPUT TRUNCATED]` notice to protect daemon memory.

---

## 4. Secret & Credential Redaction Engine

All strings destined for logging, UI activity cards, or database records are sanitized through a regex redaction pipeline:

```python
REDACTION_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",                  # OpenAI Keys
    r"ghp_[a-zA-Z0-9]{36}",                   # GitHub Personal Access Tokens
    r"gho_[a-zA-Z0-9]{36}",                   # GitHub OAuth Tokens
    r"AKIA[0-9A-Z]{16}",                      # AWS Access Key IDs
    r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",        # Bearer Authorization Tokens
    r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----[\s\S]+?-----END \1 PRIVATE KEY-----", # Private Keys
]
```

Matched credential tokens are replaced with `[REDACTED_SECRET]` before persistence or transmission over the WebSocket bus.

---

## 5. Human-in-the-Loop Risk Governance Matrix

Every tool invocation evaluates against the Risk Matrix before execution:

| Risky Action Type | Trigger Condition | Risk Level | Operator Decision Required |
| :--- | :--- | :---: | :---: |
| `git_push` | Any `git push` command | **CRITICAL** | Yes (Always) |
| `delete_file` | Deleting files in workspace | **HIGH** | Yes |
| `overwrite_file` | Full replacement of core configuration files | **MEDIUM** | Yes |
| `shell_command` | Commands containing `rm -rf`, `format`, `dd`, `curl \| sh` | **CRITICAL** | Yes |
| `package_installation` | `pip install`, `npm install` | **MEDIUM** | Yes |
| `external_network` | Unsanctioned outbound socket connections | **HIGH** | Yes |

### Operator Actions
- **`APPROVE_ONCE`:** Authorizes the single tool call currently pending.
- **`APPROVE_SESSION`:** Whitelists the action pattern for the remainder of the active agent session.
- **`REJECT`:** Aborts the tool execution immediately, raising an `ApprovalRejectedError` and prompting the agent to choose an alternative strategy.
