import sqlite3

from core.database import get_conn, init_db


class TestDatabaseMigration:
    def test_missing_column_is_added(self, setup_db):
        conn = get_conn()
        conn.execute('ALTER TABLE members DROP COLUMN phone')
        conn.commit()
        conn.close()

        init_db()

        conn = get_conn()
        cols = {r[1] for r in conn.execute('PRAGMA table_info(members)')}
        conn.close()
        assert 'phone' in cols

    def test_no_missing_columns_on_fresh_db(self, setup_db):
        init_db()
        conn = get_conn()
        rows = conn.execute('PRAGMA table_info(members)').fetchall()
        conn.close()
        names = {r[1] for r in rows}
        for col in ('member_id', 'name', 'phone', 'joined_date', 'deposit_amount',
                    'is_admin', 'dob', 'address', 'photo_url', 'password'):
            assert col in names
