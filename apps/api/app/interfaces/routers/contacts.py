"""Contacts and Contact Lists router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import (
    ContactCreate,
    ContactListCreate,
    ContactListMemberRead,
    ContactListRead,
    ContactListUpdate,
    ContactRead,
    ContactUpdate,
)
from app.application.services.contacts import (
    add_contact_to_list,
    get_contact_list_count,
    get_list_member_count,
    remove_contact_from_list,
    upsert_contact,
)
from app.domain.models import Contact, ContactList, ContactListMember

router = APIRouter(prefix="/contacts", tags=["contacts"])
lists_router = APIRouter(prefix="/contact-lists", tags=["contact-lists"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_contact_or_404(db: Session, contact_id: int) -> Contact:
    c = db.get(Contact, contact_id)
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return c


def _get_list_or_404(db: Session, list_id: int) -> ContactList:
    cl = db.get(ContactList, list_id)
    if cl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact list not found"
        )
    return cl


def _to_contact_read(db: Session, c: Contact) -> ContactRead:
    cr = ContactRead.model_validate(c)
    cr.list_count = get_contact_list_count(db, c.id)
    return cr


def _to_list_read(db: Session, cl: ContactList) -> ContactListRead:
    lr = ContactListRead.model_validate(cl)
    lr.member_count = get_list_member_count(db, cl.id)
    return lr


# ---------------------------------------------------------------------------
# Contacts CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)) -> ContactRead:
    existing = db.scalar(
        select(Contact).where(Contact.email == str(payload.email).lower())
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists",
        )
    contact = Contact(
        email=str(payload.email).lower(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        custom_fields=payload.custom_fields,
        status=payload.status,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return _to_contact_read(db, contact)


@router.get("", response_model=list[ContactRead])
def list_contacts(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
) -> list[ContactRead]:
    q = select(Contact).order_by(Contact.created_at.desc()).limit(limit).offset(offset)
    if status:
        q = select(Contact).where(Contact.status == status).order_by(Contact.created_at.desc()).limit(limit).offset(offset)
    rows = list(db.scalars(q))
    return [_to_contact_read(db, c) for c in rows]


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(contact_id: int, db: Session = Depends(get_db)) -> ContactRead:
    return _to_contact_read(db, _get_contact_or_404(db, contact_id))


@router.put("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int, payload: ContactUpdate, db: Session = Depends(get_db)
) -> ContactRead:
    contact = _get_contact_or_404(db, contact_id)
    if payload.email is not None:
        contact.email = str(payload.email).lower()
    if payload.first_name is not None:
        contact.first_name = payload.first_name
    if payload.last_name is not None:
        contact.last_name = payload.last_name
    if payload.custom_fields is not None:
        contact.custom_fields = payload.custom_fields
    if payload.status is not None:
        contact.status = payload.status
    db.commit()
    db.refresh(contact)
    return _to_contact_read(db, contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)) -> None:
    contact = _get_contact_or_404(db, contact_id)
    db.delete(contact)
    db.commit()


# ---------------------------------------------------------------------------
# Contact list membership
# ---------------------------------------------------------------------------


@router.post(
    "/{contact_id}/lists/{list_id}",
    response_model=ContactListMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_to_list(
    contact_id: int, list_id: int, db: Session = Depends(get_db)
) -> ContactListMemberRead:
    _get_contact_or_404(db, contact_id)
    _get_list_or_404(db, list_id)
    member = add_contact_to_list(db, contact_list_id=list_id, contact_id=contact_id)
    db.commit()
    db.refresh(member)
    return ContactListMemberRead.model_validate(member)


@router.delete("/{contact_id}/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_list(
    contact_id: int, list_id: int, db: Session = Depends(get_db)
) -> None:
    _get_contact_or_404(db, contact_id)
    _get_list_or_404(db, list_id)
    removed = remove_contact_from_list(db, contact_list_id=list_id, contact_id=contact_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact is not a member of this list"
        )
    db.commit()


@router.get("/{contact_id}/lists", response_model=list[ContactListMemberRead])
def get_contact_lists(
    contact_id: int, db: Session = Depends(get_db)
) -> list[ContactListMemberRead]:
    _get_contact_or_404(db, contact_id)
    rows = list(
        db.scalars(
            select(ContactListMember).where(ContactListMember.contact_id == contact_id)
        )
    )
    return [ContactListMemberRead.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# Contact Lists CRUD
# ---------------------------------------------------------------------------


@lists_router.post("", response_model=ContactListRead, status_code=status.HTTP_201_CREATED)
def create_contact_list(
    payload: ContactListCreate, db: Session = Depends(get_db)
) -> ContactListRead:
    cl = ContactList(name=payload.name, description=payload.description)
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return _to_list_read(db, cl)


@lists_router.get("", response_model=list[ContactListRead])
def list_contact_lists(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ContactListRead]:
    rows = list(
        db.scalars(
            select(ContactList)
            .order_by(ContactList.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return [_to_list_read(db, cl) for cl in rows]


@lists_router.get("/{list_id}", response_model=ContactListRead)
def get_contact_list(list_id: int, db: Session = Depends(get_db)) -> ContactListRead:
    return _to_list_read(db, _get_list_or_404(db, list_id))


@lists_router.put("/{list_id}", response_model=ContactListRead)
def update_contact_list(
    list_id: int, payload: ContactListUpdate, db: Session = Depends(get_db)
) -> ContactListRead:
    cl = _get_list_or_404(db, list_id)
    cl.name = payload.name
    cl.description = payload.description
    db.commit()
    db.refresh(cl)
    return _to_list_read(db, cl)


@lists_router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_list(list_id: int, db: Session = Depends(get_db)) -> None:
    cl = _get_list_or_404(db, list_id)
    db.delete(cl)
    db.commit()


@lists_router.get("/{list_id}/members", response_model=list[ContactListMemberRead])
def list_members(list_id: int, db: Session = Depends(get_db)) -> list[ContactListMemberRead]:
    _get_list_or_404(db, list_id)
    rows = list(
        db.scalars(
            select(ContactListMember).where(ContactListMember.contact_list_id == list_id)
        )
    )
    return [ContactListMemberRead.model_validate(r) for r in rows]
