"""File digests for backup delivery.

Telegram delivery hashes each backup before sending it through this shared
chunked SHA-256 rather than a private copy.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Hex SHA-256 of a file, streamed so a large backup stays off the heap."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
