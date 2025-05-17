from flask import Blueprint, jsonify
from models.transaction import Transaction
from models.wallet import Wallet
from models.user import User
from collections import defaultdict
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__)

# View all flagged transactions
@admin_bp.route('/flagged-transactions', methods=['GET'])
@jwt_required()
def flagged_transactions():
    identity = get_jwt_identity()
    user = User.objects(id=identity).first()

    if not user or user.role != "admin":
        return jsonify({"msg": "Forbidden: Admin access required"}), 403

    flagged = Transaction.objects(is_flagged=True).order_by('-timestamp')

    results = []
    for txn in flagged:
        results.append({
            "txn_id": str(txn.id),
            "user": txn.user.username if txn.user else "Unknown",
            "type": txn.type,
            "amount": txn.amount,
            "currency": txn.currency,
            "timestamp": txn.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "target_user": txn.target_user.username if txn.target_user else None,
            "review_status": txn.review_status,
            "review_comment": txn.review_comment or ""
        })

    return jsonify(results), 200

# Top users by total balance across all currencies
@admin_bp.route('/top-users', methods=['GET'])
@jwt_required()
def top_users_by_balance():
    identity = get_jwt_identity()
    user = User.objects(id=identity).first()

    if not user or user.role != "admin":
        return jsonify({"msg": "Forbidden: Admin access required"}), 403

    user_totals = {}

    for wallet in Wallet.objects:
        username = wallet.user.username
        user_totals.setdefault(username, 0)
        user_totals[username] += wallet.balance

    sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)

    top_users = [{"username": user, "total_balance": round(balance, 2)} for user, balance in sorted_users[:10]]

    return jsonify(top_users), 200

# Total wallet balances by currency (system-wide)
@admin_bp.route('/total-balances', methods=['GET'])
@jwt_required()
def total_balances_by_currency():
    identity = get_jwt_identity()
    user = User.objects(id=identity).first()

    if not user or user.role != "admin":
        return jsonify({"msg": "Forbidden: Admin access required"}), 403
    totals = defaultdict(float)

    for wallet in Wallet.objects:
        totals[wallet.currency] += wallet.balance

    return jsonify({currency: round(balance, 2) for currency, balance in totals.items()}), 200

@admin_bp.route('/review-flagged', methods=['POST'])
@jwt_required()
def review_flagged_transaction():
    identity = get_jwt_identity()
    admin_user = User.objects(id=identity).first()

    if not admin_user or admin_user.role != "admin":
        return jsonify({"msg": "Forbidden: Admin access required"}), 403

    data = request.get_json()
    txn_id = data.get("txn_id")
    status = data.get("status")  # 'cleared' or 'rejected'
    comment = data.get("review_comment", "")

    if status not in ["cleared", "rejected"]:
        return jsonify({"msg": "Invalid status. Must be 'cleared' or 'rejected'."}), 400

    txn = Transaction.objects(id=txn_id).first()
    if not txn:
        return jsonify({"msg": "Transaction not found"}), 404
    if not txn.is_flagged:
        return jsonify({"msg": "This transaction is not flagged"}), 400

    txn.review_status = status
    txn.review_comment = comment
    txn.save()

    return jsonify({
        "msg": f"Transaction marked as {status}.",
        "txn_id": str(txn.id),
        "review_comment": txn.review_comment
    }), 200