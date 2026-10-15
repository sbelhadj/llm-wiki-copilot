from pathlib import Path

import wiki_check
from conftest import ROOT, git

ALL = ",".join(wiki_check.CATEGORIES)


def findings(repo: Path, **kw) -> dict:
    return wiki_check.run_checks(wiki_check.detect_layout(repo), **kw)


def test_sample_kb_is_clean():
    assert wiki_check.main(["--root", str(ROOT / "kb-central"), "--fail-on", ALL]) == 0


def test_repo_template_is_clean():
    assert wiki_check.main(["--root", str(ROOT / "repo-template"), "--fail-on", ALL]) == 0


def test_detects_uncited_broken_unknown_and_frontmatter(kb):
    page = kb / "wiki" / "concepts" / "idempotency-keys.md"
    page.write_text(page.read_text() + "\nThis line cites nothing.\nSee [[no-such-page]]. [src:deadbeef0000]\n")
    (kb / "wiki" / "concepts" / "bare.md").write_text("# Bare\n\nA claim. [src:5cef8ed51c95]\n")
    f = findings(kb)
    assert any("idempotency-keys.md" in x for x in f["uncited"])
    assert any("[[no-such-page]]" in x for x in f["broken"])
    assert any("deadbeef0000" in x for x in f["unknown_source"])
    assert any("bare.md: missing type, updated" in x for x in f["frontmatter"])
    assert any("bare.md" in x for x in f["orphans"])
    assert any("bare.md" in x for x in f["unindexed"])


def test_related_section_and_code_blocks_need_no_citation(kb):
    page = kb / "wiki" / "concepts" / "idempotency-keys.md"
    page.write_text(page.read_text() + "\n```bash\nmake stub-up\n```\n")
    assert findings(kb)["uncited"] == []


def test_raw_edit_is_rejected_when_staged(kb):
    raw = kb / "raw" / "adrs" / "adr-112-gateway-timeouts.md"
    raw.write_text(raw.read_text() + "\nEdited after the fact.\n")
    git(kb, "add", "-A")
    assert any("adr-112" in x for x in findings(kb, staged=True)["raw_modified"])


def test_raw_delete_is_rejected_against_base(kb):
    git(kb, "switch", "-q", "-c", "feature")
    git(kb, "rm", "-q", "raw/runbooks/payment-gateway-runbook-2024.md")
    git(kb, "commit", "-q", "-m", "delete raw")
    assert any("runbook" in x for x in findings(kb, base="main")["raw_modified"])


def test_manifest_may_only_grow(kb):
    manifest = kb / "raw" / "manifest.jsonl"
    manifest.write_text(manifest.read_text() + '{"hash": "aaaaaaaaaaaa", "path": "raw/x.md"}\n')
    git(kb, "add", "-A")
    assert findings(kb, staged=True)["raw_modified"] == []

    git(kb, "commit", "-q", "-m", "append")
    lines = manifest.read_text().splitlines()
    manifest.write_text("\n".join(lines[1:]) + "\n")
    git(kb, "add", "-A")
    assert any("manifest" in x for x in findings(kb, staged=True)["raw_modified"])


def test_staged_mode_checks_only_staged_pages(kb):
    other = kb / "wiki" / "entities" / "acquirer-routing.md"
    other.write_text(other.read_text() + "\nUncited but not staged.\n")
    assert findings(kb, staged=True)["uncited"] == []
    git(kb, "add", str(other))
    assert len(findings(kb, staged=True)["uncited"]) == 1


def test_exit_code_follows_fail_on(kb):
    (kb / "wiki" / "concepts" / "lonely.md").write_text(
        "---\ntype: concept\nupdated: 2026-10-15\n---\n# Lonely\n\nA claim. [src:5cef8ed51c95]\n")
    assert wiki_check.main(["--root", str(kb)]) == 0                       # orphans only warn by default
    assert wiki_check.main(["--root", str(kb), "--fail-on", "orphans"]) == 1
