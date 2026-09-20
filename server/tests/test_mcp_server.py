import pytest
import tempfile
from pathlib import Path

from contextos.mcp.server import create_mcp_server
from contextos.storage.db import DatabaseManager
import contextos.storage.db as db_mod

@pytest.fixture
def isolated_mcp_server():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test_mcp.db")
        old_db = db_mod.db
        db_mod.db = test_db

        mcp = create_mcp_server()
        try:
            yield mcp
        finally:
            db_mod.db = old_db

@pytest.mark.asyncio
async def test_mcp_server_initialization(isolated_mcp_server):
    mcp = isolated_mcp_server
    assert mcp.name == "contextos"

@pytest.mark.asyncio
async def test_project_tools(isolated_mcp_server):
    mcp = isolated_mcp_server
    tool_get = mcp._tool_manager.get_tool("project_get")
    assert tool_get is not None

    res = await tool_get.fn(project_id="contextos")
    assert res["project_id"] == "contextos"
    assert "workspace_root" in res
    assert "db_path" in res

    tool_status = mcp._tool_manager.get_tool("project_status")
    status_res = await tool_status.fn(project_id="contextos")
    assert status_res["project_id"] == "contextos"
    assert status_res["status"] == "healthy"
    assert "git_branch" in status_res

@pytest.mark.asyncio
async def test_memory_and_decision_tools(isolated_mcp_server):
    mcp = isolated_mcp_server

    # 1. memory_remember
    rem_tool = mcp._tool_manager.get_tool("memory_remember")
    item = await rem_tool.fn(content="FastMCP v2 supports stdio and sse", memory_type="semantic", tags=["mcp"])
    assert item["id"].startswith("mem_")
    assert "FastMCP" in item["content"]

    # 2. memory_search
    search_tool = mcp._tool_manager.get_tool("memory_search")
    results = await search_tool.fn(query="FastMCP")
    assert len(results) >= 1
    assert "FastMCP" in results[0]["content"]

    # 3. memory_decision_add
    decision_tool = mcp._tool_manager.get_tool("memory_decision_add")
    adr = await decision_tool.fn(
        title="Standardize on FastMCP v2",
        context="External clients require unified tool calling.",
        decision="Expose all ContextOS features as MCP tools.",
        consequences="Cross-IDE interoperability guaranteed.",
        alternatives=["Custom JSON-RPC", "REST only"],
    )
    assert adr["id"].startswith("adr_")
    assert adr["status"] == "accepted"
    assert len(adr["alternatives_considered"]) == 2

@pytest.mark.asyncio
async def test_context_tools(isolated_mcp_server):
    mcp = isolated_mcp_server

    # 1. context_build
    build_tool = mcp._tool_manager.get_tool("context_build")
    bundle = await build_tool.fn(
        intent="Audit security boundaries",
        active_task="Review path jailing implementation",
        budget=3500,
        session_id="mcp_sess_ctx",
    )
    assert bundle["total_tokens"] <= 3500
    assert "compiled_prompt" in bundle
    assert "tier_token_counts" in bundle

    # 2. context_search
    search_tool = mcp._tool_manager.get_tool("context_search")
    c_res = await search_tool.fn(query="security")
    assert isinstance(c_res, list)

@pytest.mark.asyncio
async def test_session_continuity_tools(isolated_mcp_server):
    mcp = isolated_mcp_server

    # 1. session_checkpoint
    chk_tool = mcp._tool_manager.get_tool("session_checkpoint")
    chk = await chk_tool.fn(
        session_id="mcp_session_test",
        agent_id="ag_mcp_01",
        state_summary="Verified MCP tools registration",
        active_task="Add E2E tests",
        modified_files=["server/contextos/mcp/server.py"],
    )
    assert chk["id"].startswith("chk_")

    # 2. session_resume
    resume_tool = mcp._tool_manager.get_tool("session_resume")
    resumption = await resume_tool.fn(checkpoint_id_or_session_id=chk["id"])
    assert resumption["resumed_task"] == "Add E2E tests"
    assert "server/contextos/mcp/server.py" in resumption["modified_files"]

    # 3. session_import
    import_tool = mcp._tool_manager.get_tool("session_import")
    imported = await import_tool.fn(
        source_agent="codex",
        session_data={
            "session_id": "mcp_imported_sess",
            "title": "Imported via MCP",
            "messages": [{"role": "user", "content": "Ping MCP"}],
        },
    )
    assert imported["source_agent"] == "codex"
    assert len(imported["turns"]) == 1

@pytest.mark.asyncio
async def test_agent_and_task_tools(isolated_mcp_server):
    mcp = isolated_mcp_server

    # 1. agent_list
    list_tool = mcp._tool_manager.get_tool("agent_list")
    agents = await list_tool.fn()
    assert isinstance(agents, list)

    # 2. agent_delegate
    delegate_tool = mcp._tool_manager.get_tool("agent_delegate")
    delegated = await delegate_tool.fn(
        from_agent_id="ag_primary",
        to_role="reviewer",
        task="Review uncommitted changes in server/contextos/mcp/",
    )
    assert delegated["delegation_status"] == "delegated"
    sub_agent_id = delegated["delegated_agent_id"]
    assert sub_agent_id.startswith("ag_reviewer_")

    # 3. agent_status
    status_tool = mcp._tool_manager.get_tool("agent_status")
    status = await status_tool.fn(agent_id=sub_agent_id)
    assert status["agent"]["id"] == sub_agent_id
    assert "metrics" in status

    # 4. task_get
    task_tool = mcp._tool_manager.get_tool("task_get")
    task_info = await task_tool.fn(agent_id=sub_agent_id)
    assert "Review uncommitted changes" in task_info["task_description"]

@pytest.mark.asyncio
async def test_diff_and_telemetry_tools(isolated_mcp_server):
    mcp = isolated_mcp_server

    # 1. git_diff_summary
    diff_tool = mcp._tool_manager.get_tool("git_diff_summary")
    diff_summary = await diff_tool.fn()
    assert "diff_stat" in diff_summary
    assert "status_short" in diff_summary

    # 2. token_metrics
    metrics_tool = mcp._tool_manager.get_tool("token_metrics")
    metrics = await metrics_tool.fn()
    assert "total_compilations" in metrics
    assert metrics["estimated"] is True
