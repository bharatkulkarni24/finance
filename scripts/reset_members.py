import sys
import os
from datetime import datetime

# Ensure project root is on sys.path so we can import models when running from scripts/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models import get_conn, generate_dues_for_member_internal

def reset_members():
    names = [
        'Govindrao Kulkarni',
        'Nachiket Bhenki',
        'Bhimbhatt Bhenki',
        'Suchiket Bhenki',
        'Rohan Kulkarni',
        'Bharat Kulkarni',
        'Bhargav Kulkarni',
        'Sangeeta Kulkarni',
        'Indiresh Joshi',
        'Kiran Joshi',
        'Indira Sarnad',
        'Sanjeev Joshi'
    ]

    conn = get_conn()
    cur = conn.cursor()

    # Clear existing members and related simple tables (contributions/dues/payments/loans/transactions)
    cur.execute('DELETE FROM contributions')
    cur.execute('DELETE FROM dues')
    cur.execute('DELETE FROM payments')
    cur.execute('DELETE FROM loans')
    cur.execute('DELETE FROM transactions')
    cur.execute('DELETE FROM members')

    joined = datetime.utcnow().date().isoformat()
    # Inspect existing member columns so this script works on older DBs
    cur.execute("PRAGMA table_info(members)")
    cols = [r[1] for r in cur.fetchall()]
    wanted = ['name', 'phone', 'joined_date', 'deposit_amount', 'is_admin', 'dob', 'address', 'photo_url']
    for i, n in enumerate(names):
        vals = []
        is_admin = 1 if i == 0 else 0
        for c in wanted:
            if c == 'name':
                vals.append(n)
            elif c == 'phone':
                vals.append('')
            elif c == 'joined_date':
                vals.append(joined)
            elif c == 'deposit_amount':
                vals.append(30000)
            elif c == 'is_admin':
                if 'is_admin' in cols:
                    vals.append(is_admin)
            elif c in ('dob', 'address', 'photo_url'):
                if c in cols:
                    vals.append('')

        # Build insert statement for available columns
        insert_cols = [c for c in wanted if (c in cols) or c in ('name','phone','joined_date','deposit_amount')]
        placeholders = ','.join('?' for _ in insert_cols)
        sql = f"INSERT INTO members ({','.join(insert_cols)}) VALUES ({placeholders})"
        cur.execute(sql, tuple(vals[:len(insert_cols)]))
        member_id = cur.lastrowid
        cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (member_id, joined, 30000, 'deposit'))
        generate_dues_for_member_internal(cur, member_id, datetime.utcnow().date())

    conn.commit()
    conn.close()
    print(f'Replaced members with {len(names)} entries (first is admin).')

if __name__ == '__main__':
    reset_members()
