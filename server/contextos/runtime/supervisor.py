import uuid
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from contextos.models.agent import Agent, AgentRole, AgentStatus, AgentPermissions, TokenUsage
from contextos.models.event import EventEnvelope, EventType
from contextos.models.approval import ApprovalRequest, RiskLevel, ApprovalDecision
import contextos.storage.db as db_mod
from contextos.workspace.base import Workspace
from contextos.workspace.local import LocalWorkspace
from contextos.workspace.file_editor_tool import FileEditorTool
from contextos.workspace.terminal_tool import TerminalTool
from contextos.workspace.task_tracker_tool import TaskTrackerTool
from contextos.approval.policy import approval_policy
from .event_bus import event_bus

class AgentRuntime:
    """
    Unified Agent Supervisor and Execution Runtime.
    Provides lifecycle state machine management, workspace isolation, tool execution,
    and human-in-the-loop approval gates.
    """

    def __init__(self, workspace: Optional[Workspace] = None):
        self.workspace = workspace or LocalWorkspace()
        self.file_editor = FileEditorTool(self.workspace)
        self.terminal = TerminalTool(self.workspace.root_path)

        # In-memory execution state for active agents
        self._active_task_trackers: Dict[str, TaskTrackerTool] = {}
        self._pending_tool_executions: Dict[str, Dict[str, Any]] = {}

    @property
    def db(self):
        return db_mod.db


    # 1. create_agent
    def create_agent(
        self,
        name: str,
        role: AgentRole = AgentRole.CODER,
        provider: str = "OpenAI / Codex",
        model: str = "gpt-4o",
        current_task: str = "",
        permissions: Optional[AgentPermissions] = None,
        context_budget: int = 8000,
    ) -> Agent:
        agent_id = f"ag_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        perms = permissions or AgentPermissions(
            can_execute_shell=(role in (AgentRole.CODER, AgentRole.TESTER)),
            can_edit_files=(role != AgentRole.REVIEWER),
            can_git_commit=(role == AgentRole.CODER),
            can_network=(role == AgentRole.RESEARCHER),
        )

        agent = Agent(
            id=agent_id,
            name=name,
            role=role,
            provider=provider,
            model=model,
            status=AgentStatus.IDLE,
            current_task=current_task,
            created_at=now,
            last_activity_at=now,
            context_budget=context_budget,
            permissions=perms,
        )

        self.db.save_agent(agent)
        return agent

    # 2. start_agent
    async def start_agent(self, agent_id: str) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        now = datetime.now(timezone.utc)
        agent.status = AgentStatus.RUNNING
        agent.started_at = now
        agent.last_activity_at = now

        self.db.save_agent(agent)

        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.AGENT_STARTED,
                payload={
                    "name": agent.name,
                    "role": agent.role.value,
                    "provider": agent.provider,
                    "model": agent.model,
                    "task": agent.current_task,
                },
            )
        )
        return agent

    # 3. send_message / assign task
    async def send_message(self, agent_id: str, content: str) -> Dict[str, Any]:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        agent.last_activity_at = datetime.now(timezone.utc)
        self.db.save_agent(agent)

        # Emit user message event
        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.MESSAGE_CREATED,
                payload={"role": "user", "content": content},
            )
        )

        # Agent thinking event
        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.AGENT_THINKING,
                payload={"thought": f"Analyzing task request: '{content}'"},
            )
        )

        # Parse intent for tool requirement
        # If command or shell execution requested
        if content.startswith("$") or "run " in content.lower() or "execute " in content.lower():
            raw_cmd = content[1:].strip() if content.startswith("$") else content.split("run ", 1)[-1].strip()
            return await self.request_tool_execution(
                agent_id=agent.id,
                action_name="terminal.execute",
                action_type="shell_command",
                arguments={"command": raw_cmd},
                affected_resource="terminal:subprocess",
                reason=f"Task requested execution of '{raw_cmd}'",
            )

        # Default conversational acknowledgment
        return {
            "status": "acknowledged",
            "agent_id": agent.id,
            "message": f"Task '{content}' received by {agent.name}.",
        }

    # Tool execution gateway with approval gate
    async def request_tool_execution(
        self,
        agent_id: str,
        action_name: str,
        action_type: str,
        arguments: Dict[str, Any],
        affected_resource: str,
        reason: str,
    ) -> Dict[str, Any]:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Emit tool requested event
        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.TOOL_REQUESTED,
                payload={"tool": action_name, "arguments": arguments},
            )
        )

        # Check approval policy
        requires_approval, risk_level, risk_reason = approval_policy.evaluate_risk(action_name, arguments)
        is_session_ok = approval_policy.is_session_approved(agent.session_id, action_type)

        if requires_approval and not is_session_ok:
            # Create approval request
            approval_req = ApprovalRequest(
                agent_id=agent.id,
                session_id=agent.session_id,
                action_type=action_type,
                action_name=action_name,
                command=arguments.get("command"),
                arguments=arguments,
                risk_level=risk_level,
                affected_resource=affected_resource,
                reason=f"{reason} ({risk_reason})",
            )
            self.db.save_approval(approval_req)

            # Transition agent to WAITING_APPROVAL
            agent.status = AgentStatus.WAITING_APPROVAL
            self.db.save_agent(agent)

            # Cache pending execution context
            self._pending_tool_executions[approval_req.id] = {
                "agent_id": agent.id,
                "action_name": action_name,
                "arguments": arguments,
                "approval_req": approval_req,
            }

            # Emit approval required event
            await event_bus.emit(
                EventEnvelope(
                    agent_id=agent.id,
                    session_id=agent.session_id,
                    type=EventType.TOOL_APPROVAL_REQUIRED,
                    payload=approval_req.model_dump(mode="json"),
                )
            )

            return {
                "status": "waiting_approval",
                "approval_id": approval_req.id,
                "risk_level": risk_level.value,
                "message": "Action requires human approval before proceeding.",
            }

        # Otherwise execute directly
        return await self._execute_tool_internal(agent.id, action_name, arguments)

    # 4. approve_tool
    async def approve_tool(self, approval_id: str, decision: ApprovalDecision = ApprovalDecision.APPROVE_ONCE) -> Dict[str, Any]:
        approval_req = self.db.get_approval(approval_id)
        if not approval_req:
            raise ValueError(f"Approval request {approval_id} not found")

        approval_policy.record_decision(approval_req, decision)

        context = self._pending_tool_executions.pop(approval_id, None)
        if not context:
            return {"status": "resolved", "approval_id": approval_id, "decision": decision.value}

        agent_id = context["agent_id"]
        action_name = context["action_name"]
        arguments = context["arguments"]

        # Restore agent status to RUNNING
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = AgentStatus.RUNNING
            self.db.save_agent(agent)

        # Execute approved tool
        result = await self._execute_tool_internal(agent_id, action_name, arguments)
        return {
            "status": "approved_and_executed",
            "approval_id": approval_id,
            "decision": decision.value,
            "result": result,
        }

    # 5. reject_tool
    async def reject_tool(self, approval_id: str) -> Dict[str, Any]:
        approval_req = self.db.get_approval(approval_id)
        if not approval_req:
            raise ValueError(f"Approval request {approval_id} not found")

        approval_policy.record_decision(approval_req, ApprovalDecision.REJECT)
        context = self._pending_tool_executions.pop(approval_id, None)

        if context:
            agent_id = context["agent_id"]
            agent = self.get_agent(agent_id)
            if agent:
                agent.status = AgentStatus.RUNNING
                self.db.save_agent(agent)

            await event_bus.emit(
                EventEnvelope(
                    agent_id=agent_id,
                    session_id=approval_req.session_id,
                    type=EventType.TOOL_COMPLETED,
                    payload={
                        "tool": approval_req.action_name,
                        "rejected": True,
                        "message": "Action was rejected by human operator.",
                    },
                )
            )

        return {"status": "rejected", "approval_id": approval_id}

    # Internal tool execution
    async def _execute_tool_internal(self, agent_id: str, action_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.get_agent(agent_id)
        session_id = agent.session_id if agent else "default_session"

        # Emit tool started event
        await event_bus.emit(
            EventEnvelope(
                agent_id=agent_id,
                session_id=session_id,
                type=EventType.TOOL_STARTED,
                payload={"tool": action_name, "arguments": arguments},
            )
        )

        output: Any = None
        error: Optional[str] = None

        if action_name in ("terminal.execute", "terminal_execute"):
            cmd = arguments.get("command", "")
            cmd_res = self.workspace.execute_command(cmd)
            output = cmd_res.model_dump()
            if cmd_res.exit_code != 0:
                error = cmd_res.stderr

            await event_bus.emit(
                EventEnvelope(
                    agent_id=agent_id,
                    session_id=session_id,
                    type=EventType.TERMINAL_OUTPUT,
                    payload={"stdout": cmd_res.stdout, "stderr": cmd_res.stderr, "exit_code": cmd_res.exit_code},
                )
            )

        elif action_name in ("file_editor.write", "file_write"):
            path = arguments.get("path", "")
            content = arguments.get("content", "")
            self.workspace.write_file(path, content)
            output = f"Wrote {len(content)} bytes to {path}"

            await event_bus.emit(
                EventEnvelope(
                    agent_id=agent_id,
                    session_id=session_id,
                    type=EventType.FILE_CHANGED,
                    payload={"path": path, "size": len(content)},
                )
            )

        elif action_name in ("file_editor.read", "file_read"):
            path = arguments.get("path", "")
            output = self.workspace.read_file(path)

            await event_bus.emit(
                EventEnvelope(
                    agent_id=agent_id,
                    session_id=session_id,
                    type=EventType.FILE_READ,
                    payload={"path": path},
                )
            )

        # Emit tool completed event
        await event_bus.emit(
            EventEnvelope(
                agent_id=agent_id,
                session_id=session_id,
                type=EventType.TOOL_COMPLETED,
                payload={"tool": action_name, "result": output, "error": error},
            )
        )

        return {"tool": action_name, "output": output, "error": error}

    # 6. pause_agent
    async def pause_agent(self, agent_id: str) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        agent.status = AgentStatus.PAUSED
        agent.last_activity_at = datetime.now(timezone.utc)
        self.db.save_agent(agent)

        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.AGENT_PAUSED,
                payload={"status": "PAUSED"},
            )
        )
        return agent

    # 7. resume_agent
    async def resume_agent(self, agent_id: str) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        agent.status = AgentStatus.RUNNING
        agent.last_activity_at = datetime.now(timezone.utc)
        self.db.save_agent(agent)

        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.AGENT_STARTED,
                payload={"status": "RESUMED"},
            )
        )
        return agent

    # 8. stop_agent
    async def stop_agent(self, agent_id: str) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        agent.status = AgentStatus.STOPPED
        agent.last_activity_at = datetime.now(timezone.utc)
        self.db.save_agent(agent)

        await event_bus.emit(
            EventEnvelope(
                agent_id=agent.id,
                session_id=agent.session_id,
                type=EventType.AGENT_COMPLETED,
                payload={"status": "STOPPED_BY_USER"},
            )
        )
        return agent

    # 9. restart_agent
    async def restart_agent(self, agent_id: str) -> Agent:
        await self.stop_agent(agent_id)
        return await self.start_agent(agent_id)

    # 10. get_agent
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.db.get_agent(agent_id)

    # 11. list_agents
    def list_agents(self) -> List[Agent]:
        return self.db.list_agents()

    # 12. get_events
    def get_events(self, agent_id: Optional[str] = None, limit: int = 100) -> List[EventEnvelope]:
        return self.db.list_events(agent_id=agent_id, limit=limit)

    # 13. get_metrics
    def get_metrics(self, agent_id: str) -> Dict[str, Any]:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        return {
            "agent_id": agent.id,
            "status": agent.status.value,
            "tokens": agent.token_usage.model_dump(),
            "context_budget": agent.context_budget,
            "runtime_seconds": agent.runtime_seconds,
            "last_activity_at": agent.last_activity_at.isoformat(),
        }

agent_runtime = AgentRuntime()
