from flask import Blueprint, jsonify, request, render_template, current_app, session
from werkzeug.security import check_password_hash

from core.database import strip_sensitive
from core.models.member import get_all_members, find_member_by_name, get_member
from core.rate_limit import too_many, record_failure, record_success
from core.session import create_admin_session, destroy_admin_session

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    try:
        members = [strip_sensitive(m) for m in get_all_members()]
    except Exception:
        members = []
    return render_template('index.html', members=members)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name', '').strip()
    pin = data.get('pin', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    ip_key = f'ip:{request.remote_addr or "?"}'
    name_key = f'name:{name.lower()}'
    if too_many(ip_key) or too_many(name_key):
        return jsonify({'error': 'Too many failed attempts. Please wait a few minutes and try again.'}), 429
    member = find_member_by_name(name)
    if not member:
        record_failure(ip_key)
        record_failure(name_key)
        return jsonify({'error': 'Member not found'}), 404
    if not pin:
        return jsonify({'error': 'Password is needed'}), 400
    stored = member.get('password') or ''
    if not stored or not check_password_hash(stored, pin):
        record_failure(ip_key)
        record_failure(name_key)
        return jsonify({'error': 'Incorrect password'}), 401
    record_success(ip_key)
    record_success(name_key)
    result = strip_sensitive(member)
    if member['is_admin']:
        result['token'] = create_admin_session(member['member_id'])
    session['member_id'] = member['member_id']
    session.permanent = True
    return jsonify(result)


@auth_bp.route('/api/me', methods=['GET'])
def me():
    member_id = session.get('member_id')
    if not member_id:
        return jsonify({'error': 'not logged in'}), 401
    member = get_member(member_id)
    if not member:
        session.clear()
        return jsonify({'error': 'not logged in'}), 401
    result = strip_sensitive(member)
    return jsonify(result)


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('X-ADMIN-TOKEN', '')
    if token:
        destroy_admin_session(token)
    session.clear()
    return jsonify({'status': 'ok'})


@auth_bp.route('/api/client_error', methods=['POST'])
def client_error():
    data = request.get_json(silent=True) or {}
    current_app.logger.error(
        f"CLIENT_ERROR: {data.get('message')} at {data.get('url')}:{data.get('line')}:{data.get('col')} -- ua={data.get('ua')}; stack={data.get('stack')}",
    )
    return jsonify({'status': 'logged'})
