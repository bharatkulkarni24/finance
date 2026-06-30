from datetime import datetime, date
from typing import Optional, Union
from dataclasses import dataclass

from core.database import get_conn, row_to_dict


@dataclass
class Loan:
    id: Optional[int] = None
    member_id: Optional[int] = None
    principal: float = 0.0
    outstanding: float = 0.0
    rate_monthly: float = 0.01
    term_months: int = 12
    status: str = 'applied'
    disbursed_date: Optional[Union[str, date]] = None
    last_accrual_date: Optional[Union[str, date]] = None


def create_loan(member_id: int, amount: float, term_months: int = 12) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    today = datetime.utcnow().date().isoformat()
    cur.execute(
        'INSERT INTO loans (member_id, principal, outstanding, rate_monthly, term_months, status, disbursed_date, last_accrual_date) VALUES (?,?,?,?,?,?,?,?)',
        (member_id, amount, amount, 0.01, term_months, 'applied', None, today),
    )
    loan_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM loans WHERE id=?', (loan_id,))
    loan = row_to_dict(cur.fetchone())
    conn.close()
    return loan


def get_loan(loan_id: int) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM loans WHERE id=?', (loan_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def approve_loan(loan_id: int):
    conn = get_conn()
    cur = conn.cursor()
    today = datetime.utcnow().date().isoformat()
    cur.execute(
        'UPDATE loans SET status=?, disbursed_date=?, last_accrual_date=? WHERE id=?',
        ('active', today, today, loan_id),
    )
    conn.commit()
    conn.close()


def reject_loan(loan_id: int, reason: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        'UPDATE loans SET status=?, reject_reason=?, last_accrual_date=? WHERE id=?',
        ('rejected', reason, now, loan_id),
    )
    conn.commit()
    conn.close()


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

    if isinstance(loan, dict) and loan.get('id'):
        if cur is None:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                'UPDATE loans SET outstanding=?, last_accrual_date=? WHERE id=?',
                (new_out, as_of_date.isoformat(), loan['id']),
            )
            conn.commit()
            conn.close()
        else:
            cur.execute(
                'UPDATE loans SET outstanding=?, last_accrual_date=? WHERE id=?',
                (new_out, as_of_date.isoformat(), loan['id']),
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
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, loan['id']))
    cur.execute(
        'INSERT INTO payments (member_id, loan_id, date, amount, interest_paid, principal_paid, late_fee_paid) VALUES (?,?,?,?,?,?,?)',
        (loan['member_id'], loan['id'], datetime.utcnow().date().isoformat(), amount, 0.0, to_apply, 0.0),
    )
    pay_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM payments WHERE id=?', (pay_id,))
    pay = row_to_dict(cur.fetchone())
    conn.close()
    loan['outstanding'] = new_out
    return pay


def list_pending_loans():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT l.*, m.name as member_name FROM loans l LEFT JOIN members m ON l.member_id=m.id WHERE l.status='applied' ORDER BY l.last_accrual_date",
    )
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
