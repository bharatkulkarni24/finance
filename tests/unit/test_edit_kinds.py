"""Edit Entries: entry_deposit & loan_disbursed kinds (added Aug 2026)."""
from core.database import get_conn
from core.models.edit import delete_entry, edit_entry


def _add_member(name='Edit Kind Member'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO members (name, password, is_admin, joined_date, entry_deposit_amount) VALUES (?, '', 0, '2025-04-01', 25000)",
        (name,),
    )
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid


def _add_loan(mid, principal=10000.0, outstanding=None, status='active', disbursed='2026-01-10'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO loans (member_id, loan_principal, outstanding, rate_monthly, term_months, status, disbursed_date) VALUES (?,?,?,?,?,?,?)',
        (mid, principal, principal if outstanding is None else outstanding, 0.01, 10, status, disbursed),
    )
    loan_id = cur.lastrowid
    conn.commit()
    conn.close()
    return loan_id


def _add_repayment(mid, loan_id, amount, pay_date='2026-02-10'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO member_ledger (member_id, pay_date, total_amount, share_amount, loan_principal, loan_interest, fine, loan_id) VALUES (?,?,?,?,?,0,0,?)',
        (mid, pay_date + 'T12:00:00', amount, 0, amount, loan_id),
    )
    conn.commit()
    conn.close()


def _loan(loan_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM loans WHERE loan_id=?', (loan_id,)).fetchone()
    conn.close()
    return dict(row)


def _member(mid):
    conn = get_conn()
    row = conn.execute('SELECT * FROM members WHERE member_id=?', (mid,)).fetchone()
    conn.close()
    return dict(row)


class TestEntryDepositKind:
    def test_edit_updates_amount_and_date(self):
        mid = _add_member('Dep Edit')
        r = edit_entry({'kind': 'entry_deposit', 'member_id': mid, 'amount': 30000, 'date': '2025-05-01'})
        assert r == {'status': 'ok'}
        m = _member(mid)
        assert m['entry_deposit_amount'] == 30000
        assert m['joined_date'] == '2025-05-01'

    def test_edit_keeps_date_when_not_given(self):
        mid = _add_member('Dep Keep Date')
        edit_entry({'kind': 'entry_deposit', 'member_id': mid, 'amount': 1000})
        assert _member(mid)['joined_date'] == '2025-04-01'

    def test_edit_requires_member(self):
        assert edit_entry({'kind': 'entry_deposit', 'amount': 100}) == {'error': 'member required'}

    def test_edit_unknown_member(self):
        assert edit_entry({'kind': 'entry_deposit', 'member_id': 99999, 'amount': 100}) == {'error': 'member not found'}

    def test_delete_zeroes_deposit(self):
        mid = _add_member('Dep Delete')
        r = delete_entry({'kind': 'entry_deposit', 'member_id': mid})
        assert r == {'status': 'ok'}
        assert _member(mid)['entry_deposit_amount'] == 0


class TestLoanDisbursedKind:
    def test_edit_raises_outstanding(self):
        mid = _add_member('Loan Up')
        lid = _add_loan(mid, principal=10000)
        r = edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 12000})
        assert r == {'status': 'ok'}
        l = _loan(lid)
        assert l['loan_principal'] == 12000
        assert l['outstanding'] == 12000

    def test_edit_lowers_outstanding(self):
        mid = _add_member('Loan Down')
        lid = _add_loan(mid, principal=10000)
        edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 7500})
        l = _loan(lid)
        assert l['loan_principal'] == 7500
        assert l['outstanding'] == 7500

    def test_edit_updates_disbursed_date(self):
        mid = _add_member('Loan Date')
        lid = _add_loan(mid, principal=5000)
        edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 5000, 'date': '2026-03-15'})
        assert _loan(lid)['disbursed_date'] == '2026-03-15'

    def test_edit_blocked_below_repayments(self):
        mid = _add_member('Loan Guard')
        lid = _add_loan(mid, principal=10000, outstanding=6000)
        _add_repayment(mid, lid, 4000)  # 4000 already repaid
        r = edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 1500})
        assert 'error' in r and 'below' in r['error']
        # nothing changed
        assert _loan(lid)['loan_principal'] == 10000

    def test_full_cycle_status_flip(self):
        mid = _add_member('Loan Cycle')
        lid = _add_loan(mid, principal=10000, outstanding=6000)
        _add_repayment(mid, lid, 4000)
        # shrink principal to exactly the repaid amount -> fully repaid
        edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 4000})
        assert _loan(lid)['status'] == 'repaid'
        # raise it again -> active with adjusted outstanding
        edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 10000})
        l = _loan(lid)
        assert l['status'] == 'active'
        assert l['outstanding'] == 6000

    def test_delete_blocked_with_repayments(self):
        mid = _add_member('Loan NoDel')
        lid = _add_loan(mid, principal=8000)
        _add_repayment(mid, lid, 2000)
        r = delete_entry({'kind': 'loan_disbursed', 'transaction_id': lid})
        assert 'error' in r and 'repayments' in r['error']
        assert _loan(lid) is not None

    def test_delete_without_repayments(self):
        mid = _add_member('Loan Del')
        lid = _add_loan(mid, principal=8000)
        assert delete_entry({'kind': 'loan_disbursed', 'transaction_id': lid}) == {'status': 'ok'}
        conn = get_conn()
        n = conn.execute('SELECT COUNT(*) FROM loans WHERE loan_id=?', (lid,)).fetchone()[0]
        conn.close()
        assert n == 0


class TestSharedValidation:
    def test_unknown_kind_edit_and_delete(self):
        assert edit_entry({'kind': 'bogus'}) == {'error': 'unknown kind'}
        assert delete_entry({'kind': 'bogus'}) == {'error': 'unknown kind'}

    def test_audit_logged_for_both_kinds(self):
        mid = _add_member('Audit Row')
        lid = _add_loan(mid, principal=1000)
        edit_entry({'kind': 'loan_disbursed', 'transaction_id': lid, 'amount': 2000})
        edit_entry({'kind': 'entry_deposit', 'member_id': mid, 'amount': 26000})
        delete_entry({'kind': 'entry_deposit', 'member_id': mid})
        conn = get_conn()
        n = conn.execute("SELECT COUNT(*) FROM audit_log WHERE action IN ('update','delete')").fetchone()[0]
        conn.close()
        assert n >= 3


class TestSplitDateMove:
    def _day_total(self, mid, day):
        conn = get_conn()
        n = conn.execute(
            'SELECT COALESCE(SUM(total_amount),0) FROM member_ledger WHERE member_id=? AND substr(pay_date,1,10)=?',
            (mid, day),
        ).fetchone()[0]
        conn.close()
        return round(n, 2)

    def test_resplit_moves_entry_to_new_date_without_duplicate(self):
        mid = _add_member('Split Move')
        edit_entry({'kind': 'split', 'member_id': mid, 'date': '2026-03-05',
                    'share': 1000, 'fine': 50, 'loan_interest': 0, 'loan_principal': 0})
        assert self._day_total(mid, '2026-03-05') == 1050
        # Admin corrects: same split moved to the 7th
        r = edit_entry({'kind': 'split', 'member_id': mid, 'date': '2026-03-07',
                        'orig_date': '2026-03-05',
                        'share': 1200, 'fine': 0, 'loan_interest': 0, 'loan_principal': 0})
        assert r == {'status': 'ok'}
        assert self._day_total(mid, '2026-03-05') == 0      # old day cleared
        assert self._day_total(mid, '2026-03-07') == 1200   # corrected entry only

    def test_resplit_same_day_still_works(self):
        mid = _add_member('Split Same Day')
        edit_entry({'kind': 'split', 'member_id': mid, 'date': '2026-04-02', 'share': 900})
        r = edit_entry({'kind': 'split', 'member_id': mid, 'date': '2026-04-02',
                        'orig_date': '2026-04-02', 'share': 950})
        assert r == {'status': 'ok'}
        assert self._day_total(mid, '2026-04-02') == 950
