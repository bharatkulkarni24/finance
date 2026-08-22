from datetime import date, datetime

import os

from flask import Blueprint, jsonify, request, Response, send_file

from core.config import now_ist
from core.models.payment import approve_payment_request, reject_payment_request, admin_direct_entry
from core.models.loan import approve_loan, reject_loan
from core.models.requests import list_submitted_requests, list_rejected_items
from core.models.fd import add_fd, add_fd_installment, close_fd, get_fd_entries
from core.models.transaction import add_transaction, get_recent_transactions, get_admin_stats, get_passbook_entries, get_period_summary
from core.models.report import get_report_data, build_report_pdf
from core.models.edit import list_entries, edit_entry, delete_entry, list_audit_log
from core.session import check_admin_token, require_member_or_admin

admin_bp = Blueprint('admin', __name__)



@admin_bp.route('/api/admin/submitted_requests', methods=['GET'])
def admin_submitted_requests():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(list_submitted_requests())


@admin_bp.route('/api/admin/rejected_requests', methods=['GET'])
def admin_rejected_requests():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(list_rejected_items())


@admin_bp.route('/api/admin/approve_request/<int:req_id>', methods=['POST'])
def admin_approve_request(req_id):
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    approver_id = data.get('approver_id') or 0
    res = approve_payment_request(req_id, approver_id)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'approved', 'request': res})


@admin_bp.route('/api/admin/reject_request/<int:req_id>', methods=['POST'])
def admin_reject_request(req_id):
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    approver_id = data.get('approver_id') or 0
    reason = data.get('reason', '')
    res = reject_payment_request(req_id, approver_id, reason)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'rejected', 'request': res})


@admin_bp.route('/api/admin/fd/add', methods=['POST'])
def admin_fd_add():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
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
    if isinstance(fd, dict) and fd.get('error'):
        return jsonify(fd), 400
    return jsonify(fd)


@admin_bp.route('/api/admin/fd/installment', methods=['POST'])
def admin_fd_installment():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
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
    if isinstance(inst, dict) and inst.get('error'):
        return jsonify(inst), 400
    if not inst:
        return jsonify({'error': 'parent scheme not found'}), 404
    return jsonify(inst)


@admin_bp.route('/api/admin/fd/close/<int:fd_id>', methods=['POST'])
def admin_fd_close(fd_id):
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    fd = close_fd(fd_id, data.get('end_date', ''), float(data.get('interest_earned', 0)))
    if not fd:
        return jsonify({'error': 'not found or already closed'}), 404
    return jsonify(fd)


@admin_bp.route('/api/admin/fd/list', methods=['GET'])
def admin_fd_list():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    status = request.args.get('status')
    entries = get_fd_entries(status)
    return jsonify(entries)


@admin_bp.route('/api/admin/income-expense/add', methods=['POST'])
def admin_income_expense_add():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    row = add_transaction(
        debit_credit=data.get('type', 'credit'),
        amount=float(data.get('amount', 0)),
        description=data.get('description', ''),
        entry_date=data.get('entry_date', ''),
    )
    return jsonify(row)


@admin_bp.route('/api/admin/transactions', methods=['GET'])
def admin_transactions():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_recent_transactions(100))


@admin_bp.route('/api/admin/passbook', methods=['GET'])
def admin_passbook():
    if not require_member_or_admin():
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_passbook_entries())


@admin_bp.route('/api/admin/period_summary', methods=['GET'])
def admin_period_summary():
    if not require_member_or_admin():
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_period_summary())


@admin_bp.route('/api/admin/entries', methods=['GET'])
def admin_entries():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
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
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    return jsonify(edit_entry(data))


@admin_bp.route('/api/admin/entries/delete', methods=['POST'])
def admin_entries_delete():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    return jsonify(delete_entry(data))


@admin_bp.route('/api/admin/audit_log', methods=['GET'])
def admin_audit_log_route():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(list_audit_log())


@admin_bp.route('/api/admin/backup/download', methods=['GET'])
def admin_backup_download():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    from core.backup import create_snapshot, BACKUP_DIR, _prune
    stamp = now_ist().strftime('%Y%m%d-%H%M%S')
    path = os.path.join(BACKUP_DIR, f'finance-backup-{stamp}.db')
    try:
        create_snapshot(path)
        _prune()
    except Exception:
        return jsonify({'error': 'backup_failed'}), 500
    return send_file(path, as_attachment=True, download_name=f'finance-backup-{stamp}.db')


@admin_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    if not require_member_or_admin():
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(get_admin_stats())


@admin_bp.route('/api/admin/approve_loan/<int:req_id>', methods=['POST'])
def approve_loan_route(req_id):
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    approver_id = data.get('approver_id') or 0
    loan = approve_loan(req_id, approver_id)
    if not loan:
        return jsonify({'error': 'not found'}), 404
    if isinstance(loan, dict) and loan.get('error'):
        return jsonify(loan), 400
    return jsonify({'status': 'approved', 'loan': loan})


@admin_bp.route('/api/admin/reject_loan/<int:req_id>', methods=['POST'])
def reject_loan_route(req_id):
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    approver_id = data.get('approver_id') or 0
    reason = data.get('reason', '')
    res = reject_loan(req_id, approver_id, reason)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'rejected', 'request': res})


@admin_bp.route('/api/admin/export_report', methods=['GET'])
def admin_export_report():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    f = request.args.get('from', '')
    t = request.args.get('to', '')
    try:
        date.fromisoformat(f)
        date.fromisoformat(t)
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid_dates', 'message': 'Provide from/to as YYYY-MM-DD'}), 400
    if t < f:
        return jsonify({'error': 'invalid_range', 'message': 'to date must be on or after from date'}), 400
    data = get_report_data(f, t)
    pdf_bytes = build_report_pdf(data)
    filename = f'SLV_Finance_Report_{f}_to_{t}.pdf'
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


@admin_bp.route('/api/admin/direct_entry', methods=['POST'])
def admin_direct_entry_route():
    if not check_admin_token(request.headers.get('X-ADMIN-TOKEN', '')):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    member_id = int(data.get('member_id', 0))
    if not member_id:
        return jsonify({'error': 'member_id is required'}), 400
    share_amount = float(data.get('share_amount', 0))
    fine = float(data.get('fine', 0))
    loan_principal = float(data.get('loan_principal', 0))
    loan_interest = float(data.get('loan_interest', 0))
    entry_date = data.get('entry_date', '')
    note = data.get('note', '')
    admin_direct_entry(
        member_id=member_id,
        share_amount=share_amount,
        fine=fine,
        loan_principal=loan_principal,
        loan_interest=loan_interest,
        entry_date=entry_date or None,
        note=note,
    )
    return jsonify({'status': 'ok'})
