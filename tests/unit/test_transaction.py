from core.models.transaction import (
    add_transaction, get_recent_transactions,
    get_member_statement, get_admin_stats, get_passbook_entries,
)
from core.models.member import create_member
from core.models.loan import create_loan, approve_loan, apply_payment_to_loan, get_loan
from core.models.fd import add_fd
from core.models.payment import admin_direct_entry


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestTransactionSimple:
    def test_add_income_transaction(self, setup_db):
        t = add_transaction('credit', 10000, 'Test deposit')
        assert t['amount'] == 10000
        assert t['debit_credit'] == 'credit'


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestTransactionZero:
    def test_add_transaction_zero_amount(self, setup_db):
        t = add_transaction('credit', 0, 'zero')
        assert t['amount'] == 0

    def test_get_recent_transactions_empty(self, setup_db):
        txns = get_recent_transactions()
        assert txns == []

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
        assert t['description'] == 'Donation'

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
        csv = get_member_statement(m['member_id'])
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
        req = create_loan(m['member_id'], 50000, 12)
        approve_loan(req['req_id'], 0)
        add_fd(100000, '2026-01-01', 12, 7, 'SBI')
        stats = get_admin_stats()
        assert stats['total_lent'] >= 50000
        assert stats['hardlocked_fd'] >= 100000

    def test_passbook_contains_initial_deposit(self, setup_db):
        m = create_member('Passbook Test')
        entries = get_passbook_entries()
        deposit_entries = [e for e in entries if e['category'] == 'Entry Deposit' and e['member_name'] == 'Passbook Test']
        assert len(deposit_entries) == 1
        assert deposit_entries[0]['amount'] == 25000
        assert deposit_entries[0]['debit_credit'] == 'credit'

    def test_passbook_descending_order(self, setup_db):
        m = create_member('Order Test')
        admin_direct_entry(m['member_id'], share_amount=100, entry_date='2026-06-01')
        admin_direct_entry(m['member_id'], share_amount=200, entry_date='2026-06-02')
        entries = get_passbook_entries()
        ts_filtered = [e['ts'] for e in entries if e['member_name'] == 'Order Test']
        assert ts_filtered == sorted(ts_filtered, reverse=True)

    def test_passbook_no_duplicate_entries(self, setup_db):
        m = create_member('Dedup Test')
        admin_direct_entry(m['member_id'], share_amount=500, entry_date='2026-06-01')
        entries = get_passbook_entries()
        member_entries = [e for e in entries if e['member_name'] == 'Dedup Test']
        assert len(member_entries) == 2  # entry deposit + share
        assert len([e for e in member_entries if e['category'] == 'Share']) == 1

    def test_passbook_includes_fd_entries(self, setup_db):
        add_fd(100000, '2026-01-01', 12, 7, 'HDFC')
        entries = get_passbook_entries()
        fd_deposits = [e for e in entries if e['category'] == 'FD Deposit']
        assert len(fd_deposits) >= 1

    def test_passbook_split_on_combined_entry(self, setup_db):
        from core.models.payment import admin_direct_entry
        m = create_member('Split Test')
        admin_direct_entry(m['member_id'], share_amount=500, fine=50, loan_principal=1000, loan_interest=200, entry_date='2026-07-01')
        entries = get_passbook_entries()
        member_entries = [e for e in entries if e['member_name'] == 'Split Test']
        combined = [e for e in member_entries if e.get('split')]
        assert len(combined) == 1
        assert combined[0]['split'] == {'share': 500, 'fine': 50, 'loan_interest': 200, 'loan_principal': 1000}
        assert combined[0]['category'] == 'Payment'

    def test_passbook_no_split_on_non_member_entries(self, setup_db):
        add_transaction('credit', 5000, 'Rental Income', '2026-07-01T12:00:00')
        entries = get_passbook_entries()
        assert all('split' not in e for e in entries if e['category'] == 'Other Income')

    def test_add_income_transaction_large(self, setup_db):
        t = add_transaction('credit', 1000000, 'Large deposit')
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
        req = create_loan(m['member_id'], 10000, 12)
        loan = approve_loan(req['req_id'], 0)
        loan_dict = get_loan(loan['loan_id'])
        apply_payment_to_loan(loan_dict, 2000)
        csv = get_member_statement(m['member_id'])
        assert 'loan_principal' in csv


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestTransactionException:
    def test_get_member_statement_nonexistent(self, setup_db):
        csv = get_member_statement(99999)
        assert 'type,date,amount,details' in csv
