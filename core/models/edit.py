from datetime import date as dt_date, datetime

from core.database import get_conn, row_to_dict
from core.models.loan import compute_interest_accrued
from core.models.requests import _as_datetime

VALID_KINDS = ('share', 'loan_principal', 'income', 'expense', 'fine', 'fd', 'split')
SPLIT_KINDS = ('share', 'fine', 'loan_principal', 'split')
GROUP_KINDS = ('share', 'fine', 'loan_principal', 'split')
DEPOSIT_FILTER = 'share_amount=0 AND loan_principal=0 AND loan_interest=0 AND fine=0'


def _payment_kind(share, loan, interest, fine):
    share = share or 0
    loan = loan or 0
    interest = interest or 0
    fine = fine or 0
    if share > 0 and (loan > 0 or interest > 0 or fine > 0):
        return 'payment'
    if share > 0:
        return 'share'
    if loan > 0 or interest > 0:
        return 'loan_principal'
    if fine > 0:
        return 'fine'
    return 'deposit'


def _derive_kind(d):
    return _payment_kind(d.get('share_amount'), d.get('loan_principal'), d.get('loan_interest'), d.get('fine'))


def _kind_filter(etype):
    if etype == 'share':
        return 'p.share_amount > 0'
    if etype == 'loan_principal':
        return '(p.loan_principal > 0 OR p.loan_interest > 0)'
    if etype == 'fine':
        return 'p.fine > 0'
    if etype == 'split':
        return 'NOT (' + DEPOSIT_FILTER + ')'
    return None


def _entry_kind(row, etype):
    rk = _derive_kind(row)
    if rk in ('share', 'deposit', 'fine', 'loan_principal'):
        return rk
    if etype == 'share':
        return 'share'
    if etype == 'loan_principal':
        return 'loan_principal'
    if etype == 'fine':
        return 'fine'
    return 'split'


def list_audit_log(limit=200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT a.*, m.name AS changed_by_name, p.member_id AS pay_member_id, pm.name AS pay_member_name "
        "FROM audit_log a "
        "LEFT JOIN members m ON m.member_id = a.changed_by "
        "LEFT JOIN member_ledger p ON p.pay_id = a.pay_id "
        "LEFT JOIN members pm ON pm.member_id = p.member_id "
        "ORDER BY a.changed_at DESC LIMIT ?",
        (limit,),
    )
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def list_entries(etype='all', member_id=None, q='', date_from=None, date_to=None, limit=200):
    conn = get_conn()
    cur = conn.cursor()
    out = []
    like = '%' + (q or '') + '%'

    if etype in ('all', 'share', 'loan_principal', 'fine', 'split'):
        sql = ("SELECT p.*, m.name AS member_name FROM member_ledger p LEFT JOIN members m ON m.member_id=p.member_id WHERE 1=1")
        params = []
        kf = _kind_filter(etype)
        if kf:
            sql += ' AND ' + kf
        if member_id:
            sql += ' AND p.member_id=?'
            params.append(member_id)
        if q:
            sql += ' AND (m.name LIKE ?)'
            params.append(like)
        if date_from:
            sql += ' AND substr(p.pay_date,1,10) >= ?'
            params.append(date_from)
        if date_to:
            sql += ' AND substr(p.pay_date,1,10) <= ?'
            params.append(date_to)
        sql += ' ORDER BY p.pay_date DESC, p.pay_id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, params)
        for r in cur.fetchall():
            d = dict(r)
            kind = _entry_kind(d, etype)
            entry = {
                'id': 'p' + str(d['pay_id']),
                'kind': kind,
                'member_id': d['member_id'],
                'member_name': d['member_name'] or '(No member)',
                'date': (d['pay_date'] or '')[:10],
                'amount': d['total_amount'],
                'description': d['description'] or '',
                'debit_credit': 'credit',
                'loan_principal': None,
                'loan_interest': None,
                'fine': None,
                'contribution_id': None,
                'transaction_id': None,
                'payment_id': d['pay_id'],
            }
            if kind == 'share':
                entry['amount'] = d['share_amount'] or 0
            elif kind == 'loan_principal':
                entry['amount'] = round((d['loan_principal'] or 0) + (d['loan_interest'] or 0), 2)
                entry['loan_principal'] = d['loan_principal']
                entry['loan_interest'] = d['loan_interest']
            elif kind == 'fine':
                entry['amount'] = d['fine'] or 0
                entry['fine'] = d['fine']
            elif kind == 'split':
                entry['loan_principal'] = d['loan_principal']
                entry['loan_interest'] = d['loan_interest']
                entry['fine'] = d['fine']
            out.append(entry)

    if etype in ('all', 'income', 'expense'):
        sql = ("SELECT t.*, m.name AS member_name FROM group_ledger t LEFT JOIN members m ON m.member_id=t.member_id "
               "WHERE t.member_id IS NULL")
        params = []
        if etype == 'income':
            sql += " AND t.debit_credit='credit'"
        elif etype == 'expense':
            sql += " AND t.debit_credit='debit'"
        if member_id:
            sql += ' AND t.member_id=?'
            params.append(member_id)
        if q:
            sql += ' AND (m.name LIKE ? OR t.description LIKE ?)'
            params.append(like)
            params.append(like)
        if date_from:
            sql += ' AND substr(t.timestamp,1,10) >= ?'
            params.append(date_from)
        if date_to:
            sql += ' AND substr(t.timestamp,1,10) <= ?'
            params.append(date_to)
        sql += ' ORDER BY t.timestamp DESC, t.trn_id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, params)
        for r in cur.fetchall():
            d = dict(r)
            if d['debit_credit'] == 'credit':
                kind = 'income'
            else:
                kind = 'expense'
            out.append({
                'id': 't' + str(d['trn_id']),
                'kind': kind,
                'member_id': d['member_id'],
                'member_name': d['member_name'] or '(No member)',
                'date': (d['timestamp'] or '')[:10],
                'amount': d['amount'],
                'description': d['description'],
                'debit_credit': d['debit_credit'],
                'loan_principal': None,
                'loan_interest': None,
                'fine': None,
                'contribution_id': None,
                'transaction_id': d['trn_id'],
                'payment_id': None,
            })

    attach_split(cur, out)
    if etype in ('all', 'split'):
        out = _group_split_rows(out)
    conn.close()
    out.sort(key=lambda e: (e['date'] or ''), reverse=True)
    return out


def _split_map(cur):
    sm = {}
    for r in cur.execute(
        "SELECT member_id, substr(pay_date,1,10) d, SUM(share_amount) s, SUM(fine) f, SUM(loan_interest) i, SUM(loan_principal) p FROM member_ledger GROUP BY member_id, d"
    ).fetchall():
        sm[(r['member_id'], r['d'])] = {
            'share': r['s'] or 0,
            'fine': r['f'] or 0,
            'loan_interest': r['i'] or 0,
            'loan_principal': r['p'] or 0,
        }
    return sm


def attach_split(cur, out):
    sm = _split_map(cur)
    for e in out:
        if e['kind'] in SPLIT_KINDS:
            e['split'] = sm.get((e['member_id'], e['date']), {
                'share': 0, 'fine': 0, 'loan_interest': 0, 'loan_principal': 0,
            })


def _group_split_rows(out):
    """Collapse member payment rows into one 'split' row per (member, date)."""
    grouped = []
    seen = set()
    for e in out:
        if e['kind'] in GROUP_KINDS:
            key = (e['member_id'], e['date'])
            if key in seen:
                continue
            seen.add(key)
            sp = e.get('split') or {}
            total = (sp.get('share') or 0) + (sp.get('fine') or 0) + (sp.get('loan_interest') or 0) + (sp.get('loan_principal') or 0)
            grouped.append({
                'id': 's{}'.format(e['member_id'] if e['member_id'] is not None else '0') + '-' + e['date'],
                'kind': 'split',
                'member_id': e['member_id'],
                'member_name': e['member_name'],
                'date': e['date'],
                'amount': round(total, 2),
                'description': '',
                'debit_credit': 'credit',
                'loan_principal': None,
                'loan_interest': None,
                'fine': None,
                'contribution_id': None,
                'transaction_id': None,
                'payment_id': None,
                'split': sp,
            })
        else:
            grouped.append(e)
    return grouped


def _revert_loan_principal(cur, member_id, date):
    for r in cur.execute(
        'SELECT loan_id, loan_principal FROM member_ledger WHERE member_id=? AND substr(pay_date,1,10)=? AND loan_id IS NOT NULL AND loan_principal > 0',
        (member_id, date),
    ).fetchall():
        cur.execute('UPDATE loans SET outstanding = ROUND(COALESCE(outstanding,0) + ?, 2) WHERE loan_id=?', (r['loan_principal'], r['loan_id']))


def _apply_new_principal(cur, member_id, loan_principal):
    if not loan_principal or loan_principal <= 0:
        return None
    cur.execute("SELECT * FROM loans WHERE member_id=? AND status='active' ORDER BY loan_id ASC", (member_id,))
    active_loans = [row_to_dict(r) for r in cur.fetchall()]
    if not active_loans:
        return None
    remaining = loan_principal
    loan_id = None
    for loan in active_loans:
        compute_interest_accrued(loan, dt_date.today(), cur)
        if remaining > 0:
            to_apply = min(remaining, loan['outstanding'] or 0)
            new_out = round((loan['outstanding'] or 0) - to_apply, 2)
            if new_out <= 0:
                cur.execute('UPDATE loans SET outstanding=?, status=? WHERE loan_id=?', (0, 'repaid', loan['loan_id']))
            else:
                cur.execute('UPDATE loans SET outstanding=? WHERE loan_id=?', (new_out, loan['loan_id']))
            remaining -= to_apply
            loan_id = loan['loan_id']
    return loan_id


def _log_audit(cur, pay_id, action, changed_by, old, new):
    cur.execute(
        'INSERT INTO audit_log (pay_id, action, changed_by, changed_at, old_share_amount, new_share_amount, old_fine, new_fine, old_loan_interest, new_loan_interest, old_loan_principal, new_loan_principal, old_total_amount, new_total_amount) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (
            pay_id, action, changed_by, datetime.utcnow().isoformat(),
            old.get('share_amount', 0) or 0, new.get('share_amount', 0) or 0,
            old.get('fine', 0) or 0, new.get('fine', 0) or 0,
            old.get('loan_interest', 0) or 0, new.get('loan_interest', 0) or 0,
            old.get('loan_principal', 0) or 0, new.get('loan_principal', 0) or 0,
            old.get('total_amount', 0) or 0, new.get('total_amount', 0) or 0,
        ),
    )


def _day_split(cur, member_id, date):
    cur.execute(
        "SELECT SUM(share_amount) s, SUM(fine) f, SUM(loan_interest) i, SUM(loan_principal) p FROM member_ledger WHERE member_id=? AND substr(pay_date,1,10)=?",
        (member_id, date),
    )
    r = cur.fetchone()
    s = dict(r) if r else {}
    share = s.get('s') or 0
    fine = s.get('f') or 0
    interest = s.get('i') or 0
    principal = s.get('p') or 0
    return {
        'share_amount': share,
        'fine': fine,
        'loan_interest': interest,
        'loan_principal': principal,
        'total_amount': round(share + fine + interest + principal, 2),
    }


def resplit(member_id, date, share, fine, loan_interest, loan_principal, changed_by=None):
    """Set the full monthly payment split for one member on one date."""
    member_id = int(member_id)
    date = (date or '')[:10]
    share = float(share or 0)
    fine = float(fine or 0)
    loan_interest = float(loan_interest or 0)
    loan_principal = float(loan_principal or 0)
    conn = get_conn()
    cur = conn.cursor()

    old = _day_split(cur, member_id, date)
    _revert_loan_principal(cur, member_id, date)
    cur.execute("DELETE FROM member_ledger WHERE member_id=? AND substr(pay_date,1,10)=? AND NOT (" + DEPOSIT_FILTER + ")", (member_id, date))

    total = round(share + fine + loan_interest + loan_principal, 2)
    new_pay_id = None
    if total > 0:
        new_loan_id = _apply_new_principal(cur, member_id, loan_principal)
        cur.execute(
            'INSERT INTO member_ledger (member_id, pay_date, total_amount, share_amount, loan_principal, loan_interest, fine, loan_id, created_at, modified_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (member_id, _as_datetime(date), total, share, loan_principal, loan_interest, fine, new_loan_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        new_pay_id = cur.lastrowid

    _log_audit(
        cur, new_pay_id, 'update', changed_by, old,
        {
            'share_amount': share,
            'fine': fine,
            'loan_interest': loan_interest,
            'loan_principal': loan_principal,
            'total_amount': total,
        },
    )

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
            data.get('fine', 0),
            data.get('loan_interest', 0),
            data.get('loan_principal', 0),
            data.get('changed_by'),
        )

    conn = get_conn()
    cur = conn.cursor()
    member_id = data.get('member_id')
    if member_id in (None, ''):
        member_id = None
    else:
        member_id = int(member_id)
    amount = float(data.get('amount') or 0)
    date = (data.get('date') or '')[:10] or None
    changed_by = data.get('changed_by')

    if kind in ('share', 'loan_principal', 'fine'):
        pay_id = data.get('payment_id')
        if not pay_id:
            conn.close()
            return {'error': 'missing payment_id'}
        cur.execute('SELECT * FROM member_ledger WHERE pay_id=?', (int(pay_id),))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {'error': 'not found'}
        d = dict(row)
        old = {
            'share_amount': d.get('share_amount', 0) or 0,
            'fine': d.get('fine', 0) or 0,
            'loan_interest': d.get('loan_interest', 0) or 0,
            'loan_principal': d.get('loan_principal', 0) or 0,
            'total_amount': d.get('total_amount', 0) or 0,
        }
        new = dict(old)
        now = datetime.utcnow().isoformat()
        if d.get('loan_principal'):
            _revert_loan_principal(cur, d['member_id'], d['pay_date'][:10])
        if kind == 'share':
            cur.execute('UPDATE member_ledger SET member_id=?, pay_date=?, total_amount=?, share_amount=?, loan_principal=0, loan_interest=0, fine=0, modified_at=? WHERE pay_id=?',
                        (member_id, _as_datetime(date), amount, amount, now, int(pay_id)))
            new = {'share_amount': amount, 'fine': 0, 'loan_interest': 0, 'loan_principal': 0, 'total_amount': amount}
        elif kind == 'fine':
            cur.execute('UPDATE member_ledger SET member_id=?, pay_date=?, total_amount=?, fine=?, modified_at=? WHERE pay_id=?',
                        (member_id, _as_datetime(date), amount, amount, now, int(pay_id)))
            new = {'share_amount': 0, 'fine': amount, 'loan_interest': 0, 'loan_principal': 0, 'total_amount': amount}
        else:
            new_loan_id = _apply_new_principal(cur, member_id, amount)
            cur.execute('UPDATE member_ledger SET member_id=?, pay_date=?, total_amount=?, loan_principal=?, loan_interest=0, fine=0, loan_id=?, modified_at=? WHERE pay_id=?',
                        (member_id, _as_datetime(date), amount, amount, new_loan_id, now, int(pay_id)))
            new = {'share_amount': 0, 'fine': 0, 'loan_interest': 0, 'loan_principal': amount, 'total_amount': amount}
        _log_audit(cur, int(pay_id), 'update', changed_by, old, new)
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    tid = int(data.get('transaction_id'))
    ts = (date + 'T12:00:00') if date else None
    if ts:
        cur.execute('UPDATE group_ledger SET member_id=?, amount=?, timestamp=? WHERE trn_id=?', (member_id, amount, ts, tid))
    else:
        cur.execute('UPDATE group_ledger SET member_id=?, amount=? WHERE trn_id=?', (member_id, amount, tid))
    conn.commit()
    conn.close()
    return {'status': 'ok'}


def delete_entry(data):
    kind = data.get('kind')
    if kind not in VALID_KINDS:
        return {'error': 'unknown kind'}
    conn = get_conn()
    cur = conn.cursor()
    changed_by = data.get('changed_by')

    if kind == 'split':
        member_id = int(data.get('member_id'))
        date = (data.get('date') or '')[:10]
        old = _day_split(cur, member_id, date)
        _revert_loan_principal(cur, member_id, date)
        cur.execute("DELETE FROM member_ledger WHERE member_id=? AND substr(pay_date,1,10)=? AND NOT (" + DEPOSIT_FILTER + ")", (member_id, date))
        _log_audit(cur, None, 'delete', changed_by, old, {
            'share_amount': 0, 'fine': 0, 'loan_interest': 0, 'loan_principal': 0, 'total_amount': 0,
        })
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    if kind in ('share', 'loan_principal', 'fine'):
        pay_id = int(data.get('payment_id'))
        cur.execute('SELECT * FROM member_ledger WHERE pay_id=?', (pay_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {'error': 'not found'}
        d = dict(row)
        old = {
            'share_amount': d.get('share_amount', 0) or 0,
            'fine': d.get('fine', 0) or 0,
            'loan_interest': d.get('loan_interest', 0) or 0,
            'loan_principal': d.get('loan_principal', 0) or 0,
            'total_amount': d.get('total_amount', 0) or 0,
        }
        if d.get('loan_principal'):
            _revert_loan_principal(cur, d['member_id'], d['pay_date'][:10])
        cur.execute('DELETE FROM member_ledger WHERE pay_id=?', (pay_id,))
        _log_audit(cur, pay_id, 'delete', changed_by, old, {
            'share_amount': 0, 'fine': 0, 'loan_interest': 0, 'loan_principal': 0, 'total_amount': 0,
        })
        conn.commit()
        conn.close()
        return {'status': 'ok'}

    tid = int(data.get('transaction_id'))
    cur.execute('DELETE FROM group_ledger WHERE trn_id=?', (tid,))
    conn.commit()
    conn.close()
    return {'status': 'ok'}
