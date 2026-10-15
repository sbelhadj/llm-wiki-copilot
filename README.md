# LLM Wiki for GitHub Copilot Business

Reference implementation of the setup described in [Stop retrieving, start compiling: the LLM Wiki pattern](https://tech-tech.life/2026/10/15/stop-retrieving-start-compiling-the-llm-wiki-pattern/). It gives a Copilot Business team an agent-maintained knowledge base: sources are compiled once into cross-linked markdown pages, and every agent, IDE and bot reads those pages instead of re-retrieving raw documents.

It runs with VS Code agent mode, Copilot CLI and GitHub Actions. The only Python dependency is the `mcp` package, for the MCP server.

## What is in here

```text
llm-wiki-copilot/
├── kb-central/            # the org-wide knowledge repo: copy it into its own GitHub repository
│   ├── raw/               # immutable sources + manifest.jsonl (3 sample documents)
│   ├── wiki/              # compiled pages, index.md, log.md (sample: a payment gateway domain)
│   ├── .github/           # schema (instructions), curator/reader agents, prompts, workflows
│   ├── mcp/               # wiki_mcp: the MCP server (pip package + Dockerfile)
│   ├── scripts/           # ingest_batch.sh (Copilot CLI, one source per run)
│   └── tools/             # wiki_check.py, wiki_manifest.py
├── repo-template/         # files to add to every code repository (.wiki/ module memory)
├── scripts/install-into-repo.sh
├── tools/                 # canonical copies of the shared tools
└── tests/                 # 40 tests: validator, manifest, MCP server, config sanity
```

## How the pieces map to the pattern

| LLM Wiki concept | File | Notes |
| --- | --- | --- |
| Raw sources (layer 1) | `raw/`, `.wiki/raw/` | Append-only, enforced by `wiki_check.py` in pre-commit and CI |
| Wiki (layer 2) | `wiki/`, `.wiki/` | `index.md` catalog, `log.md` journal, pages with `[src:<hash>]` on every claim |
| Schema (layer 3) | `.github/instructions/wiki.instructions.md` | Path-scoped Copilot instructions, applied when the agent touches the wiki |
| Curator and reader roles | `.github/agents/wiki-*.agent.md` | Write access is decided by each agent's tool list |
| Ingest, query, lint | `.github/prompts/wiki-*.prompt.md` | Slash commands in VS Code chat |
| Session memory | `repo-template/.github/prompts/wiki-session-end.prompt.md` | Run after committing a task |
| Validator | `tools/wiki_check.py` | Deterministic, no model, no dependencies |
| Shared read surface | `kb-central/mcp/` | `wiki://index`, `wiki://page/{slug}`, `search`, `neighbors`, `history`, `propose_edit` |
| Batch and scheduled work | `scripts/ingest_batch.sh`, `.github/workflows/` | Copilot CLI in programmatic mode, results land as PRs |

## Quick start

### 1. Try it locally (five minutes)

```bash
pip install ./kb-central/mcp pytest
python -m pytest -q tests                           # 40 passed
cd kb-central
python tools/wiki_check.py                          # wiki_check: 0 finding(s)
python -m wiki_mcp --root . --read-only             # stdio MCP server (Ctrl+C to stop)
```

Open `kb-central/` in VS Code, enable agent mode, and run `/wiki-query why is the gateway timeout 12 seconds?`. The answer should cite `[[request-timeouts]]` and `[[incident-2026-08-14]]` and flag the open rate-limit conflict.

### 2. Stand up kb-central

1. Create a repository (for example `your-org/kb-central`) and copy the `kb-central/` folder into it. Delete the sample `raw/` and `wiki/` content, or keep it until your first real ingest.
2. Ask an org owner to enable, in the organization's Copilot policies:
   - MCP servers in Copilot. If you use an MCP registry allowlist, add your internal server.
   - Copilot CLI, for the members who run batch ingest.
3. Review content exclusions. Do not exclude `raw/` or `wiki/`.
4. Create a service seat for the curator. Store its token as the `WIKI_CURATOR_TOKEN` Actions secret.
5. Run `git config core.hooksPath .githooks` in each clone.
6. Ingest your first 10 to 20 high-value sources by hand with `/wiki-ingest` and read every diff. Tighten the schema based on what you see.
7. Deploy the MCP server centrally (`kb-central/mcp/Dockerfile`) behind your SSO proxy, with an ACL file (`mcp/acl.example.json`).

### 3. Add module memory to a code repository

```bash
scripts/install-into-repo.sh ../payments-service https://kb.your-org.example/mcp
```

The script never overwrites files. It appends the LLM Wiki block to an existing `AGENTS.md` and `.github/copilot-instructions.md`, and skips everything else that already exists. After that:

- Developers run `/wiki-session-end` after committing a task, then review and commit the wiki diff.
- `wiki-ingest-pr.yml` compiles every merged PR into `.wiki/` and opens a follow-up PR.
- `wiki-check.yml` blocks PRs that edit raw files or add uncited claims.

## The validator

```bash
python tools/wiki_check.py                 # all pages
python tools/wiki_check.py --staged        # staged pages and staged raw/ changes (pre-commit, agents)
python tools/wiki_check.py --base origin/main --fail-on raw_modified,uncited,broken,unindexed   # CI
python tools/wiki_check.py --json          # machine-readable, used by /wiki-lint
```

| Category | Fails by default | Meaning |
| --- | --- | --- |
| `raw_modified` | yes | A raw file was edited, deleted or renamed, or the manifest changed other than by appending |
| `uncited` | yes | A prose line has no `[src:...]` tag. Lines made only of `[[links]]`, code blocks and tables are exempt |
| `unknown_source` | yes | `[src:<hash>]` is not in the manifest (`git:` and `pr:` tags are not checked) |
| `broken` | yes | `[[link]]` to a page that does not exist |
| `frontmatter` | yes | Page lacks `type` or `updated` |
| `duplicate_slug` | yes | Two pages with the same file name |
| `orphans` | warning | No page links here (index.md does not count) |
| `unindexed` | warning (error in CI) | Page missing from `index.md` |

## Things to check against your environment

These parts depend on Copilot features that change often. They are marked in the files and worth a five-minute check before rollout:

- **Agent tool names.** The agents use the `read`, `search`, `edit` and `execute` tool sets and `llm-wiki/*`. Compare them with the tool picker in your VS Code version.
- **Model pinning.** The `model:` line in each agent is commented out. Set it to a name from your model picker.
- **Copilot CLI in Actions.** The workflows pass the curator token as `COPILOT_GITHUB_TOKEN`. Check GitHub's Copilot CLI docs for the current variable name and required permission.
- **Prompt files from the CLI.** Headless runs reference prompt files by path ("Follow .github/prompts/wiki-ingest.prompt.md ...") rather than relying on slash commands, which works whether or not your CLI version expands them.
- **MCP SDK version.** `wiki_mcp` runs on both `mcp` 1.x (FastMCP) and 2.x (MCPServer); the test suite passes on both.
- **Billing.** Ingest and lint consume GitHub AI Credits. Track them per curator seat.

## Development

```bash
make test        # run the test suite
make sync        # copy tools/ into kb-central/tools and repo-template/tools
make check       # validate both sample wikis
```

`tests/test_layout.py` fails if the copies of the shared tools drift from `tools/`.
