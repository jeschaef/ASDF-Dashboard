import uuid

from flask_login import UserMixin
from app.db import db


class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True)  # 36 chars = 32 hex digits + 4 dashes
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String)
    session_token = db.Column(db.String(36), unique=True, index=True)    # alternative user id (for each session)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.id = uuid.uuid4().hex

    def __str__(self):
        return f"User[id={self.id}, email={self.email}, name={self.name}, session_token={self.session_token}]"

    def get_id(self):
        return self.session_token
