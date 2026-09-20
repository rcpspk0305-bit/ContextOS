import pytest
import tempfile
from pathlib import Path
from contextos.models.agent import AgentRole, AgentStatus
from contextos.runtime.supervisor import AgentRuntime
from contextos.workspace.local import LocalWorkspace
from contextos.storage.db import DatabaseManager

@pytest.mark.asyncio
async def test_agent_lifecycle_state_machine():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db_path = Path(tmp_dir) / "test.db"
        test_db = DatabaseManager(test_db_path)
        runtime = AgentRuntime(workspace=LocalWorkspace(root_path=Path(tmp_dir)))

        # Patch runtime to use isolated test DB
        import contextos.storage.db as db_mod
        old_db = db_mod.db
        db_mod.db = test_db
        try:
            # 1. Create agent (Status IDLE)
            agent = runtime.create_agent(
                name="Test Reviewer",
                role=AgentRole.REVIEWER,
                provider="OpenAI / Codex",
                model="o3-mini",
                current_task="Audit uncommitted security diff",
            )
            assert agent.id.startswith("ag_reviewer_")
            assert agent.status == AgentStatus.IDLE

            # 2. Start agent (Status RUNNING)
            started = await runtime.start_agent(agent.id)
            assert started.status == AgentStatus.RUNNING
            assert started.started_at is not None

            # 3. Pause agent (Status PAUSED)
            paused = await runtime.pause_agent(agent.id)
            assert paused.status == AgentStatus.PAUSED

            # 4. Resume agent (Status RUNNING)
            resumed = await runtime.resume_agent(agent.id)
            assert resumed.status == AgentStatus.RUNNING

            # 5. Stop agent (Status STOPPED)
            stopped = await runtime.stop_agent(agent.id)
            assert stopped.status == AgentStatus.STOPPED

            # 6. Verify retrieval and metrics
            fetched = runtime.get_agent(agent.id)
            assert fetched is not None
            assert fetched.id == agent.id

            metrics = runtime.get_metrics(agent.id)
            assert metrics["agent_id"] == agent.id
            assert metrics["status"] == AgentStatus.STOPPED.value
        finally:
            db_mod.db = old_db


@pytest.mark.asyncio
async def test_approval_rejection_flow():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "test.db")
        runtime = AgentRuntime(workspace=LocalWorkspace(root_path=Path(tmp_dir)))

        import contextos.storage.db as db_mod
        old_db = db_mod.db
        db_mod.db = test_db
        try:
            agent = runtime.create_agent(
                name="Coder Agent",
                role=AgentRole.CODER,
                provider="OpenAI / Codex",
                model="gpt-4o",
            )
            await runtime.start_agent(agent.id)

            # Trigger dangerous command requiring approval
            result = await runtime.send_message(agent.id, "run rm -rf /")
            assert result["status"] == "waiting_approval"
            approval_id = result["approval_id"]

            agent_state = runtime.get_agent(agent.id)
            assert agent_state.status == AgentStatus.WAITING_APPROVAL

            # Reject tool execution
            reject_res = await runtime.reject_tool(approval_id)
            assert reject_res["status"] == "rejected"

            agent_after = runtime.get_agent(agent.id)
            assert agent_after.status == AgentStatus.RUNNING

            # Events emitted
            from contextos.models.event import EventType
            events = runtime.get_events(agent_id=agent.id)
            completed_events = [e for e in events if e.type == EventType.TOOL_COMPLETED]
            assert len(completed_events) > 0
            assert completed_events[0].payload.get("rejected") is True
        finally:
            db_mod.db = old_db


def test_approval_policy_risk_matrix():
    from contextos.approval.policy import ApprovalPolicy
    from contextos.models.approval import RiskLevel

    policy = ApprovalPolicy()

    # 1. Shell commands - dangerous
    req, risk, _ = policy.evaluate_risk("terminal.execute", {"command": "rm -rf node_modules"})
    assert req is True
    assert risk == RiskLevel.CRITICAL

    # 2. Shell commands - package install
    req, risk, _ = policy.evaluate_risk("terminal.execute", {"command": "npm install lodash"})
    assert req is True
    assert risk == RiskLevel.HIGH

    # 3. File delete
    req, risk, _ = policy.evaluate_risk("file_editor.delete", {"path": "src/main.ts"})
    assert req is True
    assert risk == RiskLevel.CRITICAL

    # 4. Git push
    req, risk, _ = policy.evaluate_risk("git.push", {})
    assert req is True
    assert risk == RiskLevel.HIGH

    # 5. Safe file write
    req, risk, _ = policy.evaluate_risk("file_editor.write", {"path": "test.txt"})
    assert req is False
    assert risk == RiskLevel.LOW


def test_task_tracker_workflow():
    from contextos.workspace.task_tracker_tool import TaskTrackerTool

    tracker = TaskTrackerTool(
        task_description="Build Auth Subsystem",
        checklist=["Define User model", "Add JWT middleware", "Write login tests"]
    )
    summary = tracker.get_progress_summary()
    assert summary["total_items"] == 3
    assert summary["completed_count"] == 0
    assert summary["all_done"] is False
    assert summary["current_item"] == "Define User model"

    # Complete item 1
    msg = tracker.mark_completed("item_1")
    assert "item_1 marked as completed" in msg
    summary2 = tracker.get_progress_summary()
    assert summary2["completed_count"] == 1
    assert summary2["current_item"] == "Add JWT middleware"

    # Error on invalid item
    with pytest.raises(ValueError):
        tracker.mark_completed("nonexistent_item")


@pytest.mark.asyncio
async def test_event_bus_dispatch_and_persistence():
    import tempfile
    from pathlib import Path
    from contextos.runtime.event_bus import EventBus
    from contextos.models.event import EventEnvelope, EventType
    from contextos.storage.db import DatabaseManager

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = DatabaseManager(Path(tmp_dir) / "bus.db")
        import contextos.storage.db as db_mod
        old_db = db_mod.db
        db_mod.db = test_db

        bus = EventBus()
        received_events = []

        bus.subscribe(lambda evt: received_events.append(evt))

        try:
            test_evt = EventEnvelope(
                agent_id="test_agent",
                session_id="session_123",
                type=EventType.AGENT_STARTED,
                payload={"msg": "Hello Bus"}
            )
            await bus.emit(test_evt)

            assert len(received_events) == 1
            assert received_events[0].payload["msg"] == "Hello Bus"

            # Check persistence in sqlite
            persisted = test_db.list_events(agent_id="test_agent")
            assert len(persisted) == 1
            assert persisted[0].agent_id == "test_agent"
        finally:
            db_mod.db = old_db


