import tempfile
from pathlib import Path
import pytest
import contextos.storage.db as db_mod
from contextos.storage.db import DatabaseManager

@pytest.fixture(autouse=True, scope="session")
def isolate_test_database(tmp_path_factory):
    """
    Autouse fixture that ensures every pytest test run operates against a fresh,
    isolated SQLite database in a temporary directory, completely isolating the
    test suite from the production database at .contextos/contextos.db.
    """
    session_dir = tmp_path_factory.mktemp("contextos_test_db")
    test_db_path = session_dir / "test_session.db"
    test_db = DatabaseManager(test_db_path)

    # Save original db target
    original_target = db_mod.db.get_target() if hasattr(db_mod.db, "get_target") else db_mod.db

    # Redirect proxy target
    if hasattr(db_mod.db, "set_target"):
        db_mod.db.set_target(test_db)
    else:
        db_mod.db = test_db

    import contextos.runtime.supervisor as sup
    import contextos.memory.engine as mem_eng
    import contextos.analytics.engine as ana_eng
    import contextos.api.routes as routes

    orig_sup_db = getattr(sup, "db", None)
    sup.db = test_db
    routes.db = test_db
    mem_eng.db = test_db
    ana_eng.db = test_db

    yield test_db

    # Teardown and restore
    if hasattr(db_mod.db, "set_target"):
        db_mod.db.set_target(original_target)
    else:
        db_mod.db = original_target

    if orig_sup_db is not None:
        sup.db = orig_sup_db
    routes.db = original_target
    mem_eng.db = original_target
    ana_eng.db = original_target
