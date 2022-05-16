import datetime
import uuid

from flask_login import UserMixin
from app.db import db

UUID_LENGTH = 36  # 36 chars = 32 hex digits + 4 dashes
EMAIL_LENGTH = 100
USER_NAME_LENGTH = 20
PASSWORD_LENGTH = 64
DATASET_NAME_LENGTH = 30
FILE_NAME_LENGTH = 50


class User(db.Model, UserMixin):
    id = db.Column(db.String(UUID_LENGTH), primary_key=True)
    email = db.Column(db.String(EMAIL_LENGTH), unique=True, nullable=False)
    name = db.Column(db.String(USER_NAME_LENGTH), unique=True, nullable=False)  # todo upper limit
    password = db.Column(db.String(PASSWORD_LENGTH))
    session_token = db.Column(db.String(UUID_LENGTH), unique=True, index=True)  # alternative user id (for session)
    datasets = db.relationship('Dataset')
    tasks = db.relationship('Task', lazy='select')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.id = uuid.uuid4().hex  # auto-generate id

    def __str__(self):
        return f"User[id={self.id}, email={self.email}, name={self.name}, session_token={self.session_token}]"

    def get_id(self):
        return self.session_token   # return session token instead of id (for login manager)


class Dataset(db.Model):
    __table_args__ = (
        db.UniqueConstraint('name', 'owner', name='unique_name_owner'),
    )
    id = db.Column(db.String(UUID_LENGTH), primary_key=True)
    name = db.Column(db.String(DATASET_NAME_LENGTH), nullable=False)
    owner = db.Column(db.String(UUID_LENGTH), db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime)
    label_column = db.Column(db.String)
    prediction_column = db.Column(db.String)

    def __init__(self, *args, **kwargs):
        super(Dataset, self).__init__(*args, **kwargs)
        self.id = uuid.uuid4().hex  # auto-generate id
        self.upload_date = datetime.datetime.now()  # set upload date on creation

    def __str__(self):
        return f"Dataset[id={self.id}, name={self.name}, owner={self.owner}, " \
               f"label_column={self.label_column}, prediction_column={self.prediction_column}]"


class Task(db.Model):
    id = db.Column(db.String(UUID_LENGTH), primary_key=True)
    owner = db.Column(db.String(UUID_LENGTH), db.ForeignKey('user.id'), nullable=False)

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)

    def __str__(self):
        return f"Task[id={self.id}, owner={self.owner}]"
