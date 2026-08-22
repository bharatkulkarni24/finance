import os
import secrets
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'finance.db')

# India Standard Time, expressed as a fixed offset (IST has no DST).
IST_OFFSET = timedelta(hours=5, minutes=30)


def now_ist() -> datetime:
    """Current IST as a naive datetime, matching the DB's string format.

    All entry timestamps flow through this so records carry Indian wall-clock
    time regardless of the server's own timezone.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None) + IST_OFFSET


def today_ist():
    """Current calendar date in India (naive), for day-boundary logic."""
    return now_ist().date()


def _load_secret_key() -> str:
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    path = os.path.join(BASE_DIR, '.secret_key')
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing = f.read().strip()
        if existing:
            return existing
    key = secrets.token_hex(32)
    with open(path, 'w') as f:
        f.write(key)
    return key


SECRET_KEY = _load_secret_key()
