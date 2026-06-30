from datetime import date, timedelta
import pytest

from core.models.loan import (
    Loan, create_loan, get_loan, approve_loan, reject_loan,
    compute_interest_accrued, apply_payment_to_loan, list_pending_loans,
)
from core.database import get_conn, row_to_dict


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestLoanSimple:
    def test_loan_dataclass_defaults(self):
        loan = Loan()
        assert loan.id is None
        assert loan.principal == 0.0
        assert loan.outstanding == 0.0
        assert loan.rate_monthly == 0.01
        assert loan.term_months == 12
        assert loan.status == 'applied'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestLoanZero:
    def test_create_zero_amount_loan(self, setup_db):
        loan = create_loan(member_id=1, amount=0, term_months=12)
        assert loan['principal'] == 0
        assert loan['outstanding'] == 0
        assert loan['status'] == 'applied'

    def test_interest_no_accrual_on_applied_loan(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000, status='applied')
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0

    def test_interest_zero_outstanding(self):
        loan = Loan(member_id=1, principal=10000, outstanding=0,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0

    def test_get_loan_nonexistent(self):
        loan = get_loan(99999)
        assert loan is None

    def test_approve_nonexistent_loan_does_not_raise(self):
        approve_loan(99999)

    def test_reject_nonexistent_loan_does_not_raise(self):
        reject_loan(99999, 'test reason')

    def test_list_pending_loans_empty(self):
        loans = list_pending_loans()
        assert loans == []

    def test_zero_days_interest(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    status='active', disbursed_date=date(2026, 6, 22),
                    last_accrual_date=date(2026, 6, 22))
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestLoanOne:
    def test_create_one_loan(self, setup_db):
        loan = create_loan(member_id=1, amount=10000, term_months=12)
        assert loan['id'] is not None
        assert loan['principal'] == 10000
        assert loan['outstanding'] == 10000
        assert loan['status'] == 'applied'

    def test_get_one_loan(self, setup_db):
        created = create_loan(member_id=1, amount=5000, term_months=6)
        fetched = get_loan(created['id'])
        assert fetched['id'] == created['id']
        assert fetched['principal'] == 5000

    def test_approve_one_loan(self, setup_db):
        loan = create_loan(member_id=1, amount=10000, term_months=12)
        approve_loan(loan['id'])
        fetched = get_loan(loan['id'])
        assert fetched['status'] == 'active'
        assert fetched['disbursed_date'] is not None

    def test_reject_one_loan(self, setup_db):
        loan = create_loan(member_id=1, amount=10000, term_months=12)
        reject_loan(loan['id'], 'Not eligible')
        fetched = get_loan(loan['id'])
        assert fetched['status'] == 'rejected'
        assert fetched['reject_reason'] == 'Not eligible'

    def test_one_period_interest(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest = compute_interest_accrued(loan, date(2026, 1, 31))
        assert round(interest, 2) == 100.0


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestLoanMany:
    def test_create_multiple_loans(self, setup_db):
        loans = []
        for i in range(5):
            l = create_loan(member_id=1, amount=(i + 1) * 1000, term_months=12)
            loans.append(l)
        assert len(loans) == 5
        assert loans[0]['principal'] == 1000
        assert loans[4]['principal'] == 5000

    def test_multiple_interest_periods(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest1 = compute_interest_accrued(loan, date(2026, 2, 1))
        assert round(interest1, 2) == pytest.approx(103.33, rel=0.01)
        interest2 = compute_interest_accrued(loan, date(2026, 3, 1))
        assert round(interest2, 2) > 0

    def test_list_multiple_pending_loans(self, setup_db):
        create_loan(member_id=1, amount=5000, term_months=12)
        create_loan(member_id=2, amount=10000, term_months=24)
        pending = list_pending_loans()
        assert len(pending) == 2

    def test_multiple_payments_on_loan(self, setup_db):
        loan = create_loan(member_id=1, amount=10000, term_months=12)
        approve_loan(loan['id'])
        loan_dict = get_loan(loan['id'])
        pay1 = apply_payment_to_loan(loan_dict, 3000)
        assert pay1['amount'] == 3000
        assert loan_dict['outstanding'] == 7000
        pay2 = apply_payment_to_loan(loan_dict, 4000)
        assert pay2['amount'] == 4000
        assert loan_dict['outstanding'] == 3000


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestLoanBoundary:
    def test_interest_exact_30_days(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        interest = compute_interest_accrued(loan, date(2026, 1, 31))
        assert round(interest, 2) == 100.0

    def test_interest_1_day(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    rate_monthly=0.01, term_months=12,
                    status='active', disbursed_date=date(2026, 6, 1),
                    last_accrual_date=date(2026, 6, 1))
        interest = compute_interest_accrued(loan, date(2026, 6, 2))
        assert round(interest, 2) == pytest.approx(3.33, rel=0.01)

    def test_payment_exact_outstanding(self):
        loan = Loan(member_id=1, principal=5000, outstanding=5000,
                    status='active', disbursed_date=date(2026, 1, 1),
                    last_accrual_date=date(2026, 1, 1))
        loan_dict = {'id': 1, 'member_id': 1, 'outstanding': 5000}
        pay = apply_payment_to_loan(loan_dict, 5000)
        assert loan_dict['outstanding'] == 0

    def test_payment_exceeds_outstanding(self, setup_db):
        loan = create_loan(member_id=1, amount=3000, term_months=12)
        approve_loan(loan['id'])
        loan_dict = get_loan(loan['id'])
        pay = apply_payment_to_loan(loan_dict, 9999)
        assert loan_dict['outstanding'] == 0

    def test_term_minimum_1_month(self, setup_db):
        loan = create_loan(member_id=1, amount=5000, term_months=1)
        assert loan['term_months'] == 1

    def test_loan_amount_boundary_large(self, setup_db):
        loan = create_loan(member_id=1, amount=999999, term_months=12)
        assert loan['principal'] == 999999

    def test_loan_boundary_zero_term(self, setup_db):
        loan = create_loan(member_id=1, amount=5000, term_months=0)
        assert loan['term_months'] == 0


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestLoanInterface:
    def test_approve_updates_db(self, setup_db):
        loan = create_loan(member_id=1, amount=10000, term_months=12)
        approve_loan(loan['id'])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT status, disbursed_date FROM loans WHERE id=?', (loan['id'],))
        row = dict(cur.fetchone())
        conn.close()
        assert row['status'] == 'active'
        assert row['disbursed_date'] is not None

    def test_interest_accrual_persists_to_db(self, setup_db):
        loan = create_loan(member_id=1, amount=10000, term_months=12)
        approve_loan(loan['id'])
        loan_dict = get_loan(loan['id'])
        compute_interest_accrued(loan_dict, date(2026, 8, 1))
        refreshed = get_loan(loan['id'])
        assert refreshed['outstanding'] > 10000

    def test_member_name_in_pending_loans(self, setup_db):
        from core.models.member import create_member
        m = create_member('Test Member')
        create_loan(member_id=m['id'], amount=5000, term_months=12)
        pending = list_pending_loans()
        assert any(p['member_name'] == 'Test Member' for p in pending)

    def test_reject_reason_stored(self, setup_db):
        loan = create_loan(member_id=1, amount=5000, term_months=12)
        reject_loan(loan['id'], 'Low credit score')
        fetched = get_loan(loan['id'])
        assert fetched['reject_reason'] == 'Low credit score'

    def test_dict_and_dataclass_interest_consistency(self):
        dict_loan = {'id': 1, 'member_id': 1, 'principal': 10000, 'outstanding': 10000,
                     'rate_monthly': 0.01, 'term_months': 12, 'status': 'active',
                     'disbursed_date': '2026-01-01', 'last_accrual_date': '2026-01-01'}
        dc_loan = Loan(member_id=1, principal=10000, outstanding=10000,
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

    def test_payment_on_nonexistent_loan_requires_dict_with_id(self, setup_db):
        bad_loan = {'id': 99999, 'member_id': 1, 'outstanding': 5000}
        result = apply_payment_to_loan(bad_loan, 100)
        assert result is not None
        assert 'id' in result

    def test_interest_on_loan_without_disbursement(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    status='applied')
        interest = compute_interest_accrued(loan, date(2026, 6, 22))
        assert interest == 0.0

    def test_interest_with_negative_days(self):
        loan = Loan(member_id=1, principal=10000, outstanding=10000,
                    rate_monthly=0.01, status='active',
                    disbursed_date=date(2026, 6, 22),
                    last_accrual_date=date(2026, 6, 22))
        interest = compute_interest_accrued(loan, date(2026, 6, 20))
        assert interest == 0.0
