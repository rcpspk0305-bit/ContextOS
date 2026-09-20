import os
import re
from pathlib import Path
from typing import Optional

from contextos.config import settings
from .base import Workspace, CommandResult
from .terminal_tool import TerminalTool

class LocalWorkspace(Workspace):
    def __init__(self, root_path: Optional[Path] = None):
        self._root = (root_path or settings.PROJECT_ROOT).resolve()
        self._terminal = TerminalTool(workspace_root=self._root)

    @property
    def root_path(self) -> Path:
        return self._root

    def validate_path(self, target_path: str | Path) -> Path:
        """
        Guarantees target path is strictly contained inside workspace root boundary.
        Prevents directory traversal attacks via '../' or out-of-boundary absolute paths.
        """
        raw_path = Path(target_path)
        if not raw_path.is_absolute():
            resolved = (self._root / raw_path).resolve()
        else:
            resolved = raw_path.resolve()

        # Strict commonpath verification
        try:
            common = os.path.commonpath([str(self._root), str(resolved)])
            if common != str(self._root):
                raise PermissionError(
                    f"Security violation: path traversal outside workspace root detected: {target_path}"
                )
        except ValueError:
            # Different drives on Windows (e.g. C: vs D:)
            raise PermissionError(
                f"Security violation: path traversal across drive letters detected: {target_path}"
            )

        return resolved

    def redact_secrets(self, text: str) -> str:
        """Redacts sensitive credentials, tokens, and API keys."""
        redacted = text
        # OpenAI, GitHub, Gemini, Bearer patterns
        patterns = [
            (r'sk-[a-zA-Z0-9_-]{20,}', '[REDACTED_API_KEY]'),
            (r'AIza[a-zA-Z0-9_-]{35}', '[REDACTED_GEMINI_KEY]'),
            (r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
            (r'(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}', r'\1[REDACTED_TOKEN]'),
            (r'(password|secret|token|key)\s*[:=]\s*["\']?([^"\'\s]+)["\']?', r'\1=[REDACTED]'),
        ]
        for pattern, repl in patterns:
            redacted = re.sub(pattern, repl, redacted, flags=re.IGNORECASE)
        return redacted

    def execute_command(self, command: str, timeout_seconds: Optional[int] = None) -> CommandResult:
        result = self._terminal.execute(command, timeout_seconds=timeout_seconds)
        # Redact secrets from output
        result.stdout = self.redact_secrets(result.stdout)
        result.stderr = self.redact_secrets(result.stderr)
        return result

    def read_file(self, target_path: str | Path, offset_lines: int = 1, limit_lines: int = 200) -> str:
        safe_path = self.validate_path(target_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")

        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        start = max(0, offset_lines - 1)
        end = min(len(lines), start + limit_lines)
        return "".join(lines[start:end])

    def write_file(self, target_path: str | Path, content: str) -> None:
        safe_path = self.validate_path(target_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def delete_file(self, target_path: str | Path) -> None:
        safe_path = self.validate_path(target_path)
        if safe_path.exists():
            if safe_path.is_dir():
                raise PermissionError(f"Directory deletion must be handled explicitly: {target_path}")
            safe_path.unlink()
