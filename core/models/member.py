from datetime import date
from typing import Optional

from werkzeug.security import generate_password_hash

from core.database import get_conn, row_to_dict
from core.models.requests import list_member_requests


def get_all_members():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM members')
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def create_member(name: str, phone: Optional[str] = '', is_admin: int = 0,
                  dob: Optional[str] = '', address: Optional[str] = '',
                  photo_url: Optional[str] = '',
                  deposit_amount: Optional[float] = None,
                  deposit_date: Optional[str] = None,
                  password: Optional[str] = '') -> dict:
    conn = get_conn()
    cur = conn.cursor()
    dep_amt = deposit_amount if deposit_amount is not None else 25000
    joined = (deposit_date or date.today().isoformat())
    pw_hash = generate_password_hash(password) if password else ''
    cur.execute(
        'INSERT INTO members (name, phone, joined_date, deposit_amount, is_admin, dob, address, photo_url, password) VALUES (?,?,?,?,?,?,?,?,?)',
        (name, phone, joined, dep_amt, is_admin, dob, address, photo_url, pw_hash),
    )
    member_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM members WHERE member_id=?', (member_id,))
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
    cur.execute('SELECT * FROM members WHERE member_id=?', (member_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    m = row_to_dict(row)
    if full:
        cur.execute('SELECT * FROM loans WHERE member_id=?', (member_id,))
        m['loans'] = [row_to_dict(r) for r in cur.fetchall()]
        cur.execute('SELECT * FROM member_ledger WHERE member_id=? ORDER BY pay_date', (member_id,))
        m['payments'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        m['requests'] = list_member_requests(member_id)
    conn.close()
    return m


def update_member(member_id: int, phone: Optional[str] = None, dob: Optional[str] = None, address: Optional[str] = None, photo_url: Optional[str] = None, password_hash: Optional[str] = None) -> Optional[dict]:
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
    if password_hash is not None:
        updates.append('password = ?')
        params.append(password_hash)
    if not updates:
        conn.close()
        return get_member(member_id, full=True)
    params.append(member_id)
    cur.execute(f'UPDATE members SET {", ".join(updates)} WHERE member_id=?', params)
    conn.commit()
    conn.close()
    return get_member(member_id, full=True)
