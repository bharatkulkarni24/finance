from flask import Blueprint, jsonify, request

from core.models.loan import create_loan

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('/api/members/<int:member_id>/apply_loan', methods=['POST'])
def apply_loan(member_id):
    data = request.json
    amount = float(data.get('amount'))
    term = int(data.get('term_months', 12))
    loan = create_loan(member_id, amount, term)
    return jsonify({'loan': loan}), 201
