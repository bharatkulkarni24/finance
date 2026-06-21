import sqlite3
from datetime import datetime, date
from typing import Optional, Union
from dataclasses import dataclass


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

DB_PATH = 'finance.db'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        joined_date TEXT NOT NULL,
        deposit_amount REAL DEFAULT 30000,
        is_admin INTEGER DEFAULT 0,
        dob TEXT,
        address TEXT,
        photo_url TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS contributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        date TEXT,
        amount REAL,
        type TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS dues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        due_date TEXT,
        amount REAL,
        paid INTEGER DEFAULT 0
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        principal REAL,
        outstanding REAL,
        rate_monthly REAL,
        term_months INTEGER,
        status TEXT,
        disbursed_date TEXT,
        last_accrual_date TEXT,
        reject_reason TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        loan_id INTEGER,
        date TEXT,
        amount REAL,
        interest_paid REAL,
        principal_paid REAL,
        late_fee_paid REAL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        timestamp TEXT,
        desc TEXT,
        debit_credit TEXT,
        amount REAL,
        source TEXT DEFAULT ''
    )
    ''')

    try:
        cur.execute("ALTER TABLE transactions ADD COLUMN source TEXT DEFAULT ''")
    except:
        pass

    cur.execute('''
    CREATE TABLE IF NOT EXISTS payment_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        date_submitted TEXT,
        txn_date TEXT,
        amount REAL,
        type TEXT,
        note TEXT,
        screenshot TEXT,
        status TEXT DEFAULT 'pending',
        approved_by INTEGER,
        approved_date TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS fd_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        start_date TEXT NOT NULL,
        term_months INTEGER NOT NULL,
        interest_rate REAL NOT NULL,
        status TEXT DEFAULT 'active',
        maturity_date TEXT,
        interest_earned REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT
    )
    ''')

    cur.execute('PRAGMA table_info(members)')
    existing = [row['name'] for row in cur.fetchall()]
    if 'is_admin' not in existing:
        cur.execute('ALTER TABLE members ADD COLUMN is_admin INTEGER DEFAULT 0')
    if 'dob' not in existing:
        cur.execute('ALTER TABLE members ADD COLUMN dob TEXT')
    if 'address' not in existing:
        cur.execute('ALTER TABLE members ADD COLUMN address TEXT')
    if 'photo_url' not in existing:
        cur.execute('ALTER TABLE members ADD COLUMN photo_url TEXT')
    # ensure txn_date exists in payment_requests
    cur.execute('PRAGMA table_info(payment_requests)')
    pr_cols = [row['name'] for row in cur.fetchall()]
    if 'txn_date' not in pr_cols:
        try:
            cur.execute('ALTER TABLE payment_requests ADD COLUMN txn_date TEXT')
        except Exception:
            pass
    if 'reject_reason' not in pr_cols:
        try:
            cur.execute('ALTER TABLE payment_requests ADD COLUMN reject_reason TEXT')
        except Exception:
            pass
    # ensure reject_reason exists in loans
    cur.execute('PRAGMA table_info(loans)')
    loan_cols = [row['name'] for row in cur.fetchall()]
    if 'reject_reason' not in loan_cols:
        try:
            cur.execute('ALTER TABLE loans ADD COLUMN reject_reason TEXT')
        except Exception:
            pass

    conn.commit()
    conn.close()


def seed_db():
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as c FROM members')
    if cur.fetchone()['c'] > 0:
        conn.close()
        return
    initial_members = [
        {'name': 'Govindrao Kulkarni', 'is_admin': 1},
        {'name': 'Nachiket Bhenki', 'is_admin': 0},
        {'name': 'Bhimbhatt Bhenki', 'is_admin': 0},
        {'name': 'Suchiket Bhenki', 'is_admin': 0},
        {'name': 'Rohan Kulkarni', 'is_admin': 0},
        {'name': 'Bharat Kulkarni', 'is_admin': 0},
        {'name': 'Bhargav Kulkarni', 'is_admin': 0},
        {'name': 'Sangeeta Kulkarni', 'is_admin': 0},
        {'name': 'Indiresh Joshi', 'is_admin': 0},
        {'name': 'Kiran Joshi', 'is_admin': 0},
        {'name': 'Indira Sarnad', 'is_admin': 0},
        {'name': 'Sanjeev Joshi', 'is_admin': 0}
    ]
    for member in initial_members:
        joined = datetime.utcnow().date().isoformat()
        cur.execute('INSERT INTO members (name, phone, joined_date, deposit_amount, is_admin, dob, address, photo_url) VALUES (?,?,?,?,?,?,?,?)', (member['name'], '', joined, 30000, member['is_admin'], '', '', ''))
        member_id = cur.lastrowid
        cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (member_id, joined, 30000, 'deposit'))
        generate_dues_for_member_internal(cur, member_id, datetime.utcnow().date())
    conn.commit()
    conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


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
    cur.execute('INSERT INTO members (name, phone, joined_date, deposit_amount, is_admin, dob, address, photo_url) VALUES (?,?,?,?,?,?,?,?)', (name, phone, joined, 30000, is_admin, dob, address, photo_url))
    member_id = cur.lastrowid
    cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (member_id, joined, 30000, 'deposit'))
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
        # return contributions in descending order (newest first)
        m['contributions'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        cur.execute('SELECT * FROM loans WHERE member_id=?', (member_id,))
        m['loans'] = [row_to_dict(r) for r in cur.fetchall()]
        cur.execute('SELECT * FROM payments WHERE member_id=? ORDER BY date', (member_id,))
        m['payments'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        cur.execute('SELECT * FROM dues WHERE member_id=? ORDER BY due_date', (member_id,))
        # dues newest first
        m['dues'] = [row_to_dict(r) for r in cur.fetchall()][::-1]
        cur.execute('SELECT * FROM payment_requests WHERE member_id=? ORDER BY date_submitted DESC', (member_id,))
        m['payment_requests'] = [row_to_dict(r) for r in cur.fetchall()]
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


def add_contribution(member_id: int, when: date, amount: float, type: str = 'share'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (member_id, when.isoformat(), amount, type))
    cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)', (member_id, datetime.utcnow().isoformat(), 'Share payment' if type == 'share' else 'Deposit', 'credit', amount))
    conn.commit()
    conn.close()


def create_loan(member_id: int, amount: float, term_months: int = 12) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    today = datetime.utcnow().date().isoformat()
    cur.execute('INSERT INTO loans (member_id, principal, outstanding, rate_monthly, term_months, status, disbursed_date, last_accrual_date) VALUES (?,?,?,?,?,?,?,?)', (member_id, amount, amount, 0.01, term_months, 'applied', None, today))
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
    cur.execute('UPDATE loans SET status=?, disbursed_date=?, last_accrual_date=? WHERE id=?', ('active', today, today, loan_id))
    conn.commit()
    conn.close()


def reject_loan(loan_id: int, reason: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('UPDATE loans SET status=?, reject_reason=?, last_accrual_date=? WHERE id=?', ('rejected', reason, now, loan_id))
    conn.commit()
    conn.close()


def compute_interest_accrued(loan: Union[dict, Loan], as_of_date: date) -> float:
    # support both dict-backed loans (from DB) and Loan dataclass instances (tests)
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
    # normalize last to date
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

    # persist update only when loan is dict and has an id
    if isinstance(loan, dict) and loan.get('id'):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('UPDATE loans SET outstanding=?, last_accrual_date=? WHERE id=?', (new_out, as_of_date.isoformat(), loan['id']))
        conn.commit()
        conn.close()
        _set(loan, 'outstanding', new_out)
        _set(loan, 'last_accrual_date', as_of_date.isoformat())
    else:
        # update in-memory Loan instance
        _set(loan, 'outstanding', new_out)
        _set(loan, 'last_accrual_date', as_of_date)

    return interest


def apply_payment_to_loan(loan: dict, amount: float) -> dict:
    to_apply = min(amount, loan['outstanding'])
    new_out = round(loan['outstanding'] - to_apply, 2)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, loan['id']))
    cur.execute('INSERT INTO payments (member_id, loan_id, date, amount, interest_paid, principal_paid, late_fee_paid) VALUES (?,?,?,?,?,?,?)', (loan['member_id'], loan['id'], datetime.utcnow().date().isoformat(), amount, 0.0, to_apply, 0.0))
    pay_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM payments WHERE id=?', (pay_id,))
    pay = row_to_dict(cur.fetchone())
    conn.close()
    loan['outstanding'] = new_out
    return pay


def pay_due(member_id: int, due_id: int, amount: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE dues SET paid=1 WHERE id=? AND member_id=?', (due_id, member_id))
    cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (member_id, datetime.utcnow().date().isoformat(), amount, 'share'))
    cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)', (member_id, datetime.utcnow().isoformat(), f'Due payment #{due_id}', 'credit', amount))
    conn.commit()
    cur.execute('SELECT * FROM dues WHERE id=?', (due_id,))
    due = row_to_dict(cur.fetchone())
    conn.close()
    return due


def get_member_statement(member_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    out = 'type,date,amount,details\n'
    cur.execute('SELECT * FROM contributions WHERE member_id=? ORDER BY date', (member_id,))
    for c in cur.fetchall():
        r = row_to_dict(c)
        out += f"{r['type']},{r['date']},{r['amount']},\n"
    cur.execute('SELECT * FROM payments WHERE member_id=? ORDER BY date', (member_id,))
    for p in cur.fetchall():
        r = row_to_dict(p)
        out += f"payment,{r['date']},{r['amount']},loan:{r['loan_id']};interest:{r['interest_paid']};principal:{r['principal_paid']}\n"
    conn.close()
    return out


def create_payment_request(member_id: int, amount: float, ptype: str, note: str = '', screenshot: str = '', txn_date: str = None) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO payment_requests (member_id, date_submitted, amount, type, note, screenshot, status, txn_date) VALUES (?,?,?,?,?,?,?,?)', (member_id, now, amount, ptype, note, screenshot, 'pending', txn_date))
    req_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (req_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def list_pending_requests():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pr.*, m.name as member_name FROM payment_requests pr LEFT JOIN members m ON pr.member_id=m.id WHERE pr.status='pending' ORDER BY pr.date_submitted")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def list_pending_loans():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT l.*, m.name as member_name FROM loans l LEFT JOIN members m ON l.member_id=m.id WHERE l.status='applied' ORDER BY l.last_accrual_date")
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
    cur.execute('UPDATE payment_requests SET status=?, approved_by=?, approved_date=? WHERE id=?', ('approved', approver_id, now, request_id))
    # use requested txn_date if provided, otherwise use approval date
    use_date = reqd.get('txn_date') or now[:10]
    if reqd['type'] == 'share':
        cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (reqd['member_id'], use_date, reqd['amount'], 'share'))
        cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)', (reqd['member_id'], now, 'Share payment (approved)', 'credit', reqd['amount']))
    else:
        # Find the member's active loan to apply the payment
        cur.execute('SELECT * FROM loans WHERE member_id=? AND status=?', (reqd['member_id'], 'active'))
        active_loan = cur.fetchone()
        loan_id = None
        if active_loan:
            loan_dict = row_to_dict(active_loan)
            to_apply = min(reqd['amount'], loan_dict['outstanding'])
            new_out = round(loan_dict['outstanding'] - to_apply, 2)
            cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, loan_dict['id']))
            loan_id = loan_dict['id']
            # compute interest before recording payment
            from datetime import date as dt_date
            compute_interest_accrued(loan_dict, dt_date.today())
        cur.execute('INSERT INTO payments (member_id, loan_id, date, amount, interest_paid, principal_paid, late_fee_paid) VALUES (?,?,?,?,?,?,?)', (reqd['member_id'], loan_id, use_date, reqd['amount'], 0.0, reqd['amount'], 0.0))
        cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)', (reqd['member_id'], now, 'Loan payment (approved)', 'credit', reqd['amount']))
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
    cur.execute('UPDATE payment_requests SET status=?, approved_by=?, approved_date=?, reject_reason=? WHERE id=?', ('rejected', approver_id, now, reason, request_id))
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
    # Only allow cancelling pending requests by the same member
    if r.get('member_id') != member_id or r.get('status') != 'pending':
        conn.close()
        return None
    now = datetime.utcnow().isoformat()
    cur.execute('UPDATE payment_requests SET status=?, approved_by=?, approved_date=?, reject_reason=? WHERE id=?', ('cancelled', member_id, now, 'cancelled_by_member', request_id))
    conn.commit()
    cur.execute('SELECT * FROM payment_requests WHERE id=?', (request_id,))
    out = row_to_dict(cur.fetchone())
    conn.close()
    return out


def admin_add_funds(amount: float, note: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)', (None, now, note or 'Admin add funds', 'credit', amount))
    conn.commit()
    cur.execute('SELECT * FROM transactions WHERE id=?', (cur.lastrowid,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def add_transaction(debit_credit: str, amount: float, desc: str = '', entry_date: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    ts = entry_date if entry_date else datetime.utcnow().isoformat()
    cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount, source) VALUES (?,?,?,?,?,?)',
                (None, ts, desc, debit_credit, amount, 'manual_ie'))
    conn.commit()
    cur.execute('SELECT * FROM transactions WHERE id=?', (cur.lastrowid,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def get_recent_transactions(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE source='manual_ie' ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_admin_stats():
    conn = get_conn()
    cur = conn.cursor()
    # breakdowns
    cur.execute("SELECT SUM(amount) FROM contributions WHERE type='deposit'")
    deposits_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(amount) FROM contributions WHERE type='share'")
    shares_total = cur.fetchone()[0] or 0.0
    # payments received (loan payments recorded in payments table)
    cur.execute("SELECT SUM(principal_paid) FROM payments")
    loan_principal_received = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(interest_paid) FROM payments")
    loan_interest_received = cur.fetchone()[0] or 0.0
    # other income = FD interest + manual income entries
    cur.execute("SELECT SUM(amount) FROM transactions WHERE debit_credit='credit' AND (desc LIKE 'FD Interest%' OR source='manual_ie')")
    others_total = cur.fetchone()[0] or 0.0
    # expenses from debit transactions
    cur.execute("SELECT SUM(amount) FROM transactions WHERE debit_credit='debit'")
    expenses_total = cur.fetchone()[0] or 0.0
    # recompute total_collected as sum of these categories minus expenses
    total_collected = deposits_total + shares_total + loan_principal_received + loan_interest_received + others_total - expenses_total
    # member count
    cur.execute("SELECT COUNT(*) FROM members")
    member_count = cur.fetchone()[0] or 0
    # loan metrics
    cur.execute("SELECT SUM(outstanding) FROM loans WHERE status='active'")
    total_outstanding = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(principal) FROM loans WHERE status='active'")
    total_lent = cur.fetchone()[0] or 0.0
    conn.close()
    hardlocked_fd = get_active_fd_total()
    cash_on_hand = total_collected - total_outstanding - hardlocked_fd
    available_to_lend = total_collected - total_lent - hardlocked_fd
    return {
        'total_collected': total_collected,
        'deposits_total': deposits_total,
        'shares_total': shares_total,
        'loan_principal_received': loan_principal_received,
        'loan_interest_received': loan_interest_received,
        'others_total': others_total,
        'expenses_total': expenses_total,
        'total_lent': total_lent,
        'total_outstanding': total_outstanding,
        'hardlocked_fd': hardlocked_fd,
        'cash_on_hand': cash_on_hand,
        'available_to_lend': available_to_lend,
        'member_count': member_count,
        'group_start_date': 'April 2025',
        'share_amount': 500,
        'one_time_amount': 25000,
        'total_period_months': 36,
        'loan_interest_rate': 1,
    }


def generate_dues_for_member_internal(cur, member_id: int, start_date: date, months: int = 36, monthly_amount: float = 500):
    d = start_date
    for i in range(months):
        try:
            due_date = d.replace(day=10)
        except ValueError:
            due_date = d
        cur.execute('INSERT INTO dues (member_id, due_date, amount, paid) VALUES (?,?,?,?)', (member_id, due_date.isoformat(), monthly_amount, 0))
        year = d.year + (d.month // 12)
        month = d.month % 12 + 1
        d = d.replace(year=year, month=month)


def add_fd(amount: float, start_date: str, term_months: int, interest_rate: float, notes: str = ''):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    sd = datetime.strptime(start_date, '%Y-%m-%d')
    import calendar
    months = term_months
    year = sd.year + (sd.month - 1 + months) // 12
    month = (sd.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(sd.day, last_day)
    maturity_date = f'{year:04d}-{month:02d}-{day:02d}'
    cur.execute('INSERT INTO fd_entries (amount, start_date, term_months, interest_rate, status, notes, created_at, maturity_date) VALUES (?,?,?,?,?,?,?,?)',
                (amount, start_date, term_months, interest_rate, 'active', notes, now, maturity_date))
    fd_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM fd_entries WHERE id=?', (fd_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def close_fd(fd_id: int, end_date: str, interest_earned: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE fd_entries SET status=?, interest_earned=?, maturity_date=? WHERE id=? AND status=?',
                ('matured', interest_earned, end_date, fd_id, 'active'))
    if cur.rowcount == 0:
        conn.close()
        return None
    cur.execute('SELECT * FROM fd_entries WHERE id=?', (fd_id,))
    fd = row_to_dict(cur.fetchone())
    if interest_earned > 0:
        cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
                    (None, datetime.utcnow().isoformat(), f'FD Interest - {fd["notes"] or fd_id}', 'credit', interest_earned))
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


def get_passbook_entries():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT ts, category, member_name, amount, debit_credit FROM (
        SELECT c.date || 'T12:00:00' as ts, 'Share' as category, m.name as member_name, c.amount as amount, 'credit' as debit_credit
        FROM contributions c JOIN members m ON m.id = c.member_id WHERE c.type='share'
        UNION ALL
        SELECT c.date || 'T12:00:00', 'Deposit', m.name, c.amount, 'credit'
        FROM contributions c JOIN members m ON m.id = c.member_id WHERE c.type='deposit'
        UNION ALL
        SELECT p.date || 'T12:00:00', 'Loan Payment', m.name, p.principal_paid + p.interest_paid + COALESCE(p.late_fee_paid,0), 'credit'
        FROM payments p JOIN loans l ON l.id = p.loan_id JOIN members m ON m.id = l.member_id
        UNION ALL
        SELECT l.disbursed_date || 'T12:00:00', 'Loan Disbursed', m.name, l.principal, 'debit'
        FROM loans l JOIN members m ON m.id = l.member_id WHERE l.disbursed_date IS NOT NULL AND l.status IN ('active','repaid')
        UNION ALL
        SELECT t.timestamp,
            CASE
                WHEN t.desc LIKE 'FD Interest%' THEN 'FD Interest'
                WHEN t.desc LIKE 'Share%' THEN 'Share'
                WHEN t.desc LIKE 'Deposit%' THEN 'Deposit'
                WHEN t.desc LIKE 'Loan%' AND t.debit_credit='credit' THEN 'Loan Payment'
                WHEN t.desc LIKE 'Due payment%' THEN 'Due Payment'
                WHEN t.source='manual_ie' AND t.debit_credit='credit' THEN 'Income'
                WHEN t.source='manual_ie' AND t.debit_credit='debit' THEN 'Expense'
                WHEN t.desc='Admin add funds' THEN 'Income'
                ELSE t.desc
            END as category,
            m.name as member_name, t.amount, t.debit_credit
        FROM transactions t LEFT JOIN members m ON m.id = t.member_id
        UNION ALL
        SELECT f.start_date || 'T12:00:00', 'FD Deposit', NULL, f.amount, 'debit'
        FROM fd_entries f
        UNION ALL
        SELECT f.maturity_date || 'T12:00:00', 'FD Matured', NULL, f.amount + COALESCE(f.interest_earned,0), 'credit'
        FROM fd_entries f WHERE f.status='matured'
    ) ORDER BY ts DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
