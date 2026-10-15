#!/usr/bin/env python3
"""wiki_check: deterministic validator for an LLM Wiki.

The agent writes pages; this script decides whether they may be committed.
It needs no model and no third-party packages, so it runs the same way in a
pre-commit hook, in CI, and inside a Copilot CLI session.

Layouts (auto-detected from --root):
  * kb-central style:  <root>/wiki/  and  <root>/raw/
  * in-repo style:     <root>/.wiki/ and  <root>/.wiki/raw/

Checks (category names are what --fail-on accepts):
  raw_modified    a file under raw/ was modified, deleted or renamed
                  (manifest.jsonl may only grow by appended lines)
  uncited         a prose line in a page carries no [src:...] tag
  unknown_source  a [src:<hash>] tag points to a hash missing from the manifest
  broken          a [[link]] points to a page that does not exist
  frontmatter     a page lacks the required `type` or `updated` keys
  duplicate_slug  two pages share the same file name (slugs must be unique)
  orphans         a page no other page links to (index.md does not count)
  unindexed       a page that index.md does not list

Exit code is 1 when any category listed in --fail-on has findings.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
SRC_RE = re.compile(r"\[src:([^\]]+)\]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")

PAGE_DIRS = ("entities", "concepts", "syntheses", "playbooks", "sources")
SPECIAL_PAGES = ("index", "log")
REQUIRED_KEYS = ("type", "updated")

CATEGORIES = (
    "raw_modified", "uncited", "unknown_source", "broken",
    "frontmatter", "duplicate_slug", "orphans", "unindexed",
)
DEFAULT_FAIL_ON = "raw_modified,uncited,unknown_source,broken,frontmatter,duplicate_slug"


@dataclass
class Layout:
    root: Path
    wiki: Path
    raw: Path

    @property
    def manifest(self) -> Path:
        return self.raw / "manifest.jsonl"


@dataclass
class Page:
    slug: str
    path: Path
    meta: dict
    body: str
    body_offset: int
    links: list[str] = field(default_factory=list)


def detect_layout(root: Path) -> Layout:
    if (root / ".wiki").is_dir():
        return Layout(root, root / ".wiki", root / ".wiki" / "raw")
    if (root / "wiki").is_dir():
        return Layout(root, root / "wiki", root / "raw")
    raise SystemExit(f"wiki_check: no wiki/ or .wiki/ directory under {root}")


def parse_frontmatter(text: str) -> tuple[dict, str, int]:
    """Minimal YAML frontmatter reader: `key: value` and `key: [a, b]`."""
    if not text.startswith("---\n"):
        return {}, text, 1
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text, 1
    fm = text[4:end]
    meta: dict = {}
    for line in fm.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            value = value.strip("'\"")
        meta[key.strip()] = value
    body = text[end + 4:]
    # line index 0 of body.splitlines() is the remainder of the closing '---' line
    return meta, body, fm.count("\n") + 3


def load_pages(layout: Layout) -> tuple[dict[str, Page], list[tuple[str, list[str]]]]:
    pages: dict[str, Page] = {}
    seen: dict[str, list[str]] = {}
    paths = [layout.wiki / f"{name}.md" for name in SPECIAL_PAGES]
    for d in PAGE_DIRS:
        paths += sorted((layout.wiki / d).rglob("*.md")) if (layout.wiki / d).is_dir() else []
    for path in paths:
        if not path.is_file():
            continue
        slug = path.stem
        seen.setdefault(slug, []).append(str(path.relative_to(layout.root)))
        meta, body, offset = parse_frontmatter(path.read_text(encoding="utf-8"))
        links = [m.group(1).strip() for m in LINK_RE.finditer(strip_code(body))]
        pages[slug] = Page(slug, path, meta, body, offset, links)
    duplicates = [(s, p) for s, p in seen.items() if len(p) > 1]
    return pages, duplicates


def strip_code(body: str) -> str:
    out, in_code = [], False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if not in_code:
            out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def is_navigation_only(line: str) -> bool:
    rest = LINK_RE.sub("", line)
    rest = MD_LINK_RE.sub("", rest)
    return re.fullmatch(r"[\s\-*·,|•]*", rest) is not None


def uncited_lines(page: Page) -> list[int]:
    if page.slug in SPECIAL_PAGES:
        return []
    found, in_code = [], False
    for i, line in enumerate(page.body.splitlines()):
        stripped = line.strip()
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code or not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("<!--", "|")):  # comments and tables are not checked
            continue
        # Lines made only of [[links]] (e.g. under ## Related) are navigation, not claims.
        # Any other line needs a source, whatever section it sits in.
        if is_navigation_only(stripped):
            continue
        if not SRC_RE.search(stripped):
            found.append(page.body_offset + i)
    return found


def manifest_hashes(layout: Layout) -> set[str]:
    hashes: set[str] = set()
    if not layout.manifest.is_file():
        return hashes
    for line in layout.manifest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                hashes.add(json.loads(line)["hash"])
            except (ValueError, KeyError):
                continue
    return hashes


def source_tags(page: Page) -> list[str]:
    tags: list[str] = []
    for m in SRC_RE.finditer(strip_code(page.body)):
        tags += [t.strip() for t in m.group(1).split(",") if t.strip()]
    return tags


def git(layout: Layout, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=layout.root, capture_output=True, text=True)


def in_git_repo(layout: Layout) -> bool:
    return git(layout, "rev-parse", "--is-inside-work-tree").returncode == 0


def raw_changes(layout: Layout, staged: bool, base: str | None) -> list[str]:
    """Modified, deleted or renamed files under raw/, plus non-append manifest edits."""
    if not (staged or base) or not in_git_repo(layout):
        return []
    raw_rel = str(layout.raw.relative_to(layout.root))
    manifest_rel = str(layout.manifest.relative_to(layout.root))
    diff_args = ["diff", "--name-status", "--diff-filter=MDR"]
    diff_args += ["--cached"] if staged else [f"{base}...HEAD"]
    proc = git(layout, *diff_args, "--", raw_rel)
    problems = []
    for line in proc.stdout.splitlines():
        status, *paths = line.split("\t")
        if paths and paths[0] == manifest_rel and status == "M":
            old = git(layout, "show", f"{'HEAD' if staged else base}:{manifest_rel}").stdout
            new = git(layout, "show", f":{manifest_rel}").stdout if staged else layout.manifest.read_text(encoding="utf-8")
            if new.startswith(old):
                continue
            problems.append(f"{manifest_rel}: manifest changed other than by appending lines")
            continue
        problems.append(f"{' -> '.join(paths)}: {status} (raw/ is append-only)")
    return problems


def staged_pages(layout: Layout, pages: dict[str, Page]) -> set[str]:
    proc = git(layout, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    changed = {str((layout.root / p).resolve()) for p in proc.stdout.splitlines()}
    return {s for s, p in pages.items() if str(p.path.resolve()) in changed}


def run_checks(layout: Layout, staged: bool = False, base: str | None = None) -> dict[str, list[str]]:
    pages, duplicates = load_pages(layout)
    findings: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    rel = lambda p: str(p.path.relative_to(layout.root))  # noqa: E731

    findings["raw_modified"] = raw_changes(layout, staged, base)
    findings["duplicate_slug"] = [f"{s}: {', '.join(p)}" for s, p in duplicates]

    scope = staged_pages(layout, pages) if staged and in_git_repo(layout) else set(pages)
    known = manifest_hashes(layout)
    for slug in sorted(scope):
        page = pages[slug]
        for n in uncited_lines(page):
            findings["uncited"].append(f"{rel(page)}:{n}: claim without [src:...] tag")
        for tag in source_tags(page):
            if ":" not in tag and tag not in known:  # git:/pr: tags are not in the manifest
                findings["unknown_source"].append(f"{rel(page)}: [src:{tag}] not in manifest")
        for link in page.links:
            if link not in pages:
                findings["broken"].append(f"{rel(page)}: [[{link}]] has no page")
        if slug not in SPECIAL_PAGES:
            missing = [k for k in REQUIRED_KEYS if k not in page.meta]
            if missing:
                findings["frontmatter"].append(f"{rel(page)}: missing {', '.join(missing)}")

    indexed = set(pages["index"].links) if "index" in pages else set()
    inbound: dict[str, int] = {s: 0 for s in pages}
    for page in pages.values():
        if page.slug in SPECIAL_PAGES:
            continue
        for link in set(page.links) - {page.slug}:
            if link in inbound:
                inbound[link] += 1
    for slug, page in sorted(pages.items()):
        if slug in SPECIAL_PAGES or page.meta.get("status") == "retired":
            continue
        if slug not in indexed:
            findings["unindexed"].append(f"{rel(page)}: not listed in index.md")
        if inbound[slug] == 0 and page.meta.get("type") != "source":
            findings["orphans"].append(f"{rel(page)}: no inbound [[links]]")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="check staged pages and staged raw/ changes")
    mode.add_argument("--all", action="store_true", help="check every page (default)")
    ap.add_argument("--base", help="git ref to diff raw/ against, e.g. origin/main (CI)")
    ap.add_argument("--fail-on", default=DEFAULT_FAIL_ON,
                    help=f"comma-separated categories that fail the run (default: {DEFAULT_FAIL_ON})")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    args = ap.parse_args(argv)

    fail_on = {c.strip() for c in args.fail_on.split(",") if c.strip()}
    unknown = fail_on - set(CATEGORIES)
    if unknown:
        ap.error(f"unknown categories: {', '.join(sorted(unknown))}")

    layout = detect_layout(Path(args.root).resolve())
    findings = run_checks(layout, staged=args.staged, base=args.base)
    failed = sorted(c for c in fail_on if findings[c])

    if args.json:
        print(json.dumps({"findings": findings, "failed": failed}, indent=2, ensure_ascii=False))
    else:
        for cat in CATEGORIES:
            items = findings[cat]
            if not items:
                continue
            level = "ERROR" if cat in fail_on else "warn"
            print(f"[{level}] {cat} ({len(items)})")
            for item in items:
                print(f"    {item}")
        total = sum(len(v) for v in findings.values())
        print(f"wiki_check: {total} finding(s), {len(failed)} failing categor{'y' if len(failed) == 1 else 'ies'}"
              + (f": {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
