"""Evidence and media storage behind an interface.

Phase 1 ships one implementation, ``LocalFilesystemStorage``. Callers depend on the
``EvidenceStorage`` protocol so an object store (MinIO or another S3-compatible service) can be
added later without changing them (ADR-0001).

Stored objects are immutable: writing different bytes to an existing key is an error, and writing
identical bytes is an idempotent no-op.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# One to eight "/"-separated segments. Each segment starts with an alphanumeric character, which
# rules out "." and ".." segments, hidden files and empty segments (so no path traversal).
_SEGMENT = r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}"
_KEY_PATTERN = re.compile(rf"{_SEGMENT}(?:/{_SEGMENT}){{0,7}}")


class StorageError(Exception):
    """Base class for storage failures."""


class InvalidStorageKeyError(StorageError):
    """The key is malformed or would resolve outside the storage root."""


class ObjectNotFoundError(StorageError):
    """No object exists for the key."""


class ObjectConflictError(StorageError):
    """The key already holds different content; stored objects are immutable."""


@dataclass(frozen=True)
class StoredObject:
    key: str
    size_bytes: int
    sha256: str


class EvidenceStorage(Protocol):
    def put(self, key: str, data: bytes) -> StoredObject: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...

    def check_health(self) -> None:
        """Raise if the storage cannot currently be used."""


class LocalFilesystemStorage:
    """Stores objects as files beneath a root directory."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def ensure_root(self) -> None:
        """Create the root directory if it does not exist."""
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        if not _KEY_PATTERN.fullmatch(key):
            msg = "invalid storage key"
            raise InvalidStorageKeyError(msg)
        path = (self._root / key).resolve()
        # resolve() follows symlinks, so this also rejects a link that points outside the root.
        if not path.is_relative_to(self._root):
            msg = "storage key resolves outside the storage root"
            raise InvalidStorageKeyError(msg)
        return path

    @staticmethod
    def _sha256_of_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def put(self, key: str, data: bytes) -> StoredObject:
        path = self._path_for(key)
        digest = hashlib.sha256(data).hexdigest()
        stored = StoredObject(key=key, size_bytes=len(data), sha256=digest)

        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        temp_path = Path(temp_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                # A hard link fails if the target exists, so a concurrent writer can never be
                # silently overwritten (unlike os.replace).
                os.link(temp_path, path)
            except FileExistsError:
                if self._sha256_of_file(path) != digest:
                    msg = "key already holds different content"
                    raise ObjectConflictError(msg) from None
        finally:
            temp_path.unlink(missing_ok=True)
        return stored

    def get(self, key: str) -> bytes:
        path = self._path_for(key)
        try:
            return path.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            msg = "no object for key"
            raise ObjectNotFoundError(msg) from None

    def exists(self, key: str) -> bool:
        return self._path_for(key).is_file()

    def check_health(self) -> None:
        if not self._root.is_dir():
            msg = "storage root is not an existing directory"
            raise StorageError(msg)
        if not os.access(self._root, os.W_OK | os.X_OK):
            msg = "storage root is not writable"
            raise StorageError(msg)
