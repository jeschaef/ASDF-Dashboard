from app.db import db


class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # 36 chars = 32 hex digits + 4 dashes
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String, unique=True, nullable=False)
    password = db.column(db.String)
