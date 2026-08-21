from datetime import datetime, date

from core.database import get_conn, row_to_dict
from core.models.loan import compute_interest_accrued
from core.models.requests import _as_datetime, next_req_no, _fetch


def create_payment_request(member_id: int, amount: float, note: str = '', screenshot: str = '', txn_date: str = None, fine: float = 0.0, share_amount: float = 0.0, loan_principal: float = 0.0, loan_interest: float = 0.0) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    req_no = next_req_no('payment')
    cur.execute(
        'INSERT INTO requests (req_no, member_id, item_type, date_submitted, pay_date, share_amount, loan_principal, loan_interest, fine, total_amount, note, screenshot, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (req_no, member_id, 'payment', now, _as_datetime(txn_date), share_amount, loan_principal, loan_interest, fine, amount, note, screenshot, 'submitted'),
    )
    req_id = cur.lastrowid
    conn.commit()
    req = _fetch(cur, req_id)
    conn.close()
    return req


def _active_loans(cur, member_id):
    cur.execute(
        "SELECT * FROM loans WHERE member_id=? AND status='active' ORDER BY loan_id ASC",
        (member_id,),
    )
    return [row_to_dict(r) for r in cur.fetchall()]


def _apply_loan_payment(cur, active_loans, loan_amt, interest_amt):
    """Apply loan principal and interest to active loans (oldest first).

    Returns (loan_id, remaining_loan_amt) where loan_id is the last loan
    that received principal (for ledger linkage).
    """
    loan_id = None
    remaining = loan_amt or 0
    for loan in active_loans:
        compute_interest_accrued(loan, date.today(), cur)
        if remaining > 0:
            to_apply = min(remaining, loan['outstanding'] or 0)
            new_out = round((loan['outstanding'] or 0) - to_apply, 2)
            if new_out <= 0:
                cur.execute(
                    'UPDATE loans SET outstanding=?, status=? WHERE loan_id=?',
                    (0, 'repaid', loan['loan_id']),
                )
            else:
                cur.execute(
                    'UPDATE loans SET outstanding=? WHERE loan_id=?',
                    (new_out, loan['loan_id']),
                )
            remaining -= to_apply
            loan_id = loan['loan_id']
    return loan_id


def approve_payment_request(request_id: int, approver_id: int):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    req = _fetch(cur, request_id)
    if not req or req['item_type'] != 'payment' or req['status'] != 'submitted':
        conn.close()
        return None
    cur.execute(
        'UPDATE requests SET status=?, approved_by=?, approved_date=? WHERE req_id=?',
        ('approved', approver_id, now, request_id),
    )
    use_date = _as_datetime(req.get('pay_date'))
    share_amt = req['share_amount'] or 0
    loan_amt = req['loan_principal'] or 0
    interest_amt = req['loan_interest'] or 0
    fine = req.get('fine', 0.0) or 0.0
    if not share_amt and not loan_amt and not interest_amt:
        share_amt = req.get('total_amount') or 0
    total = round((share_amt or 0) + (loan_amt or 0) + (interest_amt or 0) + (fine or 0), 2)

    loan_id = None
    if loan_amt > 0 or interest_amt > 0:
        active_loans = _active_loans(cur, req['member_id'])
        if active_loans:
            loan_id = _apply_loan_payment(cur, active_loans, loan_amt, interest_amt)

    cur.execute(
        'INSERT INTO member_ledger (member_id, pay_date, total_amount, share_amount, loan_principal, loan_interest, fine, request_id, loan_id, req_no, created_at, modified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
        (req['member_id'], use_date, total, share_amt, loan_amt, interest_amt, fine, request_id, loan_id, req['req_no'], now, now),
    )
    conn.commit()
    out = _fetch(cur, request_id)
    conn.close()
    return out


def reject_payment_request(request_id: int, approver_id: int, reason: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    req = _fetch(cur, request_id)
    if not req or req['item_type'] != 'payment' or req['status'] != 'submitted':
        conn.close()
        return None
    cur.execute(
        'UPDATE requests SET status=?, rejected_by=?, rejected_date=?, reject_reason=? WHERE req_id=?',
        ('rejected', approver_id, now, reason, request_id),
    )
    conn.commit()
    out = _fetch(cur, request_id)
    conn.close()
    return out


def admin_direct_entry(member_id: int, share_amount: float = 0, fine: float = 0,
                       loan_principal: float = 0, loan_interest: float = 0,
                       entry_date: str = None, note: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    use_date = _as_datetime(entry_date)

    loan_id = None
    if loan_principal > 0:
        active_loans = _active_loans(cur, member_id)
        if active_loans:
            loan_id = _apply_loan_payment(cur, active_loans, loan_principal, 0)

    total = round((share_amount or 0) + (loan_principal or 0) + (loan_interest or 0) + (fine or 0), 2)
    if total > 0:
        cur.execute(
            'INSERT INTO member_ledger (member_id, pay_date, total_amount, share_amount, loan_principal, loan_interest, fine, description, loan_id, created_at, modified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (member_id, use_date, total, share_amount, loan_principal, loan_interest, fine, note, loan_id, now, now),
        )
    conn.commit()
    conn.close()
    return {'status': 'ok'}
