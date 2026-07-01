from datetime import datetime

from core.database import get_conn, row_to_dict
from core.models.fd import get_active_fd_total


def admin_add_funds(amount: float, note: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
        (None, now, note or 'Admin add funds', 'credit', amount),
    )
    conn.commit()
    cur.execute('SELECT * FROM transactions WHERE id=?', (cur.lastrowid,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def add_transaction(debit_credit: str, amount: float, desc: str = '', entry_date: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    ts = entry_date if entry_date else datetime.utcnow().isoformat()
    cur.execute(
        'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount, source) VALUES (?,?,?,?,?,?)',
        (None, ts, desc, debit_credit, amount, 'manual_ie'),
    )
    conn.commit()
    cur.execute('SELECT * FROM transactions WHERE id=?', (cur.lastrowid,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def get_recent_transactions(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM transactions WHERE source='manual_ie' ORDER BY timestamp DESC LIMIT ?", (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_member_statement(member_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    out = 'type,date,amount,details\n'
    cur.execute('SELECT * FROM contributions WHERE member_id=? ORDER BY date', (member_id,))
    for c in cur.fetchall():
        r = row_to_dict(c)
        out += f"{r['type']},{r['date']},{r['amount']},\n"
    cur.execute('SELECT * FROM payments WHERE member_id=? ORDER BY date', (member_id,))
    for p in cur.fetchall():
        r = row_to_dict(p)
        out += f"payment,{r['date']},{r['amount']},loan:{r['loan_id']};interest:{r['interest_paid']};principal:{r['principal_paid']}\n"
    conn.close()
    return out


def get_admin_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM contributions WHERE type='deposit'")
    deposits_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(amount) FROM contributions WHERE type='share'")
    shares_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(principal_paid) FROM payments")
    loan_principal_received = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(interest_paid) FROM payments")
    loan_interest_received = cur.fetchone()[0] or 0.0
    cur.execute(
        "SELECT SUM(amount) FROM transactions WHERE debit_credit='credit' AND (desc LIKE 'FD Interest%' OR source='manual_ie' OR desc='Late fee')",
    )
    others_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(amount) FROM transactions WHERE debit_credit='debit'")
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


def get_passbook_entries():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT ts, category, member_name, amount, debit_credit FROM (
        SELECT p.date || 'T12:00:00' as ts, 'Loan Payment' as category, m.name as member_name, p.principal_paid + p.interest_paid + COALESCE(p.late_fee_paid,0) as amount, 'credit' as debit_credit
        FROM payments p JOIN loans l ON l.id = p.loan_id JOIN members m ON m.id = l.member_id
        UNION ALL
        SELECT l.disbursed_date || 'T12:00:00', 'Loan Disbursed', m.name, l.principal, 'debit'
        FROM loans l JOIN members m ON m.id = l.member_id WHERE l.disbursed_date IS NOT NULL AND l.status IN ('active','repaid')
        UNION ALL
        SELECT t.timestamp,
            CASE
                WHEN t.desc LIKE 'FD Interest%' THEN 'FD Interest'
                WHEN t.desc LIKE 'Share%' THEN 'Share'
                WHEN t.desc LIKE 'Deposit%' THEN 'Deposit'
                WHEN t.desc = 'Initial deposit' THEN 'Deposit'
                WHEN t.desc LIKE 'Loan%' AND t.debit_credit='credit' THEN 'Loan Payment'
                WHEN t.desc LIKE 'Due payment%' THEN 'Due Payment'
                WHEN t.source='manual_ie' AND t.debit_credit='credit' THEN 'Income'
                WHEN t.source='manual_ie' AND t.debit_credit='debit' THEN 'Expense'
                WHEN t.desc='Admin add funds' THEN 'Income'
                ELSE t.desc
            END as category,
            m.name as member_name, t.amount, t.debit_credit
        FROM transactions t LEFT JOIN members m ON m.id = t.member_id
        UNION ALL
        SELECT f.start_date || 'T12:00:00', 'FD Deposit', NULL, f.amount, 'debit'
        FROM fd_entries f
        UNION ALL
        SELECT f.maturity_date || 'T12:00:00', 'FD Matured', NULL, f.amount, 'credit'
        FROM fd_entries f WHERE f.status='matured'
    ) ORDER BY ts DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
