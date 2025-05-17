from datetime import datetime, timedelta
from models.transaction import Transaction
from models.user import User

def check_fraud_transfer(user, currency):
    now = datetime.utcnow()
    one_min_ago = now - timedelta(minutes=1)

    recent_transfers = Transaction.objects(
        user=user,
        type="transfer",
        currency=currency,
        timestamp__gte=one_min_ago
    )

    if recent_transfers.count() >= 5:
        return True
    return False

def check_fraud_withdraw(amount):
    return amount > 50000
