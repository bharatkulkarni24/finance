import calendar
from datetime import datetime

from core.database import get_conn, row_to_dict


def add_fd(amount: float, start_date: str, term_months: int, interest_rate: float, notes: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    sd = datetime.strptime(start_date, '%Y-%m-%d')
    months = term_months
    year = sd.year + (sd.month - 1 + months) // 12
    month = (sd.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(sd.day, last_day)
    maturity_date = f'{year:04d}-{month:02d}-{day:02d}'
    cur.execute(
        'INSERT INTO fd_entries (amount, start_date, term_months, interest_rate, status, notes, created_at, maturity_date) VALUES (?,?,?,?,?,?,?,?)',
        (amount, start_date, term_months, interest_rate, 'active', notes, now, maturity_date),
    )
    fd_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM fd_entries WHERE id=?', (fd_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def close_fd(fd_id: int, end_date: str, interest_earned: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE fd_entries SET status=?, interest_earned=?, maturity_date=? WHERE id=? AND status=?',
        ('matured', interest_earned, end_date, fd_id, 'active'),
    )
    if cur.rowcount == 0:
        conn.close()
        return None
    cur.execute('SELECT * FROM fd_entries WHERE id=?', (fd_id,))
    fd = row_to_dict(cur.fetchone())
    if interest_earned > 0:
        cur.execute(
            'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
            (None, datetime.utcnow().isoformat(), f'FD Interest - {fd["notes"] or fd_id}', 'credit', interest_earned),
        )
    conn.commit()
    conn.close()
    return fd


def get_fd_entries(status: str = None):
    conn = get_conn()
    cur = conn.cursor()
    if status:
        cur.execute('SELECT * FROM fd_entries WHERE status=? ORDER BY start_date DESC', (status,))
    else:
        cur.execute('SELECT * FROM fd_entries ORDER BY start_date DESC')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_active_fd_total():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM fd_entries WHERE status='active'")
    total = cur.fetchone()[0]
    conn.close()
    return total
