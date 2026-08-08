from core.database import get_conn

VALID_KINDS = ('share', 'deposit', 'loan_payment', 'income', 'expense', 'late_fee')


def _match_contribution_txn(cur, member_id, amount, ctype):
    if ctype == 'share':
        cur.execute(
            "SELECT id FROM transactions WHERE member_id=? AND amount=? AND (desc LIKE 'Share%' OR desc LIKE 'Due payment%') ORDER BY id DESC LIMIT 1",
            (member_id, amount),
        )
    else:
        cur.execute(
            "SELECT id FROM transactions WHERE member_id=? AND amount=? AND (desc LIKE '%Deposit%' OR desc LIKE '%deposit%') ORDER BY id DESC LIMIT 1",
            (member_id, amount),
        )
    row = cur.fetchone()
    return row['id'] if row else None


def _match_payment_txn(cur, member_id, amount):
    cur.execute(
        "SELECT id FROM transactions WHERE member_id=? AND amount=? AND (desc LIKE 'Loan%' OR desc LIKE 'Due payment%') ORDER BY id DESC LIMIT 1",
        (member_id, amount),
    )
    row = cur.fetchone()
    return row['id'] if row else None


def list_entries(etype='all', member_id=None, q='', limit=200):
    conn = get_conn()
    cur = conn.cursor()
    out = []
    like = '%' + (q or '') + '%'

    if etype in ('all', 'share', 'deposit'):
        sql = ("SELECT c.id, c.member_id, m.name AS member_name, c.date, c.amount, c.type "
               "FROM contributions c LEFT JOIN members m ON m.id=c.member_id "
               "WHERE c.type IN ('share','deposit')")
        params = []
        if etype in ('share', 'deposit'):
            sql += ' AND c.type=?'
            params.append(etype)
        if member_id:
            sql += ' AND c.member_id=?'
            params.append(member_id)
        if q:
            sql += ' AND (m.name LIKE ?)'
            params.append(like)
        sql += ' ORDER BY c.date DESC, c.id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, params)
        for r in cur.fetchall():
            d = dict(r)
            out.append({
                'id': 'c' + str(d['id']),
                'kind': d['type'],
                'member_id': d['member_id'],
                'member_name': d['member_name'] or '(No member)',
                'date': (d['date'] or '')[:10],
                'amount': d['amount'],
                'principal': None,
                'interest': None,
                'fine': None,
                'contribution_id': d['id'],
                'transaction_id': _match_contribution_txn(cur, d['member_id'], d['amount'], d['type']),
                'payment_id': None,
            })

    if etype in ('all', 'loan_payment'):
        sql = ("SELECT p.id, p.member_id, m.name AS member_name, p.date, p.amount, "
               "p.interest_paid, p.principal_paid, COALESCE(p.late_fee_paid,0) AS late_fee_paid "
               "FROM payments p LEFT JOIN members m ON m.id=p.member_id WHERE 1=1")
        params = []
        if member_id:
            sql += ' AND p.member_id=?'
            params.append(member_id)
        if q:
            sql += ' AND (m.name LIKE ?)'
            params.append(like)
        sql += ' ORDER BY p.date DESC, p.id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, params)
        for r in cur.fetchall():
            d = dict(r)
            out.append({
                'id': 'p' + str(d['id']),
                'kind': 'loan_payment',
                'member_id': d['member_id'],
                'member_name': d['member_name'] or '(No member)',
                'date': (d['date'] or '')[:10],
                'amount': d['amount'],
                'principal': d['principal_paid'],
                'interest': d['interest_paid'],
                'fine': d['late_fee_paid'],
                'contribution_id': None,
                'transaction_id': _match_payment_txn(cur, d['member_id'], d['amount']),
                'payment_id': d['id'],
            })

    if etype in ('all', 'income', 'expense', 'late_fee'):
        sql = ("SELECT t.id, t.member_id, m.name AS member_name, t.timestamp, t.desc, t.debit_credit, t.amount, t.source "
               "FROM transactions t LEFT JOIN members m ON m.id=t.member_id "
               "WHERE (t.source='manual_ie' OR t.desc='Late fee' OR t.desc LIKE 'FD Interest%')")
        params = []
        if etype == 'income':
            sql += " AND t.debit_credit='credit'"
        elif etype == 'expense':
            sql += " AND t.source='manual_ie' AND t.debit_credit='debit'"
        elif etype == 'late_fee':
            sql += " AND t.desc='Late fee'"
        if member_id:
            sql += ' AND t.member_id=?'
            params.append(member_id)
        if q:
            sql += ' AND (m.name LIKE ? OR t.desc LIKE ?)'
            params.append(like)
            params.append(like)
        sql += ' ORDER BY t.timestamp DESC, t.id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, params)
        for r in cur.fetchall():
            d = dict(r)
            if d['desc'] == 'Late fee':
                kind = 'late_fee'
            elif d['debit_credit'] == 'credit':
                kind = 'income'
            else:
                kind = 'expense'
            out.append({
                'id': 't' + str(d['id']),
                'kind': kind,
                'member_id': d['member_id'],
                'member_name': d['member_name'] or '(No member)',
                'date': (d['timestamp'] or '')[:10],
                'amount': d['amount'],
                'desc': d['desc'],
                'debit_credit': d['debit_credit'],
                'principal': None,
                'interest': None,
                'fine': None,
                'contribution_id': None,
                'transaction_id': d['id'],
                'payment_id': None,
            })

    conn.close()
    out.sort(key=lambda e: (e['date'] or ''), reverse=True)
    return out


def edit_entry(data):
    kind = data.get('kind')
    if kind not in VALID_KINDS:
        return {'error': 'unknown kind'}
    conn = get_conn()
    cur = conn.cursor()

    if kind in ('share', 'deposit'):
        cid = int(data.get('contribution_id'))
        member_id = data.get('member_id')
        if member_id in (None, ''):
            conn.close()
            return {'error': 'member required'}
        member_id = int(member_id)
        amount = float(data.get('amount') or 0)
        date = data.get('date') or ''
        cur.execute('UPDATE contributions SET member_id=?, amount=?, date=? WHERE id=?', (member_id, amount, date, cid))
        tid = data.get('transaction_id')
        if tid:
            cur.execute('UPDATE transactions SET member_id=?, amount=? WHERE id=?', (member_id, amount, int(tid)))
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    if kind == 'loan_payment':
        pid = int(data.get('payment_id'))
        member_id = data.get('member_id')
        if member_id in (None, ''):
            conn.close()
            return {'error': 'member required'}
        member_id = int(member_id)
        principal = float(data.get('principal') or 0)
        interest = float(data.get('interest') or 0)
        fine = float(data.get('fine') or 0)
        amount = round(principal + interest + fine, 2)
        date = data.get('date') or ''
        cur.execute('SELECT * FROM payments WHERE id=?', (pid,))
        old = cur.fetchone()
        if not old:
            conn.close()
            return {'error': 'not found'}
        oldd = dict(old)
        if oldd.get('loan_id'):
            cur.execute('SELECT * FROM loans WHERE id=?', (oldd['loan_id'],))
            lrow = cur.fetchone()
            if lrow:
                new_out = round((lrow['outstanding'] or 0) + (oldd['principal_paid'] or 0), 2)
                cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, lrow['id']))
        new_loan_id = None
        if principal > 0:
            cur.execute("SELECT id, outstanding FROM loans WHERE member_id=? AND status='active' ORDER BY id DESC LIMIT 1", (member_id,))
            lrow = cur.fetchone()
            if lrow:
                new_loan_id = lrow['id']
                to_apply = min(principal, lrow['outstanding'] or 0)
                new_out = round((lrow['outstanding'] or 0) - to_apply, 2)
                cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, lrow['id']))
        cur.execute(
            'UPDATE payments SET member_id=?, loan_id=?, date=?, amount=?, interest_paid=?, principal_paid=?, late_fee_paid=? WHERE id=?',
            (member_id, new_loan_id, date, amount, interest, principal, fine, pid),
        )
        tid = data.get('transaction_id')
        if tid:
            cur.execute('UPDATE transactions SET member_id=?, amount=? WHERE id=?', (member_id, amount, int(tid)))
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    tid = int(data.get('transaction_id'))
    member_id = data.get('member_id')
    if member_id in (None, ''):
        member_id = None
    else:
        member_id = int(member_id)
    amount = float(data.get('amount') or 0)
    date = data.get('date') or ''
    ts = date + 'T12:00:00' if date else None
    if ts:
        cur.execute('UPDATE transactions SET member_id=?, amount=?, timestamp=? WHERE id=?', (member_id, amount, ts, tid))
    else:
        cur.execute('UPDATE transactions SET member_id=?, amount=? WHERE id=?', (member_id, amount, tid))
    conn.commit()
    conn.close()
    return {'status': 'ok'}


def delete_entry(data):
    kind = data.get('kind')
    if kind not in VALID_KINDS:
        return {'error': 'unknown kind'}
    conn = get_conn()
    cur = conn.cursor()

    if kind in ('share', 'deposit'):
        cid = int(data.get('contribution_id'))
        cur.execute('DELETE FROM contributions WHERE id=?', (cid,))
        tid = data.get('transaction_id')
        if tid:
            cur.execute('DELETE FROM transactions WHERE id=?', (int(tid),))
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    if kind == 'loan_payment':
        pid = int(data.get('payment_id'))
        cur.execute('SELECT * FROM payments WHERE id=?', (pid,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {'error': 'not found'}
        d = dict(row)
        if d.get('loan_id') and d.get('principal_paid'):
            cur.execute('SELECT * FROM loans WHERE id=?', (d['loan_id'],))
            lrow = cur.fetchone()
            if lrow:
                new_out = round((lrow['outstanding'] or 0) + d['principal_paid'], 2)
                cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (new_out, lrow['id']))
        cur.execute('DELETE FROM payments WHERE id=?', (pid,))
        tid = data.get('transaction_id')
        if tid:
            cur.execute('DELETE FROM transactions WHERE id=?', (int(tid),))
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    tid = int(data.get('transaction_id'))
    cur.execute('DELETE FROM transactions WHERE id=?', (tid,))
    conn.commit()
    conn.close()
    return {'status': 'ok'}
