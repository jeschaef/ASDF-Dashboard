import logging

import email_validator
import pandas as pd

from flask import redirect, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from pandas.errors import ParserError, EmptyDataError
from wtforms import HiddenField, PasswordField, BooleanField, SubmitField, FileField, StringField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp, Email

from app.auth import verify_password
from app.blueprints.util import get_redirect_target, is_safe_url, get_user_quota
from app.model import *

log = logging.getLogger()


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, was_submitted=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''
        self.was_submitted = was_submitted

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

    def is_submitted(self):
        # to handle multiple forms on one page, add attribute was submitted to submission check
        return self.was_submitted and super().is_submitted()


class LoginForm(RedirectForm):
    email_or_username = StringField('Email/Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me?')
    submit = SubmitField('Log In')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, **kwargs):
        # Parent validation
        initial_validation = super().validate()
        if not initial_validation:
            return False

        # Check if email/username is known & password is correct (if user exists)
        # Also stores the user to prevent second database access
        user = User.query.filter_by(email=self.email_or_username.data).first()
        if not user:  # not found by email
            user = User.query.filter_by(name=self.email_or_username.data).first()

        if not user or not verify_password(self.password.data, user.password):
            error_msg = 'Invalid email/password'
            self.email_or_username.errors.append(error_msg)
            self.password.errors.append(error_msg)
            return False

        self.user = user
        return True


def _check_password(password):
    # Count lowercase, uppercase and numbers
    lowers = uppers = digits = 0
    for ch in password:
        if ch.islower():
            lowers += 1
        if ch.isupper():
            uppers += 1
        if ch.isdigit():
            digits += 1
    if not (lowers and uppers and digits):
        raise ValidationError(
            "Password must contain at least one digit and both a lower case and an upper case letter.")


class RegisterForm(RedirectForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=USER_NAME_LENGTH),
                                                   Regexp("^[a-zA-Z0-9_\\-\\.]+$",
                                                          message="Only alphanumeric characters and '_', '-' or '.' "
                                                                  "are allowed")
                                                   ])
    email = StringField('Email', validators=[DataRequired(),
                                             Email(check_deliverability=False),   # just syntax check
                                             Length(max=EMAIL_LENGTH)])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=MIN_PASSWORD_LENGTH, max=PASSWORD_LENGTH)])
    confirm = PasswordField('Verify password',
                            validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def validate_password(self, field):
        _check_password(field.data)


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
        super().__init__(*args, **kwargs)
        self.owner = owner

    def validate(self, **kwargs):
        # Parent validation
        initial_validation = super().validate()
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
        super().__init__(*args, **kwargs)
        self.owner = owner


class ChangePasswordForm(RedirectForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired(),
                                                             Length(min=MIN_PASSWORD_LENGTH, max=PASSWORD_LENGTH)])
    confirm = PasswordField('Verify new password', validators=[DataRequired(),
                                                               EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change password')

    def __init__(self, current_user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = current_user_id

    def validate_old_password(self, field):
        user = User.query.get(self.owner)
        if not verify_password(field.data, user.password):
            raise ValidationError('Invalid password')

    def validate_new_password(self, field):
        _check_password(field.data)


class PasswordConfirmationForm(RedirectForm):
    password = PasswordField('Enter your password for confirmation', validators=[DataRequired()])

    def __init__(self, current_user_id, field_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = current_user_id
        self.password.id = field_id

    def validate_password(self, field):
        user = User.query.get(self.owner)
        if not verify_password(field.data, user.password):
            raise ValidationError('Invalid password')


class ForgotPasswordForm(RedirectForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=EMAIL_LENGTH)])
    submit = SubmitField('Send email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_email(self, field):
        # Check if an account with this email exists
        user = User.query.filter_by(email=field.data).first()
        if not user:
            raise ValidationError("Email not registered")


class ResetPasswordForm(RedirectForm):
    password = PasswordField('New password', validators=[DataRequired(),
                                                             Length(min=MIN_PASSWORD_LENGTH, max=PASSWORD_LENGTH)])
    confirm = PasswordField('Verify new password', validators=[DataRequired(),
                                                               EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Confirm')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_password(self, field):
        _check_password(field.data)
