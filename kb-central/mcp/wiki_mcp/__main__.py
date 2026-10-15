"""Run the wiki MCP server.

  python -m wiki_mcp --root /path/to/kb-central                      # stdio, with propose_edit
  python -m wiki_mcp --root . --read-only                            # stdio, navigation only
  python -m wiki_mcp --root /srv/kb-central --transport http --port 8765 --acl acl.json
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .core import WikiStore
from .server import build_server, run_server


def main() -> None:
    ap = argparse.ArgumentParser(prog="wiki_mcp", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.environ.get("WIKI_ROOT", "."),
                    help="repository root containing wiki/ or .wiki/ (env WIKI_ROOT)")
    ap.add_argument("--read-only", action="store_true", help="do not expose propose_edit")
    ap.add_argument("--queue", help="directory for proposed edits (default: <root>/review-queue)")
    ap.add_argument("--acl", help="JSON file mapping caller identities to readable wiki directories")
    ap.add_argument("--name", default="llm-wiki")
    ap.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    store = WikiStore(Path(args.root), queue_dir=Path(args.queue) if args.queue else None,
                      acl_file=Path(args.acl) if args.acl else None)
    server = build_server(store, read_only=args.read_only, name=args.name)
    # HTTP endpoint: http://<host>:<port>/mcp
    run_server(server, "stdio" if args.transport == "stdio" else "http", args.host, args.port)


if __name__ == "__main__":
    main()
