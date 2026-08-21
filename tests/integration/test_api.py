import os
import sys
import io
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
    # Mechanics tests run on tiny seeded books; suspend the insufficient-funds
    # guard so loan approvals / FD operations in fixtures aren't blocked.
    core.config.ALLOW_OVERLEND = True
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


ADMIN_NAME = 'Govindrao Kulkarni'
ADMIN_PASSWORD = 'test-admin-pw'


def _set_password(name, password):
    from werkzeug.security import generate_password_hash
    from core.database import get_conn
    conn = get_conn()
    conn.execute('UPDATE members SET password=? WHERE name=?', (generate_password_hash(password), name))
    conn.commit()
    conn.close()


def _admin_login(client):
    _set_password(ADMIN_NAME, ADMIN_PASSWORD)
    resp = client.post('/api/login', json={'name': ADMIN_NAME, 'pin': ADMIN_PASSWORD})
    assert resp.status_code == 200
    return resp.get_json()['token']


def _admin_headers(client):
    token = getattr(client, '_admin_token', None)
    if token is None:
        token = _admin_login(client)
        client._admin_token = token
    return {'X-ADMIN-TOKEN': token}


def _create_member(client, name='Test Member'):
    resp = client.post('/api/members', json={'name': name}, headers=_admin_headers(client))
    assert resp.status_code == 201
    return resp.get_json()['member_id']


def _login_member(client, name, password='test-pw'):
    _set_password(name, password)
    resp = client.post('/api/login', json={'name': name, 'pin': password})
    assert resp.status_code == 200


def _create_and_login_member(client, name='Test Member', password='test-pw'):
    mid = _create_member(client, name)
    _login_member(client, name, password)
    return mid


def _apply_and_approve_loan(client, mid, amount=10000, term_months=12):
    _login_member(client, 'Test Member')
    r = client.post(f'/api/members/{mid}/apply_loan', json={'amount': amount, 'term_months': term_months})
    req_id = r.get_json()['request']['req_id']
    return client.post(f'/api/admin/approve_loan/{req_id}', headers=_admin_headers(client))


def _submit_and_approve_payment(client, mid, payload):
    _login_member(client, 'Test Member')
    r = client.post(f'/api/members/{mid}/submit_payment_request', json=payload)
    req_id = r.get_json()['request']['req_id']
    return client.post(f'/api/admin/approve_request/{req_id}', headers=_admin_headers(client))


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
        _set_password(ADMIN_NAME, ADMIN_PASSWORD)
        resp = client.post('/api/login', json={'name': ADMIN_NAME, 'pin': ADMIN_PASSWORD})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['is_admin'] == 1
        assert data.get('token')

    def test_login_member(self, client):
        mid = _create_member(client, 'Regular User')
        _set_password('Regular User', 'test-member-pw')
        resp = client.post('/api/login', json={'name': 'Regular User', 'pin': 'test-member-pw'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['is_admin'] == 0
        assert 'token' not in data


class TestAPISession:
    def test_me_returns_logged_in_user(self, client):
        _set_password(ADMIN_NAME, ADMIN_PASSWORD)
        client.post('/api/login', json={'name': ADMIN_NAME, 'pin': ADMIN_PASSWORD})
        resp = client.get('/api/me')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['name'] == ADMIN_NAME

    def test_me_unauthorized_when_not_logged_in(self, client):
        resp = client.get('/api/me')
        assert resp.status_code == 401

    def test_logout_clears_session(self, client):
        _set_password(ADMIN_NAME, ADMIN_PASSWORD)
        client.post('/api/login', json={'name': ADMIN_NAME, 'pin': ADMIN_PASSWORD})
        assert client.get('/api/me').status_code == 200
        client.post('/api/logout')
        assert client.get('/api/me').status_code == 401

    def test_session_survives_refresh(self, client):
        _set_password(ADMIN_NAME, ADMIN_PASSWORD)
        client.post('/api/login', json={'name': ADMIN_NAME, 'pin': ADMIN_PASSWORD})
        fresh = client.get('/api/me')
        assert fresh.status_code == 200
        assert fresh.get_json()['name'] == ADMIN_NAME


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestAPIZero:
    def test_login_no_name(self, client):
        resp = client.post('/api/login', json={'name': '', 'pin': ''})
        assert resp.status_code == 400
        assert resp.get_json()['error'] == 'Name is required'

    def test_login_missing_password(self, client):
        resp = client.post('/api/login', json={'name': ADMIN_NAME, 'pin': ''})
        assert resp.status_code == 400
        assert resp.get_json()['error'] == 'Password is needed'

    def test_login_nonexistent_member(self, client):
        resp = client.post('/api/login', json={'name': 'Nobody', 'pin': ''})
        assert resp.status_code == 404

    def test_login_admin_wrong_pin(self, client):
        _set_password(ADMIN_NAME, ADMIN_PASSWORD)
        resp = client.post('/api/login', json={'name': ADMIN_NAME, 'pin': 'wrong'})
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Incorrect password'

    def test_get_nonexistent_member(self, client):
        resp = client.get('/api/members/99999')
        assert resp.status_code == 401  # anonymous access is blocked before existence check
        resp = client.get('/api/members/99999', headers=_admin_headers(client))
        assert resp.status_code == 404  # authenticated admin gets a proper 404

    def test_unauthorized_admin_endpoint(self, client):
        resp = client.get('/api/admin/stats')
        assert resp.status_code == 401

    def test_period_summary_unauthorized(self, client):
        resp = client.get('/api/admin/period_summary')
        assert resp.status_code == 401

    def test_apply_loan_zero_amount(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/apply_loan', json={'amount': 0, 'term_months': 12})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['request']['loan_amount'] == 0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestAPIOne:
    def test_get_one_member(self, client):
        _admin_headers(client)
        resp = client.get('/api/members/1001')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['member_id'] == 1001
        assert 'loans' in data
        assert 'payments' in data

    def test_apply_one_loan(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['request']['loan_amount'] == 10000
        assert data['request']['loan_term_months'] == 12
        assert data['request']['status'] == 'submitted'

    def test_approve_one_loan(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        resp = client.post('/api/admin/approve_loan/1', headers=_admin_headers(client),
                           json={'approver_id': 0})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'approved'
        assert data['loan']['status'] == 'active'

    def test_submit_payment_request(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/submit_payment_request',
                           json={'amount': 500, 'type': 'share'})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'submitted'

    def test_admin_stats(self, client):
        resp = client.get('/api/admin/stats', headers=_admin_headers(client))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['member_count'] >= 1

    def test_admin_period_summary(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        resp = client.get('/api/admin/period_summary', headers=_admin_headers(client))
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'months' in data and 'years' in data
        assert 'monthly' in data and 'yearly' in data
        latest_month = data['months'][-1]
        assert data['monthly'][latest_month]['share'] == 500
        for key in ('share', 'loan_principal', 'loan_interest', 'fine'):
            assert key in data['monthly'][latest_month]


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestAPIMany:
    def test_create_multiple_members(self, client):
        for name in ['M1', 'M2', 'M3']:
            client.post('/api/members', json={'name': name}, headers=_admin_headers(client))
        resp = client.get('/api/members')
        data = resp.get_json()
        names = [m['name'] for m in data]
        assert 'M1' in names
        assert 'M2' in names
        assert 'M3' in names

    def test_multiple_loans(self, client):
        mid = _create_and_login_member(client)
        for i in range(3):
            client.post(f'/api/members/{mid}/apply_loan', json={'amount': (i + 1) * 5000, 'term_months': 12})
        resp = client.get('/api/admin/submitted_requests', headers=_admin_headers(client))
        data = resp.get_json()
        loan_requests = [r for r in data if r['item_type'] == 'loan']
        assert len(loan_requests) >= 3


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestAPIBoundary:
    def test_update_member(self, client):
        resp = client.patch('/api/members/1001', headers=_admin_headers(client),
                            json={'phone': '1234567890', 'address': 'New Address'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['phone'] == '1234567890'
        assert data['address'] == 'New Address'

    def test_self_update_member(self, client):
        mid = _create_and_login_member(client)
        resp = client.patch(f'/api/members/{mid}/self', json={'phone': '9876543210'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['phone'] == '9876543210'

    def test_large_loan_amount(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/apply_loan',
                           json={'amount': 1000000, 'term_months': 12})
        assert resp.status_code == 201
        assert resp.get_json()['request']['loan_amount'] == 1000000

    def test_submit_payment_with_note(self, client):
        mid = _create_and_login_member(client)
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
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        resp = client.get('/api/admin/entries', headers=_admin_headers(client))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1
        share = next(e for e in data if e['kind'] == 'split' and e['member_name'] == 'Test Member')
        assert share['split']['share'] == 500

    def test_list_entries_filtered(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        resp = client.get(f'/api/admin/entries?member_id={mid}', headers=_admin_headers(client))
        data = resp.get_json()
        assert data and all(e['member_id'] == mid for e in data)
        resp = client.get('/api/admin/entries?type=share', headers=_admin_headers(client))
        data = resp.get_json()
        assert data and all(e['kind'] == 'share' for e in data)

    def test_list_entries_date_filter(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        share = next(e for e in client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
                     if e['kind'] == 'split' and e['member_name'] == 'Test Member')
        today = share['date']
        data = client.get(f'/api/admin/entries?date_from={today}&date_to={today}',
                          headers=_admin_headers(client)).get_json()
        assert any(e['id'] == share['id'] for e in data)
        data = client.get('/api/admin/entries?date_from=2000-01-01&date_to=2000-01-01',
                          headers=_admin_headers(client)).get_json()
        assert not any(e['id'] == share['id'] for e in data)

    def test_list_entries_split_kind(self, client):
        mid = _create_member(client)
        _apply_and_approve_loan(client, mid)
        _submit_and_approve_payment(client, mid, {'amount': 500, 'share_amount': 500})
        _submit_and_approve_payment(client, mid, {'amount': 700, 'share_amount': 500, 'fine': 200})
        _submit_and_approve_payment(client, mid,
                                    {'amount': 2000, 'loan_principal': 2000})
        data = client.get('/api/admin/entries?type=split', headers=_admin_headers(client)).get_json()
        mine = [e for e in data if e['member_id'] == mid]
        assert len(mine) == 1
        assert mine[0]['kind'] == 'split'
        assert mine[0]['split']['share'] == 1000
        assert mine[0]['split']['fine'] == 200

    def test_resplit_full_split(self, client):
        mid = _create_member(client)
        _apply_and_approve_loan(client, mid)
        _submit_and_approve_payment(client, mid, {'amount': 500, 'share_amount': 500})
        share = next(e for e in client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
                     if e['kind'] == 'split' and e['member_name'] == 'Test Member')
        resp = client.post('/api/admin/entries/edit', headers=_admin_headers(client),
                           json={'kind': 'split', 'member_id': mid, 'date': share['date'],
                                 'share': 500, 'fine': 100, 'loan_interest': 50, 'loan_principal': 1000})
        assert resp.status_code == 200
        data = client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
        split = next(e for e in data if e['kind'] == 'split' and e['member_id'] == mid)
        assert split['split']['share'] == 500
        assert split['split']['fine'] == 100
        assert split['split']['loan_interest'] == 50
        assert split['split']['loan_principal'] == 1000

    def test_income_filter_excludes_late_fee_and_fd(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 550, 'share_amount': 500, 'fine': 50})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        resp = client.post('/api/admin/fd/add', headers=_admin_headers(client),
                           json={'amount': 10000, 'start_date': '2026-01-01', 'term_months': 12,
                                 'interest_rate': 8.5, 'notes': 'Test FD'})
        fd_id = resp.get_json()['fd_id']
        resp = client.post(f'/api/admin/fd/close/{fd_id}', headers=_admin_headers(client),
                           json={'end_date': '2026-12-01', 'interest_earned': 850})
        assert resp.status_code == 200
        fd_data = client.get('/api/admin/entries?type=fd', headers=_admin_headers(client)).get_json()
        assert any(e['kind'] == 'fd' and e['amount'] == 850 for e in fd_data)
        lf_data = client.get('/api/admin/entries?type=fine', headers=_admin_headers(client)).get_json()
        assert any(e['kind'] == 'fine' for e in lf_data)
        income = client.get('/api/admin/entries?type=income', headers=_admin_headers(client)).get_json()
        assert not any(e['kind'] == 'fine' for e in income)
        assert not any(e['kind'] == 'fd' for e in income)

    def test_edit_share_entry(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'share_amount': 500})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        data = client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
        share = next(e for e in data if e['kind'] == 'split' and e['member_name'] == 'Test Member')
        resp = client.post('/api/admin/entries/edit', headers=_admin_headers(client),
                           json={'kind': 'split', 'member_id': mid, 'date': share['date'],
                                 'share': 600, 'fine': 0, 'loan_interest': 0, 'loan_principal': 0})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers=_admin_headers(client))
        payments = resp.get_json()['payments']
        assert any(p['share_amount'] == 600 and (p['pay_date'] or '')[:10] == share['date'] for p in payments)

    def test_edit_loan_principal_adjusts_outstanding(self, client):
        mid = _create_member(client)
        _apply_and_approve_loan(client, mid)
        _submit_and_approve_payment(client, mid,
                                    {'amount': 2000, 'loan_principal': 2000})
        data = client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
        lp = next(e for e in data if e['kind'] == 'split' and e['member_id'] == mid)
        resp = client.post('/api/admin/entries/edit', headers=_admin_headers(client),
                           json={'kind': 'split', 'member_id': mid, 'date': lp['date'],
                                 'share': 0, 'fine': 0, 'loan_interest': 100, 'loan_principal': 1500})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers=_admin_headers(client))
        loan = resp.get_json()['loans'][0]
        assert loan['outstanding'] == 10000 - 1500
        resp = client.get('/api/admin/entries', headers=_admin_headers(client))
        lp2 = next(e for e in resp.get_json() if e['id'] == lp['id'])
        assert lp2['split']['loan_principal'] == 1500
        assert lp2['split']['loan_interest'] == 100

    def test_edit_income_entry(self, client):
        resp = client.post('/api/admin/income-expense/add', headers=_admin_headers(client),
                           json={'type': 'credit', 'amount': 1000, 'description': 'Donation'})
        assert resp.status_code == 200
        data = client.get('/api/admin/entries?type=income', headers=_admin_headers(client)).get_json()
        entry = next(e for e in data if e['description'] == 'Donation')
        resp = client.post('/api/admin/entries/edit', headers=_admin_headers(client),
                           json={'kind': 'income', 'transaction_id': entry['transaction_id'],
                                 'member_id': None, 'date': '2026-08-05', 'amount': 1200,
                                 'description': 'Donation'})
        assert resp.status_code == 200
        data = client.get('/api/admin/entries?type=income', headers=_admin_headers(client)).get_json()
        edited = next(e for e in data if e['transaction_id'] == entry['transaction_id'])
        assert edited['amount'] == 1200

    def test_delete_share_entry(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request', json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        data = client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
        share = next(e for e in data if e['kind'] == 'split' and e['member_name'] == 'Test Member')
        resp = client.post('/api/admin/entries/delete', headers=_admin_headers(client),
                           json={'kind': 'split', 'member_id': mid, 'date': share['date']})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers=_admin_headers(client))
        payments = resp.get_json()['payments']
        assert not any(p['share_amount'] and (p['pay_date'] or '')[:10] == share['date'] for p in payments)

    def test_delete_loan_principal_restores_outstanding(self, client):
        mid = _create_member(client)
        _apply_and_approve_loan(client, mid)
        _submit_and_approve_payment(client, mid,
                                    {'amount': 2000, 'loan_principal': 2000})
        data = client.get('/api/admin/entries', headers=_admin_headers(client)).get_json()
        lp = next(e for e in data if e['kind'] == 'split' and e['member_id'] == mid)
        resp = client.post('/api/admin/entries/delete', headers=_admin_headers(client),
                           json={'kind': 'split', 'member_id': mid, 'date': lp['date']})
        assert resp.status_code == 200
        resp = client.get(f'/api/members/{mid}', headers=_admin_headers(client))
        loan = resp.get_json()['loans'][0]
        assert loan['outstanding'] == 10000


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestAPIInterface:
    def test_approve_loan_updates_member_view(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 10000, 'term_months': 12})
        client.post('/api/admin/approve_loan/1', headers=_admin_headers(client))
        resp = client.get(f'/api/members/{mid}')
        data = resp.get_json()
        assert any(l['status'] == 'active' for l in data['loans'])

    def test_payment_request_appears_in_admin(self, client):
        mid = _create_and_login_member(client, 'Alice')
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        resp = client.get('/api/admin/submitted_requests', headers=_admin_headers(client))
        data = resp.get_json()
        assert len(data) >= 1
        assert data[0]['member_name'] == 'Alice'
        assert data[0]['item_type'] == 'payment'

    def test_rejected_requests_endpoint(self, client):
        mid = _create_and_login_member(client, 'Bob')
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        resp = client.post('/api/admin/reject_request/1', headers=_admin_headers(client),
                           json={'approver_id': 0, 'reason': 'Duplicate entry'})
        assert resp.status_code == 200
        data = client.get('/api/admin/rejected_requests', headers=_admin_headers(client)).get_json()
        assert any(r['req_id'] == 1 and r['reject_reason'] == 'Duplicate entry' for r in data)

    def test_approve_payment_creates_payment(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/submit_payment_request',
                    json={'amount': 500, 'type': 'share'})
        client.post('/api/admin/approve_request/1', headers=_admin_headers(client))
        resp = client.get(f'/api/members/{mid}')
        data = resp.get_json()
        shares = [p for p in data['payments'] if p['share_amount'] == 500]
        assert any(p['total_amount'] == 500 for p in shares)

    def test_reject_loan_with_reason(self, client):
        mid = _create_and_login_member(client)
        client.post(f'/api/members/{mid}/apply_loan', json={'amount': 5000, 'term_months': 12})
        resp = client.post('/api/admin/reject_loan/1',
                           headers=_admin_headers(client),
                           json={'approver_id': 0, 'reason': 'Not enough collateral'})
        assert resp.status_code == 200
        resp2 = client.get(f'/api/members/{mid}')
        data = resp2.get_json()
        req = next((r for r in data['requests'] if r['req_id'] == 1), None)
        assert req is not None
        assert req['status'] == 'rejected'
        assert req['reject_reason'] == 'Not enough collateral'
        assert data['loans'] == []  # no loan row is created for rejected loans

    def test_passbook_endpoint(self, client):
        resp = client.get('/api/admin/passbook', headers=_admin_headers(client))
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestAPIException:
    def test_404_for_unknown_route(self, client):
        resp = client.get('/api/unknown_route')
        assert resp.status_code == 404

    def test_member_update_unauthorized_without_pin(self, client):
        resp = client.patch('/api/members/1001', json={'phone': '123'})
        assert resp.status_code == 401

    def test_upload_photo_no_file(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/upload_photo')
        assert resp.status_code == 400

    def test_upload_photo_rejects_non_image(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/upload_photo',
                           data={'photo': (io.BytesIO(b'<script>alert(1)</script>'), 'evil.html')},
                           content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_upload_photo_rejects_oversize(self, client):
        mid = _create_and_login_member(client)
        big = io.BytesIO(b'x' * (2 * 1024 * 1024 + 1))
        resp = client.post(f'/api/members/{mid}/upload_photo',
                           data={'photo': (big, 'big.png')},
                           content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_contribute_with_no_data(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/contribute', json={})
        assert resp.status_code == 400  # amount must be > 0

    def test_contribute_creates_payment_request(self, client):
        mid = _create_and_login_member(client)
        resp = client.post(f'/api/members/{mid}/contribute', json={'amount': 500})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'submitted'
        assert data['request']['share_amount'] == 500

    def test_admin_fd_add_unauthorized(self, client):
        resp = client.post('/api/admin/fd/add', json={'amount': 50000})
        assert resp.status_code == 401

    def test_statement_endpoint(self, client):
        mid = _create_and_login_member(client)
        resp = client.get(f'/api/members/{mid}/statement')
        assert resp.status_code == 200
        assert resp.content_type == 'text/csv'
