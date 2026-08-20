from datetime import datetime, date
from typing import Optional, Union
from dataclasses import dataclass

from core.database import get_conn, row_to_dict
from core.models.requests import next_req_no, _fetch


def _as_datetime(value: str) -> str:
    if not value:
        return datetime.utcnow().isoformat()
    return value if 'T' in value else value + 'T00:00:00'


@dataclass
class Loan:
    loan_id: Optional[int] = None
    member_id: Optional[int] = None
    loan_principal: float = 0.0
    outstanding: float = 0.0
    rate_monthly: float = 0.01
    term_months: int = 12
    status: str = 'active'
    disbursed_date: Optional[Union[str, date]] = None
    last_accrual_date: Optional[Union[str, date]] = None


def create_loan(member_id: int, amount: float, term_months: int = 12) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    req_no = next_req_no('loan')
    cur.execute(
        'INSERT INTO requests (req_no, member_id, item_type, date_submitted, loan_amount, loan_term_months, status) VALUES (?,?,?,?,?,?,?)',
        (req_no, member_id, 'loan', now, amount, term_months, 'submitted'),
    )
    req_id = cur.lastrowid
    conn.commit()
    req = _fetch(cur, req_id)
    conn.close()
    return req


def get_loan(loan_id: int) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM loans WHERE loan_id=?', (loan_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def approve_loan(req_id: int, approver_id: int = 0):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    today = date.today().isoformat()
    req = _fetch(cur, req_id)
    if not req or req['item_type'] != 'loan' or req['status'] != 'submitted':
        conn.close()
        return None
    cur.execute(
        'UPDATE requests SET status=?, approved_by=?, approved_date=? WHERE req_id=?',
        ('approved', approver_id, now, req_id),
    )
    cur.execute(
        'INSERT INTO loans (member_id, loan_principal, outstanding, rate_monthly, term_months, status, disbursed_date, last_accrual_date, request_id, req_no) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (req['member_id'], req['loan_amount'], req['loan_amount'], 0.01, req['loan_term_months'], 'active', today, today, req_id, req['req_no']),
    )
    loan_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM loans WHERE loan_id=?', (loan_id,))
    loan = row_to_dict(cur.fetchone())
    conn.close()
    return loan


def reject_loan(req_id: int, approver_id: int = 0, reason: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    req = _fetch(cur, req_id)
    if not req or req['item_type'] != 'loan' or req['status'] != 'submitted':
        conn.close()
        return None
    cur.execute(
        'UPDATE requests SET status=?, rejected_by=?, rejected_date=?, reject_reason=? WHERE req_id=?',
        ('rejected', approver_id, now, reason, req_id),
    )
    conn.commit()
    out = _fetch(cur, req_id)
    conn.close()
    return out


def compute_interest_accrued(loan: Union[dict, Loan], as_of_date: date, cur=None) -> float:
    def _get(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _set(obj, key, value):
        if isinstance(obj, dict):
            obj[key] = value
        else:
            setattr(obj, key, value)

    status = _get(loan, 'status')
    disb = _get(loan, 'disbursed_date')
    if status != 'active' or not disb:
        return 0.0
    last = _get(loan, 'last_accrual_date') or disb
    if isinstance(last, str):
        last_date = date.fromisoformat(last)
    elif isinstance(last, date):
        last_date = last
    else:
        return 0.0
    days = (as_of_date - last_date).days
    if days <= 0:
        return 0.0
    outstanding = _get(loan, 'outstanding') or 0.0
    rate = _get(loan, 'rate_monthly') or 0.0
    interest = outstanding * rate * (days / 30.0)
    new_out = round(outstanding + interest, 2)

    loan_id = _get(loan, 'loan_id')
    if isinstance(loan, dict) and loan_id:
        if cur is None:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                'UPDATE loans SET outstanding=?, last_accrual_date=? WHERE loan_id=?',
                (new_out, as_of_date.isoformat(), loan_id),
            )
            conn.commit()
            conn.close()
        else:
            cur.execute(
                'UPDATE loans SET outstanding=?, last_accrual_date=? WHERE loan_id=?',
                (new_out, as_of_date.isoformat(), loan_id),
            )
        _set(loan, 'outstanding', new_out)
        _set(loan, 'last_accrual_date', as_of_date.isoformat())
    else:
        _set(loan, 'outstanding', new_out)
        _set(loan, 'last_accrual_date', as_of_date)

    return interest


def apply_payment_to_loan(loan: dict, amount: float) -> dict:
    to_apply = min(amount, loan['outstanding'])
    new_out = round(loan['outstanding'] - to_apply, 2)
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE loans SET outstanding=? WHERE loan_id=?', (new_out, loan['loan_id']))
    cur.execute(
        'INSERT INTO member_ledger (member_id, pay_date, total_amount, loan_principal, loan_id, created_at, modified_at) VALUES (?,?,?,?,?,?,?)',
        (loan['member_id'], _as_datetime(date.today().isoformat()), amount, to_apply, loan['loan_id'], now, now),
    )
    pay_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM member_ledger WHERE pay_id=?', (pay_id,))
    pay = row_to_dict(cur.fetchone())
    conn.close()
    loan['outstanding'] = new_out
    return pay
