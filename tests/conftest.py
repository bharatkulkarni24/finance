import sys
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / 'test.db')
    import core.config
    core.config.DB_PATH = db_path
    from core.database import init_db
    init_db()
    from core.rate_limit import reset
    reset()
    yield


@pytest.fixture
def seed_db():
    from core.database import seed_db
    seed_db()
