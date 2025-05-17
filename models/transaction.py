from mongoengine import Document, ReferenceField, FloatField, StringField, DateTimeField
from models.user import User
from datetime import datetime
from mongoengine import BooleanField

class Transaction(Document):
    user = ReferenceField(User)
    type = StringField(choices=["deposit", "withdraw", "transfer"])
    amount = FloatField()
    currency = StringField(default="INR")  # New field
    target_user = ReferenceField(User, required=False)
    timestamp = DateTimeField(default=datetime.utcnow)
    is_flagged = BooleanField(default=False)
    review_status = StringField(default="pending")  # ✅ 'pending', 'cleared', 'rejected'
    review_comment = StringField()  # ✅ optional admin note