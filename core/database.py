import sqlite3

import core.config


def get_conn():
    conn = sqlite3.connect(core.config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def strip_sensitive(m: dict) -> dict:
    m.pop('password', None)
    return m


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        joined_date TEXT NOT NULL,
        deposit_amount REAL DEFAULT 25000,
        is_admin INTEGER DEFAULT 0,
        dob TEXT,
        address TEXT,
        photo_url TEXT,
        password TEXT DEFAULT ''
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        principal REAL,
        outstanding REAL,
        rate_monthly REAL,
        term_months INTEGER,
        status TEXT,
        disbursed_date TEXT,
        last_accrual_date TEXT,
        request_id INTEGER,
        req_no TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS member_ledger (
        pay_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        pay_date TEXT,
        total_amount REAL DEFAULT 0,
        share_amount REAL DEFAULT 0,
        loan_principal REAL DEFAULT 0,
        loan_interest REAL DEFAULT 0,
        late_fee REAL DEFAULT 0,
        description TEXT DEFAULT '',
        request_id INTEGER,
        loan_id INTEGER,
        req_no TEXT,
        created_at TEXT,
        modified_at TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS group_ledger (
        trn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        timestamp TEXT,
        description TEXT,
        debit_credit TEXT,
        amount REAL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        req_id INTEGER PRIMARY KEY AUTOINCREMENT,
        req_no TEXT,
        member_id INTEGER,
        item_type TEXT,
        date_submitted TEXT,
        pay_date TEXT,
        share_amount REAL DEFAULT 0,
        loan_payment REAL DEFAULT 0,
        interest_amount REAL DEFAULT 0,
        late_fee REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        note TEXT DEFAULT '',
        screenshot TEXT DEFAULT '',
        loan_principal REAL DEFAULT 0,
        loan_term_months INTEGER DEFAULT 0,
        status TEXT DEFAULT 'submitted',
        approved_by INTEGER,
        approved_date TEXT,
        rejected_by INTEGER,
        rejected_date TEXT,
        reject_reason TEXT DEFAULT ''
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pay_id INTEGER,
        action TEXT,
        changed_by INTEGER,
        changed_at TEXT,
        old_share_amount REAL,
        new_share_amount REAL,
        old_late_fee REAL,
        new_late_fee REAL,
        old_loan_interest REAL,
        new_loan_interest REAL,
        old_loan_principal REAL,
        new_loan_principal REAL,
        old_total_amount REAL,
        new_total_amount REAL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS fixed_deposits (
        fd_id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        start_date TEXT NOT NULL,
        term_months INTEGER NOT NULL,
        interest_rate REAL NOT NULL,
        status TEXT DEFAULT 'active',
        maturity_date TEXT,
        interest_earned REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT,
        investment_type TEXT DEFAULT 'one_time',
        parent_id INTEGER DEFAULT NULL,
        installment_date TEXT DEFAULT NULL
    )
    ''')

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
        {'member_id': 1001, 'name': 'Govindrao Kulkarni', 'is_admin': 1},
        {'member_id': 1002, 'name': 'Bharat Kulkarni', 'is_admin': 1},
    ]
    for member in initial_members:
        joined = '2025-04-01'
        cur.execute(
            'INSERT INTO members (member_id, name, phone, joined_date, deposit_amount, is_admin, dob, address, photo_url) VALUES (?,?,?,?,?,?,?,?,?)',
            (member['member_id'], member['name'], '', joined, 25000, member['is_admin'], '', '', ''),
        )
        cur.execute(
            'INSERT INTO member_ledger (member_id, pay_date, total_amount, created_at, modified_at) VALUES (?,?,?,?,?)',
            (member['member_id'], joined + 'T12:00:00', 25000, joined + 'T12:00:00', joined + 'T12:00:00'),
        )
    conn.commit()
    conn.close()
