from mongoengine import Document, ReferenceField, FloatField, StringField
from models.user import User

class Wallet(Document):
    user = ReferenceField(User, required=True)
    currency = StringField(required=True)
    balance = FloatField(default=0.0)

    meta = {
        'indexes': [
            {'fields': ['user', 'currency'], 'unique': True}  # ✅ Unique by (user, currency)
        ]
    }
