"""DB is the default TLS record; an uncommented .env line forces over it.

The paths the panel serves from are a separate question (``backend.tls_paths``:
.env declares, else ``/etc/ovmanager/tls``). What this pins is the record half
— which value ``/tls/settings`` calls the source — plus the boot rule that
follows from it: a restored database without files is a record, so a boot that
finds no pair generates a fresh self-signed one at the serving paths and stays
on HTTPS.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import api
from backend.config import config


@pytest.fixture
def client():
    return TestClient(api)


@pytest.fixture
def tls_record():
    """Snapshot and restore the shared database's TLS record around one test."""
    from backend.db.crud.settings import get_settings
    from backend.db.engine import SessionLocal

    fields = ("ssl_cert_file", "ssl_key_file", "cert_method", "acme_domain", "acme_email")
    db = SessionLocal()
    try:
        settings = get_settings(db)
        before = {name: getattr(settings, name) for name in fields}
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        settings = get_settings(db)
        for name, value in before.items():
            setattr(settings, name, value)
        db.commit()
    finally:
        db.close()


def _owner_headers(make_session_token) -> dict:
    return {"Authorization": f"Bearer {make_session_token(config.ADMIN_USERNAME, 'owner')}"}


def test_db_is_the_default_and_env_forces_over_it(client, make_session_token, tls_record, monkeypatch, tmp_path):
    headers = _owner_headers(make_session_token)
    monkeypatch.setitem(config.model_config, "env_file", str(tmp_path / "no-such-env"))

    put = client.put(
        "/api/tls/settings",
        json={"cert_file": "/srv/custom/fullchain.pem", "key_file": "/srv/custom/privkey.pem"},
        headers=headers,
    )
    assert put.json()["success"] is True, put.json()

    fields = client.get("/api/tls/settings", headers=headers).json()["data"]["fields"]
    assert fields["cert_file"]["source"] == "db"
    assert fields["cert_file"]["effective"] == "/srv/custom/fullchain.pem"
    assert fields["cert_file"]["overridden"] is False

    env_file = tmp_path / ".env"
    env_file.write_text("SSL_KEYFILE=/forced/privkey.pem\nSSL_CERTFILE=/forced/fullchain.pem\n", encoding="utf-8")
    monkeypatch.setitem(config.model_config, "env_file", str(env_file))

    fields = client.get("/api/tls/settings", headers=headers).json()["data"]["fields"]
    assert fields["cert_file"]["source"] == "env"
    assert fields["cert_file"]["effective"] == "/forced/fullchain.pem"
    assert fields["cert_file"]["overridden"] is True


def test_boot_missing_pair_generates_self_signed_at_the_serving_paths(tls_record, monkeypatch, tmp_path):
    """No pair at the serving paths means a fresh identity there, never HTTP."""
    import backend.routers.tls as tlsr
    from backend import tls_paths
    from backend.db.crud.settings import get_settings
    from backend.db.engine import SessionLocal

    monkeypatch.setitem(config.model_config, "env_file", str(tmp_path / "no-such-env"))
    monkeypatch.setattr(config, "SSL_KEYFILE", "")
    monkeypatch.setattr(config, "SSL_CERTFILE", "")
    monkeypatch.delenv("SSL_KEYFILE", raising=False)
    monkeypatch.delenv("SSL_CERTFILE", raising=False)
    monkeypatch.setattr(tls_paths, "DEFAULT_DIR", str(tmp_path / "tls"))
    monkeypatch.setattr(tlsr, "_installer_public_ip", lambda: None)

    key, cert = tlsr.ensure_serving_pair()

    assert Path(key).is_file(), f"boot left no key at the serving path: {key}"
    assert Path(cert).is_file(), f"boot left no certificate at the serving path: {cert}"
    tlsr._validate_pair(Path(key).read_bytes(), Path(cert).read_bytes())

    db = SessionLocal()
    try:
        settings = get_settings(db)
        assert settings.cert_method == "selfsigned"
        assert settings.ssl_key_file == key
        assert settings.ssl_cert_file == cert
    finally:
        db.close()
