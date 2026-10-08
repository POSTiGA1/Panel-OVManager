"""Admin CRUD. One row: the owner."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.models import Admin


def get_admin_by_username(db: Session, username: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    return admin


def get_admin_by_telegram_id(db: Session, tg_id: int):
    return db.query(Admin).filter(Admin.telegram_id == tg_id, Admin.is_owner.is_(True)).first()
