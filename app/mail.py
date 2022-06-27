from email.mime.image import MIMEImage
from os import getenv

from flask import render_template
from flask_mailman import Mail, EmailMessage

from app.util import get_project_root

mail = Mail()


def send_confirmation_mail(name, recipient, confirmation_url):
    body = render_template("mail/confirmation.html", name=name, confirmation_url=confirmation_url)
    msg = EmailMessage(subject="Confirm your registration",
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
