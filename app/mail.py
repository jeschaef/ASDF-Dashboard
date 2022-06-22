from os import getenv

from flask import render_template
from flask_mailman import Mail, EmailMessage

from app.util import get_project_root

mail = Mail()


def send_confirmation_mail(app, name, recipient, confirmation_url):
    body = render_template("mail/confirmation.html", name=name, confirmation_url=confirmation_url)
    msg = EmailMessage(subject="Confirm your registration",
                        body=body,
                        from_email=getenv("MAIL_SENDER", "noreply@example.com"),
                        to=[recipient])
    msg.content_subtype = 'html'

    # Embed logo
    file_path = get_project_root() / "static/logo.png"
    with app.open_resource(file_path) as res:
        msg.attach(filename="logo.png",  content=res.read(), mimetype='image/png',
                    headers=[['Content-ID', '<logo_png>']])

    msg.send()
