from datetime import date
import pytest

from core.models.payment import (
    add_contribution, create_payment_request,
    approve_payment_request,
    reject_payment_request,
    admin_direct_entry,
)
from core.models.requests import list_submitted_requests
from core.models.member import create_member, get_member
from core.models.loan import create_loan, approve_loan, get_loan
from core.database import get_conn


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestPaymentSimple:
    def test_create_payment_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        assert req['total_amount'] == 500
        assert req['status'] == 'submitted'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestPaymentZero:
    def test_create_payment_request_zero_amount(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 0)
        assert req['total_amount'] == 0

    def test_list_submitted_requests_empty(self, setup_db):
        requests = list_submitted_requests()
        assert requests == []

    def test_approve_nonexistent_request(self, setup_db):
        result = approve_payment_request(99999, 0)
        assert result is None

    def test_reject_nonexistent_request(self, setup_db):
        result = reject_payment_request(99999, 0)
        assert result is None


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestPaymentOne:
    def test_create_and_list_one_pending(self, setup_db):
        m = create_member('Test')
        create_payment_request(m['member_id'], 500, share_amount=500)
        pending = list_submitted_requests()
        assert len(pending) == 1
        assert pending[0]['member_name'] == 'Test'

    def test_approve_one_share_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        result = approve_payment_request(req['req_id'], m['member_id'])
        assert result['status'] == 'approved'
        assert result['approved_by'] == m['member_id']

    def test_reject_one_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        result = reject_payment_request(req['req_id'], m['member_id'], reason='Not eligible')
        assert result['status'] == 'rejected'
        assert result['rejected_by'] == m['member_id']
        assert result['reject_reason'] == 'Not eligible'

    def test_reject_without_reason_defaults_empty(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        result = reject_payment_request(req['req_id'], m['member_id'])
        assert result['status'] == 'rejected'
        assert result['reject_reason'] == ''


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestPaymentMany:
    def test_multiple_pending_requests(self, setup_db):
        m = create_member('Test')
        for i in range(3):
            create_payment_request(m['member_id'], (i + 1) * 100, share_amount=(i + 1) * 100)
        pending = list_submitted_requests()
        assert len(pending) == 3

    def test_approve_one_among_many(self, setup_db):
        m = create_member('Test')
        r1 = create_payment_request(m['member_id'], 500, share_amount=500)
        r2 = create_payment_request(m['member_id'], 1000, share_amount=1000)
        approve_payment_request(r1['req_id'], 0)
        pending = list_submitted_requests()
        assert len(pending) == 1
        assert pending[0]['req_id'] == r2['req_id']


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestPaymentBoundary:
    def test_approve_share_creates_payment(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        approve_payment_request(req['req_id'], 0)
        member = get_member(m['member_id'], full=True)
        shares = [p for p in member['payments'] if p['share_amount'] == 500]
        assert any(p['total_amount'] == 500 for p in shares)

    def test_approve_share_with_late_fee_splits(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 900, fine=200, share_amount=700)
        approve_payment_request(req['req_id'], 0)
        member = get_member(m['member_id'], full=True)
        pay = next(p for p in member['payments'] if p['share_amount'] == 700)
        assert pay['fine'] == 200
        assert pay['total_amount'] == 900

    def test_approve_loan_request_updates_loan(self, setup_db):
        m = create_member('Test')
        req = create_loan(m['member_id'], 10000, 12)
        loan = approve_loan(req['req_id'], 0)
        pay_req = create_payment_request(m['member_id'], 3000, loan_principal=3000)
        approve_payment_request(pay_req['req_id'], 0)
        updated_loan = get_loan(loan['loan_id'])
        assert updated_loan['outstanding'] == pytest.approx(7000, abs=5)

    def test_approve_wrong_member_fails(self, setup_db):
        m1 = create_member('Owner')
        m2 = create_member('Stranger')
        req = create_payment_request(m1['member_id'], 500, share_amount=500)
        result = approve_payment_request(req['req_id'], m2['member_id'])
        assert result is not None

    def test_approve_already_rejected_fails(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        reject_payment_request(req['req_id'], 0)
        result = approve_payment_request(req['req_id'], m['member_id'])
        assert result is None


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestPaymentInterface:
    def test_approve_share_creates_payment_record(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        approve_payment_request(req['req_id'], 0)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM member_ledger WHERE member_id=? AND share_amount=500", (m['member_id'],))
        pays = [dict(r) for r in cur.fetchall()]
        conn.close()
        assert len(pays) == 1
        assert pays[0]['share_amount'] == 500

    def test_approve_loan_request_creates_payment_record(self, setup_db):
        m = create_member('Test')
        req = create_loan(m['member_id'], 10000, 12)
        approve_loan(req['req_id'], 0)
        pay_req = create_payment_request(m['member_id'], 3000, loan_principal=3000)
        approve_payment_request(pay_req['req_id'], 0)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM member_ledger WHERE member_id=?', (m['member_id'],))
        payments = [dict(r) for r in cur.fetchall()]
        conn.close()
        assert any(p['loan_principal'] == 3000 for p in payments)

    def test_admin_direct_entry_split(self, setup_db):
        m = create_member('Test')
        admin_direct_entry(m['member_id'], share_amount=500, fine=100, entry_date='2026-06-10')
        member = get_member(m['member_id'], full=True)
        pay = next(p for p in member['payments'] if p['share_amount'] == 500)
        assert pay['fine'] == 100
        assert pay['total_amount'] == 600


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestPaymentException:
    def test_add_contribution_invalid_member(self, setup_db):
        result = add_contribution(99999, date.today(), 500, 'share')
        assert result is None

    def test_create_payment_request_no_member(self, setup_db):
        result = create_payment_request(99999, 500)
        assert result is not None
        assert result['member_id'] == 99999
