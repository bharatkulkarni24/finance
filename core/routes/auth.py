from flask import Blueprint, jsonify, request, render_template, current_app
from werkzeug.security import check_password_hash

from core.config import ADMIN_PIN
from core.database import strip_sensitive
from core.models.member import get_all_members, find_member_by_name

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
    member = find_member_by_name(name)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    if member['is_admin']:
        if pin != ADMIN_PIN:
            return jsonify({'error': 'Admin PIN required'}), 401
    else:
        stored = member.get('password') or ''
        if stored and not check_password_hash(stored, pin):
            return jsonify({'error': 'Incorrect password'}), 401
    return jsonify(strip_sensitive(member))


@auth_bp.route('/api/client_error', methods=['POST'])
def client_error():
    data = request.get_json(silent=True) or {}
    current_app.logger.error(
        f"CLIENT_ERROR: {data.get('message')} at {data.get('url')}:{data.get('line')}:{data.get('col')} -- ua={data.get('ua')}; stack={data.get('stack')}",
    )
    return jsonify({'status': 'logged'})
