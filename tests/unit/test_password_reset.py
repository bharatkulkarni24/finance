"""Admin password-reset route behaviour."""
import sqlite3

import pytest

from core.session import create_admin_session


def _add_member(name='Test Member', is_admin=0):
    from core.database import get_conn
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO members (name, password, is_admin, joined_date, entry_deposit_amount) VALUES (?, '', ?, '2025-04-01', 100)",
        (name, is_admin),
    )
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid


def _name_of(member_id):
    from core.database import get_conn
    conn = get_conn()
    name = conn.execute('SELECT name FROM members WHERE member_id=?', (member_id,)).fetchone()[0]
    conn.close()
    return name


@pytest.fixture
def client(setup_db, seed_db):
    from core import create_app
    return create_app().test_client()


@pytest.fixture
def admin_token(setup_db, seed_db):
    from core.database import get_conn
    conn = get_conn()
    row = conn.execute("SELECT member_id FROM members WHERE is_admin=1 LIMIT 1").fetchone()
    conn.close()
    return create_admin_session(row['member_id'])


class TestAdminResetPassword:
    def test_reset_then_login_works(self, client, admin_token):
        mid = _add_member('Reset Me')
        r = client.post(f'/api/members/{mid}/reset_password',
                        headers={'X-ADMIN-TOKEN': admin_token},
                        json={'new_password': 'fresh123'})
        assert r.status_code == 200
        assert r.get_json()['status'] == 'ok'

        # wrong password rejected, new one accepted
        r = client.post('/api/login', json={'name': 'Reset Me', 'pin': 'wrong'})
        assert r.status_code == 401
        r = client.post('/api/login', json={'name': 'Reset Me', 'pin': 'fresh123'})
        assert r.status_code == 200

    def test_requires_admin(self, client):
        mid = _add_member('No Token')
        r = client.post(f'/api/members/{mid}/reset_password',
                        json={'new_password': 'whatever1'})
        assert r.status_code == 401

    def test_rejects_short_password(self, client, admin_token):
        mid = _add_member('Short Pw')
        r = client.post(f'/api/members/{mid}/reset_password',
                        headers={'X-ADMIN-TOKEN': admin_token},
                        json={'new_password': 'ab'})
        assert r.status_code == 400

    def test_unknown_member_404(self, client, admin_token):
        r = client.post('/api/members/99999/reset_password',
                        headers={'X-ADMIN-TOKEN': admin_token},
                        json={'new_password': 'longenough'})
        assert r.status_code == 404

    def test_old_password_no_longer_valid(self, client, admin_token):
        from werkzeug.security import generate_password_hash
        from core.database import get_conn
        mid = _add_member('Had Old')
        conn = get_conn()
        conn.execute('UPDATE members SET password=? WHERE member_id=?',
                     (generate_password_hash('oldpass9'), mid))
        conn.commit()
        conn.close()

        r = client.post('/api/login', json={'name': 'Had Old', 'pin': 'oldpass9'})
        assert r.status_code == 200

        client.post(f'/api/members/{mid}/reset_password',
                    headers={'X-ADMIN-TOKEN': admin_token},
                    json={'new_password': 'brandnew7'})
        r = client.post('/api/login', json={'name': 'Had Old', 'pin': 'oldpass9'})
        assert r.status_code == 401
        r = client.post('/api/login', json={'name': 'Had Old', 'pin': 'brandnew7'})
        assert r.status_code == 200
