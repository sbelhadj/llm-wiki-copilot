# wiki-mcp

MCP server that exposes a compiled LLM Wiki. It reads `wiki/` (kb-central layout) or `.wiki/` (in-repo layout) and never writes to it.

| Surface | Kind | Purpose |
| --- | --- | --- |
| `wiki://index` | resource | The catalog. Clients read it first. |
| `wiki://page/{slug}` | resource | One page, frontmatter included. |
| `read_index`, `read_page` | tools | Same reads, for clients that do not support resources. |
| `search` | tool | BM25 over titles, aliases, summaries and headings. |
| `neighbors` | tool | Inbound and outbound links around a page, up to depth 3. |
| `history` | tool | Recent git commits touching a page. |
| `propose_edit` | tool | Queues a change in `review-queue/` for the curator. Absent with `--read-only`. |

## Install

```bash
pip install ./kb-central/mcp          # or: pip install "git+https://github.com/<org>/kb-central#subdirectory=mcp"
```

## Run

```bash
# local, stdio (what .vscode/mcp.json starts)
python -m wiki_mcp --root . --read-only

# central, HTTP behind your SSO proxy
python -m wiki_mcp --root /srv/kb-central --transport http --host 0.0.0.0 --port 8765 --acl acl.json
```

The HTTP endpoint is `http://<host>:<port>/mcp`. Put it behind a reverse proxy that authenticates users and sets `X-Forwarded-User` (or `X-Forwarded-Email`). The server reads that header to apply the ACL. Over stdio, the identity comes from the `WIKI_CALLER` environment variable.

## Access control

Without `--acl`, every page is readable. With it, each caller sees only the directories listed for them, and `wiki://index` is filtered to match:

```json
{
  "default": ["entities", "concepts", "sources", "syntheses"],
  "users": {
    "curator-bot@corp.example": ["*"],
    "finance-lead@corp.example": ["*"]
  }
}
```

See `acl.example.json`.

## Review queue

`propose_edit` writes one JSON file per proposal to `review-queue/` (or `--queue`). The `/wiki-review-queue` prompt in kb-central has the curator process it: apply, validate, commit, and move the file to `review-queue/done/`.
