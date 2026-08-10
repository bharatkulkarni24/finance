import pytest

from core.models.fd import add_fd, close_fd, get_fd_entries, get_active_fd_total
from core.database import get_conn


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestFDSimple:
    def test_add_fd(self, setup_db):
        fd = add_fd(amount=50000, start_date='2026-01-01',
                    term_months=12, interest_rate=7, notes='SBI')
        assert fd['amount'] == 50000
        assert fd['status'] == 'active'
        assert fd['interest_rate'] == 7
        assert fd['notes'] == 'SBI'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestFDZero:
    def test_get_fd_entries_empty(self, setup_db):
        entries = get_fd_entries()
        assert entries == []

    def test_get_active_fd_total_zero(self, setup_db):
        total = get_active_fd_total()
        assert total == 0

    def test_close_nonexistent_fd(self, setup_db):
        result = close_fd(99999, '2026-06-22', 1000)
        assert result is None

    def test_add_fd_zero_amount(self, setup_db):
        fd = add_fd(amount=0, start_date='2026-01-01',
                    term_months=12, interest_rate=7)
        assert fd['amount'] == 0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestFDOne:
    def test_add_one_fd(self, setup_db):
        fd = add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        entries = get_fd_entries()
        assert len(entries) == 1
        assert entries[0]['fd_id'] == fd['fd_id']

    def test_close_one_fd(self, setup_db):
        fd = add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        closed = close_fd(fd['fd_id'], '2026-06-22', 2500)
        assert closed['status'] == 'matured'
        assert closed['interest_earned'] == 2500

    def test_active_fd_total_one(self, setup_db):
        add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        total = get_active_fd_total()
        assert total == 50000


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestFDMany:
    def test_add_multiple_fds(self, setup_db):
        add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        add_fd(100000, '2026-03-01', 24, 8, 'HDFC')
        entries = get_fd_entries()
        assert len(entries) == 2

    def test_active_fd_total_multiple(self, setup_db):
        add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        add_fd(100000, '2026-03-01', 24, 8, 'HDFC')
        total = get_active_fd_total()
        assert total == 150000

    def test_filter_by_status_active(self, setup_db):
        fd1 = add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        fd2 = add_fd(100000, '2026-03-01', 24, 8, 'HDFC')
        close_fd(fd1['fd_id'], '2026-06-22', 2500)
        active = get_fd_entries(status='active')
        assert len(active) == 1
        assert active[0]['fd_id'] == fd2['fd_id']

    def test_filter_by_status_matured(self, setup_db):
        fd1 = add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        fd2 = add_fd(100000, '2026-03-01', 24, 8, 'HDFC')
        close_fd(fd1['fd_id'], '2026-06-22', 2500)
        matured = get_fd_entries(status='matured')
        assert len(matured) == 1
        assert matured[0]['fd_id'] == fd1['fd_id']


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestFDBoundary:
    def test_fd_minimum_term(self, setup_db):
        fd = add_fd(10000, '2026-01-01', 1, 7, 'Test')
        assert fd['term_months'] == 1

    def test_fd_very_large_amount(self, setup_db):
        fd = add_fd(1000000, '2026-01-01', 12, 7, 'Large')
        assert fd['amount'] == 1000000

    def test_fd_zero_interest_rate(self, setup_db):
        fd = add_fd(10000, '2026-01-01', 12, 0, 'No Interest')
        assert fd['interest_rate'] == 0

    def test_fd_maturity_date_calculation(self, setup_db):
        fd = add_fd(10000, '2026-01-15', 3, 7, 'Test')
        assert fd['maturity_date'] == '2026-04-15'

    def test_fd_maturity_year_boundary(self, setup_db):
        fd = add_fd(10000, '2026-11-01', 3, 7, 'Cross Year')
        assert fd['maturity_date'] == '2027-02-01'


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestFDInterface:
    def test_close_fd_creates_interest_transaction(self, setup_db):
        fd = add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        close_fd(fd['fd_id'], '2026-06-22', 2500)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM group_ledger WHERE description LIKE 'FD Interest%'")
        txns = [dict(r) for r in cur.fetchall()]
        conn.close()
        assert len(txns) == 1
        assert txns[0]['amount'] == 2500

    def test_active_fd_excludes_closed(self, setup_db):
        add_fd(50000, '2026-01-01', 12, 7, 'SBI')
        fd2 = add_fd(25000, '2026-03-01', 12, 7, 'HDFC')
        close_fd(fd2['fd_id'], '2026-06-22', 1500)
        total = get_active_fd_total()
        assert total == 50000


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestFDException:
    def test_add_fd_invalid_date(self, setup_db):
        with pytest.raises(Exception):
            add_fd(10000, 'not-a-date', 12, 7, 'Bad Date')

    def test_close_already_closed_fd_fails(self, setup_db):
        fd = add_fd(10000, '2026-01-01', 12, 7, 'Test')
        close_fd(fd['fd_id'], '2026-06-22', 500)
        result = close_fd(fd['fd_id'], '2026-07-22', 600)
        assert result is None
