from datetime import date
import pytest

from core.database import get_conn
from core.models.member import create_member, get_member
from core.models.payment import create_payment_request, approve_payment_request, admin_direct_entry
from core.models.requests import list_submitted_requests
from core.models.transaction import get_period_summary, get_admin_stats


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestDuesSimple:
    def test_approve_monthly_share_creates_payment(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        approve_payment_request(req['req_id'], 0)
        full = get_member(m['member_id'], full=True)
        shares = [p for p in full['payments'] if p['share_amount'] == 500]
        assert len(shares) == 1


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestDuesZero:
    def _not_deposit(self, p):
        return p['share_amount'] or p['loan_principal'] or p['loan_interest'] or p['late_fee']

    def test_no_payments_for_new_member(self, setup_db):
        m = create_member('Test')
        full = get_member(m['member_id'], full=True)
        assert len([p for p in full['payments'] if self._not_deposit(p)]) == 0

    def test_period_summary_empty(self, setup_db):
        summary = get_period_summary()
        assert summary['months'] == []

    def test_zero_amount_entry_skipped(self, setup_db):
        m = create_member('Test')
        admin_direct_entry(m['member_id'], share_amount=0, late_fee=0, entry_date='2026-06-10')
        full = get_member(m['member_id'], full=True)
        assert len([p for p in full['payments'] if self._not_deposit(p)]) == 0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestDuesOne:
    def test_one_share_payment(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        approve_payment_request(req['req_id'], 0)
        full = get_member(m['member_id'], full=True)
        assert any(p['share_amount'] == 500 for p in full['payments'])

    def test_one_share_with_late_fee(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 600, late_fee=100, share_amount=500)
        approve_payment_request(req['req_id'], 0)
        full = get_member(m['member_id'], full=True)
        pay = next(p for p in full['payments'] if p['share_amount'] == 500)
        assert pay['late_fee'] == 100
        assert pay['total_amount'] == 600


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestDuesMany:
    def test_many_months_payments(self, setup_db):
        m = create_member('Test')
        for i in range(3):
            create_payment_request(m['member_id'], 500, share_amount=500)
        pending = [r for r in list_submitted_requests() if r['member_name'] == 'Test']
        assert len(pending) == 3

    def test_period_summary_aggregates_months(self, setup_db):
        m = create_member('Test')
        for i in range(3):
            req = create_payment_request(m['member_id'], 500, share_amount=500)
            approve_payment_request(req['req_id'], 0)
        summary = get_period_summary()
        assert len(summary['months']) == 1
        month = summary['months'][0]
        assert summary['monthly'][month]['share'] == 1500


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestDuesBoundary:
    def test_due_on_due_date_no_late_fee(self, setup_db):
        m = create_member('Test')
        admin_direct_entry(m['member_id'], share_amount=500, late_fee=0, entry_date='2026-06-10')
        summary = get_period_summary()
        month = summary['months'][0]
        assert summary['monthly'][month]['share'] == 500
        assert summary['monthly'][month]['fine'] == 0

    def test_due_one_day_late_has_fine(self, setup_db):
        m = create_member('Test')
        admin_direct_entry(m['member_id'], share_amount=500, late_fee=50, entry_date='2026-06-11')
        summary = get_period_summary()
        month = summary['months'][0]
        assert summary['monthly'][month]['fine'] == 50

    def test_stats_include_late_fees(self, setup_db):
        m = create_member('Test')
        admin_direct_entry(m['member_id'], share_amount=500, late_fee=100, entry_date='2026-06-11')
        stats = get_admin_stats()
        assert stats['shares_total'] == 500
        assert stats['others_total'] >= 100


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestDuesInterface:
    def test_create_member_has_deposit_payment(self, setup_db):
        m = create_member('Test')
        full = get_member(m['member_id'], full=True)
        deposit = next(
            (p for p in full['payments']
             if not p['share_amount'] and not p['loan_principal'] and not p['loan_interest'] and not p['late_fee']),
            None,
        )
        assert deposit is not None and deposit['total_amount'] == 25000

    def test_approved_share_counts_in_stats(self, setup_db):
        m = create_member('Test')
        req = create_payment_request(m['member_id'], 500, share_amount=500)
        approve_payment_request(req['req_id'], 0)
        stats = get_admin_stats()
        assert stats['shares_total'] >= 500


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestDuesException:
    def test_payment_for_nonexistent_member(self, setup_db):
        admin_direct_entry(99999, share_amount=500, entry_date='2026-06-10')
        full = get_member(99999, full=True)
        assert full is None
