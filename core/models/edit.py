from datetime import date as dt_date

from core.database import get_conn, row_to_dict
from core.models.loan import compute_interest_accrued

VALID_KINDS = ('share', 'deposit', 'loan_payment', 'income', 'expense', 'late_fee', 'fd')
SPLIT_KINDS = ('share', 'late_fee', 'loan_payment')


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


def list_entries(etype='all', member_id=None, q='', date_from=None, date_to=None, limit=200):
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
        if date_from:
            sql += ' AND c.date >= ?'
            params.append(date_from)
        if date_to:
            sql += ' AND c.date <= ?'
            params.append(date_to)
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
        if date_from:
            sql += ' AND p.date >= ?'
            params.append(date_from)
        if date_to:
            sql += ' AND p.date <= ?'
            params.append(date_to)
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

    if etype in ('all', 'income', 'expense', 'late_fee', 'fd'):
        sql = ("SELECT t.id, t.member_id, m.name AS member_name, t.timestamp, t.desc, t.debit_credit, t.amount, t.source "
               "FROM transactions t LEFT JOIN members m ON m.id=t.member_id "
               "WHERE (t.source='manual_ie' OR t.desc='Late fee' OR t.desc LIKE 'FD Interest%')")
        params = []
        if etype == 'income':
            sql += " AND t.source='manual_ie' AND t.debit_credit='credit'"
        elif etype == 'expense':
            sql += " AND t.source='manual_ie' AND t.debit_credit='debit'"
        elif etype == 'late_fee':
            sql += " AND t.desc='Late fee'"
        elif etype == 'fd':
            sql += " AND t.desc LIKE 'FD Interest%'"
        if member_id:
            sql += ' AND t.member_id=?'
            params.append(member_id)
        if q:
            sql += ' AND (m.name LIKE ? OR t.desc LIKE ?)'
            params.append(like)
            params.append(like)
        if date_from:
            sql += ' AND substr(t.timestamp,1,10) >= ?'
            params.append(date_from)
        if date_to:
            sql += ' AND substr(t.timestamp,1,10) <= ?'
            params.append(date_to)
        sql += ' ORDER BY t.timestamp DESC, t.id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, params)
        for r in cur.fetchall():
            d = dict(r)
            if d['desc'] == 'Late fee':
                kind = 'late_fee'
            elif d['desc'] and d['desc'].startswith('FD Interest'):
                kind = 'fd'
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

    attach_split(cur, out)
    conn.close()
    out.sort(key=lambda e: (e['date'] or ''), reverse=True)
    return out


def _split_map(cur):
    sm = {}
    for r in cur.execute(
        "SELECT member_id, date, SUM(amount) s FROM contributions WHERE type='share' GROUP BY member_id, date"
    ).fetchall():
        sm.setdefault((r['member_id'], (r['date'] or '')[:10]), {})['share'] = r['s']
    for r in cur.execute(
        "SELECT member_id, substr(timestamp,1,10) d, SUM(amount) s FROM transactions WHERE desc='Late fee' GROUP BY member_id, substr(timestamp,1,10)"
    ).fetchall():
        sm.setdefault((r['member_id'], r['d'] or ''), {})['late_fee'] = r['s']
    for r in cur.execute(
        "SELECT member_id, date, SUM(principal_paid) p, SUM(interest_paid) i FROM payments GROUP BY member_id, date"
    ).fetchall():
        key = (r['member_id'], (r['date'] or '')[:10])
        sm.setdefault(key, {}).update({'principal': r['p'] or 0, 'interest': r['i'] or 0})
    return sm


def attach_split(cur, out):
    sm = _split_map(cur)
    for e in out:
        if e['kind'] in SPLIT_KINDS:
            s = sm.get((e['member_id'], e['date']), {})
            e['split'] = {
                'share': s.get('share') or 0,
                'late_fee': s.get('late_fee') or 0,
                'interest': s.get('interest') or 0,
                'principal': s.get('principal') or 0,
            }


def resplit(member_id, date, share, late_fee, loan_interest, loan_principal):
    """Set the full monthly payment split for one member on one date."""
    member_id = int(member_id)
    date = (date or '')[:10]
    share = float(share or 0)
    late_fee = float(late_fee or 0)
    loan_interest = float(loan_interest or 0)
    loan_principal = float(loan_principal or 0)
    conn = get_conn()
    cur = conn.cursor()

    # ---- Share ----
    cur.execute("SELECT id, amount FROM contributions WHERE member_id=? AND date=? AND type='share' ORDER BY id", (member_id, date))
    share_rows = cur.fetchall()
    for extra in share_rows[1:]:
        tid = _match_contribution_txn(cur, member_id, extra['amount'], 'share')
        cur.execute('DELETE FROM contributions WHERE id=?', (extra['id'],))
        if tid:
            cur.execute('DELETE FROM transactions WHERE id=?', (tid,))
    if share > 0 and share_rows:
        old_amount = share_rows[0]['amount']
        cur.execute('UPDATE contributions SET amount=? WHERE id=?', (share, share_rows[0]['id']))
        tid = _match_contribution_txn(cur, member_id, old_amount, 'share')
        if tid:
            cur.execute('UPDATE transactions SET amount=? WHERE id=?', (share, tid))
    elif share > 0:
        cur.execute('INSERT INTO contributions (member_id, date, amount, type) VALUES (?,?,?,?)', (member_id, date, share, 'share'))
        cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
                    (member_id, date + 'T12:00:00', 'Share payment (admin)', 'credit', share))
    else:
        for r in share_rows:
            tid = _match_contribution_txn(cur, member_id, r['amount'], 'share')
            cur.execute('DELETE FROM contributions WHERE id=?', (r['id'],))
            if tid:
                cur.execute('DELETE FROM transactions WHERE id=?', (tid,))

    # ---- Late fee ----
    cur.execute("SELECT id, amount FROM transactions WHERE member_id=? AND substr(timestamp,1,10)=? AND desc='Late fee' ORDER BY id", (member_id, date))
    lf_rows = cur.fetchall()
    for extra in lf_rows[1:]:
        cur.execute('DELETE FROM transactions WHERE id=?', (extra['id'],))
    if late_fee > 0 and lf_rows:
        cur.execute('UPDATE transactions SET amount=? WHERE id=?', (late_fee, lf_rows[0]['id']))
    elif late_fee > 0:
        cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
                    (member_id, date + 'T12:00:00', 'Late fee', 'credit', late_fee))
    else:
        for r in lf_rows:
            cur.execute('DELETE FROM transactions WHERE id=?', (r['id'],))

    # ---- Loan ----
    cur.execute('SELECT id, loan_id, amount, principal_paid FROM payments WHERE member_id=? AND date=? ORDER BY id', (member_id, date))
    pay_rows = cur.fetchall()
    for r in pay_rows:
        if r['loan_id'] and r['principal_paid']:
            cur.execute('SELECT outstanding FROM loans WHERE id=?', (r['loan_id'],))
            lrow = cur.fetchone()
            if lrow:
                cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (round((lrow['outstanding'] or 0) + r['principal_paid'], 2), r['loan_id']))
    total_pay = round(loan_principal + loan_interest, 2)
    if total_pay > 0:
        new_loan_id = None
        cur.execute("SELECT * FROM loans WHERE member_id=? AND status='active' ORDER BY id DESC LIMIT 1", (member_id,))
        active = cur.fetchone()
        if active:
            loan_dict = row_to_dict(active)
            compute_interest_accrued(loan_dict, dt_date.today(), cur)
            to_apply = min(loan_principal, loan_dict['outstanding'] or 0)
            cur.execute('UPDATE loans SET outstanding=? WHERE id=?', (round((loan_dict['outstanding'] or 0) - to_apply, 2), loan_dict['id']))
            new_loan_id = loan_dict['id']
        if pay_rows:
            old_amount = pay_rows[0]['amount']
            cur.execute('UPDATE payments SET loan_id=?, amount=?, interest_paid=?, principal_paid=?, late_fee_paid=0 WHERE id=?',
                        (new_loan_id, total_pay, loan_interest, loan_principal, pay_rows[0]['id']))
            tid = _match_payment_txn(cur, member_id, old_amount)
            if tid:
                cur.execute('UPDATE transactions SET amount=? WHERE id=?', (total_pay, tid))
        else:
            cur.execute('INSERT INTO payments (member_id, loan_id, date, amount, interest_paid, principal_paid, late_fee_paid) VALUES (?,?,?,?,?,?,?)',
                        (member_id, new_loan_id, date, total_pay, loan_interest, loan_principal, 0.0))
            cur.execute('INSERT INTO transactions (member_id, timestamp, desc, debit_credit, amount) VALUES (?,?,?,?,?)',
                        (member_id, date + 'T12:00:00', 'Loan payment (admin)', 'credit', total_pay))
    for extra in pay_rows[1:]:
        tid = _match_payment_txn(cur, member_id, extra['amount'])
        cur.execute('DELETE FROM payments WHERE id=?', (extra['id'],))
        if tid:
            cur.execute('DELETE FROM transactions WHERE id=?', (tid,))
    if total_pay <= 0 and pay_rows:
        tid = _match_payment_txn(cur, member_id, pay_rows[0]['amount'])
        cur.execute('DELETE FROM payments WHERE id=?', (pay_rows[0]['id'],))
        if tid:
            cur.execute('DELETE FROM transactions WHERE id=?', (tid,))

    conn.commit()
    conn.close()
    return {'status': 'ok'}


def edit_entry(data):
    kind = data.get('kind')
    if kind not in VALID_KINDS:
        return {'error': 'unknown kind'}
    if kind in SPLIT_KINDS:
        member_id = data.get('member_id')
        if member_id in (None, ''):
            return {'error': 'member required'}
        return resplit(
            member_id,
            data.get('date') or '',
            data.get('share', data.get('amount', 0)),
            data.get('late_fee', 0),
            data.get('interest', 0),
            data.get('principal', 0),
        )
    conn = get_conn()
    cur = conn.cursor()

    if kind == 'deposit':
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
