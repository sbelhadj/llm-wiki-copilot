---
description: Compile one raw source into the wiki
agent: wiki-curator
argument-hint: path under raw/, e.g. raw/adrs/adr-120.md
---
Ingest ${input:source:path under raw/}.

1. Register it: `python tools/wiki_manifest.py add <path>`. Use the printed hash as `<hash>` below.
   If the source is already in the manifest and `wiki/sources/<hash>.md` exists, stop and say so.
2. Read the source and `wiki/index.md`. Plan: list every entity and concept the source touches, each mapped to an
   existing slug or marked NEW. Use the llm-wiki `search` tool for names not obviously in the index. Show the plan.
3. Write `wiki/sources/<hash>.md`: origin, date, key claims, what it supersedes.
4. Update every mapped page and create every NEW page from the templates in the schema. Expect 5 to 15 pages.
   - Add new facts with `[src:<hash>]`.
   - A fact that contradicts an existing cited claim goes under `## Conflicts`, ending with `Open.` Do not edit the old claim.
   - Bump `revisions` and set `updated` to today on every page you rewrite.
5. Add reciprocal `[[links]]`. Update `wiki/index.md` for every created page and every changed summary.
6. `git add wiki/ raw/manifest.jsonl` then `python tools/wiki_check.py --staged`. Fix until it passes.
7. Append to `wiki/log.md`: `## [<today>] ingest | <file name> | <n> pages` with created/updated lists, plus one `conflict` line per conflict.
