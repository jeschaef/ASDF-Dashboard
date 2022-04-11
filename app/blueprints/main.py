from flask import Blueprint, render_template
from flask_mail import Message
from app import mail

main = Blueprint('main', __name__)


# a simple page that says hello & sends a mail (blocked by testing)
@main.route('/')
def index():
    msg = Message("Hello",
                  sender="from@example.com",
                  recipients=["to@example.com"])
    mail.send(msg)
    return render_template('index.html')
