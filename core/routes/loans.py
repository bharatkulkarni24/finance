from datetime import datetime

from flask import Blueprint, jsonify, request

from core.models.loan import create_loan, get_loan, compute_interest_accrued, apply_payment_to_loan

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('/api/members/<int:member_id>/apply_loan', methods=['POST'])
def apply_loan(member_id):
    data = request.json
    amount = float(data.get('amount'))
    term = int(data.get('term_months', 12))
    loan = create_loan(member_id, amount, term)
    return jsonify({'loan': loan}), 201


@loans_bp.route('/api/members/<int:member_id>/pay_loan', methods=['POST'])
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
