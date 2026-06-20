from models import Loan, compute_interest_accrued
from datetime import date, timedelta


def test_interest_accrual():
    loan = Loan(member_id=1, principal=10000, outstanding=10000, rate_monthly=0.01, term_months=12, status='active', disbursed_date=date(2026,1,1), last_accrual_date=date(2026,1,1))
    # accrue 30 days -> ~1% interest
    interest = compute_interest_accrued(loan, date(2026,1,31))
    assert round(interest,2) == 100.0
