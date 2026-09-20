import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Generator
from datetime import datetime, timezone

from contextos.config import settings
from contextos.models.agent import Agent, AgentStatus, AgentRole, TokenUsage, AgentPermissions
from contextos.models.event import EventEnvelope, EventType
from contextos.models.approval import ApprovalRequest, RiskLevel
from contextos.models.memory import (
    MemoryType,
    MemoryItem,
    DecisionRecord,
    Checkpoint,
    UniversalTurn,
    UniversalSessionEnvelope,
)
from contextos.models.analytics import (
    TokenRecord,
    AnalyticsSummary,
    BreakdownItem,
)

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.db_path
        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                current_task TEXT,
                project_id TEXT,
                session_id TEXT,
                created_at TEXT,
                started_at TEXT,
                last_activity_at TEXT,
                context_budget INTEGER,
                token_usage TEXT,
                permissions TEXT,
                runtime_seconds INTEGER
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_name TEXT NOT NULL,
                command TEXT,
                arguments TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                affected_resource TEXT NOT NULL,
                reason TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                context TEXT NOT NULL,
                decision TEXT NOT NULL,
                consequences TEXT,
                status TEXT NOT NULL,
                alternatives_considered TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                state_summary TEXT NOT NULL,
                active_task TEXT,
                modified_files TEXT NOT NULL,
                open_decisions TEXT NOT NULL,
                context_tokens_used INTEGER NOT NULL,
                metadata TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_envelopes (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                source_agent TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                turns TEXT NOT NULL,
                artifacts TEXT NOT NULL,
                decisions TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)

            try:
                cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    content,
                    tags,
                    tokenize = 'porter unicode61'
                )
                """)
            except Exception:
                pass

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_records (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                project_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                agent_id TEXT,
                task_id TEXT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                candidate_tokens INTEGER NOT NULL,
                selected_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                tokens_avoided INTEGER NOT NULL,
                cache_hit_tokens INTEGER NOT NULL,
                cost_without_usd REAL NOT NULL,
                cost_with_usd REAL NOT NULL,
                cost_saved_usd REAL NOT NULL,
                bytes_avoided INTEGER NOT NULL,
                estimated INTEGER NOT NULL,
                metadata TEXT NOT NULL
            )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_records_project ON token_records(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_records_session ON token_records(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_records_agent ON token_records(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_records_provider ON token_records(provider)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_records_model ON token_records(model)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_records_timestamp ON token_records(timestamp)")

            conn.commit()

    # Agent Operations
    def save_agent(self, agent: Agent):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO agents (
                id, name, role, provider, model, status, current_task,
                project_id, session_id, created_at, started_at, last_activity_at,
                context_budget, token_usage, permissions, runtime_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent.id,
                agent.name,
                agent.role.value,
                agent.provider,
                agent.model,
                agent.status.value,
                agent.current_task,
                agent.project_id,
                agent.session_id,
                agent.created_at.isoformat(),
                agent.started_at.isoformat() if agent.started_at else None,
                agent.last_activity_at.isoformat(),
                agent.context_budget,
                agent.token_usage.model_dump_json(),
                agent.permissions.model_dump_json(),
                agent.runtime_seconds,
            ))
            conn.commit()

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_agent(row)

    def list_agents(self) -> List[Agent]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents ORDER BY last_activity_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_agent(r) for r in rows]

    def _row_to_agent(self, row: sqlite3.Row) -> Agent:
        return Agent(
            id=row["id"],
            name=row["name"],
            role=AgentRole(row["role"]),
            provider=row["provider"],
            model=row["model"],
            status=AgentStatus(row["status"]),
            current_task=row["current_task"] or "",
            project_id=row["project_id"] or "contextos",
            session_id=row["session_id"] or "default_session",
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            last_activity_at=datetime.fromisoformat(row["last_activity_at"]),
            context_budget=row["context_budget"] or 8000,
            token_usage=TokenUsage.model_validate_json(row["token_usage"]) if row["token_usage"] else TokenUsage(),
            permissions=AgentPermissions.model_validate_json(row["permissions"]) if row["permissions"] else AgentPermissions(),
            runtime_seconds=row["runtime_seconds"] or 0,
        )

    # Event Operations
    def save_event(self, event: EventEnvelope):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO events (id, agent_id, session_id, type, timestamp, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.agent_id,
                event.session_id,
                event.type.value,
                event.timestamp.isoformat(),
                json.dumps(event.payload),
            ))
            conn.commit()

    def list_events(self, agent_id: Optional[str] = None, limit: int = 100) -> List[EventEnvelope]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if agent_id:
                cursor.execute(
                    "SELECT * FROM events WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (agent_id, limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [
                EventEnvelope(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    session_id=r["session_id"],
                    type=EventType(r["type"]),
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    payload=json.loads(r["payload"]),
                )
                for r in rows
            ]

    # Approval Operations
    def save_approval(self, approval: ApprovalRequest):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO approvals (
                id, agent_id, session_id, action_type, action_name,
                command, arguments, risk_level, affected_resource, reason, timestamp, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                approval.id,
                approval.agent_id,
                approval.session_id,
                approval.action_type,
                approval.action_name,
                approval.command,
                json.dumps(approval.arguments),
                approval.risk_level.value,
                approval.affected_resource,
                approval.reason,
                approval.timestamp.isoformat(),
                approval.status,
            ))
            conn.commit()

    def update_approval(self, approval_id: str, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE approvals SET status = ? WHERE id = ?", (status, approval_id))
            conn.commit()

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_approval(row)

    def list_approvals(self, status: Optional[str] = None) -> List[ApprovalRequest]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM approvals WHERE status = ? ORDER BY timestamp DESC", (status,))
            else:
                cursor.execute("SELECT * FROM approvals ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            return [self._row_to_approval(r) for r in rows]

    def _row_to_approval(self, row: sqlite3.Row) -> ApprovalRequest:
        return ApprovalRequest(
            id=row["id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            action_type=row["action_type"],
            action_name=row["action_name"],
            command=row["command"],
            arguments=json.loads(row["arguments"]),
            risk_level=RiskLevel(row["risk_level"]),
            affected_resource=row["affected_resource"],
            reason=row["reason"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            status=row["status"],
        )

    # Audit Logging
    def log_audit(self, agent_id: Optional[str], action: str, status: str, details: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO audit_logs (agent_id, action, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (
                agent_id,
                action,
                status,
                details,
                datetime.now(timezone.utc).isoformat(),
            ))
            conn.commit()

    # Memory Operations
    def save_memory(self, memory: MemoryItem):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO memories (
                id, project_id, session_id, type, content, tags, metadata, created_at, updated_at, access_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.project_id,
                memory.session_id,
                memory.type.value,
                memory.content,
                json.dumps(memory.tags),
                json.dumps(memory.metadata),
                memory.created_at.isoformat(),
                memory.updated_at.isoformat(),
                memory.access_count,
            ))
            try:
                cursor.execute("DELETE FROM memories_fts WHERE id = ?", (memory.id,))
                cursor.execute(
                    "INSERT INTO memories_fts (id, content, tags) VALUES (?, ?, ?)",
                    (memory.id, memory.content, " ".join(memory.tags)),
                )
            except Exception:
                pass
            conn.commit()

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE memories SET access_count = access_count + 1 WHERE id = ?", (memory_id,))
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            conn.commit()
            return self._row_to_memory(row)

    def delete_memory(self, memory_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            affected = cursor.rowcount
            try:
                cursor.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
            except Exception:
                pass
            conn.commit()
            return affected > 0

    def search_memories(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[MemoryItem]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if memory_type:
                conditions.append("m.type = ?")
                params.append(memory_type.value if hasattr(memory_type, "value") else str(memory_type))

            if project_id:
                conditions.append("m.project_id = ?")
                params.append(project_id)

            if session_id:
                conditions.append("m.session_id = ?")
                params.append(session_id)

            # Try FTS5 search first if query provided
            fts_rows = None
            if query and query.strip():
                try:
                    clean_q = "".join(c for c in query if c.isalnum() or c in (" ", "_", "-")).strip()
                    if clean_q:
                        words = [w for w in clean_q.split() if len(w) > 1]
                        if words:
                            fts_expr = " OR ".join(f"{w}*" for w in words)
                            fts_sql = "SELECT id, rank FROM memories_fts WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?"
                            cursor.execute(fts_sql, (fts_expr, limit))
                            fts_rows = {r["id"]: r["rank"] for r in cursor.fetchall()}
                except Exception:
                    fts_rows = None

            if fts_rows:
                placeholders = ",".join("?" for _ in fts_rows.keys())
                conditions.append(f"m.id IN ({placeholders})")
                params.extend(list(fts_rows.keys()))
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                sql = f"SELECT * FROM memories m {where_clause}"
                cursor.execute(sql, params)
                results = [self._row_to_memory(r) for r in cursor.fetchall()]
                for res in results:
                    res.relevance_score = float(fts_rows.get(res.id, 0.0))
                results.sort(key=lambda x: x.relevance_score or 0.0)
            else:
                if query and query.strip():
                    conditions.append("(m.content LIKE ? OR m.tags LIKE ?)")
                    params.append(f"%{query.strip()}%")
                    params.append(f"%{query.strip()}%")

                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                sql = f"SELECT * FROM memories m {where_clause} ORDER BY m.created_at DESC LIMIT ?"
                params.append(limit)
                cursor.execute(sql, params)
                results = [self._row_to_memory(r) for r in cursor.fetchall()]

            # In-memory tag filtering if specified
            if tags:
                tag_set = set(t.lower() for t in tags)
                results = [r for r in results if tag_set.intersection(set(t.lower() for t in r.tags))]

            return results

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            type=MemoryType(row["type"]),
            content=row["content"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            access_count=row["access_count"],
        )

    # Decision (ADR) Operations
    def save_decision(self, decision: DecisionRecord):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO decisions (
                id, project_id, session_id, title, context, decision, consequences, status, alternatives_considered, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.id,
                decision.project_id,
                decision.session_id,
                decision.title,
                decision.context,
                decision.decision,
                decision.consequences,
                decision.status,
                json.dumps(decision.alternatives_considered),
                decision.created_at.isoformat(),
            ))
            conn.commit()

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_decision(row)

    def list_decisions(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[DecisionRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            sql = f"SELECT * FROM decisions {where_clause} ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            cursor.execute(sql, params)
            return [self._row_to_decision(r) for r in cursor.fetchall()]

    def _row_to_decision(self, row: sqlite3.Row) -> DecisionRecord:
        return DecisionRecord(
            id=row["id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            title=row["title"],
            context=row["context"],
            decision=row["decision"],
            consequences=row["consequences"] or "",
            status=row["status"],
            alternatives_considered=json.loads(row["alternatives_considered"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # Checkpoint Operations
    def save_checkpoint(self, checkpoint: Checkpoint):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO checkpoints (
                id, project_id, session_id, agent_id, timestamp, state_summary,
                active_task, modified_files, open_decisions, context_tokens_used, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint.id,
                checkpoint.project_id,
                checkpoint.session_id,
                checkpoint.agent_id,
                checkpoint.timestamp.isoformat(),
                checkpoint.state_summary,
                checkpoint.active_task,
                json.dumps(checkpoint.modified_files),
                json.dumps(checkpoint.open_decisions),
                checkpoint.context_tokens_used,
                json.dumps(checkpoint.metadata),
            ))
            conn.commit()

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_checkpoint(row)

    def list_checkpoints(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Checkpoint]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            sql = f"SELECT * FROM checkpoints {where_clause} ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            cursor.execute(sql, params)
            return [self._row_to_checkpoint(r) for r in cursor.fetchall()]

    def _row_to_checkpoint(self, row: sqlite3.Row) -> Checkpoint:
        return Checkpoint(
            id=row["id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            state_summary=row["state_summary"],
            active_task=row["active_task"] or "",
            modified_files=json.loads(row["modified_files"]),
            open_decisions=json.loads(row["open_decisions"]),
            context_tokens_used=row["context_tokens_used"],
            metadata=json.loads(row["metadata"]),
        )

    # Session Envelope Operations
    def save_session_envelope(self, envelope: UniversalSessionEnvelope):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO session_envelopes (
                id, session_id, source_agent, title, summary, turns, artifacts, decisions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                envelope.id,
                envelope.session_id,
                envelope.source_agent,
                envelope.title,
                envelope.summary,
                json.dumps([t.model_dump(mode="json") for t in envelope.turns]),
                json.dumps(envelope.artifacts),
                json.dumps(envelope.decisions),
                envelope.created_at.isoformat(),
            ))
            conn.commit()

    def get_session_envelope(self, session_id: str) -> Optional[UniversalSessionEnvelope]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM session_envelopes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None
            turns_data = json.loads(row["turns"])
            return UniversalSessionEnvelope(
                id=row["id"],
                session_id=row["session_id"],
                source_agent=row["source_agent"],
                title=row["title"],
                summary=row["summary"] or "",
                turns=[UniversalTurn.model_validate(t) for t in turns_data],
                artifacts=json.loads(row["artifacts"]),
                decisions=json.loads(row["decisions"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    # Token Records & Telemetry Operations
    def save_token_record(self, record: TokenRecord):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO token_records (
                id, timestamp, project_id, session_id, agent_id, task_id,
                provider, model, candidate_tokens, selected_tokens, output_tokens,
                tokens_avoided, cache_hit_tokens, cost_without_usd, cost_with_usd,
                cost_saved_usd, bytes_avoided, estimated, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.timestamp.isoformat(),
                record.project_id,
                record.session_id,
                record.agent_id,
                record.task_id,
                record.provider,
                record.model,
                record.candidate_tokens,
                record.selected_tokens,
                record.output_tokens,
                record.tokens_avoided,
                record.cache_hit_tokens,
                record.cost_without_usd,
                record.cost_with_usd,
                record.cost_saved_usd,
                record.bytes_avoided,
                1 if record.estimated else 0,
                json.dumps(record.metadata),
            ))
            conn.commit()

    def _row_to_token_record(self, row: sqlite3.Row) -> TokenRecord:
        return TokenRecord(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            project_id=row["project_id"],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            task_id=row["task_id"],
            provider=row["provider"],
            model=row["model"],
            candidate_tokens=row["candidate_tokens"],
            selected_tokens=row["selected_tokens"],
            output_tokens=row["output_tokens"],
            tokens_avoided=row["tokens_avoided"],
            cache_hit_tokens=row["cache_hit_tokens"],
            cost_without_usd=row["cost_without_usd"],
            cost_with_usd=row["cost_with_usd"],
            cost_saved_usd=row["cost_saved_usd"],
            bytes_avoided=row["bytes_avoided"],
            estimated=bool(row["estimated"]),
            metadata=json.loads(row["metadata"]),
        )

    def list_token_records(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[TokenRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)
            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM token_records {where_clause} ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            cursor.execute(sql, params)
            return [self._row_to_token_record(r) for r in cursor.fetchall()]

    def get_token_summary(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AnalyticsSummary:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"""
            SELECT
                COUNT(*) as total_events,
                COALESCE(SUM(candidate_tokens), 0) as total_candidate,
                COALESCE(SUM(selected_tokens), 0) as total_selected,
                COALESCE(SUM(output_tokens), 0) as total_output,
                COALESCE(SUM(tokens_avoided), 0) as total_avoided,
                COALESCE(SUM(bytes_avoided), 0) as total_bytes,
                COALESCE(SUM(cost_without_usd), 0.0) as total_cost_without,
                COALESCE(SUM(cost_with_usd), 0.0) as total_cost_with,
                COALESCE(SUM(cost_saved_usd), 0.0) as total_cost_saved,
                COALESCE(SUM(cache_hit_tokens), 0) as total_cache_hits,
                COALESCE(SUM(CASE WHEN estimated = 1 THEN 1 ELSE 0 END), 0) as estimated_count,
                COALESCE(SUM(CASE WHEN estimated = 0 THEN 1 ELSE 0 END), 0) as reported_count
            FROM token_records {where_clause}
            """
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if not row or row["total_events"] == 0:
                return AnalyticsSummary()

            total_events = row["total_events"]
            total_cand = row["total_candidate"]
            total_avoid = row["total_avoided"]
            est_count = row["estimated_count"]
            rep_count = row["reported_count"]
            ratio = round((total_avoid / total_cand) * 100.0, 2) if total_cand > 0 else 0.0
            est_pct = round((est_count / total_events) * 100.0, 1) if total_events > 0 else 100.0

            return AnalyticsSummary(
                total_events=total_events,
                total_candidate_tokens=total_cand,
                total_selected_tokens=row["total_selected"],
                total_output_tokens=row["total_output"],
                total_tokens_avoided=total_avoid,
                overall_reduction_ratio=ratio,
                bytes_not_transmitted=row["total_bytes"],
                total_cost_without_usd=round(row["total_cost_without"], 4),
                total_cost_with_usd=round(row["total_cost_with"], 4),
                cost_saved_usd=round(row["total_cost_saved"], 4),
                cache_hits=row["total_cache_hits"],
                estimated_percentage=est_pct,
                provider_reported_events=rep_count,
                estimated_events=est_count,
            )

    def get_token_breakdown(
        self,
        dimension: str = "provider",
        project_id: Optional[str] = None,
    ) -> List[BreakdownItem]:
        valid_dimensions = {
            "provider": "provider",
            "model": "model",
            "agent": "agent_id",
            "project": "project_id",
            "session": "session_id",
        }
        col = valid_dimensions.get(dimension.lower(), "provider")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"""
            SELECT
                COALESCE({col}, 'unknown') as dim_key,
                COUNT(*) as event_count,
                COALESCE(SUM(candidate_tokens), 0) as cand,
                COALESCE(SUM(selected_tokens), 0) as sel,
                COALESCE(SUM(output_tokens), 0) as out_tok,
                COALESCE(SUM(tokens_avoided), 0) as avoided,
                COALESCE(SUM(cost_without_usd), 0.0) as cost_without,
                COALESCE(SUM(cost_with_usd), 0.0) as cost_with,
                COALESCE(SUM(cost_saved_usd), 0.0) as cost_saved
            FROM token_records {where_clause}
            GROUP BY {col}
            ORDER BY avoided DESC
            """
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            items = []
            for r in rows:
                c = r["cand"]
                a = r["avoided"]
                ratio = round((a / c) * 100.0, 2) if c > 0 else 0.0
                items.append(
                    BreakdownItem(
                        dimension=dimension,
                        key=str(r["dim_key"]),
                        count=r["event_count"],
                        candidate_tokens=c,
                        selected_tokens=r["sel"],
                        output_tokens=r["out_tok"],
                        tokens_avoided=a,
                        reduction_ratio=ratio,
                        cost_without_usd=round(r["cost_without"], 4),
                        cost_with_usd=round(r["cost_with"], 4),
                        cost_saved_usd=round(r["cost_saved"], 4),
                    )
                )
            return items

db = DatabaseManager()

