from datetime import datetime
from typing import Optional

from core.database import get_conn, row_to_dict
from core.models.dues import generate_dues_for_member_internal


def get_all_members():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM members')
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def create_member(name: str, phone: Optional[str] = '', is_admin: int = 0, dob: Optional[str] = '', address: Optional[str] = '', photo_url: Optional[str] = '') -> dict:
    conn = get_conn()
    cur = conn.cursor()
    joined = datetime.utcnow().date().isoformat()
    cur.execute(
        'INSERT INTO members (name, phone, joined_date, deposit_amount, is_admin, dob, address, photo_url) VALUES (?,?,?,?,?,?,?,?)',
        (name, phone, joined, 25000, is_admin, dob, address, photo_url),
    )
    member_id = cur.lastrowid
    cur.execute(
        'INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)',
        (member_id, joined, 25000, 'deposit'),
    )
    cur.execute(
        'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
        (member_id, datetime.utcnow().isoformat(), 'Initial deposit', 'credit', 25000),
    )
    generate_dues_for_member_internal(cur, member_id, datetime.utcnow().date())
    conn.commit()
    cur.execute('SELECT * FROM members WHERE id=?', (member_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def find_member_by_name(name: str) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM members WHERE LOWER(name)=LOWER(?)', (name,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def get_member(member_id: int, full: bool = False) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM members WHERE id=?', (member_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    m = row_to_dict(row)
    if full:
        cur.execute('SELECT * FROM contributions WHERE member_id=? ORDER BY date', (member_id,))
        m['contributions'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        cur.execute('SELECT * FROM loans WHERE member_id=?', (member_id,))
        m['loans'] = [row_to_dict(r) for r in cur.fetchall()]
        cur.execute('SELECT * FROM payments WHERE member_id=? ORDER BY date', (member_id,))
        m['payments'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        cur.execute('SELECT * FROM dues WHERE member_id=? ORDER BY due_date', (member_id,))
        m['dues'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        cur.execute('SELECT * FROM payment_requests WHERE member_id=? ORDER BY date_submitted DESC', (member_id,))
        m['payment_requests'] = [row_to_dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM transactions WHERE member_id=? AND desc='Late fee' ORDER BY timestamp", (member_id,))
        m['late_fees'] = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return m


def update_member(member_id: int, phone: Optional[str] = None, dob: Optional[str] = None, address: Optional[str] = None, photo_url: Optional[str] = None) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    updates = []
    params = []
    if phone is not None:
        updates.append('phone = ?')
        params.append(phone)
    if dob is not None:
        updates.append('dob = ?')
        params.append(dob)
    if address is not None:
        updates.append('address = ?')
        params.append(address)
    if photo_url is not None:
        updates.append('photo_url = ?')
        params.append(photo_url)
    if not updates:
        conn.close()
        return get_member(member_id, full=True)
    params.append(member_id)
    cur.execute(f'UPDATE members SET {", ".join(updates)} WHERE id=?', params)
    conn.commit()
    conn.close()
    return get_member(member_id, full=True)
