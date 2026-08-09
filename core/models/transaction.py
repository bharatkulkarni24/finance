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
        "SELECT * FROM group_ledger WHERE member_id IS NULL AND description NOT LIKE 'FD Interest%' ORDER BY timestamp DESC LIMIT ?", (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def _stmt_type(r):
    if not r['share_amount'] and not r['loan_principal'] and not r['loan_interest'] and not r['late_fee']:
        return 'deposit'
    if r['share_amount'] and (r['loan_principal'] or r['loan_interest'] or r['late_fee']):
        return 'payment'
    if r['share_amount']:
        return 'share'
    if r['loan_principal'] or r['loan_interest']:
        return 'loan_payment'
    if r['late_fee']:
        return 'late_fee'
    return 'payment'


def get_member_statement(member_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    out = 'type,date,amount,details\n'
    cur.execute('SELECT * FROM member_ledger WHERE member_id=? ORDER BY pay_date', (member_id,))
    for p in cur.fetchall():
        r = row_to_dict(p)
        details = f"share:{r['share_amount']};principal:{r['loan_principal']};interest:{r['loan_interest']};late_fee:{r['late_fee']};loan:{r['loan_id']}"
        out += f"{_stmt_type(r)},{r['pay_date']},{r['total_amount']},{details}\n"
    conn.close()
    return out


def get_admin_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT SUM(total_amount) FROM member_ledger WHERE share_amount=0 AND loan_principal=0 AND loan_interest=0 AND late_fee=0")
    deposits_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(share_amount) FROM member_ledger")
    shares_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(loan_principal) FROM member_ledger")
    loan_principal_received = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(loan_interest) FROM member_ledger")
    loan_interest_received = cur.fetchone()[0] or 0.0
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM group_ledger WHERE debit_credit='credit' AND (description LIKE 'FD Interest%' OR member_id IS NULL)",
    )
    txn_others = cur.fetchone()[0] or 0.0
    cur.execute("SELECT COALESCE(SUM(late_fee),0) FROM member_ledger")
    late_fees_total = cur.fetchone()[0] or 0.0
    others_total = txn_others + late_fees_total
    cur.execute("SELECT SUM(amount) FROM group_ledger WHERE debit_credit='debit'")
    expenses_total = cur.fetchone()[0] or 0.0
    total_collected = deposits_total + shares_total + loan_principal_received + loan_interest_received + others_total - expenses_total
    cur.execute("SELECT COUNT(*) FROM members")
    member_count = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(outstanding) FROM loans WHERE status='active'")
    total_outstanding = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(principal) FROM loans WHERE status='active'")
    total_lent = cur.fetchone()[0] or 0.0
    conn.close()
    hardlocked_fd = get_active_fd_total()
    cash_on_hand = total_collected - total_lent - hardlocked_fd
    available_to_lend = cash_on_hand
    return {
        'total_collected': total_collected,
        'deposits_total': deposits_total,
        'shares_total': shares_total,
        'loan_principal_received': loan_principal_received,
        'loan_interest_received': loan_interest_received,
        'others_total': others_total,
        'expenses_total': expenses_total,
        'total_lent': total_lent,
        'total_outstanding': total_outstanding,
        'hardlocked_fd': hardlocked_fd,
        'cash_on_hand': cash_on_hand,
        'available_to_lend': available_to_lend,
        'member_count': member_count,
        'group_start_date': 'April 2025',
        'share_amount': 500,
        'one_time_amount': 25000,
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
    cur.execute("SELECT substr(pay_date,1,7) m, SUM(late_fee) s FROM member_ledger WHERE pay_date IS NOT NULL GROUP BY m")
    fine_by_month = {r['m']: r['s'] for r in cur.fetchall()}
    conn.close()

    months = sorted(set(share_by_month) | set(principal_by_month) | set(interest_by_month) | set(fine_by_month))
    yearly_keys = sorted({m[:4] for m in months})

    monthly = {}
    for m in months:
        monthly[m] = {
            'share': round(share_by_month.get(m, 0.0) or 0.0, 2),
            'principal': round(principal_by_month.get(m, 0.0) or 0.0, 2),
            'interest': round(interest_by_month.get(m, 0.0) or 0.0, 2),
            'fine': round(fine_by_month.get(m, 0.0) or 0.0, 2),
        }

    yearly = {}
    for y in yearly_keys:
        vals = [monthly[m] for m in months if m[:4] == y]
        yearly[y] = {
            'share': round(sum(v['share'] for v in vals), 2),
            'principal': round(sum(v['principal'] for v in vals), 2),
            'interest': round(sum(v['interest'] for v in vals), 2),
            'fine': round(sum(v['fine'] for v in vals), 2),
        }

    return {'months': months, 'years': yearly_keys, 'monthly': monthly, 'yearly': yearly}


def get_passbook_entries():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT ts, category, member_name, amount, debit_credit FROM (
        SELECT p.pay_date as ts,
            CASE
                WHEN p.share_amount = 0 AND p.loan_principal = 0 AND p.loan_interest = 0 AND p.late_fee = 0 THEN 'Deposit'
                WHEN p.late_fee > 0 AND p.share_amount = 0 AND p.loan_principal = 0 AND p.loan_interest = 0 THEN 'Late Fee'
                WHEN p.share_amount > 0 AND (p.loan_principal > 0 OR p.loan_interest > 0) THEN 'Payment'
                WHEN p.share_amount > 0 THEN 'Share'
                ELSE 'Loan Payment'
            END as category,
            m.name as member_name, p.total_amount as amount, 'credit' as debit_credit
        FROM member_ledger p LEFT JOIN members m ON m.member_id = p.member_id
        UNION ALL
        SELECT l.disbursed_date || 'T12:00:00', 'Loan Disbursed', m.name, l.principal, 'debit'
        FROM loans l JOIN members m ON m.member_id = l.member_id WHERE l.disbursed_date IS NOT NULL AND l.status IN ('active','repaid')
        UNION ALL
        SELECT t.timestamp,
            CASE
                WHEN t.description LIKE 'FD Interest%' THEN 'FD Interest'
                WHEN t.debit_credit='credit' THEN 'Income'
                ELSE 'Expense'
            END as category,
            m.name as member_name, t.amount, t.debit_credit
        FROM group_ledger t LEFT JOIN members m ON m.member_id = t.member_id
        WHERE t.member_id IS NULL
        UNION ALL
        SELECT f.start_date || 'T12:00:00', 'FD Deposit', NULL, f.amount, 'debit'
        FROM fixed_deposits f WHERE f.amount > 0
        UNION ALL
        SELECT f.maturity_date || 'T12:00:00', 'FD Matured', NULL, f.amount, 'credit'
        FROM fixed_deposits f WHERE f.status='matured' AND f.amount > 0
    ) ORDER BY ts DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
