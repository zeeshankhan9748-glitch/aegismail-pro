"""Contacts application service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Contact, ContactList, ContactListMember


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


def upsert_contact(
    db: Session,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    custom_fields: dict | None = None,
    status: str = "active",
) -> tuple[Contact, bool]:
    """Return (contact, created).  If contact with *email* exists, update fields."""
    normalized = email.strip().lower()
    contact = db.scalar(select(Contact).where(Contact.email == normalized))
    if contact is None:
        contact = Contact(
            email=normalized,
            first_name=first_name,
            last_name=last_name,
            custom_fields=custom_fields,
            status=status,
        )
        db.add(contact)
        return contact, True
    # Update existing
    if first_name is not None:
        contact.first_name = first_name
    if last_name is not None:
        contact.last_name = last_name
    if custom_fields is not None:
        contact.custom_fields = {**(contact.custom_fields or {}), **custom_fields}
    return contact, False


def get_contact_list_count(db: Session, contact_id: int) -> int:
    return db.scalar(
        select(func.count()).where(ContactListMember.contact_id == contact_id)
    ) or 0


# ---------------------------------------------------------------------------
# Contact list membership
# ---------------------------------------------------------------------------


def add_contact_to_list(
    db: Session, contact_list_id: int, contact_id: int
) -> ContactListMember:
    """Add contact to list; silently no-ops if already a member."""
    existing = db.scalar(
        select(ContactListMember).where(
            ContactListMember.contact_list_id == contact_list_id,
            ContactListMember.contact_id == contact_id,
        )
    )
    if existing:
        return existing
    member = ContactListMember(contact_list_id=contact_list_id, contact_id=contact_id)
    db.add(member)
    return member


def remove_contact_from_list(
    db: Session, contact_list_id: int, contact_id: int
) -> bool:
    """Remove contact from list; returns True if removed, False if not found."""
    member = db.scalar(
        select(ContactListMember).where(
            ContactListMember.contact_list_id == contact_list_id,
            ContactListMember.contact_id == contact_id,
        )
    )
    if member is None:
        return False
    db.delete(member)
    return True


def get_list_member_count(db: Session, contact_list_id: int) -> int:
    return db.scalar(
        select(func.count()).where(ContactListMember.contact_list_id == contact_list_id)
    ) or 0
