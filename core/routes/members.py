import os
from datetime import datetime, date

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from core.config import ADMIN_PIN
from core.database import strip_sensitive
from core.models.member import get_all_members, create_member, get_member, update_member
from core.models.payment import add_contribution, create_payment_request, cancel_payment_request
from core.models.transaction import get_member_statement
from core.models.loan import compute_interest_accrued

members_bp = Blueprint('members', __name__)


@members_bp.route('/api/members', methods=['GET', 'POST'])
def members():
    if request.method == 'GET':
        ms = get_all_members()
        return jsonify([strip_sensitive(m) for m in ms])
    data = request.json
    dep_amt = data.get('deposit_amount')
    if dep_amt is not None:
        dep_amt = float(dep_amt)
    m = create_member(
        data.get('name'),
        data.get('phone', ''),
        int(data.get('is_admin', 0)),
        data.get('dob', ''),
        data.get('address', ''),
        data.get('photo_url', ''),
        deposit_amount=dep_amt,
        deposit_date=data.get('deposit_date'),
        password=data.get('password', ''),
    )
    return jsonify(strip_sensitive(m)), 201


@members_bp.route('/api/members/<int:member_id>', methods=['GET'])
def get_member_route(member_id):
    m = get_member(member_id, full=True)
    if not m:
        return jsonify({'error': 'not found'}), 404
    for loan in m.get('loans', []):
        if loan['status'] == 'active':
            compute_interest_accrued(loan, date.today())
    m = get_member(member_id, full=True)
    return jsonify(strip_sensitive(m))


@members_bp.route('/api/members/<int:member_id>', methods=['PATCH'])
def update_member_route(member_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json
    member = update_member(
        member_id,
        phone=data.get('phone'),
        dob=data.get('dob'),
        address=data.get('address'),
        photo_url=data.get('photo_url'),
    )
    if not member:
        return jsonify({'error': 'not found'}), 404
    return jsonify(member)


@members_bp.route('/api/members/<int:member_id>/self', methods=['PATCH'])
def self_update_member(member_id):
    data = request.json or {}
    phone = data.get('phone')
    dob = data.get('dob')
    address = data.get('address')
    photo_url = data.get('photo_url')
    password = data.get('password')
    current_password = data.get('current_password')
    password_hash = None
    if password:
        member = get_member(member_id)
        if not member:
            return jsonify({'error': 'not found'}), 404
        stored = member.get('password') or ''
        if stored and not check_password_hash(stored, current_password or ''):
            return jsonify({'error': 'Current password is incorrect'}), 401
        password_hash = generate_password_hash(password)
    member = update_member(member_id, phone=phone, dob=dob, address=address, photo_url=photo_url, password_hash=password_hash)
    if not member:
        return jsonify({'error': 'not found'}), 404
    return jsonify(strip_sensitive(member))


@members_bp.route('/api/members/<int:member_id>/upload_photo', methods=['POST'])
def upload_member_photo(member_id):
    if 'photo' not in request.files:
        return jsonify({'error': 'no file'}), 400
    file = request.files['photo']
    if not file.filename:
        return jsonify({'error': 'no filename'}), 400
    uploads = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(uploads, exist_ok=True)
    fn = secure_filename(
        f"profile_{member_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}",
    )
    path = os.path.join(uploads, fn)
    file.save(path)
    photo_url = f"/static/uploads/{fn}"
    member = update_member(member_id, photo_url=photo_url)
    return jsonify({'status': 'ok', 'member': member})


@members_bp.route('/api/members/<int:member_id>/contribute', methods=['POST'])
def contribute(member_id):
    data = request.json
    amount = float(data.get('amount', 0))
    when = date.today()
    add_contribution(member_id, when, amount, 'share')
    return jsonify({'status': 'ok'})


@members_bp.route('/api/members/<int:member_id>/submit_payment_request', methods=['POST'])
def submit_payment_request(member_id):
    txn_date = None
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        if file.filename:
            uploads = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(uploads, exist_ok=True)
            fn = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            path = os.path.join(uploads, fn)
            file.save(path)
            screenshot = f"/static/uploads/{fn}"
        else:
            screenshot = ''
        amount = float(request.form.get('amount', 0))
        ptype = request.form.get('type', 'share')
        note = request.form.get('note', '')
        txn_date = request.form.get('txn_date') or None
        late_fee = float(request.form.get('late_fee', 0) or 0)
        share_amount = float(request.form.get('share_amount', 0) or 0)
        loan_amount = float(request.form.get('loan_amount', 0) or 0)
        interest_amount = float(request.form.get('interest_amount', 0) or 0)
    else:
        data = request.get_json(silent=True)
        if data is None:
            data = request.form or {}
        amount = float(data.get('amount', 0))
        ptype = data.get('type', 'share')
        note = data.get('note', '')
        screenshot = data.get('screenshot', '')
        txn_date = data.get('txn_date') or None
        late_fee = float(data.get('late_fee', 0) or 0)
        share_amount = float(data.get('share_amount', 0) or 0)
        loan_amount = float(data.get('loan_amount', 0) or 0)
        interest_amount = float(data.get('interest_amount', 0) or 0)
    req = create_payment_request(member_id, amount, ptype, note, screenshot, txn_date, late_fee, share_amount, loan_amount, interest_amount)
    return jsonify({'status': 'submitted', 'request': req}), 201


@members_bp.route('/api/members/<int:member_id>/cancel_request/<int:req_id>', methods=['POST'])
def cancel_request(member_id, req_id):
    res = cancel_payment_request(req_id, member_id)
    if not res:
        return jsonify({'error': 'not found or cannot cancel'}), 404
    return jsonify({'status': 'cancelled', 'request': res})


@members_bp.route('/api/members/<int:member_id>/statement', methods=['GET'])
def member_statement(member_id):
    csv_text = get_member_statement(member_id)
    return (csv_text, 200, {'Content-Type': 'text/csv'})
