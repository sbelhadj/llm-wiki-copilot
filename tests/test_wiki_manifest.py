import json

import pytest

import wiki_manifest


def test_add_is_idempotent_and_append_only(kb):
    src = kb / "raw" / "adrs" / "adr-200.md"
    src.write_text("# ADR-200\n")
    manifest = kb / "raw" / "manifest.jsonl"
    before = manifest.read_text()
    h1 = wiki_manifest.add(kb, src)
    h2 = wiki_manifest.add(kb, src)
    after = manifest.read_text()
    assert h1 == h2 and len(h1) == wiki_manifest.HASH_LEN
    assert after.startswith(before)
    assert json.loads(after.splitlines()[-1])["path"] == "raw/adrs/adr-200.md"
    assert after.count(h1) == 1


def test_refuses_files_outside_raw(kb):
    with pytest.raises(SystemExit):
        wiki_manifest.add(kb, kb / "wiki" / "index.md")
