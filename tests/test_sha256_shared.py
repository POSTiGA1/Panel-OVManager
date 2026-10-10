"""One file-digest helper for backup delivery.

Telegram delivery hashes each backup through the shared chunked SHA-256
in ``backend.utils.checksums`` rather than a private copy: these digests
gate delivery, so a divergence would be a silent hash of a corrupt backup.
"""

import hashlib

import pytest


def test_matches_a_known_digest(tmp_path):
    from backend.utils.checksums import sha256_file

    payload = b"ovmanager-backup-payload"
    target = tmp_path / "backup.db"
    target.write_bytes(payload)

    assert sha256_file(target) == hashlib.sha256(payload).hexdigest()


def test_hashes_a_file_larger_than_one_chunk(tmp_path):
    """The chunked read must not truncate or double-count."""
    from backend.utils.checksums import sha256_file

    payload = b"x" * (3 * 1024 * 1024 + 7)
    target = tmp_path / "big.db"
    target.write_bytes(payload)

    assert sha256_file(target) == hashlib.sha256(payload).hexdigest()


def test_empty_file(tmp_path):
    from backend.utils.checksums import sha256_file

    target = tmp_path / "empty"
    target.write_bytes(b"")
    assert sha256_file(target) == hashlib.sha256(b"").hexdigest()


def test_missing_file_raises(tmp_path):
    from backend.utils.checksums import sha256_file

    with pytest.raises(OSError):
        sha256_file(tmp_path / "nope")


def test_both_backup_paths_use_the_shared_helper():
    """The delivery path may not keep a private copy."""
    import inspect

    from backend.operations.backup import telegram

    src = inspect.getsource(telegram)
    assert "def _sha256" not in src, f"{telegram.__name__} still defines its own digest"
    assert "sha256_file" in src, f"{telegram.__name__} does not use the shared helper"
