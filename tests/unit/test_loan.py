from datetime import date, timedelta
import pytest

from core.models.loan import (
    Loan, create_loan, get_loan, approve_loan, reject_loan,
    compute_interest_accrued, apply_payment_to_loan,
)
from core.models.requests import list_submitted_requests
from core.database import get_conn


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestLoanSimple:
    def test_loan_dataclass_defaults(self):
        loan = Loan()
        assert loan.loan_id is None
        assert loan.loan_principal == 0.0
        assert loan.outstanding == 0.0
        assert loan.rate_monthly == 0.01
        assert loan.term_months == 12
        assert loan.status == 'active'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestLoanZero:
    def test_create_zero_amount_loan(self, setup_db):
        req = create_loan(member_id=1, amount=0, term_months=12)
        assert req['loan_amount'] == 0
        assert req['loan_term_months'] == 12
        assert req['status'] == 'submitted'
        assert get_loan(1) is None

    def test_interest_no_accrual_on_inactive_loan(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000, status='submitted')
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0

    def test_interest_zero_outstanding(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=0,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0

    def test_get_loan_nonexistent(self):
        loan = get_loan(99999)
        assert loan is None

    def test_approve_nonexistent_loan_returns_none(self, setup_db):
        assert approve_loan(99999) is None

    def test_reject_nonexistent_loan_returns_none(self, setup_db):
        assert reject_loan(99999, 0, 'test reason') is None

    def test_zero_days_interest(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                    status='active', disbursed_date=date(2026, 6, 22),
                    last_accrual_date=date(2026, 6, 22))
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestLoanOne:
    def test_create_one_loan_request(self, setup_db):
        req = create_loan(member_id=1, amount=10000, term_months=12)
        assert req['req_id'] is not None
        assert req['loan_amount'] == 10000
        assert req['loan_term_months'] == 12
        assert req['status'] == 'submitted'
        assert req['item_type'] == 'loan'

    def test_approve_creates_loan_row(self, setup_db):
        req = create_loan(member_id=1, amount=5000, term_months=6)
        loan = approve_loan(req['req_id'], 0)
        assert loan['loan_id'] is not None
        assert loan['loan_principal'] == 5000
        assert loan['outstanding'] == 5000
        assert loan['status'] == 'active'
        fetched = get_loan(loan['loan_id'])
        assert fetched['loan_id'] == loan['loan_id']

    def test_approve_one_loan(self, setup_db):
        req = create_loan(member_id=1, amount=10000, term_months=12)
        loan = approve_loan(req['req_id'], 0)
        fetched = get_loan(loan['loan_id'])
        assert fetched['status'] == 'active'
        assert fetched['disbursed_date'] is not None

    def test_reject_one_loan_creates_no_loan_row(self, setup_db):
        req = create_loan(member_id=1, amount=10000, term_months=12)
        rejected = reject_loan(req['req_id'], 0, 'Not eligible')
        assert rejected['status'] == 'rejected'
        assert rejected['reject_reason'] == 'Not eligible'
        assert get_loan(99999) is None

    def test_one_period_interest(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest = compute_interest_accrued(loan, date(2026, 1, 31))
        assert round(interest, 2) == 100.0


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestLoanMany:
    def test_create_multiple_loan_requests(self, setup_db):
        reqs = []
        for i in range(5):
            reqs.append(create_loan(member_id=1, amount=(i + 1) * 1000, term_months=12))
        assert len(reqs) == 5
        assert reqs[0]['loan_amount'] == 1000
        assert reqs[4]['loan_amount'] == 5000

    def test_multiple_interest_periods(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest1 = compute_interest_accrued(loan, date(2026, 2, 1))
        assert round(interest1, 2) == pytest.approx(103.33, rel=0.01)
        interest2 = compute_interest_accrued(loan, date(2026, 3, 1))
        assert round(interest2, 2) > 0

    def test_list_multiple_submitted_loans(self, setup_db):
        create_loan(member_id=1, amount=5000, term_months=12)
        create_loan(member_id=2, amount=10000, term_months=24)
        pending = [r for r in list_submitted_requests() if r['item_type'] == 'loan']
        assert len(pending) == 2

    def test_multiple_payments_on_loan(self, setup_db):
        req = create_loan(member_id=1, amount=10000, term_months=12)
        loan = approve_loan(req['req_id'], 0)
        loan_dict = get_loan(loan['loan_id'])
        pay1 = apply_payment_to_loan(loan_dict, 3000)
        assert pay1['total_amount'] == 3000
        assert loan_dict['outstanding'] == 7000
        pay2 = apply_payment_to_loan(loan_dict, 4000)
        assert pay2['total_amount'] == 4000
        assert loan_dict['outstanding'] == 3000


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestLoanBoundary:
    def test_interest_exact_30_days(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest = compute_interest_accrued(loan, date(2026, 1, 31))
        assert round(interest, 2) == 100.0

    def test_interest_1_day(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 6, 1),
                    last_accrual_date=date(2026, 6, 1))
        interest = compute_interest_accrued(loan, date(2026, 6, 2))
        assert round(interest, 2) == pytest.approx(3.33, rel=0.01)

    def test_payment_exact_outstanding(self):
        loan = Loan(member_id=1, loan_principal=5000, outstanding=5000,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        loan_dict = {'loan_id': 1, 'member_id': 1, 'outstanding': 5000}
        pay = apply_payment_to_loan(loan_dict, 5000)
        assert loan_dict['outstanding'] == 0

    def test_payment_exceeds_outstanding(self, setup_db):
        req = create_loan(member_id=1, amount=3000, term_months=12)
        loan = approve_loan(req['req_id'], 0)
        loan_dict = get_loan(loan['loan_id'])
        pay = apply_payment_to_loan(loan_dict, 9999)
        assert loan_dict['outstanding'] == 0

    def test_term_minimum_1_month(self, setup_db):
        req = create_loan(member_id=1, amount=5000, term_months=1)
        assert req['loan_term_months'] == 1

    def test_loan_amount_boundary_large(self, setup_db):
        req = create_loan(member_id=1, amount=999999, term_months=12)
        assert req['loan_amount'] == 999999

    def test_loan_boundary_zero_term(self, setup_db):
        req = create_loan(member_id=1, amount=5000, term_months=0)
        assert req['loan_term_months'] == 0

    def test_reapprove_after_reject_fails(self, setup_db):
        req = create_loan(member_id=1, amount=5000, term_months=12)
        reject_loan(req['req_id'], 0, 'No')
        assert approve_loan(req['req_id'], 0) is None


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestLoanInterface:
    def test_approve_updates_db(self, setup_db):
        req = create_loan(member_id=1, amount=10000, term_months=12)
        loan = approve_loan(req['req_id'], 0)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT status, disbursed_date FROM loans WHERE loan_id=?', (loan['loan_id'],))
        row = dict(cur.fetchone())
        conn.close()
        assert row['status'] == 'active'
        assert row['disbursed_date'] is not None

    def test_interest_accrual_persists_to_db(self, setup_db):
        req = create_loan(member_id=1, amount=10000, term_months=12)
        loan = approve_loan(req['req_id'], 0)
        loan_dict = get_loan(loan['loan_id'])
        compute_interest_accrued(loan_dict, date.today() + timedelta(days=35))
        refreshed = get_loan(loan['loan_id'])
        assert refreshed['outstanding'] > 10000

    def test_member_name_in_submitted_loans(self, setup_db):
        from core.models.member import create_member
        m = create_member('Test Member')
        create_loan(member_id=m['member_id'], amount=5000, term_months=12)
        pending = [r for r in list_submitted_requests() if r['item_type'] == 'loan']
        assert any(p['member_name'] == 'Test Member' for p in pending)

    def test_reject_reason_stored_on_request(self, setup_db):
        req = create_loan(member_id=1, amount=5000, term_months=12)
        rejected = reject_loan(req['req_id'], 0, 'Low credit score')
        assert rejected['reject_reason'] == 'Low credit score'

    def test_loan_req_no_sequence_includes_approved_loans(self, setup_db):
        req1 = create_loan(member_id=1, amount=5000, term_months=12)
        assert req1['req_no'] == 'L0001'
        approve_loan(req1['req_id'], 0)
        req2 = create_loan(member_id=1, amount=5000, term_months=12)
        assert req2['req_no'] == 'L0002'

    def test_dict_and_dataclass_interest_consistency(self):
        dict_loan = {'loan_id': 1, 'member_id': 1, 'loan_principal': 10000, 'outstanding': 10000,
                     'rate_monthly': 0.01, 'term_months': 12, 'status': 'active',
                     'disbursed_date': '2026-01-01', 'last_accrual_date': '2026-01-01'}
        dc_loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                       rate_monthly=0.01, term_months=12, status='active',
                       disbursed_date=date(2026, 1, 1), last_accrual_date=date(2026, 1, 1))
        interest_dict = compute_interest_accrued(dict_loan, date(2026, 2, 1))
        interest_dc = compute_interest_accrued(dc_loan, date(2026, 2, 1))
        assert round(interest_dict, 2) == round(interest_dc, 2)


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestLoanException:
    def test_get_nonexistent_loan_returns_none(self):
        loan = get_loan(-1)
        assert loan is None
        loan = get_loan(0)
        assert loan is None

    def test_payment_on_nonexistent_loan_requires_dict_with_loan_id(self, setup_db):
        bad_loan = {'loan_id': 99999, 'member_id': 1, 'outstanding': 5000}
        result = apply_payment_to_loan(bad_loan, 100)
        assert result is not None
        assert 'pay_id' in result

    def test_interest_on_loan_without_disbursement(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000, status='active')
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0

    def test_interest_with_negative_days(self):
        loan = Loan(member_id=1, loan_principal=10000, outstanding=10000,
                    rate_monthly=0.01, status='active',
                    disbursed_date=date(2026, 6, 22),
                    last_accrual_date=date(2026, 6, 22))
        interest = compute_interest_accrued(loan, date(2026, 6, 20))
        assert interest == 0.0
