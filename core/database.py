import sqlite3
from datetime import datetime, date

import core.config


def get_conn():
    conn = sqlite3.connect(core.config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        joined_date TEXT NOT NULL,
        deposit_amount REAL DEFAULT 25000,
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
    except Exception:
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
        approved_date TEXT,
        late_fee REAL DEFAULT 0
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

    cur.execute('PRAGMA table_info(fd_entries)')
    fd_cols = [row['name'] for row in cur.fetchall()]
    if 'investment_type' not in fd_cols:
        try:
            cur.execute("ALTER TABLE fd_entries ADD COLUMN investment_type TEXT DEFAULT 'one_time'")
        except Exception:
            pass
    if 'parent_id' not in fd_cols:
        try:
            cur.execute('ALTER TABLE fd_entries ADD COLUMN parent_id INTEGER DEFAULT NULL')
        except Exception:
            pass
    if 'installment_date' not in fd_cols:
        try:
            cur.execute('ALTER TABLE fd_entries ADD COLUMN installment_date TEXT DEFAULT NULL')
        except Exception:
            pass

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
    if 'late_fee' not in pr_cols:
        try:
            cur.execute("ALTER TABLE payment_requests ADD COLUMN late_fee REAL DEFAULT 0")
        except Exception:
            pass
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
        {'name': 'Sanjeev Joshi', 'is_admin': 0},
    ]
    from core.models.dues import generate_dues_for_member_internal
    for member in initial_members:
        joined = datetime.utcnow().date().isoformat()
        cur.execute(
            'INSERT INTO members (name, phone, joined_date, deposit_amount, is_admin, dob, address, photo_url) VALUES (?,?,?,?,?,?,?,?)',
            (member['name'], '', joined, 25000, member['is_admin'], '', '', ''),
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
    conn.close()
