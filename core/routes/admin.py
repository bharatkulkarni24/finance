from flask import Blueprint, jsonify, request

from core.config import ADMIN_PIN
from core.models.payment import list_pending_requests, approve_payment_request, reject_payment_request, admin_direct_entry
from core.models.loan import list_pending_loans, get_loan, approve_loan, reject_loan
from core.models.fd import add_fd, add_fd_installment, close_fd, get_fd_entries
from core.models.transaction import admin_add_funds, add_transaction, get_recent_transactions, get_admin_stats, get_passbook_entries, get_period_summary
from core.models.edit import list_entries, edit_entry, delete_entry

admin_bp = Blueprint('admin', __name__)





@admin_bp.route('/api/admin/payment_requests', methods=['GET'])
def admin_payment_requests():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    items = list_pending_requests()
    return jsonify(items)


@admin_bp.route('/api/admin/pending_loans', methods=['GET'])
def admin_pending_loans():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    items = list_pending_loans()
    return jsonify(items)


@admin_bp.route('/api/admin/approve_request/<int:req_id>', methods=['POST'])
def admin_approve_request(req_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    res = approve_payment_request(req_id, approver_id=0)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'approved', 'request': res})


@admin_bp.route('/api/admin/reject_request/<int:req_id>', methods=['POST'])
def admin_reject_request(req_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    reason = data.get('reason', '')
    res = reject_payment_request(req_id, approver_id=0, reason=reason)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'rejected', 'request': res})


@admin_bp.route('/api/admin/add_funds', methods=['POST'])
def admin_add_funds_route():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    amount = float(data.get('amount', 0))
    note = data.get('note', 'Admin add funds')
    t = admin_add_funds(amount, note)
    return jsonify({'status': 'ok', 'transaction': t})


@admin_bp.route('/api/admin/fd/add', methods=['POST'])
def admin_fd_add():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    fd = add_fd(
        amount=float(data.get('amount', 0)),
        start_date=data.get('start_date', ''),
        term_months=int(data.get('term_months', 0)),
        interest_rate=float(data.get('interest_rate', 0)),
        notes=data.get('notes', ''),
        investment_type=data.get('investment_type', 'one_time'),
    )
    return jsonify(fd)


@admin_bp.route('/api/admin/fd/installment', methods=['POST'])
def admin_fd_installment():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    parent_id = int(data.get('parent_id', 0))
    if not parent_id:
        return jsonify({'error': 'parent_id required'}), 400
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'amount must be > 0'}), 400
    installment_date = data.get('installment_date', '')
    notes = data.get('notes', '')
    inst = add_fd_installment(parent_id, amount, installment_date, notes)
    if not inst:
        return jsonify({'error': 'parent scheme not found'}), 404
    return jsonify(inst)


@admin_bp.route('/api/admin/fd/close/<int:fd_id>', methods=['POST'])
def admin_fd_close(fd_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    fd = close_fd(fd_id, data.get('end_date', ''), float(data.get('interest_earned', 0)))
    if not fd:
        return jsonify({'error': 'not found or already closed'}), 404
    return jsonify(fd)


@admin_bp.route('/api/admin/fd/list', methods=['GET'])
def admin_fd_list():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    status = request.args.get('status')
    entries = get_fd_entries(status)
    return jsonify(entries)


@admin_bp.route('/api/admin/income-expense/add', methods=['POST'])
def admin_income_expense_add():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    row = add_transaction(
        debit_credit=data.get('type', 'credit'),
        amount=float(data.get('amount', 0)),
        desc=data.get('desc', ''),
        entry_date=data.get('entry_date', ''),
    )
    return jsonify(row)


@admin_bp.route('/api/admin/transactions', methods=['GET'])
def admin_transactions():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_recent_transactions(100))


@admin_bp.route('/api/admin/passbook', methods=['GET'])
def admin_passbook():
    return jsonify(get_passbook_entries())


@admin_bp.route('/api/admin/period_summary', methods=['GET'])
def admin_period_summary():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_period_summary())


@admin_bp.route('/api/admin/entries', methods=['GET'])
def admin_entries():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    etype = request.args.get('type', 'all')
    member_id = request.args.get('member_id') or None
    q = request.args.get('q', '')
    date_from = request.args.get('date_from') or None
    date_to = request.args.get('date_to') or None
    try:
        limit = int(request.args.get('limit', 200))
    except ValueError:
        limit = 200
    return jsonify(list_entries(etype=etype, member_id=member_id, q=q, date_from=date_from, date_to=date_to, limit=limit))


@admin_bp.route('/api/admin/entries/edit', methods=['POST'])
def admin_entries_edit():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    return jsonify(edit_entry(data))


@admin_bp.route('/api/admin/entries/delete', methods=['POST'])
def admin_entries_delete():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    return jsonify(delete_entry(data))


@admin_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_admin_stats())


@admin_bp.route('/api/admin/approve_loan/<int:loan_id>', methods=['POST'])
def approve_loan_route(loan_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    approve_loan(loan_id)
    loan = get_loan(loan_id)
    return jsonify({'status': 'approved', 'loan': loan})


@admin_bp.route('/api/admin/reject_loan/<int:loan_id>', methods=['POST'])
def reject_loan_route(loan_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    reason = data.get('reason', '')
    reject_loan(loan_id, reason)
    return jsonify({'status': 'rejected'})


@admin_bp.route('/api/admin/direct_entry', methods=['POST'])
def admin_direct_entry_route():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    member_id = int(data.get('member_id', 0))
    if not member_id:
        return jsonify({'error': 'member_id is required'}), 400
    share_amount = float(data.get('share_amount', 0))
    late_fee = float(data.get('late_fee', 0))
    loan_amount = float(data.get('loan_amount', 0))
    interest_amount = float(data.get('interest_amount', 0))
    entry_date = data.get('entry_date', '')
    note = data.get('note', '')
    admin_direct_entry(
        member_id=member_id,
        share_amount=share_amount,
        late_fee=late_fee,
        loan_amount=loan_amount,
        interest_amount=interest_amount,
        entry_date=entry_date or None,
        note=note,
    )
    return jsonify({'status': 'ok'})
