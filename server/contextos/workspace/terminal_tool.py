import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from typing import Optional, Dict

from contextos.config import settings
from .base import CommandResult

class TerminalTool:
    """
    Sandboxed Terminal Tool adapted from OpenHands software-agent-sdk.
    Executes commands within dedicated OS process groups with timeout and output size limits.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def _sanitize_env(self) -> Dict[str, str]:
        """Filters sensitive API keys and secrets from child process environment."""
        clean_env = os.environ.copy()
        for key in list(clean_env.keys()):
            for pattern in settings.SENSITIVE_KEY_PATTERNS:
                if pattern in key.upper():
                    # Mask sensitive variables for child subprocess
                    clean_env.pop(key, None)
                    break
        return clean_env

    def execute(
        self,
        command: str,
        timeout_seconds: Optional[int] = None,
        working_dir: Optional[str | Path] = None,
    ) -> CommandResult:
        timeout = timeout_seconds or settings.COMMAND_TIMEOUT_SECONDS
        cwd = Path(working_dir).resolve() if working_dir else self.workspace_root

        # Process group flags for Windows vs POSIX
        kwargs: dict = {
            "cwd": str(cwd),
            "env": self._sanitize_env(),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "shell": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }

        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        start_time = time.perf_counter()
        timed_out = False
        truncated = False
        stdout_str = ""
        stderr_str = ""
        exit_code = -1

        try:
            process = subprocess.Popen(command, **kwargs)
            try:
                stdout_str, stderr_str = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                self._terminate_process_group(process)
                try:
                    stdout_str, stderr_str = process.communicate(timeout=2)
                except Exception:
                    pass
                exit_code = -9
                stderr_str += f"\n[ContextOS Process Manager] Command timed out after {timeout} seconds."

        except Exception as e:
            stderr_str = f"[ContextOS Execution Error] Failed to launch process: {str(e)}"
            exit_code = 1

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Truncate output buffer if larger than limit
        max_bytes = settings.MAX_OUTPUT_BYTES
        if len(stdout_str.encode('utf-8')) > max_bytes:
            stdout_str = stdout_str[:max_bytes] + "\n...[OUTPUT TRUNCATED: Exceeded 100KB buffer limit]"
            truncated = True

        return CommandResult(
            exit_code=exit_code,
            stdout=stdout_str,
            stderr=stderr_str,
            duration_ms=duration_ms,
            timed_out=timed_out,
            truncated=truncated,
        )

    def _terminate_process_group(self, process: subprocess.Popen):
        """Cleanly terminates the entire child process group."""
        try:
            if sys.platform == "win32":
                # Send CTRL_BREAK_EVENT to process group on Windows
                process.send_signal(signal.CTRL_BREAK_EVENT)
                time.sleep(0.2)
                process.kill()
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                time.sleep(0.2)
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
