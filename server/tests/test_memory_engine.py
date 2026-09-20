import pytest
import tempfile
from pathlib import Path
import httpx

from contextos.models.memory import (
    MemoryType,
    MemoryItem,
    DecisionRecord,
    Checkpoint,
    UniversalSessionEnvelope,
)
from contextos.memory.engine import MemoryEngine
from contextos.memory.adapters import (
    CodexSessionAdapter,
    AGYSessionAdapter,
    GenericJsonSessionAdapter,
)
from contextos.storage.db import DatabaseManager
import contextos.storage.db as db_mod
from contextos.api.app import create_app

@pytest.mark.asyncio
async def test_memory_crud_all_types():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_mem.db")
        old_db = db_mod.db
        db_mod.db = test_db

        engine = MemoryEngine()
        try:
            # 1. Test all 6 MemoryTypes
            types_to_test = [
                (MemoryType.SEMANTIC, "FastAPI uses Pydantic for request validation", ["architecture", "fastapi"]),
                (MemoryType.EPISODIC, "Deployed build v1.0.2 to staging environment", ["deployment", "staging"]),
                (MemoryType.DECISION, "Chose SQLite for local zero-dependency storage", ["storage", "adr"]),
                (MemoryType.TASK, "Implement Phase 4 ContextOS Memory Engine", ["milestone", "phase4"]),
                (MemoryType.FAILURE, "Port collision on 8000 when starting daemon", ["bug", "network"]),
                (MemoryType.CODE_REFERENCE, "FileEditorTool in server/contextos/workspace/file_editor_tool.py", ["tools", "code"]),
            ]

            created_ids = []
            for mtype, content, tags in types_to_test:
                item = await engine.remember(
                    content=content,
                    memory_type=mtype,
                    tags=tags,
                    metadata={"source": "test_suite"},
                )
                assert item.id.startswith("mem_")
                assert item.type == mtype
                assert item.content == content
                assert item.tags == tags
                created_ids.append(item.id)

            # 2. Retrieve by ID & verify access count
            first_id = created_ids[0]
            fetched = test_db.get_memory(first_id)
            assert fetched is not None
            assert fetched.access_count == 1
            fetched2 = test_db.get_memory(first_id)
            assert fetched2.access_count == 2

            # 3. Filter by type
            failure_mems = await engine.recall(memory_type=MemoryType.FAILURE)
            assert len(failure_mems) == 1
            assert "Port collision" in failure_mems[0].content

            # 4. Filter by tags
            tag_mems = await engine.recall(tags=["adr"])
            assert len(tag_mems) == 1
            assert tag_mems[0].type == MemoryType.DECISION

            # 5. Forget memory
            deleted = engine.forget(first_id)
            assert deleted is True
            assert test_db.get_memory(first_id) is None
        finally:
            db_mod.db = old_db


@pytest.mark.asyncio
async def test_memory_search_and_keyword_relevance():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_search.db")
        old_db = db_mod.db
        db_mod.db = test_db

        engine = MemoryEngine()
        try:
            await engine.remember("Authentication utilizes JWT bearer tokens", tags=["auth"])
            await engine.remember("Database indexing strategy uses B-tree and full-text FTS5", tags=["db"])
            await engine.remember("Terminal processes execute in isolated OS process groups", tags=["security"])

            # Search by keyword
            results = await engine.recall(query="Authentication")
            assert len(results) >= 1
            assert "Authentication" in results[0].content

            results_db = await engine.recall(query="database indexing")
            assert len(results_db) >= 1
            assert "B-tree" in results_db[0].content
        finally:
            db_mod.db = old_db


def test_decision_records_adr():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_adr.db")
        old_db = db_mod.db
        db_mod.db = test_db

        engine = MemoryEngine()
        try:
            adr = engine.record_decision(
                title="Use SQLite with FTS5 for Local Context Storage",
                context="Need local-first, zero-dependency persistence that works across Windows/macOS/Linux.",
                decision="Adopt SQLite with WAL mode and FTS5 full-text indexing.",
                consequences="Eliminates remote DB dependencies; simplifies setup for single-tenant local AIOS.",
                status="accepted",
                alternatives_considered=["DuckDB", "PostgreSQL", "ChromaDB standalone server"],
                project_id="contextos",
                session_id="session_adr_test",
            )
            assert adr.id.startswith("adr_")
            assert adr.status == "accepted"
            assert len(adr.alternatives_considered) == 3

            # Query decisions
            decisions = engine.get_decisions(project_id="contextos")
            assert len(decisions) == 1
            assert decisions[0].title == "Use SQLite with FTS5 for Local Context Storage"
            assert "DuckDB" in decisions[0].alternatives_considered
        finally:
            db_mod.db = old_db


def test_session_checkpoint_and_resumption():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_chk.db")
        old_db = db_mod.db
        db_mod.db = test_db

        engine = MemoryEngine()
        try:
            # 1. Record decision
            engine.record_decision(
                title="Adopt 4-Tier Context Engine",
                context="Agents exceed token limits when passing entire repo.",
                decision="Compile context into strict 4-tier token budget.",
                session_id="session_chk_1",
            )

            # 2. Save checkpoint
            chk = engine.checkpoint(
                session_id="session_chk_1",
                agent_id="ag_coder_01",
                state_summary="Implemented memory data models and SQLite FTS5 table schemas.",
                active_task="Wire memory engine to REST routes",
                modified_files=["server/contextos/models/memory.py", "server/contextos/storage/db.py"],
                open_decisions=["Cache size for FTS5 queries"],
                context_tokens_used=4200,
            )
            assert chk.id.startswith("chk_")

            # 3. Resume by checkpoint ID
            resumption = engine.resume(chk.id)
            assert resumption["resumed_task"] == "Wire memory engine to REST routes"
            assert "server/contextos/models/memory.py" in resumption["modified_files"]
            assert len(resumption["decisions"]) == 1
            assert resumption["decisions"][0].title == "Adopt 4-Tier Context Engine"
            assert "Resuming work on" in resumption["instructions"]

            # 4. Resume by session ID
            resumption_session = engine.resume("session_chk_1")
            assert resumption_session["checkpoint"].id == chk.id
        finally:
            db_mod.db = old_db


def test_verify_file_references_handles_missing_files_gracefully():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws_root = Path(tmp_dir)
        # Create one real file
        real_file = ws_root / "existing_file.py"
        real_file.write_text("print('hello')", encoding="utf-8")

        test_db = DatabaseManager(ws_root / "test_ref.db")
        old_db = db_mod.db
        db_mod.db = test_db

        engine = MemoryEngine()
        try:
            item_real = MemoryItem(
                content="Existing script reference",
                metadata={"file_path": "existing_file.py"},
            )
            item_missing = MemoryItem(
                content="Deleted old script reference",
                metadata={"file_path": "deleted_script.py"},
            )
            item_no_file = MemoryItem(
                content="General architectural principle",
                metadata={"concept": "pure_logic"},
            )

            results = engine.verify_file_references([item_real, item_missing, item_no_file], ws_root)
            assert len(results) == 3

            # Item 1: Real file
            assert results[0]["exists"] is True
            assert results[0]["status"] == "valid"

            # Item 2: Missing file - handled gracefully without exception!
            assert results[1]["exists"] is False
            assert results[1]["status"] == "file_missing"
            assert item_missing.metadata["status"] == "file_missing"

            # Item 3: No file path
            assert results[2]["has_file"] is False
        finally:
            db_mod.db = old_db


def test_cross_agent_session_adapters():
    # 1. Codex format input
    codex_raw = {
        "session_id": "session_cross_agent_1",
        "title": "Refactor Data Layer",
        "summary": "Migrated from in-memory dictionary to SQLite",
        "messages": [
            {"role": "user", "content": "Refactor the database storage layer."},
            {"role": "assistant", "content": "I will update db.py to support SQLite.", "tool_calls": [{"id": "tc1", "name": "file_write"}]},
            {"role": "tool", "content": "File written successfully.", "tool_call_id": "tc1"},
        ],
        "artifacts": ["server/contextos/storage/db.py"],
        "decisions": ["Used SQLite with WAL mode"],
    }

    codex_adapter = CodexSessionAdapter()
    envelope = codex_adapter.to_universal(codex_raw)
    assert envelope.source_agent == "codex"
    assert len(envelope.turns) == 3
    assert envelope.turns[0].role == "user"
    assert envelope.turns[1].role == "assistant"
    assert envelope.turns[1].tool_calls is not None
    assert len(envelope.artifacts) == 1

    # 2. Convert Universal Envelope -> AGY / Gemini format
    agy_adapter = AGYSessionAdapter()
    agy_payload = agy_adapter.from_universal(envelope)
    assert agy_payload["agent"] == "agy"
    assert len(agy_payload["contents"]) == 3
    assert agy_payload["contents"][0]["role"] == "user"
    assert agy_payload["contents"][1]["role"] == "model"
    assert "function_call" in agy_payload["contents"][1]["parts"][1]

    # 3. Convert AGY format -> Universal Envelope
    agy_envelope = agy_adapter.to_universal(agy_payload)
    assert agy_envelope.source_agent == "agy"
    assert len(agy_envelope.turns) == 3
    assert agy_envelope.turns[1].role == "assistant"

    # 4. Generic Adapter
    generic_adapter = GenericJsonSessionAdapter()
    gen_envelope = generic_adapter.to_universal({
        "session_id": "gen_1",
        "turns": ["Hello", {"role": "assistant", "content": "World"}]
    })
    assert len(gen_envelope.turns) == 2


@pytest.mark.asyncio
async def test_memory_api_endpoints():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_api_mem.db")
        old_db = db_mod.db
        db_mod.db = test_db

        app = create_app()
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                # 1. Create Memory
                mem_res = await client.post("/api/memories", json={
                    "content": "Tree-sitter extracts AST symbols without execution",
                    "type": "semantic",
                    "tags": ["ast", "parsing"],
                })
                assert mem_res.status_code == 200
                mem_data = mem_res.json()
                mem_id = mem_data["id"]
                assert mem_data["type"] == "semantic"

                # 2. Search Memories
                search_res = await client.get("/api/memories?query=Tree-sitter")
                assert search_res.status_code == 200
                results = search_res.json()
                assert len(results) >= 1

                # 3. Create Decision
                adr_res = await client.post("/api/decisions", json={
                    "title": "Use Pydantic v2 SettingsConfigDict",
                    "context": "Pydantic v2 deprecated inner Config class.",
                    "decision": "Use SettingsConfigDict(env_prefix='CONTEXTOS_')",
                    "consequences": "Clean type-safe configuration loading.",
                    "status": "accepted",
                    "alternatives_considered": ["os.environ direct lookups"],
                })
                assert adr_res.status_code == 200
                assert adr_res.json()["status"] == "accepted"

                # 4. List Decisions
                list_adr = await client.get("/api/decisions")
                assert list_adr.status_code == 200
                assert len(list_adr.json()) == 1

                # 5. Create Checkpoint
                chk_res = await client.post("/api/checkpoints", json={
                    "session_id": "session_api_chk",
                    "agent_id": "ag_api_01",
                    "state_summary": "Passed all API endpoints verification",
                    "active_task": "Prepare Phase 5 context engine",
                    "modified_files": ["server/contextos/api/routes.py"],
                    "open_decisions": [],
                    "context_tokens_used": 3500,
                })
                assert chk_res.status_code == 200
                chk_id = chk_res.json()["id"]

                # 6. Resume Checkpoint
                resume_res = await client.post(f"/api/checkpoints/{chk_id}/resume")
                assert resume_res.status_code == 200
                resume_data = resume_res.json()
                assert resume_data["resumed_task"] == "Prepare Phase 5 context engine"

                # 7. Import Session
                import_res = await client.post("/api/sessions/import", json={
                    "source_agent": "codex",
                    "data": {
                        "session_id": "session_imported",
                        "title": "Imported Codex Session",
                        "messages": [
                            {"role": "user", "content": "What is the status?"},
                            {"role": "assistant", "content": "All systems operational."},
                        ],
                    }
                })
                assert import_res.status_code == 200
                imported_env = import_res.json()
                assert imported_env["source_agent"] == "codex"
                assert len(imported_env["turns"]) == 2

                # 8. Delete Memory
                del_res = await client.delete(f"/api/memories/{mem_id}")
                assert del_res.status_code == 200
        finally:
            db_mod.db = old_db
