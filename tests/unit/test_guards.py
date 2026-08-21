"""Insufficient-funds guards on loan approval and FD creation."""
import pytest

from core import config
from core.models.fd import add_fd, add_fd_installment
from core.models.loan import approve_loan, reject_loan
from core.models.requests import next_req_no


@pytest.fixture
def overlend_off():
    old = getattr(config, 'ALLOW_OVERLEND', False)
    config.ALLOW_OVERLEND = False
    yield
    config.ALLOW_OVERLEND = old


def _create_loan_request(member_id=1, amount=999999999.0, term=6):
    from core.database import get_conn
    conn = get_conn()
    cur = conn.cursor()
    req_no = next_req_no('loan')
    cur.execute(
        "INSERT INTO requests (member_id, item_type, status, date_submitted, loan_amount, loan_term_months, req_no) "
        "VALUES (?, 'loan', 'submitted', datetime('now'), ?, ?, ?)",
        (member_id, amount, term, req_no),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


class TestLoanGuard:
    def test_approve_rejected_when_no_funds(self, setup_db, overlend_off):
        rid = _create_loan_request(amount=1000000.0)
        res = approve_loan(rid, approver_id=1)
        assert res.get('error') == 'insufficient_funds'
        assert res['requested'] == 1000000.0
        assert res['available'] == 0

    def test_request_stays_submitted_after_block(self, setup_db, overlend_off):
        rid = _create_loan_request(amount=1000000.0)
        approve_loan(rid, approver_id=1)
        from core.models.requests import _fetch
        from core.database import get_conn
        conn = get_conn()
        req = _fetch(conn.cursor(), rid)
        conn.close()
        assert req['status'] == 'submitted'

    def test_approve_allowed_when_funds_exist(self, setup_db, overlend_off):
        from core.database import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO members (name, password, is_admin, joined_date, entry_deposit_amount) "
            "VALUES ('Rich Member', '', 0, '2025-04-01', 50000)"
        )
        mid = cur.lastrowid
        conn.commit()
        conn.close()
        rid = _create_loan_request(member_id=mid, amount=20000.0)
        res = approve_loan(rid, approver_id=1)
        assert isinstance(res, dict) and 'error' not in res
        assert res['loan_principal'] == 20000.0

    def test_bypass_flag_restores_old_behaviour(self, setup_db):
        # With ALLOW_OVERLEND unset/True (fixture default) the guard is off.
        rid = _create_loan_request(amount=1000000.0)
        res = approve_loan(rid, approver_id=1)
        assert isinstance(res, dict) and 'error' not in res
        reject_loan(rid, approver_id=1)


class TestFDGuard:
    def test_add_fd_rejected_when_no_funds(self, setup_db, overlend_off):
        res = add_fd(amount=500000.0, start_date='2026-01-01', term_months=12,
                     interest_rate=7, notes='SBI')
        assert res.get('error') == 'insufficient_funds'
        assert res['available'] == 0

    def test_add_fd_zero_amount_still_ok(self, setup_db, overlend_off):
        res = add_fd(amount=0, start_date='2026-01-01', term_months=12, interest_rate=7)
        assert not (isinstance(res, dict) and res.get('error'))

    def test_installment_rejected_when_no_funds(self, setup_db, overlend_off):
        config.ALLOW_OVERLEND = True  # create parent scheme without guard
        parent = add_fd(amount=0, start_date='2026-01-01', term_months=0,
                        interest_rate=0, notes='scheme', investment_type='monthly')
        config.ALLOW_OVERLEND = False
        res = add_fd_installment(parent['fd_id'], 250000.0, '2026-02-01')
        assert res.get('error') == 'insufficient_funds'
