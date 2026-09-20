from pathlib import Path
from typing import Optional, List, Tuple
from .base import Workspace

class FileEditorTool:
    """
    Surgical file editing tool adapted from OpenHands software-agent-sdk.
    Enforces path boundaries and supports viewing, writing, chunk replacement, and line edits.
    """

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def view(self, path: str, view_range: Optional[Tuple[int, int]] = None) -> str:
        safe_path = self.workspace.validate_path(path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        offset = view_range[0] if view_range else 1
        limit = (view_range[1] - view_range[0] + 1) if view_range else 500
        return self.workspace.read_file(safe_path, offset_lines=offset, limit_lines=limit)

    def write(self, path: str, content: str) -> str:
        safe_path = self.workspace.validate_path(path)
        self.workspace.write_file(safe_path, content)
        return f"Successfully wrote {len(content)} characters to {path}"

    def str_replace(self, path: str, old_str: str, new_str: str) -> str:
        safe_path = self.workspace.validate_path(path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        count = content.count(old_str)
        if count == 0:
            raise ValueError(f"Target string not found in {path}")
        if count > 1:
            raise ValueError(f"Target string occurs {count} times in {path}. Must be unique for surgical replacement.")

        new_content = content.replace(old_str, new_str, 1)
        self.workspace.write_file(safe_path, new_content)
        return f"Successfully replaced unique match in {path}"

    def delete(self, path: str) -> str:
        safe_path = self.workspace.validate_path(path)
        self.workspace.delete_file(safe_path)
        return f"Successfully deleted {path}"
