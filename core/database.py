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


# Canonical column set for each table. Used by _ensure_columns() to upgrade an
# existing database when a future version adds a column (CREATE TABLE only adds
# missing tables, not missing columns). When adding a new column in a future
# release, add it here AND to the CREATE TABLE statement above/below so fresh
# databases and existing databases stay in sync.
_COLUMN_DEFS = {
    'members': {
        'member_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'name': 'TEXT NOT NULL',
        'phone': 'TEXT',
        'joined_date': 'TEXT NOT NULL',
        'entry_deposit_amount': 'REAL DEFAULT 25000',
        'is_admin': 'INTEGER DEFAULT 0',
        'dob': 'TEXT',
        'address': 'TEXT',
        'photo_url': 'TEXT',
        'password': "TEXT DEFAULT ''",
    },
    'loans': {
        'loan_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'member_id': 'INTEGER',
        'loan_principal': 'REAL',
        'outstanding': 'REAL',
        'rate_monthly': 'REAL',
        'term_months': 'INTEGER',
        'status': 'TEXT',
        'disbursed_date': 'TEXT',
        'last_accrual_date': 'TEXT',
        'request_id': 'INTEGER',
        'req_no': 'TEXT',
    },
    'member_ledger': {
        'pay_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'member_id': 'INTEGER',
        'pay_date': 'TEXT',
        'total_amount': 'REAL DEFAULT 0',
        'share_amount': 'REAL DEFAULT 0',
        'loan_principal': 'REAL DEFAULT 0',
        'loan_interest': 'REAL DEFAULT 0',
        'fine': 'REAL DEFAULT 0',
        'description': "TEXT DEFAULT ''",
        'request_id': 'INTEGER',
        'loan_id': 'INTEGER',
        'req_no': 'TEXT',
        'created_at': 'TEXT',
        'modified_at': 'TEXT',
    },
    'group_ledger': {
        'trn_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'member_id': 'INTEGER',
        'timestamp': 'TEXT',
        'description': 'TEXT',
        'debit_credit': 'TEXT',
        'amount': 'REAL',
    },
    'requests': {
        'req_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'req_no': 'TEXT',
        'member_id': 'INTEGER',
        'item_type': 'TEXT',
        'date_submitted': 'TEXT',
        'pay_date': 'TEXT',
        'share_amount': 'REAL DEFAULT 0',
        'loan_principal': 'REAL DEFAULT 0',
        'loan_interest': 'REAL DEFAULT 0',
        'fine': 'REAL DEFAULT 0',
        'total_amount': 'REAL DEFAULT 0',
        'note': "TEXT DEFAULT ''",
        'screenshot': "TEXT DEFAULT ''",
        'loan_amount': 'REAL DEFAULT 0',
        'loan_term_months': 'INTEGER DEFAULT 0',
        'status': "TEXT DEFAULT 'submitted'",
        'approved_by': 'INTEGER',
        'approved_date': 'TEXT',
        'rejected_by': 'INTEGER',
        'rejected_date': 'TEXT',
        'reject_reason': "TEXT DEFAULT ''",
    },
    'audit_log': {
        'audit_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'pay_id': 'INTEGER',
        'action': 'TEXT',
        'changed_by': 'INTEGER',
        'changed_at': 'TEXT',
        'old_share_amount': 'REAL',
        'new_share_amount': 'REAL',
        'old_fine': 'REAL',
        'new_fine': 'REAL',
        'old_loan_interest': 'REAL',
        'new_loan_interest': 'REAL',
        'old_loan_principal': 'REAL',
        'new_loan_principal': 'REAL',
        'old_total_amount': 'REAL',
        'new_total_amount': 'REAL',
    },
    'fixed_deposits': {
        'fd_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'amount': 'REAL NOT NULL',
        'start_date': 'TEXT NOT NULL',
        'term_months': 'INTEGER NOT NULL',
        'interest_rate': 'REAL NOT NULL',
        'status': "TEXT DEFAULT 'active'",
        'maturity_date': 'TEXT',
        'interest_earned': 'REAL DEFAULT 0',
        'notes': 'TEXT',
        'created_at': 'TEXT',
        'investment_type': "TEXT DEFAULT 'one_time'",
        'parent_id': 'INTEGER DEFAULT NULL',
        'installment_date': 'TEXT DEFAULT NULL',
    },
}


def _ensure_columns(cur) -> None:
    """Add any columns a newer version of the app expects but this DB lacks.

    Additive-only: existing rows and data are never touched. Column and table
    names come from the hardcoded _COLUMN_DEFS map, never from user input.
    """
    for table, columns in _COLUMN_DEFS.items():
        existing = {row['name'] for row in cur.execute(f'PRAGMA table_info({table})')}
        for col, decl in columns.items():
            if col not in existing:
                cur.execute(f'ALTER TABLE {table} ADD COLUMN {col} {decl}')


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        joined_date TEXT NOT NULL,
        entry_deposit_amount REAL DEFAULT 25000,
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
        loan_principal REAL,
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
        fine REAL DEFAULT 0,
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
        loan_principal REAL DEFAULT 0,
        loan_interest REAL DEFAULT 0,
        fine REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        note TEXT DEFAULT '',
        screenshot TEXT DEFAULT '',
        loan_amount REAL DEFAULT 0,
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
        old_fine REAL,
        new_fine REAL,
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

    # Migration: entry deposits live on members.entry_deposit_amount, not member_ledger.
    # Legacy deposit rows (rows with no split amounts) are deleted below, after the
    # split-column renames, so they are not counted twice.

    # Migration: rename members.deposit_amount to members.entry_deposit_amount for
    # a consistent user-facing name ("Entry Deposit"). Handles all cases:
    # - old column only  -> rename it
    # - both columns     -> an earlier run auto-added the new column before this
    #   rename existed; copy the real values over and drop the old column.
    cur.execute("SELECT name FROM pragma_table_info('members')")
    member_cols = {r['name'] for r in cur.fetchall()}
    if 'deposit_amount' in member_cols:
        if 'entry_deposit_amount' not in member_cols:
            cur.execute('ALTER TABLE members RENAME COLUMN deposit_amount TO entry_deposit_amount')
        else:
            cur.execute('UPDATE members SET entry_deposit_amount = deposit_amount')
            cur.execute('ALTER TABLE members DROP COLUMN deposit_amount')

    # Migration: requests.loan_payment held the loan principal component of a
    # payment request; requests.loan_principal held a loan request's amount.
    # Rename so "Loan Principal" is the payment principal everywhere and the
    # loan request amount gets the unambiguous "Loan Amount" name.
    cur.execute("SELECT name FROM pragma_table_info('requests')")
    req_cols = {r['name'] for r in cur.fetchall()}
    if 'loan_payment' in req_cols and 'loan_principal' in req_cols:
        if 'loan_amount' in req_cols:
            cur.execute('UPDATE requests SET loan_amount = loan_principal')
            cur.execute('ALTER TABLE requests DROP COLUMN loan_principal')
            cur.execute('ALTER TABLE requests RENAME COLUMN loan_payment TO loan_principal')
        else:
            cur.execute('ALTER TABLE requests RENAME COLUMN loan_payment TO loan_principal_tmp')
            cur.execute('ALTER TABLE requests RENAME COLUMN loan_principal TO loan_amount')
            cur.execute('ALTER TABLE requests RENAME COLUMN loan_principal_tmp TO loan_principal')

    # Migration: rename "Fine" columns from the old "late_fee" name.
    # member_ledger.late_fee -> fine, requests.late_fee -> fine,
    # audit_log.old_late_fee/new_late_fee -> old_fine/new_fine.
    # Handles all cases: old-only (rename), old+new (copy data, drop old),
    # new-only (nothing to do).
    for table, old, new in (
        ('member_ledger', 'late_fee', 'fine'),
        ('requests', 'late_fee', 'fine'),
        ('audit_log', 'old_late_fee', 'old_fine'),
        ('audit_log', 'new_late_fee', 'new_fine'),
    ):
        cur.execute(f"SELECT name FROM pragma_table_info('{table}')")
        cols = {r['name'] for r in cur.fetchall()}
        if old not in cols:
            continue
        if new not in cols:
            cur.execute(f'ALTER TABLE {table} RENAME COLUMN {old} TO {new}')
        else:
            cur.execute(f'UPDATE {table} SET {new} = {old} WHERE {new} IS NULL OR {new} = 0')
            cur.execute(f'ALTER TABLE {table} DROP COLUMN {old}')

    # Migration: rename requests.interest_amount to loan_interest so "Loan Interest"
    # has one name (member_ledger already uses loan_interest). Handles old-only and
    # old+new the same way as the "Fine" migration above.
    cur.execute("SELECT name FROM pragma_table_info('requests')")
    req_cols = {r['name'] for r in cur.fetchall()}
    if 'interest_amount' in req_cols:
        if 'loan_interest' not in req_cols:
            cur.execute('ALTER TABLE requests RENAME COLUMN interest_amount TO loan_interest')
        else:
            cur.execute('UPDATE requests SET loan_interest = interest_amount WHERE loan_interest IS NULL OR loan_interest = 0')
            cur.execute('ALTER TABLE requests DROP COLUMN interest_amount')

    # Migration: rename loans.principal to loan_principal so "Loan Principal" has
    # one name (member_ledger and requests already use loan_principal).
    cur.execute("SELECT name FROM pragma_table_info('loans')")
    loan_cols = {r['name'] for r in cur.fetchall()}
    if 'principal' in loan_cols:
        if 'loan_principal' not in loan_cols:
            cur.execute('ALTER TABLE loans RENAME COLUMN principal TO loan_principal')
        else:
            cur.execute('UPDATE loans SET loan_principal = principal WHERE loan_principal IS NULL OR loan_principal = 0')
            cur.execute('ALTER TABLE loans DROP COLUMN principal')

    # Remove legacy deposit rows (rows with no split amounts) so they are not counted
    # twice now that entry deposits live on members.entry_deposit_amount.
    cur.execute(
        'DELETE FROM member_ledger WHERE share_amount=0 AND loan_principal=0 AND loan_interest=0 AND fine=0'
    )

    _ensure_columns(cur)

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
            'INSERT INTO members (member_id, name, phone, joined_date, entry_deposit_amount, is_admin, dob, address, photo_url) VALUES (?,?,?,?,?,?,?,?,?)',
            (member['member_id'], member['name'], '', joined, 25000, member['is_admin'], '', '', ''),
        )
    conn.commit()
    conn.close()
