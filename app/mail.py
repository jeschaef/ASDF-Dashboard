from flask import render_template
from flask_mailman import Mail, EmailMessage

mail = Mail()


def send_confirmation_mail(name, recipient, confirmation_url):
    body = render_template("mail/confirmation.html", name=name, confirmation_url=confirmation_url)
    msg = EmailMessage(subject="Confirm your registration",
                        body=body,
                        from_email="noreply@example.com",
                        to=[recipient])

    msg.content_subtype = 'html'
    msg.send()
