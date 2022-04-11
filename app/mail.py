from flask_mail import Mail, email_dispatched

mail = Mail()


def log_message(message, app):
    app.logger.debug(f"Sent mail: {message.subject}")


email_dispatched.connect(log_message)
