---
description: Ingest a merged PR (or an existing raw file) into the repo wiki
agent: wiki-curator
argument-hint: PR number, or a path under .wiki/raw/
---
Ingest ${input:source:PR number or path under .wiki/raw/}.

1. If it is a PR number, run `bash tools/wiki_pr_digest.sh <number>`. It writes `.wiki/raw/prs/<number>.md`
   and prints the hash. If it is a path, run `python tools/wiki_manifest.py add <path>`.
   This is the only way you create files under `.wiki/raw/`.
2. Read the raw file and `.wiki/index.md`. Plan: the modules (entities) and playbooks it touches, each mapped to an
   existing slug or NEW. Show the plan.
3. Write `.wiki/sources/<hash>.md`, then update or create each page in the plan. Expect 3 to 15 pages.
   Cite with `[src:<hash>]`, or `[src:pr:<number>]` and `[src:git:<sha>]` for facts tied to a commit.
4. A fact that contradicts an existing claim goes under `## Conflicts`, ending with `Open.` Do not edit the old claim.
5. Add reciprocal links, update `.wiki/index.md`, stage, run `python tools/wiki_check.py --staged` until it passes.
6. Append to `.wiki/log.md`: `## [<today>] ingest | <file> | <n> pages`.
7. If the PR changes something other repositories depend on, propose it to kb-central with `llm-wiki/propose_edit`.
