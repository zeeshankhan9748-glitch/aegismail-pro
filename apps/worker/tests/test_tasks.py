import smtplib

from app.application.security import encrypt_secret
from app.domain.models import Message, SMTPProvider, SenderIdentity
from app.infrastructure.database import SessionLocal
from worker_app.tasks import send_email_task, settings


class RetryRequested(Exception):
    pass


def seed_message():
    session = SessionLocal()
    provider = SMTPProvider(
        name="Primary SMTP",
        host="smtp.example.com",
        port=587,
        username="mailer",
        password_encrypted=encrypt_secret("top-secret"),
        use_tls=True,
        use_ssl=False,
        throttle_limit_per_minute=60,
    )
    session.add(provider)
    session.flush()

    sender_identity = SenderIdentity(
        smtp_provider=provider,
        display_name="Demo Sender",
        from_email="noreply@example.com",
        reply_to_email="support@example.com",
    )
    session.add(sender_identity)
    session.flush()

    message = Message(
        provider=provider,
        sender_identity=sender_identity,
        recipient_email="hello@example.com",
        subject="Hello",
        body_text="Plain body",
        body_html="<p>HTML body</p>",
        status="queued",
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    session.close()
    return message.id


def load_message(message_id: int) -> Message:
    session = SessionLocal()
    message = session.get(Message, message_id)
    assert message is not None
    session.expunge(message)
    session.close()
    return message


def test_send_email_task_marks_message_sent(monkeypatch):
    message_id = seed_message()
    monkeypatch.setattr("worker_app.tasks.send_smtp_message", lambda *args, **kwargs: None)

    result = send_email_task(message_id)

    message = load_message(message_id)
    assert result["status"] == "sent"
    assert message.status == "sent"
    assert message.sent_at is not None
    assert message.attempt_count == 0


def test_send_email_task_defers_and_retries_on_failure(monkeypatch):
    message_id = seed_message()

    def raise_smtp_error(*args, **kwargs):
        raise smtplib.SMTPServerDisconnected("temporary outage")

    def fake_retry(**kwargs):
        raise RetryRequested(kwargs)

    monkeypatch.setattr("worker_app.tasks.send_smtp_message", raise_smtp_error)
    monkeypatch.setattr(send_email_task, "retry", fake_retry)

    try:
        send_email_task(message_id)
    except RetryRequested:
        pass
    else:
        raise AssertionError("Expected retry to be requested")

    message = load_message(message_id)
    assert message.status == "deferred"
    assert message.attempt_count == 1
    assert message.error_message == "temporary outage"


def test_send_email_task_marks_terminal_failure(monkeypatch):
    message_id = seed_message()
    previous_attempts = settings.smtp_max_send_attempts
    settings.smtp_max_send_attempts = 1

    try:
        monkeypatch.setattr(
            "worker_app.tasks.send_smtp_message",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                smtplib.SMTPServerDisconnected("permanent outage")
            ),
        )

        result = send_email_task(message_id)
    finally:
        settings.smtp_max_send_attempts = previous_attempts

    message = load_message(message_id)
    assert result["status"] == "failed"
    assert message.status == "failed"
    assert message.attempt_count == 1
    assert message.error_message == "permanent outage"
