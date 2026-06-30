from datetime import datetime, date

from core.database import get_conn, row_to_dict


def generate_dues_for_member_internal(cur, member_id: int, start_date: date, months: int = 36, monthly_amount: float = 500):
    y, m = start_date.year, start_date.month
    for _ in range(months):
        due_date = date(y, m, 10)
        cur.execute(
            'INSERT INTO dues (member_id, due_date, amount, paid) VALUES (?,?,?,?)',
            (member_id, due_date.isoformat(), monthly_amount, 0),
        )
        m += 1
        if m > 12:
            m = 1
            y += 1


def generate_dues_for_member(member_id: int, start_date: date, months: int = 36, monthly_amount: float = 500):
    conn = get_conn()
    cur = conn.cursor()
    generate_dues_for_member_internal(cur, member_id, start_date, months, monthly_amount)
    conn.commit()
    conn.close()


def get_dues(member_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM dues WHERE member_id=? ORDER BY due_date', (member_id,))
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def calculate_due_amount(member_id: int, as_of: date = None):
    if as_of is None:
        as_of = datetime.utcnow().date()
    dues = get_dues(member_id)
    total_due = 0.0
    total_late = 0.0
    for d in dues:
        if d['paid']:
            continue
        due_date = date.fromisoformat(d['due_date'])
        if due_date <= as_of:
            days_late = (as_of - due_date).days
            late_fee = 50 * max(0, days_late)
            total_due += d['amount']
            total_late += late_fee
    return {'due': total_due, 'late_fee': total_late, 'total': total_due + total_late}
