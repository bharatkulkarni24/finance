import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '3.1.8'

from core import create_app


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / 'test.db')
    import core.config
    core.config.DB_PATH = db_path
    from core.database import init_db, seed_db
    init_db()
    seed_db()
    yield


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


ADMIN_PIN = '1234'


def _create_member(client, name='Test Member'):
    resp = client.post('/api/members', json={'name': name})
    return resp.get_json()['id']


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestAPISimple:
    def test_index_returns_200(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_members_list(self, client):
        resp = client.get('/api/members')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_login_admin(self, client):
        resp = client.post('/api/login', json={'name': 'Govindrao Kulkarni', 'pin': ADMIN_PIN})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['is_admin'] == 1

    def test_login_member(self, client):
        mid = _create_member(client, 'Regular User')
        resp = client.post('/api/login', json={'name': 'Regular User', 'pin': ''})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['is_admin'] == 0


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestAPIZero:
    def test_login_no_name(self, client):
        resp = client.post('/api/login', json={'name': '', 'pin': ''})
        assert resp.status_code == 400

    def test_login_nonexistent_member(self, client):
        resp = client.post('/api/login', json={'name': 'Nobody', 'pin': ''})
        assert resp.status_code == 404

    def test_login_admin_wrong_pin(self, client):
        resp = client.post('/api/login', json={'name': 'Govindrao Kulkarni', 'pin': 'wrong'})
        assert resp.status_code == 401

    def test_get_nonexistent_member(self, client):
        resp = client.get('/api/members/99999')
        assert resp.status_code == 404

    def test_unauthorized_admin_endpoint(self, client):
        resp = client.get('/api/admin/stats')
        assert resp.status_code == 401

    def test_period_summary_unauthorized(self, client):
        resp = client.get('/api/admin/period_summary')
        assert resp.status_code == 401

    def test_apply_loan_zero_amount(self, client):
        mid = _create_member(client)
        resp = client.post(f'/api/members/{mid}/apply_loan', json={'amount': 0, 'term_months': 12})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['loan']['principal'] == 0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestAPIOne:
    def test_get_one_member(self, client):
        resp = client.get('/api/members/1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == 1
        assert 'loans' in data
        assert 'contributions' in data

    def test_apply_one_loan(self, client):
        mid = _create_member(client)
        resp = client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['loan']['principal'] == 10000
        assert data['loan']['status'] == 'applied'

    def test_approve_one_loan(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        resp = client.post('/api/admin/approve_loan/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'approved'
        assert data['loan']['status'] == 'active'

    def test_submit_payment_request(self, client):
        mid = _create_member(client)
        resp = client.post(f'/api/members/{mid}/submit_payment_request',
                           json={'amount': 500, 'type': 'share'})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'submitted'

    def test_admin_stats(self, client):
        resp = client.get('/api/admin/stats', headers={'X-ADMIN-PIN': ADMIN_PIN})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['member_count'] >= 1

    def test_admin_period_summary(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        resp = client.get('/api/admin/period_summary', headers={'X-ADMIN-PIN': ADMIN_PIN})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'months' in data and 'years' in data
        assert 'monthly' in data and 'yearly' in data
        latest_month = data['months'][-1]
        assert data['monthly'][latest_month]['share'] == 500
        for key in ('share', 'principal', 'interest', 'fine'):
            assert key in data['monthly'][latest_month]


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestAPIMany:
    def test_create_multiple_members(self, client):
        for name in ['M1', 'M2', 'M3']:
            client.post('/api/members', json={'name': name})
        resp = client.get('/api/members')
        data = resp.get_json()
        names = [m['name'] for m in data]
        assert 'M1' in names
        assert 'M2' in names
        assert 'M3' in names

    def test_multiple_loans(self, client):
        mid = _create_member(client)
        for i in range(3):
            client.post(f'/api/members/{mid}/apply_loan', json={'amount': (i + 1) * 5000, 'term_months': 12})
        resp = client.get('/api/admin/pending_loans', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = resp.get_json()
        assert len(data) >= 3


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestAPIBoundary:
    def test_update_member(self, client):
        resp = client.patch('/api/members/1', headers={'X-ADMIN-PIN': ADMIN_PIN},
                            json={'phone': '1234567890', 'address': 'New Address'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['phone'] == '1234567890'
        assert data['address'] == 'New Address'

    def test_self_update_member(self, client):
        mid = _create_member(client)
        resp = client.patch(f'/api/members/{mid}/self', json={'phone': '9876543210'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['phone'] == '9876543210'

    def test_large_loan_amount(self, client):
        mid = _create_member(client)
        resp = client.post(f'/api/members/{mid}/apply_loan',
                           json={'amount': 1000000, 'term_months': 12})
        assert resp.status_code == 201
        assert resp.get_json()['loan']['principal'] == 1000000

    def test_submit_payment_with_note(self, client):
        mid = _create_member(client)
        resp = client.post(f'/api/members/{mid}/submit_payment_request',
                           json={'amount': 500, 'type': 'share', 'note': 'Test payment'})
        data = resp.get_json()
        assert data['request']['note'] == 'Test payment'


# ─── Zombies: Edit Entries ─────────────────────────────────────────────────────

class TestAPIEditEntries:
    def test_entries_unauthorized(self, client):
        resp = client.get('/api/admin/entries')
        assert resp.status_code == 401

    def test_edit_unauthorized(self, client):
        mid = _create_member(client)
        resp = client.post('/api/admin/entries/edit',
                           json={'kind': 'income', 'amount': 100})
        assert resp.status_code == 401

    def test_list_entries(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        resp = client.get('/api/admin/entries', headers={'X-ADMIN-PIN': ADMIN_PIN})
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1
        share = next(e for e in data if e['kind'] == 'share')
        assert share['member_name'] == 'Test Member'
        assert share['amount'] == 500

    def test_list_entries_filtered(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        resp = client.get(f'/api/admin/entries?member_id={mid}', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = resp.get_json()
        assert data and all(e['member_id'] == mid for e in data)
        resp = client.get('/api/admin/entries?type=share', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = resp.get_json()
        assert data and all(e['kind'] == 'share' for e in data)

    def test_edit_share_entry(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = client.get('/api/admin/entries', headers={'X-ADMIN-PIN': ADMIN_PIN}).get_json()
        share = next(e for e in data if e['kind'] == 'share')
        resp = client.post('/api/admin/entries/edit', headers={'X-ADMIN-PIN': ADMIN_PIN},
                           json={'kind': 'share', 'contribution_id': share['contribution_id'],
                                 'transaction_id': share['transaction_id'], 'member_id': mid,
                                 'date': '2026-08-05', 'amount': 600})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers={'X-ADMIN-PIN': ADMIN_PIN})
        contrib = next(c for c in resp.get_json()['contributions'] if c['id'] == share['contribution_id'])
        assert contrib['amount'] == 600

    def test_edit_loan_payment_adjusts_outstanding(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        client.post('/api/admin/approve_loan/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 2000, 'type': 'loan_payment', 'loan_amount': 2000})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = client.get('/api/admin/entries', headers={'X-ADMIN-PIN': ADMIN_PIN}).get_json()
        lp = next(e for e in data if e['kind'] == 'loan_payment' and e['principal'] > 0)
        resp = client.post('/api/admin/entries/edit', headers={'X-ADMIN-PIN': ADMIN_PIN},
                           json={'kind': 'loan_payment', 'payment_id': lp['payment_id'],
                                 'transaction_id': lp['transaction_id'], 'member_id': mid,
                                 'date': '2026-08-05', 'principal': 1500, 'interest': 100, 'fine': 0})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers={'X-ADMIN-PIN': ADMIN_PIN})
        loan = resp.get_json()['loans'][0]
        assert loan['outstanding'] == 10000 - 1500
        resp = client.get('/api/admin/entries', headers={'X-ADMIN-PIN': ADMIN_PIN})
        lp2 = next(e for e in resp.get_json() if e['id'] == lp['id'])
        assert lp2['principal'] == 1500
        assert lp2['interest'] == 100

    def test_edit_income_entry(self, client):
        resp = client.post('/api/admin/income-expense/add', headers={'X-ADMIN-PIN': ADMIN_PIN},
                           json={'type': 'credit', 'amount': 1000, 'desc': 'Donation'})
        assert resp.status_code == 200
        data = client.get('/api/admin/entries?type=income', headers={'X-ADMIN-PIN': ADMIN_PIN}).get_json()
        entry = next(e for e in data if e['desc'] == 'Donation')
        resp = client.post('/api/admin/entries/edit', headers={'X-ADMIN-PIN': ADMIN_PIN},
                           json={'kind': 'income', 'transaction_id': entry['transaction_id'],
                                 'member_id': None, 'date': '2026-08-05', 'amount': 1200,
                                 'description': 'Donation'})
        assert resp.status_code == 200
        data = client.get('/api/admin/entries?type=income', headers={'X-ADMIN-PIN': ADMIN_PIN}).get_json()
        edited = next(e for e in data if e['transaction_id'] == entry['transaction_id'])
        assert edited['amount'] == 1200

    def test_delete_share_entry(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = client.get('/api/admin/entries', headers={'X-ADMIN-PIN': ADMIN_PIN}).get_json()
        share = next(e for e in data if e['kind'] == 'share')
        resp = client.post('/api/admin/entries/delete', headers={'X-ADMIN-PIN': ADMIN_PIN},
                           json={'kind': 'share', 'contribution_id': share['contribution_id'],
                                 'transaction_id': share['transaction_id']})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers={'X-ADMIN-PIN': ADMIN_PIN})
        assert all(c['id'] != share['contribution_id'] for c in resp.get_json()['contributions'])

    def test_delete_loan_payment_restores_outstanding(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        client.post('/api/admin/approve_loan/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 2000, 'type': 'loan_payment', 'loan_amount': 2000})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = client.get('/api/admin/entries', headers={'X-ADMIN-PIN': ADMIN_PIN}).get_json()
        lp = next(e for e in data if e['kind'] == 'loan_payment' and e['principal'] > 0)
        resp = client.post('/api/admin/entries/delete', headers={'X-ADMIN-PIN': ADMIN_PIN},
                           json={'kind': 'loan_payment', 'payment_id': lp['payment_id'],
                                 'transaction_id': lp['transaction_id']})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers={'X-ADMIN-PIN': ADMIN_PIN})
        loan = resp.get_json()['loans'][0]
        assert loan['outstanding'] == 10000


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestAPIInterface:
    def test_approve_loan_updates_member_view(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        client.post('/api/admin/approve_loan/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        resp = client.get(f'/api/members/{mid}')
        data = resp.get_json()
        assert any(l['status'] == 'active' for l in data['loans'])

    def test_payment_request_appears_in_admin(self, client):
        mid = _create_member(client, 'Alice')
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        resp = client.get('/api/admin/payment_requests', headers={'X-ADMIN-PIN': ADMIN_PIN})
        data = resp.get_json()
        assert len(data) >= 1
        assert data[0]['member_name'] == 'Alice'

    def test_approve_payment_creates_contribution(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers={'X-ADMIN-PIN': ADMIN_PIN})
        resp = client.get(f'/api/members/{mid}')
        data = resp.get_json()
        shares = [c for c in data['contributions'] if c['type'] == 'share']
        assert any(c['amount'] == 500 for c in shares)

    def test_reject_loan_with_reason(self, client):
        mid = _create_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 5000, 'term_months': 12})
        resp = client.post('/api/admin/reject_loan/1',
                           headers={'X-ADMIN-PIN': ADMIN_PIN, 'Content-Type': 'application/json'},
                           json={'reason': 'Not enough collateral'})
        assert resp.status_code == 200
        resp2 = client.get(f'/api/members/{mid}')
        data = resp2.get_json()
        loan = next((l for l in data['loans'] if l['id'] == 1), None)
        assert loan is not None
        assert loan['status'] == 'rejected'
        assert loan['reject_reason'] == 'Not enough collateral'

    def test_passbook_endpoint(self, client):
        resp = client.get('/api/admin/passbook', headers={'X-ADMIN-PIN': ADMIN_PIN})
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestAPIException:
    def test_404_for_unknown_route(self, client):
        resp = client.get('/api/unknown_route')
        assert resp.status_code == 404

    def test_member_update_unauthorized_without_pin(self, client):
        resp = client.patch('/api/members/1', json={'phone': '123'})
        assert resp.status_code == 401

    def test_upload_photo_no_file(self, client):
        resp = client.post('/api/members/1/upload_photo')
        assert resp.status_code == 400

    def test_contribute_with_no_data(self, client):
        mid = _create_member(client)
        resp = client.post(f'/api/members/{mid}/contribute', json={})
        assert resp.status_code == 200  # defaults to 0 amount

    def test_admin_fd_add_unauthorized(self, client):
        resp = client.post('/api/admin/fd/add', json={'amount': 50000})
        assert resp.status_code == 401

    def test_statement_endpoint(self, client):
        mid = _create_member(client)
        resp = client.get(f'/api/members/{mid}/statement')
        assert resp.status_code == 200
        assert resp.content_type == 'text/csv'
