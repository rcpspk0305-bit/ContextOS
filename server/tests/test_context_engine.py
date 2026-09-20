import pytest
import tempfile
from pathlib import Path
import httpx

from contextos.models.context import ContextBudget, ContextTier, ContextBundle
from contextos.context.tokenizer import count_tokens
from contextos.context.compressor import ASTCompressor
from contextos.context.compiler import ContextCompiler
from contextos.storage.db import DatabaseManager
import contextos.storage.db as db_mod
from contextos.memory.engine import memory_engine
from contextos.api.app import create_app

def test_tokenizer_heuristic():
    text = "def hello_world():\n    return 'Hello, ContextOS!'\n"
    tokens = count_tokens(text)
    assert tokens > 0
    assert tokens < len(text)
    assert count_tokens("") == 0

def test_ast_compressor_python():
    compressor = ASTCompressor()
    py_code = """
\"\"\"Data processing module.\"\"\"
import os
import sys

API_VERSION = "2.0.0"

class DataPipeline:
    \"\"\"High throughput data pipeline.\"\"\"

    def __init__(self, name: str, batch_size: int = 100):
        self.name = name
        self.batch_size = batch_size
        self._cache = {}
        for i in range(100):
            self._cache[i] = i * 2

    async def process_record(self, record_id: str, payload: dict) -> bool:
        \"\"\"Process an individual record with validation.\"\"\"
        if not record_id:
            raise ValueError("Invalid record_id")
        # Heavy implementation lines that take up tons of tokens
        a = 1 + 2
        b = a * 3
        c = b / 4
        return True

    def reset_state(self) -> None:
        self._cache.clear()

def standalone_helper(x: int, y: int) -> int:
    \"\"\"Helper calculation.\"\"\"
    return x + y
"""
    raw_tokens = count_tokens(py_code)
    compressed = compressor.compress("pipeline.py", py_code)
    compressed_tokens = count_tokens(compressed)

    assert "class DataPipeline:" in compressed
    assert "def __init__(self, name: str, batch_size: int" in compressed
    assert "async def process_record(self, record_id: str, payload: dict) -> bool:" in compressed
    assert "def standalone_helper(x: int, y: int) -> int:" in compressed
    assert "Heavy implementation lines" not in compressed  # Body pruned
    assert compressed_tokens < raw_tokens

def test_ast_compressor_typescript():
    compressor = ASTCompressor()
    ts_code = """
export interface UserProfile {
    id: string;
    username: string;
    email: string;
    roles: string[];
    createdAt: Date;
}

export type AuthState = "authenticated" | "anonymous" | "expired";

export class SessionManager {
    private token: string;
    constructor(token: string) {
        this.token = token;
    }
}

export async function authenticateUser(token: string): Promise<UserProfile> {
    // 50 lines of JWT parsing and validation logic...
    const decoded = token.split('.');
    return { id: "u1", username: "alice", email: "alice@test.com", roles: ["admin"], createdAt: new Date() };
}

export const formatUserName = (profile: UserProfile): string => {
    return `${profile.username} (${profile.email})`;
};
"""
    raw_tokens = count_tokens(ts_code)
    compressed = compressor.compress("auth.ts", ts_code)
    compressed_tokens = count_tokens(compressed)

    assert "export interface UserProfile" in compressed
    assert "export type AuthState" in compressed
    assert "export function authenticateUser(token: string): Promise<UserProfile>;" in compressed
    assert "export const formatUserName" in compressed
    assert compressed_tokens < raw_tokens

@pytest.mark.asyncio
async def test_token_budget_cannot_be_exceeded():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws_root = Path(tmp_dir) / "workspace"
        ws_root.mkdir()

        # Generate large code files (> 20,000 raw tokens)
        for i in range(15):
            code_lines = [
                f"# Module {i}",
                f"class Service{i}:",
                '    """Service documentation."""',
            ]
            for m in range(25):
                code_lines.extend([
                    f"    def method_{m}(self, arg1: str, arg2: int) -> bool:",
                    f'        """Method {m} description."""',
                    f"        val = '{'x' * 200}'",
                    f"        return len(val) > 100",
                ])
            (ws_root / f"service_{i}.py").write_text("\n".join(code_lines), encoding="utf-8")

        test_db = DatabaseManager(Path(tmp_dir) / "test_budget.db")
        old_db = db_mod.db
        db_mod.db = test_db

        compiler = ContextCompiler(workspace_root=ws_root)
        try:
            # Enforce tight budget of 2,500 tokens on 20,000+ token repository
            budget_limit = 2500
            bundle = await compiler.compile(
                intent="Fix method_5 in Service2",
                active_task="Refactor Service2.method_5 implementation",
                budget=budget_limit,
                workspace_root=ws_root,
            )

            # Mathematical Guarantee Assertions
            assert bundle.total_tokens <= budget_limit
            assert bundle.budget.total_budget == budget_limit
            assert bundle.candidate_tokens > 15000
            assert bundle.tokens_avoided > 12000
            assert bundle.reduction_ratio > 75.0

            # Verify partition caps were strictly honored
            assert bundle.tier_token_counts["system"] <= bundle.budget.system_budget
            assert bundle.tier_token_counts["task"] <= bundle.budget.task_budget
            assert bundle.tier_token_counts["memory"] <= bundle.budget.memory_budget
            assert bundle.tier_token_counts["source"] <= bundle.budget.source_budget
        finally:
            db_mod.db = old_db

@pytest.mark.asyncio
async def test_4_tier_partitioning_and_structure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws_root = Path(tmp_dir) / "workspace"
        ws_root.mkdir()

        (ws_root / "app.py").write_text(
            "def run_app():\n    return 'Running'\n",
            encoding="utf-8",
        )

        test_db = DatabaseManager(Path(tmp_dir) / "test_tiers.db")
        old_db = db_mod.db
        db_mod.db = test_db

        # Add memory and decision
        await memory_engine.remember("Authentication uses session cookies", session_id="test_sess")
        memory_engine.record_decision(
            title="Use FastAPI for HTTP API",
            context="Need high-performance asynchronous API.",
            decision="Adopted FastAPI with Pydantic v2 schemas.",
            session_id="test_sess",
        )

        compiler = ContextCompiler(workspace_root=ws_root)
        try:
            bundle = await compiler.compile(
                intent="Query auth status in app",
                active_task="Verify run_app returns healthy",
                session_id="test_sess",
                budget=4000,
                workspace_root=ws_root,
            )

            assert bundle.total_tokens <= 4000
            prompt = bundle.compiled_prompt

            # Verify all 4 tier section headers exist in compiled prompt
            assert "=== TIER 1: SYSTEM INSTRUCTIONS ===" in prompt
            assert "=== TIER 2: ACTIVE TASK & STATE ===" in prompt
            assert "=== TIER 3: PERSISTENT MEMORY & ARCHITECTURAL DECISIONS ===" in prompt
            assert "=== TIER 4: WORKSPACE SOURCE CODE & INTERFACES ===" in prompt

            # Verify memory and decision appeared
            assert "FastAPI" in prompt
            assert "Authentication uses session cookies" in prompt
        finally:
            db_mod.db = old_db

@pytest.mark.asyncio
async def test_context_api_endpoints():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_api_ctx.db")
        old_db = db_mod.db
        db_mod.db = test_db

        app = create_app()
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                # 1. Compile Context
                compile_res = await client.post("/api/context/compile", json={
                    "intent": "Implement authentication endpoints",
                    "active_task": "Build JWT middleware and auth router",
                    "budget": 5000,
                    "session_id": "session_api_test",
                })
                assert compile_res.status_code == 200
                bundle_data = compile_res.json()
                assert bundle_data["total_tokens"] <= 5000
                assert bundle_data["budget"]["total_budget"] == 5000
                assert "compiled_prompt" in bundle_data

                # 2. Get Context Metrics
                metrics_res = await client.get("/api/context/metrics")
                assert metrics_res.status_code == 200
                metrics_data = metrics_res.json()
                assert metrics_data["total_compilations"] >= 1
                assert metrics_data["estimated"] is True
        finally:
            db_mod.db = old_db
