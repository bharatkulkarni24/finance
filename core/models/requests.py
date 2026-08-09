from datetime import datetime

from core.database import get_conn, row_to_dict

TYPE_PAYMENT = 'payment'
TYPE_LOAN = 'loan'


def _as_datetime(value: str) -> str:
    if not value:
        return datetime.utcnow().isoformat()
    return value if 'T' in value else value + 'T00:00:00'


def next_req_no(item_type: str) -> str:
    prefix = 'P' if item_type == TYPE_PAYMENT else 'L'
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT req_no FROM requests WHERE item_type=? AND req_no IS NOT NULL ORDER BY req_no DESC LIMIT 1",
        (item_type,),
    )
    row = cur.fetchone()
    last = 0
    if row and row['req_no']:
        try:
            last = int(row['req_no'][1:])
        except ValueError:
            last = 0
    if item_type == TYPE_LOAN:
        cur.execute(
            "SELECT req_no FROM loans WHERE req_no IS NOT NULL ORDER BY req_no DESC LIMIT 1",
        )
        row = cur.fetchone()
        if row and row['req_no']:
            try:
                last = max(last, int(row['req_no'][1:]))
            except ValueError:
                pass
    conn.close()
    return f"{prefix}{last + 1:04d}"


def _fetch(cur, req_id):
    cur.execute('SELECT * FROM requests WHERE req_id=?', (req_id,))
    row = cur.fetchone()
    return row_to_dict(row) if row else None


def list_submitted_requests():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT r.*, m.name AS member_name FROM requests r LEFT JOIN members m ON r.member_id=m.member_id WHERE r.status='submitted' ORDER BY r.date_submitted",
    )
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def list_rejected_items():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT r.*, m.name AS member_name, rej.name AS rejected_by_name FROM requests r "
        "LEFT JOIN members m ON r.member_id=m.member_id "
        "LEFT JOIN members rej ON rej.member_id=r.rejected_by "
        "WHERE r.status='rejected' ORDER BY r.rejected_date DESC",
    )
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_request(req_id):
    conn = get_conn()
    cur = conn.cursor()
    req = _fetch(cur, req_id)
    conn.close()
    return req


def list_member_requests(member_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT r.*, ap.name AS approved_by_name, rej.name AS rejected_by_name FROM requests r "
        "LEFT JOIN members ap ON ap.member_id=r.approved_by "
        "LEFT JOIN members rej ON rej.member_id=r.rejected_by "
        "WHERE r.member_id=? ORDER BY r.date_submitted DESC",
        (member_id,),
    )
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
