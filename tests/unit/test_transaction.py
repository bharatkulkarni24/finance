import pytest

from core.models.transaction import (
    admin_add_funds, add_transaction, get_recent_transactions,
    get_member_statement, get_admin_stats, get_passbook_entries,
)
from core.models.member import create_member
from core.models.loan import create_loan, approve_loan
from core.models.fd import add_fd
from core.database import get_conn, row_to_dict


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestTransactionSimple:
    def test_admin_add_funds(self, setup_db):
        t = admin_add_funds(10000, 'Test deposit')
        assert t['amount'] == 10000
        assert t['debit_credit'] == 'credit'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestTransactionZero:
    def test_admin_add_funds_zero(self, setup_db):
        t = admin_add_funds(0, 'Zero')
        assert t['amount'] == 0

    def test_get_recent_transactions_empty(self, setup_db):
        txns = get_recent_transactions()
        assert txns == []

    def test_add_transaction_zero_amount(self, setup_db):
        t = add_transaction('credit', 0, 'zero')
        assert t['amount'] == 0

    def test_get_admin_stats_returns_keys(self, setup_db):
        stats = get_admin_stats()
        assert 'total_collected' in stats
        assert 'total_lent' in stats
        assert 'cash_on_hand' in stats
        assert 'member_count' in stats


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestTransactionOne:
    def test_add_one_income(self, setup_db):
        t = add_transaction('credit', 5000, 'Donation', '2026-06-01T12:00:00')
        assert t['debit_credit'] == 'credit'
        assert t['desc'] == 'Donation'

    def test_add_one_expense(self, setup_db):
        t = add_transaction('debit', 2000, 'Snacks', '2026-06-01T12:00:00')
        assert t['debit_credit'] == 'debit'

    def test_get_one_recent(self, setup_db):
        add_transaction('credit', 5000, 'Test', '2026-06-01T12:00:00')
        txns = get_recent_transactions()
        assert len(txns) == 1
        assert txns[0]['amount'] == 5000

    def test_member_statement(self, setup_db):
        m = create_member('Statement Test')
        csv = get_member_statement(m['id'])
        assert csv.startswith('type,date,amount,details')
        assert 'deposit' in csv


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestTransactionMany:
    def test_add_multiple_transactions(self, setup_db):
        for i in range(5):
            add_transaction('credit', (i + 1) * 1000, f'Income {i}', '2026-06-01T12:00:00')
        txns = get_recent_transactions(10)
        assert len(txns) == 5

    def test_get_recent_limit(self, setup_db):
        for i in range(10):
            add_transaction('credit', 100, f'T{i}', '2026-06-01T12:00:00')
        txns = get_recent_transactions(3)
        assert len(txns) == 3


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestTransactionBoundary:
    def test_stats_with_fd_and_loans(self, setup_db):
        m = create_member('Stats Test')
        loan = create_loan(m['id'], 50000, 12)
        approve_loan(loan['id'])
        add_fd(100000, '2026-01-01', 12, 7, 'SBI')
        stats = get_admin_stats()
        assert stats['total_lent'] >= 50000
        assert stats['hardlocked_fd'] >= 100000

    def test_passbook_contains_entries(self, setup_db):
        m = create_member('Passbook Test')
        entries = get_passbook_entries()
        assert isinstance(entries, list)
        if entries:
            assert 'ts' in entries[0]
            assert 'category' in entries[0]
            assert 'amount' in entries[0]

    def test_admin_add_funds_large(self, setup_db):
        t = admin_add_funds(1000000, 'Large deposit')
        assert t['amount'] == 1000000


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestTransactionInterface:
    def test_add_income_appears_in_stats(self, setup_db):
        add_transaction('credit', 15000, 'Rental Income', '2026-06-01T12:00:00')
        stats = get_admin_stats()
        assert stats['others_total'] >= 15000

    def test_add_expense_appears_in_stats(self, setup_db):
        add_transaction('debit', 5000, 'Office Rent', '2026-06-01T12:00:00')
        stats = get_admin_stats()
        assert stats['expenses_total'] >= 5000

    def test_member_statement_shows_all_types(self, setup_db):
        m = create_member('CSV Test')
        loan = create_loan(m['id'], 10000, 12)
        approve_loan(loan['id'])
        from core.models.loan import apply_payment_to_loan
        loan_dict = {'id': loan['id'], 'member_id': m['id'], 'outstanding': 10000}
        apply_payment_to_loan(loan_dict, 2000)
        csv = get_member_statement(m['id'])
        assert 'payment' in csv


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestTransactionException:
    def test_get_member_statement_nonexistent(self, setup_db):
        csv = get_member_statement(99999)
        assert 'type,date,amount,details' in csv
