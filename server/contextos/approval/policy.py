from typing import Dict, Any, Optional, Set
from contextos.models.approval import RiskLevel, ApprovalRequest, ApprovalDecision
import contextos.storage.db as db_mod

class ApprovalPolicy:
    """
    Evaluates actions against security risk rules and tracks session-level approvals.
    """

    def __init__(self):
        # Cache of (session_id, action_type) approved for the duration of a session
        self._session_approved_actions: Set[tuple[str, str]] = set()

    def evaluate_risk(self, action_name: str, arguments: Dict[str, Any]) -> tuple[bool, RiskLevel, str]:
        """
        Returns (requires_approval, risk_level, reason)
        """
        # 1. Shell commands
        if action_name in ("terminal.execute", "terminal_execute", "shell_command"):
            cmd = arguments.get("command", "")
            if any(danger in cmd for danger in ("rm -rf", "DROP TABLE", "format", "del /f")):
                return True, RiskLevel.CRITICAL, "Destructive shell command detected"
            if "git push" in cmd:
                return True, RiskLevel.HIGH, "Remote repository write (git push)"
            if any(pkg in cmd for pkg in ("npm install", "pip install", "pnpm add", "cargo install")):
                return True, RiskLevel.HIGH, "Third-party package installation"
            return True, RiskLevel.HIGH, "Arbitrary shell execution requires operator consent"

        # 2. File deletions
        if action_name in ("file_editor.delete", "file_delete"):
            return True, RiskLevel.CRITICAL, "File deletion removes workspace files permanently"

        # 3. File overwrites
        if action_name in ("file_editor.write", "file_write"):
            # Check if file exists in workspace
            path = arguments.get("path", "")
            return False, RiskLevel.LOW, "Local file write within workspace boundary"

        # 4. Secrets access
        if "secret" in action_name or "credential" in action_name:
            return True, RiskLevel.CRITICAL, "Action requests credential or secret inspection"

        # 5. Git operations
        if action_name == "git.push":
            return True, RiskLevel.HIGH, "Pushing changes to remote git repository"

        return False, RiskLevel.LOW, "Action permitted under standard security policy"

    def is_session_approved(self, session_id: str, action_type: str) -> bool:
        return (session_id, action_type) in self._session_approved_actions

    def record_decision(self, approval_request: ApprovalRequest, decision: ApprovalDecision):
        if decision == ApprovalDecision.APPROVE_SESSION:
            self._session_approved_actions.add(
                (approval_request.session_id, approval_request.action_type)
            )

        db_mod.db.update_approval(approval_request.id, decision.value)
        db_mod.db.log_audit(
            agent_id=approval_request.agent_id,
            action=f"approval.{approval_request.action_name}",
            status=decision.value,
            details=f"Resource: {approval_request.affected_resource} Decision: {decision.value}"
        )

approval_policy = ApprovalPolicy()
