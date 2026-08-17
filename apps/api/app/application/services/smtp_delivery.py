import smtplib
from email.message import EmailMessage

from app.application.security import decrypt_secret
from app.domain.models import Message, SMTPProvider, SenderIdentity

SMTP_EXCEPTIONS = (smtplib.SMTPException, OSError, TimeoutError, ValueError)


def build_smtp_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message or "SMTP connection failed"


def open_smtp_connection(provider: SMTPProvider, timeout: int) -> smtplib.SMTP:
    if provider.use_ssl:
        client = smtplib.SMTP_SSL(provider.host, provider.port, timeout=timeout)
    else:
        client = smtplib.SMTP(provider.host, provider.port, timeout=timeout)
        client.ehlo()
        if provider.use_tls:
            client.starttls()
            client.ehlo()

    if provider.username:
        password = decrypt_secret(provider.password_encrypted) if provider.password_encrypted else ""
        client.login(provider.username, password)

    return client


def test_smtp_connection(provider: SMTPProvider, timeout: int) -> tuple[bool, str]:
    try:
        client = open_smtp_connection(provider, timeout)
        client.quit()
        return True, "SMTP connection successful"
    except SMTP_EXCEPTIONS as exc:
        return False, build_smtp_error_message(exc)


def build_email_message(message: Message, sender_identity: SenderIdentity) -> EmailMessage:
    email_message = EmailMessage()
    email_message["Subject"] = message.subject
    email_message["From"] = (
        f"{sender_identity.display_name} <{sender_identity.from_email}>"
        if sender_identity.display_name
        else sender_identity.from_email
    )
    email_message["To"] = message.recipient_email
    if sender_identity.reply_to_email:
        email_message["Reply-To"] = sender_identity.reply_to_email
    email_message.set_content(message.body_text)
    if message.body_html:
        email_message.add_alternative(message.body_html, subtype="html")
    return email_message


def send_smtp_message(
    provider: SMTPProvider,
    sender_identity: SenderIdentity,
    message: Message,
    timeout: int,
) -> None:
    client = open_smtp_connection(provider, timeout)
    try:
        email_message = build_email_message(message, sender_identity)
        client.send_message(email_message)
    finally:
        client.quit()
