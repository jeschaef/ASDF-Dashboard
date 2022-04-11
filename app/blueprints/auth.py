from flask import Blueprint, render_template, redirect

from app.blueprints.forms import RegisterForm, LoginForm

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        return "Success"
    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return "Success"
    return render_template('auth/login.html', form=form)