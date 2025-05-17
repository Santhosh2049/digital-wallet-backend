from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.wallet import Wallet
from models.transaction import Transaction
from utils.fraud_check import check_fraud_transfer
from utils.fraud_check import check_fraud_withdraw
from utils.email import send_mock_email

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount', 0)
    currency = data.get('currency', 'INR').upper()

    if amount <= 0:
        return jsonify({"msg": "Invalid deposit amount"}), 400

    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    wallet = Wallet.objects(user=user, currency=currency).first()

    # If wallet doesn't exist, create one
    if not wallet:
        wallet = Wallet(user=user, balance=0.0, currency=currency)
    wallet.balance += amount
    wallet.save()

    # Save transaction
    txn = Transaction(user=user, type="deposit", amount=amount, currency=currency)
    txn.save()

    return jsonify({
        "msg": f"Deposit successful ({currency})",
        "new_balance": wallet.balance
    })



from models.transaction import Transaction

@wallet_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get("amount")
    currency = data.get("currency", "INR").upper()

    if amount <= 0:
        return jsonify({"msg": "Invalid amount"}), 400

    user = User.objects(id=user_id).first()
    wallet = Wallet.objects(user=user, currency=currency).first()

    if not wallet or wallet.balance < amount:
        return jsonify({"msg": "Insufficient balance"}), 400

    wallet.balance -= amount
    wallet.save()

    # ✅ Fraud Rule: Large withdrawal
    is_flagged = amount >= 50000

    txn = Transaction(
        user=user,
        type="withdraw",
        amount=amount,
        currency=currency,
        is_flagged=is_flagged
    )
    txn.save()
    
    if is_flagged:
        send_mock_email(
            to="admin@wallet.com",
            subject="🚨 Fraud Alert: Large Withdrawal",
            message=(
                f"User: {user.username}\n"
                f"Amount: ₹{amount}\n"
                f"Currency: {currency}\n"
                f"Txn ID: {txn.id}\n"
                f"Type: Withdrawal"
            )
        )

    return jsonify({
        "msg": f"Withdrawal successful ({currency})",
        "new_balance": wallet.balance,
        "flagged": is_flagged
    }), 200




@wallet_bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    from utils.fraud_check import check_fraud_transfer  # ✅ add this import at top

    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount', 0)
    target_username = data.get('to')
    currency = data.get('currency', 'INR').upper()

    if amount <= 0 or not target_username:
        return jsonify({"msg": "Invalid transfer data"}), 400

    sender = User.objects(id=user_id).first()
    receiver = User.objects(username=target_username).first()

    if not receiver or sender.id == receiver.id:
        return jsonify({"msg": "Invalid recipient"}), 400

    sender_wallet = Wallet.objects(user=sender, currency=currency).first()
    receiver_wallet = Wallet.objects(user=receiver, currency=currency).first()

    if not sender_wallet or sender_wallet.balance < amount:
        return jsonify({"msg": "Insufficient balance"}), 400

    if not receiver_wallet:
        receiver_wallet = Wallet(user=receiver, balance=0, currency=currency)

    sender_wallet.balance -= amount
    receiver_wallet.balance += amount

    sender_wallet.save()
    receiver_wallet.save()

    # 🔍 Check fraud before saving transaction
    txn = Transaction(user=sender, type="transfer", amount=amount, currency=currency, target_user=receiver)

    if check_fraud_transfer(sender, currency):
        txn.is_flagged = True
        send_mock_email(
            to="admin@wallet.com",
            subject="🚨 Fraud Alert: Frequent Transfers",
            message=(
                f"User: {sender.username}\n"
                f"Amount: ₹{amount}\n"
                f"Currency: {currency}\n"
                f"To: {receiver.username}\n"
                f"Txn ID: {txn.id}\n"
                f"Type: Transfer"
            )
        )

    txn.save()

    # Log deposit for receiver (not flagged)
    Transaction(user=receiver, type="deposit", amount=amount, currency=currency).save()

    return jsonify({
        "msg": f"Transferred ₹{amount} {currency} to {target_username} successfully",
        "flagged": txn.is_flagged
    })

@wallet_bp.route('/summary', methods=['GET'])
@jwt_required()
def wallet_summary():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    wallets = Wallet.objects(user=user)

    summary = []
    for wallet in wallets:
        summary.append({
            "currency": wallet.currency,
            "balance": round(wallet.balance, 2)
        })

    return jsonify({
        "username": user.username,
        "wallets": summary
    }), 200

@wallet_bp.route('/transactions', methods=['GET'])
@jwt_required()
def transaction_history():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    txns = Transaction.objects(user=user).order_by('-timestamp')

    history = []
    for txn in txns:
        entry = {
            "type": txn.type,
            "amount": txn.amount,
            "timestamp": txn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        if txn.type == "transfer":
            entry["to"] = txn.target_user.username if txn.target_user else "Unknown"
        history.append(entry)

    return jsonify(history)
