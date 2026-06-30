from datetime import datetime, date, date as dt_date

from core.database import get_conn, row_to_dict
from core.models.loan import compute_interest_accrued


def add_contribution(member_id: int, when: date, amount: float, type: str = 'share'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)',
        (member_id, when.isoformat(), amount, type),
    )
    cur.execute(
        'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
        (member_id, datetime.utcnow().isoformat(), 'Share payment' if type == 'share' else 'Deposit', 'credit', amount),
    )
    conn.commit()
    conn.close()


def pay_due(member_id: int, due_id: int, amount: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE dues SET paid=1 WHERE id=? AND member_id=?', (due_id, member_id))
    cur.execute(
        'INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)',
        (member_id, datetime.utcnow().date().isoformat(), amount, 'share'),
    )
    cur.execute(
        'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
        (member_id, datetime.utcnow().isoformat(), f'Due payment #{due_id}', 'credit', amount),
    )
    conn.commit()
    cur.execute('SELECT * FROM dues WHERE id=?', (due_id,))
    due = row_to_dict(cur.fetchone())
    conn.close()
    return due


def create_payment_request(member_id: int, amount: float, ptype: str, note: str = '', screenshot: str = '', txn_date: str = None, late_fee: float = 0.0) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        'INSERT INTO payment_requests (member_id, date_submitted, amount, type, note, screenshot, status, txn_date, late_fee) VALUES (?,?,?,?,?,?,?,?,?)',
        (member_id, now, amount, ptype, note, screenshot, 'pending', txn_date, late_fee),
    )
    req_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (req_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def list_pending_requests():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT pr.*, m.name as member_name FROM payment_requests pr LEFT JOIN members m ON pr.member_id=m.id WHERE pr.status='pending' ORDER BY pr.date_submitted",
    )
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def approve_payment_request(request_id: int, approver_id: int):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    req = cur.fetchone()
    if not req:
        conn.close()
        return None
    reqd = row_to_dict(req)
    cur.execute(
        'UPDATE payment_requests SET status=?, approved_by=?, approved_date=? WHERE id=?',
        ('approved', approver_id, now, request_id),
    )
    use_date = reqd.get('txn_date') or now[:10]
    if reqd['type'] == 'share':
        share_amount = reqd['amount']
        late_fee = reqd.get('late_fee', 0.0) or 0.0
        total = share_amount + late_fee
        cur.execute(
            'INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)',
            (reqd['member_id'], use_date, share_amount, 'share'),
        )
        cur.execute(
            'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
            (reqd['member_id'], now, 'Share payment (approved)', 'credit', share_amount),
        )
        if late_fee > 0:
            cur.execute(
                'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
                (reqd['member_id'], use_date + 'T12:00:00', 'Late fee', 'credit', late_fee),
            )
    else:
        cur.execute('SELECT * FROM loans WHERE member_id=? AND status=?', (reqd['member_id'], 'active'))
        active_loan = cur.fetchone()
        loan_id = None
        if active_loan:
            loan_dict = row_to_dict(active_loan)
            compute_interest_accrued(loan_dict, dt_date.today(), cur)
            to_apply = min(reqd['amount'], loan_dict['outstanding'])
            new_out = round(loan_dict['outstanding'] - to_apply, 2)
            cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, loan_dict['id']))
            loan_id = loan_dict['id']
        cur.execute(
            'INSERT INTO payments (member_id, loan_id, date, amount, interest_paid, principal_paid, late_fee_paid) VALUES (?,?,?,?,?,?,?)',
            (reqd['member_id'], loan_id, use_date, reqd['amount'], 0.0, reqd['amount'], 0.0),
        )
        cur.execute(
            'INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
            (reqd['member_id'], now, 'Loan payment (approved)', 'credit', reqd['amount']),
        )
    conn.commit()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    out = row_to_dict(cur.fetchone())
    conn.close()
    return out


def reject_payment_request(request_id: int, approver_id: int, reason: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    req = cur.fetchone()
    if not req:
        conn.close()
        return None
    cur.execute(
        'UPDATE payment_requests SET status=?, approved_by=?, approved_date=?, reject_reason=? WHERE id=?',
        ('rejected', approver_id, now, reason, request_id),
    )
    conn.commit()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    out = row_to_dict(cur.fetchone())
    conn.close()
    return out


def cancel_payment_request(request_id: int, member_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    req = cur.fetchone()
    if not req:
        conn.close()
        return None
    r = row_to_dict(req)
    if r.get('member_id') != member_id or r.get('status') != 'pending':
        conn.close()
        return None
    now = datetime.utcnow().isoformat()
    cur.execute(
        'UPDATE payment_requests SET status=?, approved_by=?, approved_date=?, reject_reason=? WHERE id=?',
        ('cancelled', member_id, now, 'cancelled_by_member', request_id),
    )
    conn.commit()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    out = row_to_dict(cur.fetchone())
    conn.close()
    return out
