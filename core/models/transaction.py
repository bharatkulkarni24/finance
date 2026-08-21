from datetime import datetime

from core.database import get_conn, row_to_dict
from core.models.fd import get_active_fd_total


def add_transaction(debit_credit: str, amount: float, description: str = '', entry_date: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    ts = entry_date if entry_date else datetime.utcnow().isoformat()
    cur.execute(
        'INSERT INTO group_ledger (member_id, timestamp, description, debit_credit, amount) VALUES (?,?,?,?,?)',
        (None, ts, description, debit_credit, amount),
    )
    conn.commit()
    cur.execute('SELECT * FROM group_ledger WHERE trn_id=?', (cur.lastrowid,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def get_recent_transactions(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM group_ledger WHERE member_id IS NULL ORDER BY timestamp DESC LIMIT ?", (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def _stmt_type(r):
    if not r['share_amount'] and not r['loan_principal'] and not r['loan_interest'] and not r['fine']:
        return 'deposit'
    if r['share_amount'] and (r['loan_principal'] or r['loan_interest'] or r['fine']):
        return 'payment'
    if r['share_amount']:
        return 'share'
    if r['loan_principal'] or r['loan_interest']:
        return 'loan_principal'
    if r['fine']:
        return 'fine'
    return 'payment'


def get_member_statement(member_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    out = 'type,date,amount,details\n'
    cur.execute('SELECT joined_date, entry_deposit_amount FROM members WHERE member_id=?', (member_id,))
    m = cur.fetchone()
    if m and m['entry_deposit_amount']:
        out += f"deposit,{m['joined_date']},{m['entry_deposit_amount']},entry deposit\n"
    cur.execute('SELECT * FROM member_ledger WHERE member_id=? ORDER BY pay_date', (member_id,))
    for p in cur.fetchall():
        r = row_to_dict(p)
        details = f"share:{r['share_amount']};loan_principal:{r['loan_principal']};loan_interest:{r['loan_interest']};fine:{r['fine']};loan:{r['loan_id']}"
        out += f"{_stmt_type(r)},{r['pay_date']},{r['total_amount']},{details}\n"
    conn.close()
    return out


def get_admin_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(entry_deposit_amount),0) FROM members")
    entry_deposit_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(share_amount) FROM member_ledger")
    shares_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(loan_principal) FROM member_ledger")
    loan_principal_received = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(loan_interest) FROM member_ledger")
    loan_interest_received = cur.fetchone()[0] or 0.0
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM group_ledger WHERE debit_credit='credit' AND member_id IS NULL",
    )
    others_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT COALESCE(SUM(fine),0) FROM member_ledger")
    fine_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT COALESCE(SUM(interest_earned),0) FROM fixed_deposits WHERE status='matured'")
    fd_interest_returned = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(amount) FROM group_ledger WHERE debit_credit='debit'")
    expenses_total = cur.fetchone()[0] or 0.0
    total_collected = entry_deposit_total + shares_total + loan_interest_received + others_total + fine_total + fd_interest_returned - expenses_total
    cur.execute("SELECT COUNT(*) FROM members")
    member_count = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(outstanding) FROM loans WHERE status='active'")
    total_outstanding = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(loan_principal) FROM loans WHERE status='active'")
    total_lent = cur.fetchone()[0] or 0.0
    conn.close()
    hardlocked_fd = get_active_fd_total()
    cash_on_hand = total_collected - total_lent - hardlocked_fd
    available_to_lend = cash_on_hand
    return {
        'total_collected': total_collected,
        'entry_deposit_total': entry_deposit_total,
        'shares_total': shares_total,
        'loan_principal_received': loan_principal_received,
        'loan_interest_received': loan_interest_received,
        'fd_interest_returned': fd_interest_returned,
        'others_total': others_total,
        'fines_total': fine_total,
        'expenses_total': expenses_total,
        'total_lent': total_lent,
        'total_outstanding': total_outstanding,
        'hardlocked_fd': hardlocked_fd,
        'cash_on_hand': cash_on_hand,
        'available_to_lend': available_to_lend,
        'member_count': member_count,
        'group_start_date': 'April 2025',
        'monthly_share': 500,
        'total_period_months': 36,
        'loan_interest_rate': 1,
    }


def get_period_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT substr(pay_date,1,7) m, SUM(share_amount) s FROM member_ledger WHERE pay_date IS NOT NULL GROUP BY m")
    share_by_month = {r['m']: r['s'] for r in cur.fetchall()}
    cur.execute("SELECT substr(pay_date,1,7) m, SUM(loan_principal) s FROM member_ledger WHERE pay_date IS NOT NULL GROUP BY m")
    principal_by_month = {r['m']: r['s'] for r in cur.fetchall()}
    cur.execute("SELECT substr(pay_date,1,7) m, SUM(loan_interest) s FROM member_ledger WHERE pay_date IS NOT NULL GROUP BY m")
    interest_by_month = {r['m']: r['s'] for r in cur.fetchall()}
    cur.execute("SELECT substr(pay_date,1,7) m, SUM(fine) s FROM member_ledger WHERE pay_date IS NOT NULL GROUP BY m")
    fine_by_month = {r['m']: r['s'] for r in cur.fetchall()}
    conn.close()

    months = sorted(set(share_by_month) | set(principal_by_month) | set(interest_by_month) | set(fine_by_month))
    yearly_keys = sorted({m[:4] for m in months})

    monthly = {}
    for m in months:
        monthly[m] = {
            'share': round(share_by_month.get(m, 0.0) or 0.0, 2),
            'loan_principal': round(principal_by_month.get(m, 0.0) or 0.0, 2),
            'loan_interest': round(interest_by_month.get(m, 0.0) or 0.0, 2),
            'fine': round(fine_by_month.get(m, 0.0) or 0.0, 2),
        }

    yearly = {}
    for y in yearly_keys:
        vals = [monthly[m] for m in months if m[:4] == y]
        yearly[y] = {
            'share': round(sum(v['share'] for v in vals), 2),
            'loan_principal': round(sum(v['loan_principal'] for v in vals), 2),
            'loan_interest': round(sum(v['loan_interest'] for v in vals), 2),
            'fine': round(sum(v['fine'] for v in vals), 2),
        }

    return {'months': months, 'years': yearly_keys, 'monthly': monthly, 'yearly': yearly}


def get_passbook_entries():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT ts, category, member_name, amount, debit_credit, share, fine, loan_interest, loan_principal FROM (
        SELECT m.joined_date || 'T12:00:00' as ts, 'Entry Deposit' as category, m.name as member_name, m.entry_deposit_amount as amount, 'credit' as debit_credit, NULL as share, NULL as fine, NULL as loan_interest, NULL as loan_principal
        FROM members m WHERE m.entry_deposit_amount > 0
        UNION ALL
        SELECT p.pay_date as ts,
            CASE
                WHEN p.share_amount = 0 AND p.loan_principal = 0 AND p.loan_interest = 0 AND p.fine = 0 THEN 'Entry Deposit'
                WHEN p.fine > 0 AND p.share_amount = 0 AND p.loan_principal = 0 AND p.loan_interest = 0 THEN 'Fine'
                WHEN p.share_amount > 0 AND (p.loan_principal > 0 OR p.loan_interest > 0) THEN 'Payment'
                WHEN p.share_amount > 0 THEN 'Share'
                ELSE 'Loan Principal'
            END as category,
            m.name as member_name, p.total_amount as amount, 'credit' as debit_credit,
            p.share_amount as share, p.fine as fine, p.loan_interest as loan_interest, p.loan_principal as loan_principal
        FROM member_ledger p LEFT JOIN members m ON m.member_id = p.member_id
        UNION ALL
        SELECT l.disbursed_date || 'T12:00:00', 'Loan Disbursed', m.name, l.loan_principal, 'debit', NULL, NULL, NULL, NULL
        FROM loans l JOIN members m ON m.member_id = l.member_id WHERE l.disbursed_date IS NOT NULL AND l.status IN ('active','repaid')
        UNION ALL
        SELECT t.timestamp,
            CASE
                WHEN t.debit_credit='credit' THEN 'Other Income'
                ELSE 'Expense'
            END as category,
            m.name as member_name, t.amount, t.debit_credit, NULL, NULL, NULL, NULL
        FROM group_ledger t LEFT JOIN members m ON m.member_id = t.member_id
        WHERE t.member_id IS NULL
        UNION ALL
        SELECT f.start_date || 'T12:00:00', 'FD Deposit', NULL, f.amount, 'debit', NULL, NULL, NULL, NULL
        FROM fixed_deposits f WHERE f.amount > 0
        UNION ALL
        SELECT f.maturity_date || 'T12:00:00', 'FD Gain', NULL, f.amount + COALESCE(f.interest_earned, 0), 'credit', NULL, NULL, NULL, NULL
        FROM fixed_deposits f WHERE f.status='matured' AND (f.amount + COALESCE(f.interest_earned, 0)) > 0
    ) ORDER BY ts DESC
    """)
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        split = {}
        for comp, key in (('share', 'share'), ('fine', 'fine'), ('loan_interest', 'loan_interest'), ('loan_principal', 'loan_principal')):
            if d.get(key):
                split[comp] = d[key]
        if split:
            d['split'] = split
        del d['share'], d['fine'], d['loan_interest'], d['loan_principal']
        rows.append(d)
    conn.close()
    return rows
