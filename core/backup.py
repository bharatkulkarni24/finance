"""Rolling daily backups of the SQLite database.

- maybe_backup(): called before each request; creates today's snapshot once
  per day into backups/finance-YYYY-MM-DD.db, keeps the newest KEEP dated
  copies. Manual download snapshots (finance-backup-*.db) are kept separately,
  newest MAX_MANUAL.
- create_snapshot(path): safe point-in-time copy usable while the app runs.
Backup creation must never raise into the request path.
"""
import os
import re
import sqlite3
import threading
from datetime import datetime

from core import config
from core.config import now_ist

BACKUP_DIR = os.path.join(config.BASE_DIR, 'backups')
KEEP = 14            # rolling dated copies (one per day)
MAX_MANUAL = 30      # manual download snapshots to retain
_DATED_RE = re.compile(r'^finance-\d{4}-\d{2}-\d{2}\.db$')
_MANUAL_RE = re.compile(r'^finance-backup-.+\.db$')
_lock = threading.Lock()


def today_file() -> str:
    return os.path.join(BACKUP_DIR, 'finance-' + now_ist().strftime('%Y-%m-%d') + '.db')


def create_snapshot(dest_path: str) -> str:
    """Point-in-time copy of the live DB via sqlite3's backup API."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    src = sqlite3.connect(config.DB_PATH)
    dest = sqlite3.connect(dest_path)
    try:
        src.backup(dest)
    finally:
        dest.close()
        src.close()
    return dest_path


def _prune_dir(directory, pattern, keep):
    try:
        files = sorted(f for f in os.listdir(directory) if pattern.match(f))
    except FileNotFoundError:
        return
    for name in files[:-keep] if len(files) > keep else []:
        try:
            os.remove(os.path.join(directory, name))
        except OSError:
            pass


def _prune():
    _prune_dir(BACKUP_DIR, _DATED_RE, KEEP)
    _prune_dir(BACKUP_DIR, _MANUAL_RE, MAX_MANUAL)


def maybe_backup() -> None:
    """Make today's dated backup if it doesn't exist yet; prune old ones."""
    if not _lock.acquire(blocking=False):
        return  # another worker/thread is already backing up
    try:
        if os.path.exists(today_file()):
            return
        if not os.path.exists(config.DB_PATH):
            return
        create_snapshot(today_file())
        _prune()
    except Exception:
        pass  # a failed backup must never break the app
    finally:
        _lock.release()
