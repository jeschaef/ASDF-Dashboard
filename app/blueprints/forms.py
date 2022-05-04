import logging

import pandas as pd

from flask import redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from pandas.errors import ParserError, EmptyDataError
from wtforms import HiddenField, PasswordField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, EqualTo
from wtforms_components import StringField, Email, SelectField

from app.auth import verify_password
from app.blueprints.util import get_redirect_target, is_safe_url
from app.model import User, Dataset, EMAIL_LENGTH, USER_NAME_LENGTH, PASSWORD_LENGTH, DATASET_NAME_LENGTH

log = logging.getLogger()


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        super(RedirectForm, self).__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))


class LoginForm(RedirectForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me?')
    submit = SubmitField('Log In')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self, **kwargs):
        # Parent validation
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        # Check if email (user) is known
        user = User.query.filter_by(email=self.email.data).first()
        if not user:
            self.email.errors.append('Unknown email')
            return False

        # Verify password
        if not verify_password(self.password.data, user.password):
            self.password.errors.append('Invalid password')
            return False

        # Store user
        self.user = user

        return True


class RegisterForm(RedirectForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=USER_NAME_LENGTH)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=EMAIL_LENGTH)])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=1, max=PASSWORD_LENGTH)])  # todo increase min pw length
    confirm = PasswordField('Verify password',
                            validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    def validate(self, **kwargs):
        # Parent validation
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False

        # Check if username taken
        user = User.query.filter_by(name=self.username.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False

        # Check if email already taken
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")
            return False
        return True


class UploadDatasetForm(RedirectForm):
    dataset = FileField('Upload a dataset',
                        validators=[FileRequired('No file provided!'),
                                    FileAllowed(['csv'], 'Upload must be a csv-file!')])
    name = StringField('Dataset name', validators=[DataRequired(), Length(min=1, max=DATASET_NAME_LENGTH)])
    description = StringField('Dataset description')
    label_column = StringField('Class label column name (default: class)')
    prediction_column = StringField('Prediction label column name (default: out)')
    submit = SubmitField('Upload')

    def __init__(self, owner, *args, **kwargs):
        super(UploadDatasetForm, self).__init__(*args, **kwargs)
        self.owner = owner

    def validate(self, **kwargs):
        # Parent validation
        initial_validation = super(UploadDatasetForm, self).validate()
        if not initial_validation:
            return False

        # Check if user already has a dataset with this name
        name = self.name.data
        log.debug(f"Running query for name={name} and owner={self.owner}")
        d = Dataset.query.filter_by(name=name, owner=self.owner).first()
        log.debug(f"Got dataset {d}")
        if d:
            self.name.errors.append(f"Dataset '{name}' already exists!")
            return False

        # Validate pandas csv parsing
        try:
            df = pd.read_csv(self.dataset.data)
        except (ParserError, EmptyDataError, IOError) as err:
            self.dataset.errors.append(f"Could not read csv-data from given file due to {type(err).__name__}!")
            return False

        # Validate that either label_column is given (& contained in df) or df contains column 'class'
        if self.label_column.data is None and 'class' not in df.columns:
            self.label_column.errors.append("If no column named 'class' is contained in the data, "
                                            "a class label column must be provided")
            return False

        if self.label_column.data not in df.columns:
            self.label_column.errors.append(f"Couldn't find column {self.label_column.data}")
            return False

        # Validate that either prediction_column is given (& contained in df) or df contains column 'out'
        if self.prediction_column.data is None and 'out' not in df.columns:
            self.prediction_column.errors.append("If no column named 'out' is contained in the data, "
                                            "a prediction label column must be provided")
            return False

        if self.prediction_column.data not in df.columns:
            self.prediction_column.errors.append(f"Couldn't find column {self.prediction_column.data}")
            return False

        return True


class SelectDatasetForm(RedirectForm):
    dataset = SelectField('Select a Dataset')

    def __init__(self, owner, *args, **kwargs):
        super(SelectDatasetForm, self).__init__(*args, **kwargs)
        self.owner = owner

    def validate(self, **kwargs):
        # Parent validation
        initial_validation = super(SelectDatasetForm, self).validate()
        if not initial_validation:
            return False
