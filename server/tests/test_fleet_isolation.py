import tempfile
from pathlib import Path
import pytest
from contextos.storage.db import DatabaseManager, db
from contextos.models.agent import AgentRole

def test_fresh_database_seeds_canonical_five_roles():
    """
    Verify that initializing a fresh database automatically seeds the 5 canonical
    supervised fleet roles (PLANNER, CODER, REVIEWER, RESEARCHER, TESTER)
    so the Control Center never presents an empty or single-role duplicate fleet.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db_path = Path(tmp_dir) / "fresh.db"
        fresh_db = DatabaseManager(test_db_path)
        agents = fresh_db.list_agents()

        assert len(agents) == 5, f"Expected 5 canonical agents, got {len(agents)}"
        roles = {a.role for a in agents}
        assert roles == {
            AgentRole.PLANNER,
            AgentRole.CODER,
            AgentRole.REVIEWER,
            AgentRole.RESEARCHER,
            AgentRole.TESTER,
        }

def test_conftest_isolates_db_singleton_from_production():
    """
    Ensure the global db singleton in test runs never points to the live production database.
    """
    from contextos.config import settings
    prod_path = (Path(__file__).resolve().parents[2] / ".contextos" / "contextos.db").resolve()
    current_db_path = Path(db.db_path).resolve()
    assert current_db_path != prod_path, (
        f"Test suite is running against production database: {current_db_path} == {prod_path}"
    )
