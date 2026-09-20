import pytest
import tempfile
from pathlib import Path
import httpx

from contextos.api.app import create_app
from contextos.models.agent import AgentStatus
from contextos.models.approval import ApprovalDecision
from contextos.storage.db import DatabaseManager
from contextos.workspace.local import LocalWorkspace
import contextos.runtime.supervisor as sup
import contextos.api.routes as routes

@pytest.mark.asyncio
async def test_full_agent_interaction_and_approval_flow():
    """
    End-to-End integration test proving:
    UI/API creates agent -> agent receives task -> tool request event appears ->
    approval is required -> approval is accepted -> tool executes -> result event appears -> agent finishes.
    No mock-only success path: real OS process group execution and real database records.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "integration.db")
        test_ws = LocalWorkspace(root_path=Path(tmp_dir))

        # Wire isolated test components
        import contextos.storage.db as db_mod
        from contextos.workspace.file_editor_tool import FileEditorTool
        from contextos.workspace.terminal_tool import TerminalTool

        old_db = db_mod.db
        old_ws = sup.agent_runtime.workspace
        old_file_editor = sup.agent_runtime.file_editor
        old_terminal = sup.agent_runtime.terminal

        db_mod.db = test_db
        sup.agent_runtime.workspace = test_ws
        sup.agent_runtime.file_editor = FileEditorTool(test_ws)
        sup.agent_runtime.terminal = TerminalTool(test_ws.root_path)

        try:
            app = create_app()

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                # Step 1: UI/API creates agent
                create_res = await client.post("/api/agents", json={
                    "name": "Integration Coder Agent",
                    "type": "CODER",
                    "provider": "OpenAI / Codex",
                    "model": "gpt-4o",
                    "task": "Execute verification command",
                })
                assert create_res.status_code == 200
                agent_data = create_res.json()
                agent_id = agent_data["id"]
                assert agent_data["status"] == AgentStatus.IDLE.value

                # Step 2: UI starts agent
                start_res = await client.post(f"/api/agents/{agent_id}/start")
                assert start_res.status_code == 200
                assert start_res.json()["status"] == AgentStatus.RUNNING.value

                # Step 3: Agent receives task requiring shell command execution
                msg_res = await client.post(f"/api/agents/{agent_id}/message", json={
                    "content": "run echo 'ContextOS Live Verification'"
                })
                assert msg_res.status_code == 200
                msg_data = msg_res.json()

                # Step 4: Verify tool request event appeared and approval is required
                assert msg_data["status"] == "waiting_approval"
                approval_id = msg_data["approval_id"]
                assert approval_id is not None

                # Verify agent state transitioned to WAITING_APPROVAL
                agent_check = await client.get(f"/api/agents/{agent_id}")
                assert agent_check.json()["status"] == AgentStatus.WAITING_APPROVAL.value

                # Verify approval shows up in approvals endpoint
                approvals_res = await client.get("/api/approvals?status=PENDING")
                assert approvals_res.status_code == 200
                pending_list = approvals_res.json()
                assert any(a["id"] == approval_id for a in pending_list)

                # Verify events emitted
                events_res = await client.get(f"/api/agents/{agent_id}/events")
                assert events_res.status_code == 200
                event_types = [e["type"] for e in events_res.json()]
                assert "agent.started" in event_types
                assert "tool.requested" in event_types
                assert "tool.approval_required" in event_types

                # Step 5: Approval is accepted by operator
                resolve_res = await client.post(f"/api/approvals/{approval_id}/resolve", json={
                    "decision": ApprovalDecision.APPROVE_ONCE.value
                })
                assert resolve_res.status_code == 200
                resolve_data = resolve_res.json()
                assert resolve_data["status"] == "approved_and_executed"

                # Step 6: Tool executes, real stdout captured, result event appears
                tool_output = resolve_data["result"]["output"]
                assert "ContextOS Live Verification" in tool_output["stdout"]
                assert tool_output["exit_code"] == 0

                # Step 7: Verify final events and agent state
                final_events_res = await client.get(f"/api/agents/{agent_id}/events")
                final_event_types = [e["type"] for e in final_events_res.json()]
                assert "tool.started" in final_event_types
                assert "tool.completed" in final_event_types
                assert "terminal.output" in final_event_types

                # Step 8: Agent finishes / stops
                stop_res = await client.post(f"/api/agents/{agent_id}/stop")
                assert stop_res.status_code == 200
                assert stop_res.json()["status"] == AgentStatus.STOPPED.value
        finally:
            db_mod.db = old_db
            sup.agent_runtime.workspace = old_ws
            sup.agent_runtime.file_editor = old_file_editor
            sup.agent_runtime.terminal = old_terminal

