"""Tests for Phase 4: process_import_job Celery task."""

from app.domain.models import Contact, ContactList, ContactListMember, ImportJob, SuppressionEntry
from app.infrastructure.database import SessionLocal
from worker_app.tasks import process_import_job


def _make_job(csv_data, contact_list_id=None, column_mapping=None):
    session = SessionLocal()
    job = ImportJob(
        filename="test.csv",
        status="pending",
        csv_data=csv_data,
        column_mapping=column_mapping,
        contact_list_id=contact_list_id,
    )
    session.add(job)
    session.commit()
    job_id = job.id
    session.close()
    return job_id


def _get_job(job_id):
    session = SessionLocal()
    job = session.get(ImportJob, job_id)
    session.expunge(job)
    session.close()
    return job


def _count_contacts():
    session = SessionLocal()
    from sqlalchemy import func, select
    count = session.scalar(select(func.count()).select_from(Contact))
    session.close()
    return count


def test_import_happy_path():
    csv_data = "email,first_name,last_name\nalice@example.com,Alice,Smith\nbob@example.com,Bob,Jones\n"
    job_id = _make_job(csv_data)
    result = process_import_job(job_id)
    assert result["status"] == "completed"
    assert result["imported"] == 2
    assert result["skipped"] == 0
    assert result["errors"] == 0
    assert _count_contacts() == 2


def test_import_with_invalid_email():
    csv_data = "email,first_name\ngood@example.com,Good\nnot-an-email,Bad\n"
    job_id = _make_job(csv_data)
    result = process_import_job(job_id)
    assert result["status"] == "completed"
    assert result["imported"] == 1
    assert result["errors"] == 1

    job = _get_job(job_id)
    assert job.error_report is not None
    assert len(job.error_report) == 1
    assert "Invalid email" in job.error_report[0]["error"]


def test_import_skips_suppressed_email():
    # Add suppression entry
    session = SessionLocal()
    session.add(SuppressionEntry(email="suppressed@example.com", reason="manual", source="test"))
    session.commit()
    session.close()

    csv_data = "email\nclean@example.com\nsuppressed@example.com\n"
    job_id = _make_job(csv_data)
    result = process_import_job(job_id)
    assert result["imported"] == 1
    assert result["skipped"] == 1
    assert result["errors"] == 0


def test_import_upserts_existing_contact():
    session = SessionLocal()
    session.add(Contact(email="existing@example.com", first_name="Old", status="active"))
    session.commit()
    session.close()

    csv_data = "email,first_name\nexisting@example.com,New\n"
    job_id = _make_job(csv_data)
    result = process_import_job(job_id)
    assert result["imported"] == 1

    session = SessionLocal()
    from sqlalchemy import select
    contact = session.scalar(select(Contact).where(Contact.email == "existing@example.com"))
    assert contact.first_name == "New"
    session.close()


def test_import_adds_to_contact_list():
    session = SessionLocal()
    cl = ContactList(name="TestList")
    session.add(cl)
    session.commit()
    list_id = cl.id
    session.close()

    csv_data = "email\nlistmember@example.com\n"
    job_id = _make_job(csv_data, contact_list_id=list_id)
    result = process_import_job(job_id)
    assert result["imported"] == 1

    session = SessionLocal()
    from sqlalchemy import func, select
    member_count = session.scalar(
        select(func.count()).where(ContactListMember.contact_list_id == list_id)
    )
    session.close()
    assert member_count == 1


def test_import_with_column_mapping():
    csv_data = "Email Address,Given Name\nmapped@example.com,Carol\n"
    mapping = {"email": "Email Address", "first_name": "Given Name"}
    job_id = _make_job(csv_data, column_mapping=mapping)
    result = process_import_job(job_id)
    assert result["status"] == "completed"
    assert result["imported"] == 1

    session = SessionLocal()
    from sqlalchemy import select
    contact = session.scalar(select(Contact).where(Contact.email == "mapped@example.com"))
    assert contact is not None
    assert contact.first_name == "Carol"
    session.close()


def test_import_sets_completed_at():
    csv_data = "email\nts@example.com\n"
    job_id = _make_job(csv_data)
    process_import_job(job_id)
    job = _get_job(job_id)
    assert job.status == "completed"
    assert job.completed_at is not None


def test_import_missing_job_returns_missing():
    result = process_import_job(999999)
    assert result["status"] == "missing"
