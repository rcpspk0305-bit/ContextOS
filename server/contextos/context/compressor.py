import ast
import re
from pathlib import Path
from typing import Optional, Dict, Any

class ASTCompressor:
    """
    Extracts structural interface signatures from source code files.
    Compresses large codebases by 70-90% while retaining critical type contracts,
    class methods, function signatures, and docstrings.
    """

    def compress(self, file_path: str, content: str) -> str:
        ext = Path(file_path).suffix.lower()

        if ext == ".py":
            return self.compress_python(content)
        elif ext in (".ts", ".tsx", ".js", ".jsx"):
            return self.compress_typescript(content)
        elif ext in (".md", ".markdown"):
            return self.compress_markdown(content)
        elif ext in (".json", ".yaml", ".yml"):
            return self.compress_config(content)
        else:
            return self.compress_generic(content)

    def compress_python(self, code: str) -> str:
        """Parses Python code using the standard `ast` library and emits signatures."""
        try:
            tree = ast.parse(code)
        except Exception:
            return self._regex_compress_python(code)

        lines = []

        # Module docstring
        docstring = ast.get_docstring(tree)
        if docstring:
            first_line = docstring.strip().split("\n")[0]
            lines.append(f'"""{first_line}"""\n')

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                base_str = f"({', '.join(bases)})" if bases else ""
                lines.append(f"class {node.name}{base_str}:")

                class_doc = ast.get_docstring(node)
                if class_doc:
                    first = class_doc.strip().split("\n")[0]
                    lines.append(f'    """{first}"""')

                methods_found = False
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods_found = True
                        sig = self._format_py_function(item, indent="    ")
                        lines.append(sig)

                if not methods_found:
                    lines.append("    ...")
                lines.append("")

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = self._format_py_function(node, indent="")
                lines.append(sig)
                lines.append("")

            elif isinstance(node, ast.Assign):
                # Include constant or type alias assignments
                for target in node.targets:
                    if isinstance(target, ast.Name) and (target.id.isupper() or target.id == "__all__"):
                        try:
                            lines.append(f"{target.id} = {ast.unparse(node.value)}")
                        except Exception:
                            pass

        compressed = "\n".join(lines).strip()
        return compressed if compressed else code[:400] + "\n# ... [truncated]"

    def _format_py_function(self, node: ast.AST, indent: str = "") -> str:
        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        try:
            args = ast.unparse(node.args)
        except Exception:
            args = "..."
        returns = f" -> {ast.unparse(node.returns)}" if getattr(node, "returns", None) else ""
        header = f"{indent}{prefix}{node.name}({args}){returns}:"

        doc = ast.get_docstring(node)
        if doc:
            first_line = doc.strip().split("\n")[0]
            return f'{header}\n{indent}    """{first_line}"""\n{indent}    ...'
        else:
            return f"{header}\n{indent}    ..."

    def _regex_compress_python(self, code: str) -> str:
        """Fallback regex extraction for invalid/incomplete Python syntax."""
        pattern = re.compile(r"^[ \t]*(class\s+\w+.*?:|async\s+def\s+\w+.*?:|def\s+\w+.*?:)", re.MULTILINE)
        matches = pattern.findall(code)
        if matches:
            return "\n".join(f"{m}\n    ..." for m in matches)
        return code[:400] + "\n# ... [truncated]"

    def compress_typescript(self, code: str) -> str:
        """Extracts TypeScript and JavaScript interfaces, types, functions, and classes."""
        lines = []

        # 1. Interfaces
        for m in re.finditer(r"export\s+interface\s+(\w+)(?:<.*?>)?(?:\s+extends\s+[^{]+)?\s*\{([^}]+)\}", code):
            name = m.group(1)
            lines.append(f"export interface {name} {{ ... }}")

        # 2. Type aliases
        for m in re.finditer(r"export\s+type\s+(\w+)(?:<.*?>)?\s*=\s*([^;]+);", code):
            name = m.group(1)
            val = m.group(2).strip().split("\n")[0]
            lines.append(f"export type {name} = {val[:60]}...")

        # 3. Classes and exported components
        for m in re.finditer(r"export\s+(?:default\s+)?class\s+(\w+)(?:<.*?>)?(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?", code):
            lines.append(f"{m.group(0)} {{ ... }}")

        # 4. Functions
        for m in re.finditer(r"export\s+(?:async\s+)?function\s+(\w+)(?:<.*?>)?\s*\((.*?)\)(?:\s*:\s*([^{]+))?", code):
            fn_name = m.group(1)
            params = m.group(2)
            ret = f": {m.group(3).strip()}" if m.group(3) else ""
            lines.append(f"export function {fn_name}({params}){ret};")

        # 5. Exported const arrow functions
        for m in re.finditer(r"export\s+const\s+(\w+)\s*(?::\s*([^=]+))?\s*=\s*(?:async\s*)?\((.*?)\)(?:\s*:\s*([^=]+))?\s*=>", code):
            const_name = m.group(1)
            params = m.group(3)
            ret = f": {m.group(4).strip()}" if m.group(4) else ""
            lines.append(f"export const {const_name} = ({params}){ret} => ...;")

        compressed = "\n".join(lines).strip()
        return compressed if compressed else code[:400] + "\n// ... [truncated]"

    def compress_markdown(self, content: str) -> str:
        """Extracts markdown headings and bullet summaries."""
        lines = []
        for line in content.splitlines():
            if line.startswith("#"):
                lines.append(line)
        return "\n".join(lines) if lines else content[:300]

    def compress_config(self, content: str) -> str:
        """Truncates config to top 25 lines."""
        lines = content.splitlines()[:25]
        return "\n".join(lines) + ("\n# ... [truncated]" if len(content.splitlines()) > 25 else "")

    def compress_generic(self, content: str) -> str:
        return content[:500] + ("\n... [truncated]" if len(content) > 500 else "")

ast_compressor = ASTCompressor()
