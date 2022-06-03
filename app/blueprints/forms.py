import logging

import pandas as pd

from flask import redirect, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from pandas.errors import ParserError, EmptyDataError
from wtforms import HiddenField, PasswordField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from wtforms_components import StringField, Email, SelectField

from app.auth import verify_password
from app.blueprints.util import get_redirect_target, is_safe_url, get_user_quota
from app.model import *

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

        # Check if email (user) is known & password is correct (if user exists)
        # Also stores the user to prevent second database access
        self.user = User.query.filter_by(email=self.email.data).first()
        if not self.user or not verify_password(self.password.data, self.user.password):
            error_msg = 'Invalid email/password'
            self.email.errors.append(error_msg)
            self.password.errors.append(error_msg)
            return False

        return True


class RegisterForm(RedirectForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=USER_NAME_LENGTH)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=EMAIL_LENGTH)])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=MIN_PASSWORD_LENGTH, max=PASSWORD_LENGTH)])
    confirm = PasswordField('Verify password',
                            validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    def validate_username(self, field):
        # Check if username taken
        user = User.query.filter_by(name=field.data).first()
        if user:
            raise ValidationError("Username already registered")

    def validate_email(self, field):
        # Check if email already taken
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError("Email already registered")


class FileExceedsQuota:
    def __call__(self, form, field):
        quota = get_user_quota(current_user.id)
        max_bytes = quota['quota_free']
        if len(field.data.read()) > max_bytes:
            raise ValidationError(f"Free disk quota is {max_bytes} Bytes")


class UploadDatasetForm(RedirectForm):
    dataset = FileField("", validators=[FileRequired('No file provided!'),
                                        FileAllowed(['csv'], 'Upload must be a csv-file!'),
                                        FileExceedsQuota()])
    name = StringField('Dataset name', validators=[DataRequired(), Length(min=1, max=DATASET_NAME_LENGTH)])
    description = StringField('Dataset description (optional)')
    label_column = StringField('Class label column (default: class)')
    prediction_column = StringField('Prediction label column (default: out)')
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
            self.dataset.data.seek(0)  # prevents EmptyDataError
            df = pd.read_csv(self.dataset.data)
        except (ParserError, EmptyDataError, IOError) as err:
            self.dataset.errors.append(f"Could not read csv-data from given file due to {type(err).__name__}!")
            return False

        # Validate that either label_column is given (& contained in df) or df contains column 'class'
        success = True  # accumulate following validation errors
        label = self.label_column.data
        if label == "":
            if "class" not in df.columns:
                self.label_column.errors.append("If no column named 'class' is contained in the data, "
                                                "a class label column must be provided")
                success = False
            else:
                self.label_column.data = "class"

        else:
            if label not in df.columns:
                self.label_column.errors.append(f"Couldn't find column {label}")
                success = False

        # Validate that either prediction_column is given (& contained in df) or df contains column 'out'
        prediction = self.prediction_column.data
        if prediction == "":
            if 'out' not in df.columns:
                self.prediction_column.errors.append("If no column named 'out' is contained in the data, "
                                                     "a prediction label column must be provided")
                success = False
            else:
                self.prediction_column.data = "out"
        else:
            if prediction not in df.columns:
                self.prediction_column.errors.append(f"Couldn't find column {prediction}")
                success = False

        return success


class SelectDatasetForm(RedirectForm):
    dataset = SelectField('Select a Dataset')

    def __init__(self, owner, *args, **kwargs):
        super(SelectDatasetForm, self).__init__(*args, **kwargs)
        self.owner = owner


class ChangePasswordForm(RedirectForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired(),
                                                             Length(min=MIN_PASSWORD_LENGTH, max=PASSWORD_LENGTH)])
    confirm = PasswordField('Verify new password', validators=[DataRequired(),
                                                               EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change password')

    def __init__(self, current_user_id, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = User.query.get(current_user_id)

    def validate_old_password(self, field):
        if not verify_password(field.data, self.user.password):
            raise ValidationError('Invalid password')
