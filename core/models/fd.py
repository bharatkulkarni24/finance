import calendar
from datetime import datetime

from core.database import get_conn, row_to_dict


def add_fd(amount: float, start_date: str, term_months: int, interest_rate: float, notes: str = '',
           investment_type: str = 'one_time'):
    from core.models.transaction import get_available_to_lend
    from core import config
    avail = get_available_to_lend()
    if not getattr(config, 'ALLOW_OVERLEND', False) and round(amount or 0, 2) > avail:
        return {'error': 'insufficient_funds', 'available': avail, 'requested': round(amount or 0, 2)}
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
        'INSERT INTO fixed_deposits (amount, start_date, term_months, interest_rate, status, notes, created_at, maturity_date, investment_type) VALUES (?,?,?,?,?,?,?,?,?)',
        (amount, start_date, term_months, interest_rate, 'active', notes, now, maturity_date, investment_type),
    )
    fd_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM fixed_deposits WHERE fd_id=?', (fd_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def add_fd_installment(parent_id: int, amount: float, installment_date: str, notes: str = ''):
    from core.models.transaction import get_available_to_lend
    from core import config
    avail = get_available_to_lend()
    if not getattr(config, 'ALLOW_OVERLEND', False) and round(amount or 0, 2) > avail:
        return {'error': 'insufficient_funds', 'available': avail, 'requested': round(amount or 0, 2)}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM fixed_deposits WHERE fd_id=?', (parent_id,))
    parent = cur.fetchone()
    if not parent:
        conn.close()
        return None
    now = datetime.utcnow().isoformat()
    cur.execute(
        'INSERT INTO fixed_deposits (amount, start_date, term_months, interest_rate, status, notes, created_at, maturity_date, investment_type, parent_id, installment_date) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (amount, installment_date, 0, 0, 'active', notes or '', now, None, 'installment', parent_id, installment_date),
    )
    fd_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM fixed_deposits WHERE fd_id=?', (fd_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def close_fd(fd_id: int, end_date: str, interest_earned: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM fixed_deposits WHERE fd_id=?', (fd_id,))
    fd = cur.fetchone()
    if not fd:
        conn.close()
        return None
    fd_dict = row_to_dict(fd)

    if fd_dict.get('investment_type') == 'monthly':
        # Close all linked installments
        cur.execute(
            "UPDATE fixed_deposits SET status='matured', interest_earned=0, maturity_date=? WHERE parent_id=? AND status='active'",
            (end_date, fd_id),
        )
        # Close the scheme itself
        cur.execute(
            "UPDATE fixed_deposits SET status='matured', interest_earned=?, maturity_date=? WHERE fd_id=? AND status='active'",
            (interest_earned, end_date, fd_id),
        )
    else:
        cur.execute(
            "UPDATE fixed_deposits SET status='matured', interest_earned=?, maturity_date=? WHERE fd_id=? AND status='active'",
            (interest_earned, end_date, fd_id),
        )
    if cur.rowcount == 0:
        conn.close()
        return None

    conn.commit()
    cur.execute('SELECT * FROM fixed_deposits WHERE fd_id=?', (fd_id,))
    result = row_to_dict(cur.fetchone())
    conn.close()
    return result


def get_fd_entries(status: str = None):
    conn = get_conn()
    cur = conn.cursor()
    if status:
        cur.execute('SELECT * FROM fixed_deposits WHERE status=? ORDER BY start_date DESC', (status,))
    else:
        cur.execute('SELECT * FROM fixed_deposits ORDER BY start_date DESC')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_active_fd_total():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM fixed_deposits WHERE status='active' AND investment_type != 'monthly'")
    total = cur.fetchone()[0]
    conn.close()
    return total
