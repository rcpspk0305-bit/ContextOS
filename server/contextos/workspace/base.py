from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

class CommandResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    truncated: bool = False

class Workspace(ABC):
    """
    Abstract interface for agent workspace execution.
    Can be implemented via LocalWorkspace (V1) or DockerWorkspace (future container isolation)
    without rewriting AgentRuntime.
    """

    @property
    @abstractmethod
    def root_path(self) -> Path:
        """Returns the base boundary directory of this workspace."""
        pass

    @abstractmethod
    def validate_path(self, target_path: str | Path) -> Path:
        """
        Validates target path against root boundary.
        Raises PermissionError if path attempts traversal outside workspace root.
        """
        pass

    @abstractmethod
    def execute_command(self, command: str, timeout_seconds: Optional[int] = None) -> CommandResult:
        """Executes a command within the sandboxed workspace."""
        pass

    @abstractmethod
    def read_file(self, target_path: str | Path, offset_lines: int = 1, limit_lines: int = 200) -> str:
        """Reads content from a validated file path."""
        pass

    @abstractmethod
    def write_file(self, target_path: str | Path, content: str) -> None:
        """Writes content to a validated file path."""
        pass

    @abstractmethod
    def delete_file(self, target_path: str | Path) -> None:
        """Deletes a file at a validated file path."""
        pass
