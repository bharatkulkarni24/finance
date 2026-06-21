from flask import Flask, jsonify, request, render_template
import logging
import traceback
from logging.handlers import RotatingFileHandler
from flask_cors import CORS
from models import (
    init_db,
    seed_db,
    get_all_members,
    create_member,
    find_member_by_name,
    get_member,
    update_member,
    add_contribution,
    create_loan,
    get_loan,
    approve_loan,
    compute_interest_accrued,
    apply_payment_to_loan,
    pay_due,
    get_member_statement,
)
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

ADMIN_PIN = '1234'

# ensure logs directory
os.makedirs('logs', exist_ok=True)
logfile = os.path.join('logs', 'server.log')
handler = RotatingFileHandler(logfile, maxBytes=5000000, backupCount=2)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


@app.before_request
def log_request_info():
    app.logger.info(f"REQUEST {request.method} {request.path} from {request.remote_addr}")


@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({'error': 'not_found', 'message': 'The requested URL was not found on the server.'}), 404


@app.errorhandler(500)
def handle_exception(e):
    tb = traceback.format_exc()
    app.logger.error(f"Exception on {request.path}: {str(e)}\n{tb}")
    return jsonify({'error': 'internal_server_error', 'message': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    # return last 100 lines
    try:
        with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-500:]
        return jsonify({'lines': lines})
    except Exception as ex:
        app.logger.error(f"Failed to read logs: {ex}")
        return jsonify({'error': 'failed to read logs'}), 500


@app.route('/')
def index():
    # server-render members list as a fallback for clients with cached/broken JS
    try:
        members = get_all_members()
    except Exception:
        members = []
    return render_template('index.html', members=members)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name', '').strip()
    pin = data.get('pin', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    member = find_member_by_name(name)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    if member['is_admin'] and pin != ADMIN_PIN:
        return jsonify({'error': 'Admin PIN required'}), 401
    return jsonify(member)


@app.route('/api/members', methods=['GET', 'POST'])
def members():
    if request.method == 'GET':
        ms = get_all_members()
        return jsonify(ms)
    data = request.json
    m = create_member(
        data.get('name'),
        data.get('phone', ''),
        int(data.get('is_admin', 0)),
        data.get('dob', ''),
        data.get('address', ''),
        data.get('photo_url', ''),
    )
    return jsonify(m), 201


@app.route('/api/members/<int:member_id>', methods=['PATCH'])
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


@app.route('/api/members/<int:member_id>/self', methods=['PATCH'])
def self_update_member(member_id):
    # allow member to update own basic details without admin pin
    data = request.json or {}
    phone = data.get('phone')
    dob = data.get('dob')
    address = data.get('address')
    photo_url = data.get('photo_url')
    member = update_member(member_id, phone=phone, dob=dob, address=address, photo_url=photo_url)
    if not member:
        return jsonify({'error': 'not found'}), 404
    return jsonify(member)


@app.route('/api/members/<int:member_id>/upload_photo', methods=['POST'])
def upload_member_photo(member_id):
    if 'photo' not in request.files:
        return jsonify({'error': 'no file'}), 400
    file = request.files['photo']
    if not file.filename:
        return jsonify({'error': 'no filename'}), 400
    uploads = os.path.join(app.static_folder, 'uploads')
    os.makedirs(uploads, exist_ok=True)
    fn = secure_filename(f"profile_{member_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    path = os.path.join(uploads, fn)
    file.save(path)
    photo_url = f"/static/uploads/{fn}"
    member = update_member(member_id, photo_url=photo_url)
    return jsonify({'status': 'ok', 'member': member})


@app.route('/api/members/<int:member_id>', methods=['GET'])
def get_member_route(member_id):
    m = get_member(member_id, full=True)
    if not m:
        return jsonify({'error': 'not found'}), 404
    for loan in m.get('loans', []):
        if loan['status'] == 'active':
            compute_interest_accrued(loan, datetime.utcnow().date())
    m = get_member(member_id, full=True)
    return jsonify(m)


@app.route('/api/members/<int:member_id>/contribute', methods=['POST'])
def contribute(member_id):
    data = request.json
    amount = float(data.get('amount', 0))
    when = datetime.utcnow().date()
    add_contribution(member_id, when, amount, 'share')
    return jsonify({'status': 'ok'})


@app.route('/api/members/<int:member_id>/submit_payment_request', methods=['POST'])
def submit_payment_request(member_id):
    # accept multipart/form-data (with file) or JSON
    txn_date = None
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        if file.filename:
            uploads = os.path.join(app.static_folder, 'uploads')
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
    else:
        # Accept JSON or form-encoded data when no file present
        data = request.get_json(silent=True)
        if data is None:
            data = request.form or {}
        amount = float(data.get('amount', 0))
        ptype = data.get('type', 'share')
        note = data.get('note', '')
        screenshot = data.get('screenshot', '')
        txn_date = data.get('txn_date') or None
    from models import create_payment_request
    req = create_payment_request(member_id, amount, ptype, note, screenshot, txn_date)
    return jsonify({'status': 'submitted', 'request': req}), 201


@app.route('/api/admin/payment_requests', methods=['GET'])
def admin_payment_requests():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    from models import list_pending_requests
    items = list_pending_requests()
    return jsonify(items)


@app.route('/api/admin/approve_request/<int:req_id>', methods=['POST'])
def admin_approve_request(req_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    from models import approve_payment_request
    res = approve_payment_request(req_id, approver_id=0)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'approved', 'request': res})


@app.route('/api/admin/reject_request/<int:req_id>', methods=['POST'])
def admin_reject_request(req_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    reason = data.get('reason', '')
    from models import reject_payment_request
    res = reject_payment_request(req_id, approver_id=0, reason=reason)
    if not res:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'rejected', 'request': res})


@app.route('/api/members/<int:member_id>/cancel_request/<int:req_id>', methods=['POST'])
def cancel_request(member_id, req_id):
    from models import cancel_payment_request
    res = cancel_payment_request(req_id, member_id)
    if not res:
        return jsonify({'error': 'not found or cannot cancel'}), 404
    return jsonify({'status': 'cancelled', 'request': res})


@app.route('/api/admin/add_funds', methods=['POST'])
def admin_add_funds_route():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    amount = float(data.get('amount', 0))
    note = data.get('note', 'Admin add funds')
    from models import admin_add_funds
    t = admin_add_funds(amount, note)
    return jsonify({'status': 'ok', 'transaction': t})


@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    from models import get_admin_stats
    return jsonify(get_admin_stats())


@app.route('/api/client_error', methods=['POST'])
def client_error():
    data = request.get_json(silent=True) or {}
    # log client error details for debugging
    app.logger.error(f"CLIENT_ERROR: {data.get('message')} at {data.get('url')}:{data.get('line')}:{data.get('col')} -- ua={data.get('ua')}; stack={data.get('stack')}")
    return jsonify({'status': 'logged'})


@app.route('/api/members/<int:member_id>/apply_loan', methods=['POST'])
def apply_loan(member_id):
    data = request.json
    amount = float(data.get('amount'))
    term = int(data.get('term_months', 12))
    loan = create_loan(member_id, amount, term)
    return jsonify({'loan': loan}), 201


@app.route('/api/admin/approve_loan/<int:loan_id>', methods=['POST'])
def approve_loan_route(loan_id):
    pin = request.headers.get('X-ADMIN-PIN', '')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'unauthorized'}), 401
    approve_loan(loan_id)
    loan = get_loan(loan_id)
    return jsonify({'status': 'approved', 'loan': loan})


@app.route('/api/members/<int:member_id>/pay_loan', methods=['POST'])
def pay_loan(member_id):
    data = request.json
    amount = float(data.get('amount'))
    loan_id = int(data.get('loan_id'))
    loan = get_loan(loan_id)
    if not loan:
        return jsonify({'error': 'loan not found'}), 404
    compute_interest_accrued(loan, datetime.utcnow().date())
    payment = apply_payment_to_loan(loan, amount)
    return jsonify({'status': 'ok', 'payment': payment, 'loan': loan})


@app.route('/api/members/<int:member_id>/pay_due', methods=['POST'])
def pay_due_route(member_id):
    data = request.json
    due_id = int(data.get('due_id'))
    amount = float(data.get('amount'))
    due = pay_due(member_id, due_id, amount)
    return jsonify({'status': 'ok', 'due': due})


@app.route('/api/members/<int:member_id>/statement', methods=['GET'])
def member_statement(member_id):
    csv_text = get_member_statement(member_id)
    return (csv_text, 200, {'Content-Type': 'text/csv'})


if __name__ == '__main__':
    init_db()
    seed_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
