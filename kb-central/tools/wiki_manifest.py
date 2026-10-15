#!/usr/bin/env python3
"""wiki_manifest: register raw sources by content hash.

The agent never computes hashes itself. It calls this script, which keeps
raw/manifest.jsonl append-only and prints the short hash to cite as [src:<hash>].

  python tools/wiki_manifest.py add raw/adrs/adr-120.md      # prints the hash
  python tools/wiki_manifest.py lookup a91f3c2d7e10          # prints the entry
  python tools/wiki_manifest.py list
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HASH_LEN = 12


def find_raw(root: Path) -> Path:
    for candidate in (root / ".wiki" / "raw", root / "raw"):
        if candidate.is_dir():
            return candidate
    raise SystemExit(f"wiki_manifest: no raw/ or .wiki/raw/ under {root}")


def short_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:HASH_LEN]


def entries(manifest: Path) -> list[dict]:
    if not manifest.is_file():
        return []
    return [json.loads(l) for l in manifest.read_text(encoding="utf-8").splitlines() if l.strip()]


def add(root: Path, source: Path) -> str:
    raw = find_raw(root)
    source = source.resolve()
    if raw.resolve() not in source.parents:
        raise SystemExit(f"wiki_manifest: {source} is not under {raw}")
    if source.name == "manifest.jsonl":
        raise SystemExit("wiki_manifest: refusing to register the manifest itself")
    digest = short_hash(source)
    manifest = raw / "manifest.jsonl"
    for entry in entries(manifest):
        if entry["hash"] == digest:
            return digest  # idempotent: already registered
    entry = {
        "hash": digest,
        "path": str(source.relative_to(root.resolve())),
        "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with manifest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return digest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add", help="register a raw source, print its hash")
    p_add.add_argument("paths", nargs="+")
    p_look = sub.add_parser("lookup", help="print the manifest entry for a hash")
    p_look.add_argument("hash")
    sub.add_parser("list", help="print all entries")
    args = ap.parse_args(argv)
    root = Path(args.root)

    if args.cmd == "add":
        for p in args.paths:
            print(f"{add(root, Path(p))}  {p}")
        return 0
    manifest = find_raw(root) / "manifest.jsonl"
    if args.cmd == "lookup":
        for entry in entries(manifest):
            if entry["hash"].startswith(args.hash):
                print(json.dumps(entry, ensure_ascii=False))
                return 0
        print(f"wiki_manifest: {args.hash} not found", file=sys.stderr)
        return 1
    for entry in entries(manifest):
        print(f"{entry['hash']}  {entry['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
