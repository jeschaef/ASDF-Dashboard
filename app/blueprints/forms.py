from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from app.auth import verify_password
from app.model import User


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Length(1, 100), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me?')
    submit = SubmitField('Log In')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
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


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=3, max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=64)])        # todo increase pw length
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
