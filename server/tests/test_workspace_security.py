import pytest
import tempfile
from pathlib import Path
from contextos.workspace.local import LocalWorkspace
from contextos.workspace.file_editor_tool import FileEditorTool

def test_path_jailing_prevents_traversal():
    with tempfile.TemporaryDirectory() as tmp_root:
        ws = LocalWorkspace(root_path=Path(tmp_root))

        # Safe path inside workspace
        safe_path = ws.validate_path("subdir/test.txt")
        assert safe_path.is_relative_to(ws.root_path)

        # Attack: parent directory traversal
        with pytest.raises(PermissionError) as exc_info:
            ws.validate_path("../../sensitive_file.txt")
        assert "path traversal outside workspace root" in str(exc_info.value)

        # Attack: absolute path outside workspace
        with pytest.raises(PermissionError) as exc_info:
            ws.validate_path("C:\\Windows\\System32\\calc.exe" if Path("C:\\").exists() else "/etc/passwd")
        assert "path traversal" in str(exc_info.value).lower()

def test_file_editor_surgical_replace_and_delete():
    with tempfile.TemporaryDirectory() as tmp_root:
        ws = LocalWorkspace(root_path=Path(tmp_root))
        editor = FileEditorTool(ws)

        # 1. Create file
        editor.write("src/app.py", "def run():\n    return 42\n")
        assert (Path(tmp_root) / "src" / "app.py").exists()

        # 2. View file
        content = editor.view("src/app.py")
        assert "return 42" in content

        # 3. Surgical str_replace
        editor.str_replace("src/app.py", "return 42", "return 100")
        updated = editor.view("src/app.py")
        assert "return 100" in updated

        # 4. Delete file
        editor.delete("src/app.py")
        assert not (Path(tmp_root) / "src" / "app.py").exists()

def test_secret_redaction():
    with tempfile.TemporaryDirectory() as tmp_root:
        ws = LocalWorkspace(root_path=Path(tmp_root))
        raw_log = "Error with key sk-1234567890abcdef1234567890 and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = ws.redact_secrets(raw_log)

        assert "sk-1234567890" not in sanitized
        assert "[REDACTED_API_KEY]" in sanitized
        assert "[REDACTED_TOKEN]" in sanitized
