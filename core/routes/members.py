import os
from datetime import datetime, date

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from core.database import strip_sensitive
from core.models.member import get_all_members, create_member, get_member, update_member
from core.models.payment import create_payment_request
from core.models.transaction import get_member_statement
from core.models.loan import compute_interest_accrued
from core.session import require_admin, require_self_or_admin

members_bp = Blueprint('members', __name__)

ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_PHOTO_BYTES = 2 * 1024 * 1024


def _save_uploaded_image(file, prefix: str):
    """Validate an uploaded image and store it under static/uploads.

    Returns the public URL path, or None if the file is rejected.
    """
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        return None
    data = file.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
        return None
    uploads = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(uploads, exist_ok=True)
    fn = secure_filename(f"{prefix}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}")
    path = os.path.join(uploads, fn)
    with open(path, 'wb') as f:
        f.write(data)
    return f"/static/uploads/{fn}"


@members_bp.route('/api/members', methods=['GET', 'POST'])
def members():
    if request.method == 'GET':
        ms = get_all_members()
        public = []
        for m in ms:
            m = strip_sensitive(m)
            m.pop('address', None)
            public.append(m)
        return jsonify(public)
    if not require_admin():
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json
    dep_amt = data.get('entry_deposit_amount')
    if dep_amt is not None:
        dep_amt = float(dep_amt)
    m = create_member(
        data.get('name'),
        data.get('phone', ''),
        0,
        data.get('dob', ''),
        data.get('address', ''),
        data.get('photo_url', ''),
        entry_deposit_amount=dep_amt,
        entry_deposit_date=data.get('entry_deposit_date'),
        password=data.get('password', ''),
    )
    return jsonify(strip_sensitive(m)), 201


@members_bp.route('/api/members/<int:member_id>', methods=['GET'])
def get_member_route(member_id):
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
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
    if not require_admin():
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
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
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
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
    if 'photo' not in request.files:
        return jsonify({'error': 'no file'}), 400
    photo_url = _save_uploaded_image(request.files['photo'], f'profile_{member_id}')
    if not photo_url:
        return jsonify({'error': 'unsupported file type or file too large'}), 400
    member = update_member(member_id, photo_url=photo_url)
    return jsonify({'status': 'ok', 'member': member})


@members_bp.route('/api/members/<int:member_id>/contribute', methods=['POST'])
def contribute(member_id):
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'amount must be greater than 0'}), 400
    req = create_payment_request(member_id, amount, share_amount=amount)
    return jsonify({'status': 'submitted', 'request': req}), 201


@members_bp.route('/api/members/<int:member_id>/submit_payment_request', methods=['POST'])
def submit_payment_request(member_id):
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
    txn_date = None
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        screenshot = _save_uploaded_image(file, 'screenshot') or ''
        amount = float(request.form.get('amount', 0))
        note = request.form.get('note', '')
        txn_date = request.form.get('txn_date') or None
        fine = float(request.form.get('fine', 0) or 0)
        share_amount = float(request.form.get('share_amount', 0) or 0)
        loan_principal = float(request.form.get('loan_principal', 0) or 0)
        loan_interest = float(request.form.get('loan_interest', 0) or 0)
    else:
        data = request.get_json(silent=True)
        if data is None:
            data = request.form or {}
        amount = float(data.get('amount', 0))
        note = data.get('note', '')
        screenshot = data.get('screenshot', '')
        txn_date = data.get('txn_date') or None
        fine = float(data.get('fine', 0) or 0)
        share_amount = float(data.get('share_amount', 0) or 0)
        loan_principal = float(data.get('loan_principal', 0) or 0)
        loan_interest = float(data.get('loan_interest', 0) or 0)
    req = create_payment_request(member_id, amount, note, screenshot, txn_date, fine, share_amount, loan_principal, loan_interest)
    return jsonify({'status': 'submitted', 'request': req}), 201


@members_bp.route('/api/members/<int:member_id>/statement', methods=['GET'])
def member_statement(member_id):
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
    csv_text = get_member_statement(member_id)
    return (csv_text, 200, {'Content-Type': 'text/csv'})
