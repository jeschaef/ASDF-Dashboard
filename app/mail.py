import logging
from email.mime.image import MIMEImage
from os import getenv

from flask import render_template
from flask_mailman import Mail, EmailMessage

from app.util import get_project_root

mail = Mail()
log = logging.getLogger()


def send_confirmation_mail(name, recipient, confirmation_url):
    body = render_template("mail/confirmation.html", name=name, confirmation_url=confirmation_url)
    send_mail(body, recipient, "Confirm your registration")
    log.info(f"Sent confirmation email to {recipient}")


def send_password_reset_mail(name, recipient, reset_url):
    body = render_template("mail/reset_password.html", name=name, reset_url=reset_url)
    send_mail(body, recipient, "Reset your password")
    log.info(f"Sent reset password email to {recipient}")


def send_mail(body, recipient, subject):
    msg = EmailMessage(subject=subject,
                       body=body,
                       from_email=getenv("MAIL_SENDER", "noreply@example.com"),
                       to=[recipient])
    msg.content_subtype = 'html'

    # Embed logo
    file_path = get_project_root() / "static/logo.png"
    with open(file_path, 'rb') as res:
        msg_logo = MIMEImage(res.read())
        msg_logo.add_header('Content-ID', '<logo_png>')
        msg_logo.add_header('Content-Disposition', 'inline', filename='logo.png')
        msg.attach(msg_logo)
    msg.send()
