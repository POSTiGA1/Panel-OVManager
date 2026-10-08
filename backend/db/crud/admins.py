"""Admin CRUD. One row: the owner."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.models import Admin


def get_admin_by_username(db: Session, username: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    return admin
