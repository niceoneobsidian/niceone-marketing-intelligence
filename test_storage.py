from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.platform.storage import (
    EvidenceStorage,
    InvalidStorageKeyError,
    LocalFilesystemStorage,
    ObjectConflictError,
    ObjectNotFoundError,
    StorageError,
)


@pytest.fixture
def storage(tmp_path: Path) -> LocalFilesystemStorage:
    store = LocalFilesystemStorage(tmp_path / "evidence")
    store.ensure_root()
    return store


def test_satisfies_the_storage_protocol(storage: LocalFilesystemStorage) -> None:
    protocol_user: EvidenceStorage = storage  # fails type-checking if the protocol drifts
    assert protocol_user is storage


def test_put_then_get_roundtrip_returns_verifiable_reference(
    storage: LocalFilesystemStorage,
) -> None:
    data = b"raw evidence bytes"
    stored = storage.put("ws1/item-1.bin", data)

    assert stored.key == "ws1/item-1.bin"
    assert stored.size_bytes == len(data)
    assert stored.sha256 == hashlib.sha256(data).hexdigest()
    assert storage.get("ws1/item-1.bin") == data
    assert storage.exists("ws1/item-1.bin")


def test_put_same_content_twice_is_idempotent(storage: LocalFilesystemStorage) -> None:
    first = storage.put("a.bin", b"same")
    second = storage.put("a.bin", b"same")
    assert first == second


def test_put_different_content_to_existing_key_is_rejected(
    storage: LocalFilesystemStorage,
) -> None:
    storage.put("a.bin", b"original")
    with pytest.raises(ObjectConflictError):
        storage.put("a.bin", b"tampered")
    assert storage.get("a.bin") == b"original"


def test_put_leaves_no_temporary_files(storage: LocalFilesystemStorage) -> None:
    storage.put("dir/a.bin", b"x")
    storage.put("dir/a.bin", b"x")
    leftovers = [p.name for p in (storage.root / "dir").iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_get_missing_object_raises_not_found(storage: LocalFilesystemStorage) -> None:
    with pytest.raises(ObjectNotFoundError):
        storage.get("missing.bin")
    assert not storage.exists("missing.bin")


def test_get_on_a_directory_key_raises_not_found(storage: LocalFilesystemStorage) -> None:
    storage.put("dir/a.bin", b"x")
    with pytest.raises(ObjectNotFoundError):
        storage.get("dir")


@pytest.mark.parametrize(
    "key",
    [
        "",
        "../escape",
        "a/../../escape",
        "/absolute",
        "a//b",
        "a/",
        ".hidden",
        "a/.hidden",
        "a b",
        "a\\b",
        "a/\x00b",
        "x" * 129,
        "/".join(["a"] * 9),
    ],
)
def test_invalid_keys_are_rejected(storage: LocalFilesystemStorage, key: str) -> None:
    with pytest.raises(InvalidStorageKeyError):
        storage.put(key, b"x")
    with pytest.raises(InvalidStorageKeyError):
        storage.get(key)


def test_key_cannot_escape_root_through_a_symlink(
    storage: LocalFilesystemStorage, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (storage.root / "link").symlink_to(outside, target_is_directory=True)

    with pytest.raises(InvalidStorageKeyError):
        storage.put("link/secret.bin", b"x")
    assert list(outside.iterdir()) == []


def test_health_ok_for_existing_writable_root(storage: LocalFilesystemStorage) -> None:
    storage.check_health()


def test_health_fails_when_root_is_missing(tmp_path: Path) -> None:
    with pytest.raises(StorageError):
        LocalFilesystemStorage(tmp_path / "does-not-exist").check_health()


def test_health_fails_when_root_is_a_file(tmp_path: Path) -> None:
    not_a_directory = tmp_path / "file"
    not_a_directory.write_text("x")
    with pytest.raises(StorageError):
        LocalFilesystemStorage(not_a_directory).check_health()
