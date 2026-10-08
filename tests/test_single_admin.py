"""Single-admin contract: the multi-admin surface is gone, owner login stays."""

from fastapi.testclient import TestClient

from backend.app import _run_migrations, api
from backend.auth.sessions import create_session
from backend.config import config
from backend.db import crud
from backend.db.engine import SessionLocal
from backend.db.models import Admin, User


def _owner_headers() -> dict:
    db = SessionLocal()
    try:
        raw = create_session(db, config.ADMIN_USERNAME, "owner")
    finally:
        db.close()
    return {"Authorization": f"Bearer {raw}"}


def test_creating_a_second_admin_is_refused():
    _run_migrations()
    client = TestClient(api)
    resp = client.post(
        "/api/admin/",
        json={"username": "second_admin_x", "password": "second-admin-pw1"},
        headers={**_owner_headers(), "X-Requested-With": "XMLHttpRequest"},
    )
    assert resp.status_code in (404, 410), resp.text
    assert resp.headers["content-type"].startswith("application/json")
    db = SessionLocal()
    try:
        assert crud.get_admin_by_username(db, "second_admin_x") is None
    finally:
        db.close()


def test_listing_admins_is_gone():
    _run_migrations()
    client = TestClient(api)
    resp = client.get("/api/admin/", headers=_owner_headers())
    assert resp.status_code in (403, 404)


def test_a_second_admin_cannot_log_in():
    _run_migrations()
    from backend.auth.hash import hash_password

    db = SessionLocal()
    try:
        if crud.get_admin_by_username(db, "second_login_x") is None:
            db.add(Admin(username="second_login_x", password=hash_password("second-login-pw1")))
            db.commit()
    finally:
        db.close()
    try:
        client = TestClient(api)
        resp = client.post(
            "/api/login",
            headers={"X-Requested-With": "XMLHttpRequest"},
            data={"username": "second_login_x", "password": "second-login-pw1"},
        )
        assert resp.status_code == 401
    finally:
        db = SessionLocal()
        try:
            row = crud.get_admin_by_username(db, "second_login_x")
            if row is not None:
                db.delete(row)
                db.commit()
        finally:
            db.close()


def test_owner_lists_every_user_without_scoping():
    _run_migrations()
    client = TestClient(api)
    resp = client.get("/api/users/", headers=_owner_headers())
    assert resp.status_code == 200
    data = resp.json()["data"]
    db = SessionLocal()
    try:
        db_count = db.query(User).count()
    finally:
        db.close()
    assert data["total"] == db_count
    assert len(data["users"]) == db_count
