"""Daily backup + prune behaviour (fully isolated from the real backups dir)."""
import os

import pytest

from core.database import get_conn


@pytest.fixture(autouse=True)
def isolated_backup_dir(tmp_path, monkeypatch):
    from core import backup as b
    b.BACKUP_DIR = str(tmp_path / 'backups')
    yield


def _mk_fake_dated(name):
    from core import backup as b
    os.makedirs(b.BACKUP_DIR, exist_ok=True)
    with open(os.path.join(b.BACKUP_DIR, name), 'wb') as f:
        f.write(b'x')


class TestDailyBackup:
    def test_creates_today_file_once(self, setup_db):
        from core import backup as b
        conn = get_conn()
        conn.execute("INSERT INTO group_ledger (debit_credit, amount, description) VALUES ('credit', 100, 'seed')")
        conn.commit()
        conn.close()
        assert not os.path.exists(b.today_file())
        b.maybe_backup()
        assert os.path.exists(b.today_file())
        first = open(b.today_file(), 'rb').read()
        # second call same day: no-op, file untouched
        b.maybe_backup()
        assert open(b.today_file(), 'rb').read() == first

    def test_snapshot_contains_data(self, setup_db):
        from core import backup as b
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO members (name, password, is_admin, joined_date, entry_deposit_amount) VALUES ('B', '', 0, '2025-04-01', 123)")
        conn.commit()
        mid = cur.lastrowid
        conn.close()
        dest = os.path.join(b.BACKUP_DIR, 'snapshot-test.db')
        b.create_snapshot(dest)
        import sqlite3
        snap = sqlite3.connect(dest)
        row = snap.execute('SELECT entry_deposit_amount FROM members WHERE member_id=?', (mid,)).fetchone()
        snap.close()
        os.remove(dest)
        assert row[0] == 123


class TestPrune:
    def test_keeps_only_14_dated(self, setup_db):
        from core import backup as b
        for d in range(1, 21):
            _mk_fake_dated(f'finance-2026-07-{d:02d}.db')
        b.maybe_backup()
        left = [f for f in os.listdir(b.BACKUP_DIR) if f.startswith('finance-2')]
        assert len(left) <= 14

    def test_manual_snapshots_pruned_to_30(self, setup_db):
        from core import backup as b
        for i in range(35):
            _mk_fake_dated(f'finance-backup-20260710-00000{i:02d}.db')
        b.maybe_backup()
        left = [f for f in os.listdir(b.BACKUP_DIR) if f.startswith('finance-backup-')]
        assert len(left) <= 30

    def test_missing_db_is_safe(self, setup_db, tmp_path):
        from core import config, backup as b
        old = config.DB_PATH
        config.DB_PATH = str(tmp_path / 'nope.db')
        try:
            b.maybe_backup()  # must not raise
        finally:
            config.DB_PATH = old
