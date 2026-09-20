from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from contextos.models.memory import UniversalSessionEnvelope, UniversalTurn

class BaseSessionAdapter(ABC):
    """Abstract base class for cross-agent conversation session format translation."""

    @abstractmethod
    def to_universal(self, raw_data: Dict[str, Any]) -> UniversalSessionEnvelope:
        """Convert agent-specific conversation/session data into a normalized UniversalSessionEnvelope."""
        pass

    @abstractmethod
    def from_universal(self, envelope: UniversalSessionEnvelope) -> Dict[str, Any]:
        """Convert a UniversalSessionEnvelope into agent-specific prompt/session payload."""
        pass


class CodexSessionAdapter(BaseSessionAdapter):
    """
    Adapter for OpenAI / Codex conversation formats (standard ChatML messages schema).
    """

    def to_universal(self, raw_data: Dict[str, Any]) -> UniversalSessionEnvelope:
        session_id = raw_data.get("session_id", "session_codex")
        messages = raw_data.get("messages", [])
        title = raw_data.get("title", "Codex Session")
        summary = raw_data.get("summary", "")

        turns: List[UniversalTurn] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls")
            turns.append(
                UniversalTurn(
                    role=role,
                    content=str(content),
                    tool_calls=tool_calls,
                )
            )

        return UniversalSessionEnvelope(
            session_id=session_id,
            source_agent="codex",
            title=title,
            summary=summary,
            turns=turns,
            artifacts=raw_data.get("artifacts", []),
            decisions=raw_data.get("decisions", []),
        )

    def from_universal(self, envelope: UniversalSessionEnvelope) -> Dict[str, Any]:
        messages = []
        for turn in envelope.turns:
            msg_dict: Dict[str, Any] = {
                "role": turn.role,
                "content": turn.content,
            }
            if turn.tool_calls:
                msg_dict["tool_calls"] = turn.tool_calls
            messages.append(msg_dict)

        return {
            "session_id": envelope.session_id,
            "agent": "codex",
            "title": envelope.title,
            "summary": envelope.summary,
            "messages": messages,
            "artifacts": envelope.artifacts,
            "decisions": envelope.decisions,
        }


class AGYSessionAdapter(BaseSessionAdapter):
    """
    Adapter for Google Antigravity / Gemini turn structures (contents/parts with thought/call_mcp_tool).
    """

    def to_universal(self, raw_data: Dict[str, Any]) -> UniversalSessionEnvelope:
        session_id = raw_data.get("session_id", "session_agy")
        turns_input = raw_data.get("turns") or raw_data.get("contents") or []
        title = raw_data.get("title", "Antigravity Session")
        summary = raw_data.get("summary", "")

        universal_turns: List[UniversalTurn] = []
        for item in turns_input:
            role = item.get("role", "user")
            if role == "model":
                mapped_role = "assistant"
            elif role == "user":
                mapped_role = "user"
            else:
                mapped_role = role

            parts = item.get("parts", [])
            text_chunks = []
            tool_calls = []

            for part in parts:
                if isinstance(part, str):
                    text_chunks.append(part)
                elif isinstance(part, dict):
                    if "text" in part:
                        text_chunks.append(part["text"])
                    if "thought" in part:
                        text_chunks.append(f"[Thought: {part['thought']}]")
                    if "call_mcp_tool" in part or "function_call" in part:
                        tc = part.get("call_mcp_tool") or part.get("function_call")
                        tool_calls.append(tc)

            content = "\n".join(text_chunks)
            universal_turns.append(
                UniversalTurn(
                    role=mapped_role,
                    content=content,
                    tool_calls=tool_calls if tool_calls else None,
                )
            )

        return UniversalSessionEnvelope(
            session_id=session_id,
            source_agent="agy",
            title=title,
            summary=summary,
            turns=universal_turns,
            artifacts=raw_data.get("artifacts", []),
            decisions=raw_data.get("decisions", []),
        )

    def from_universal(self, envelope: UniversalSessionEnvelope) -> Dict[str, Any]:
        contents = []
        for turn in envelope.turns:
            role = "model" if turn.role == "assistant" else turn.role
            parts: List[Dict[str, Any]] = [{"text": turn.content}]
            if turn.tool_calls:
                for tc in turn.tool_calls:
                    parts.append({"function_call": tc})
            contents.append({"role": role, "parts": parts})

        return {
            "session_id": envelope.session_id,
            "agent": "agy",
            "title": envelope.title,
            "summary": envelope.summary,
            "contents": contents,
            "artifacts": envelope.artifacts,
            "decisions": envelope.decisions,
        }


class GenericJsonSessionAdapter(BaseSessionAdapter):
    """
    Fallback adapter for generic JSON session dumps.
    """

    def to_universal(self, raw_data: Dict[str, Any]) -> UniversalSessionEnvelope:
        session_id = raw_data.get("session_id", "session_generic")
        raw_turns = raw_data.get("turns") or raw_data.get("messages") or []
        title = raw_data.get("title", "Generic Session")

        universal_turns: List[UniversalTurn] = []
        for t in raw_turns:
            if isinstance(t, str):
                universal_turns.append(UniversalTurn(role="user", content=t))
            elif isinstance(t, dict):
                universal_turns.append(
                    UniversalTurn(
                        role=t.get("role", "user"),
                        content=t.get("content") or t.get("text") or "",
                        tool_calls=t.get("tool_calls"),
                    )
                )

        return UniversalSessionEnvelope(
            session_id=session_id,
            source_agent="generic",
            title=title,
            summary=raw_data.get("summary", ""),
            turns=universal_turns,
            artifacts=raw_data.get("artifacts", []),
            decisions=raw_data.get("decisions", []),
        )

    def from_universal(self, envelope: UniversalSessionEnvelope) -> Dict[str, Any]:
        return envelope.model_dump(mode="json")
