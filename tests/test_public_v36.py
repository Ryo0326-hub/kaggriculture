"""Packaging integrity only; no engine imports, policy calls or game stepping."""

from hashlib import sha256

import pytest

from scripts import make_public_v36


def test_public_source_is_copied_byte_for_byte(tmp_path):
    output = tmp_path / "submission/main.py"
    digest = make_public_v36.build(output)
    assert digest == make_public_v36.SOURCE_SHA256
    assert sha256(output.read_bytes()).hexdigest() == digest
    assert output.read_bytes() == make_public_v36.SOURCE.read_bytes()
    assert b"Apache License" in output.read_bytes()


def test_packaging_refuses_to_overwrite_an_existing_file(tmp_path):
    output = tmp_path / "main.py"
    output.write_text("preserve this file\n")
    with pytest.raises(FileExistsError):
        make_public_v36.build(output)
    assert output.read_text() == "preserve this file\n"


def test_changed_upstream_bytes_cannot_masquerade_as_v36(tmp_path, monkeypatch):
    source = tmp_path / "changed.py"
    source.write_bytes(make_public_v36.SOURCE.read_bytes() + b"\n# changed\n")
    monkeypatch.setattr(make_public_v36, "SOURCE", source)
    output = tmp_path / "main.py"
    with pytest.raises(ValueError, match="Frozen public V36 source changed"):
        make_public_v36.build(output)
    assert not output.exists()
