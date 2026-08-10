from flask import Blueprint, jsonify, request

from core.models.loan import create_loan
from core.session import require_self_or_admin

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('/api/members/<int:member_id>/apply_loan', methods=['POST'])
def apply_loan(member_id):
    if not require_self_or_admin(member_id):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json
    amount = float(data.get('amount'))
    term = int(data.get('term_months', 12))
    req = create_loan(member_id, amount, term)
    return jsonify({'request': req}), 201
