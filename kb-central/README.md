# kb-central

Organization-wide knowledge base, maintained by an agent with the LLM Wiki pattern. Sources go into `raw/`, the `wiki-curator` agent compiles them into `wiki/`, and everyone else reads the wiki through Copilot or the MCP server.

## Layout

| Path | Owner | Rule |
| --- | --- | --- |
| `raw/` | humans, CI | Append-only. Add files; never edit or delete. `manifest.jsonl` maps hashes to files. |
| `wiki/` | `wiki-curator` agent | Compiled pages. Every claim cites `[src:<hash>]`. |
| `.github/instructions/wiki.instructions.md` | humans | The schema. Reviewed like code. |
| `review-queue/` | MCP server | Edits proposed by other repos, bots and people. |
| `mcp/` | humans | The `wiki_mcp` server. |
| `tools/` | humans | Validator and manifest helper. No dependencies. |

## Daily use

In VS Code chat (agent mode):

- `/wiki-ingest raw/adrs/adr-120.md` compiles one source.
- `/wiki-query how did the gateway timeout change?` answers with page citations.
- `/wiki-lint scope=staged` checks what you just changed.
- `/wiki-review-queue` processes proposed edits.

From a terminal:

```bash
scripts/ingest_batch.sh raw/postmortems/*.md     # one headless Copilot CLI run and one commit per source
python tools/wiki_check.py                        # validate everything
python tools/wiki_manifest.py list                # hashes to sources
```

## Automation

- `wiki-check.yml`: on every PR, rejects edits to existing raw files, uncited claims, broken links and unindexed pages.
- `wiki-ingest.yml`: when new files land in `raw/` on main, compiles them and opens a PR.
- `wiki-nightly.yml`: sampled semantic lint every weekday night, as a PR.

All three need the curator seat token in the `WIKI_CURATOR_TOKEN` secret, except `wiki-check`, which uses no model.

## Serving the wiki

```bash
pip install ./mcp
python -m wiki_mcp --root . --transport http --port 8765 --acl mcp/acl.example.json
```

Deploy it behind your SSO proxy (see `mcp/README.md` and `mcp/Dockerfile`) and point every code repo's `.vscode/mcp.json` at it.

Enable the local pre-commit check once per clone: `git config core.hooksPath .githooks`.
