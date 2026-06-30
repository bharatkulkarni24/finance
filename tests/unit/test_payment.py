from datetime import datetime, date
import pytest

from core.models.payment import (
    add_contribution, pay_due, create_payment_request,
    list_pending_requests, approve_payment_request,
    reject_payment_request, cancel_payment_request,
)
from core.models.member import create_member, get_member
from core.models.loan import create_loan, approve_loan, get_loan
from core.database import get_conn, row_to_dict


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestPaymentSimple:
    def test_create_payment_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        assert req['amount'] == 500
        assert req['status'] == 'pending'
        assert req['type'] == 'share'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestPaymentZero:
    def test_create_payment_request_zero_amount(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 0, 'share')
        assert req['amount'] == 0

    def test_list_pending_requests_empty(self, setup_db):
        requests = list_pending_requests()
        assert requests == []

    def test_approve_nonexistent_request(self, setup_db):
        result = approve_payment_request(99999, 0)
        assert result is None

    def test_reject_nonexistent_request(self, setup_db):
        result = reject_payment_request(99999, 0, 'reason')
        assert result is None

    def test_cancel_nonexistent_request(self, setup_db):
        result = cancel_payment_request(99999, 1)
        assert result is None


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestPaymentOne:
    def test_create_and_list_one_pending(self, setup_db):
        m = create_member('Test')
        create_payment_request(m['id'], 500, 'share')
        pending = list_pending_requests()
        assert len(pending) == 1
        assert pending[0]['member_name'] == 'Test'

    def test_approve_one_share_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        result = approve_payment_request(req['id'], 0)
        assert result['status'] == 'approved'
        assert result['approved_by'] == 0

    def test_reject_one_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        result = reject_payment_request(req['id'], 0, 'Not needed')
        assert result['status'] == 'rejected'
        assert result['reject_reason'] == 'Not needed'

    def test_cancel_one_pending_request(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        result = cancel_payment_request(req['id'], m['id'])
        assert result['status'] == 'cancelled'


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestPaymentMany:
    def test_multiple_pending_requests(self, setup_db):
        m = create_member('Test')
        for i in range(3):
            create_payment_request(m['id'], (i + 1) * 100, 'share')
        pending = list_pending_requests()
        assert len(pending) == 3

    def test_approve_one_among_many(self, setup_db):
        m = create_member('Test')
        r1 = create_payment_request(m['id'], 500, 'share')
        r2 = create_payment_request(m['id'], 1000, 'share')
        approve_payment_request(r1['id'], 0)
        pending = list_pending_requests()
        assert len(pending) == 1
        assert pending[0]['id'] == r2['id']


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestPaymentBoundary:
    def test_approve_share_adds_contribution(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        approve_payment_request(req['id'], 0)
        member = get_member(m['id'], full=True)
        shares = [c for c in member['contributions'] if c['type'] == 'share']
        assert any(c['amount'] == 500 for c in shares)

    def test_approve_loan_request_updates_loan(self, setup_db):
        m = create_member('Test')
        loan = create_loan(m['id'], 10000, 12)
        approve_loan(loan['id'])
        req = create_payment_request(m['id'], 3000, 'loan')
        approve_payment_request(req['id'], 0)
        updated_loan = get_loan(loan['id'])
        assert updated_loan['outstanding'] == pytest.approx(7000, abs=5)

    def test_cancel_wrong_member_fails(self, setup_db):
        m1 = create_member('Owner')
        m2 = create_member('Stranger')
        req = create_payment_request(m1['id'], 500, 'share')
        result = cancel_payment_request(req['id'], m2['id'])
        assert result is None

    def test_cancel_already_approved_fails(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        approve_payment_request(req['id'], 0)
        result = cancel_payment_request(req['id'], m['id'])
        assert result is None


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestPaymentInterface:
    def test_approve_share_creates_transaction(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['id'], 500, 'share')
        approve_payment_request(req['id'], 0)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE member_id=? AND desc LIKE 'Share%'", (m['id'],))
        txns = [dict(r) for r in cur.fetchall()]
        conn.close()
        assert len(txns) >= 1

    def test_approve_loan_request_creates_payment_record(self, setup_db):
        m = create_member('Test')
        loan = create_loan(m['id'], 10000, 12)
        approve_loan(loan['id'])
        req = create_payment_request(m['id'], 3000, 'loan')
        approve_payment_request(req['id'], 0)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM payments WHERE member_id=?', (m['id'],))
        payments = [dict(r) for r in cur.fetchall()]
        conn.close()
        assert len(payments) >= 1
        assert payments[0]['amount'] == 3000


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestPaymentException:
    def test_add_contribution_invalid_member(self, setup_db):
        result = add_contribution(99999, date.today(), 500, 'share')
        assert result is None

    def test_pay_due_invalid(self, setup_db):
        with pytest.raises(Exception):
            pay_due(99999, 99999, 500)

    def test_create_payment_request_no_member(self, setup_db):
        result = create_payment_request(99999, 500, 'share')
        assert result is not None
        assert result['member_id'] == 99999
