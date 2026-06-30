from flask import Blueprint, jsonify, request, render_template, current_app

from core.config import ADMIN_PIN
from core.models.member import get_all_members, find_member_by_name

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    try:
        members = get_all_members()
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
    if member['is_admin'] and pin != ADMIN_PIN:
        return jsonify({'error': 'Admin PIN required'}), 401
    return jsonify(member)


@auth_bp.route('/api/client_error', methods=['POST'])
def client_error():
    data = request.get_json(silent=True) or {}
    current_app.logger.error(
        f"CLIENT_ERROR: {data.get('message')} at {data.get('url')}:{data.get('line')}:{data.get('col')} -- ua={data.get('ua')}; stack={data.get('stack')}",
    )
    return jsonify({'status': 'logged'})
