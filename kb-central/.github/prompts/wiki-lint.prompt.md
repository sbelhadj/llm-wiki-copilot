---
description: Structural and semantic maintenance pass over the wiki
agent: wiki-curator
argument-hint: scope=all | scope=staged | scope=sample size=50
---
Run a lint pass. Scope: ${input:scope:all, staged, or sample size=N}.

## 1. Structural tier (no judgment needed)

Run `python tools/wiki_check.py --all --json --fail-on raw_modified` and fix mechanically:
- `broken`: relink to the right slug (use llm-wiki `search`), or create a stub page if the concept deserves one.
- `unindexed`: add the page to `wiki/index.md` under its category.
- `orphans`: link the page from the pages it is about, under `## Related`.
- `uncited`, `unknown_source`, `frontmatter`: fix from the page's own cited sources; never invent a source.

## 2. Semantic tier (sampled, bounded cost)

Skip this tier for scope=staged. For scope=sample, pick N pages, preferring pages with many inbound links and
pages not updated for 90 days. For each picked page and its direct neighbors:
- Contradictions between pages: open a `## Conflicts` entry on each affected page. Never resolve them yourself.
- Stale claims: if a newer source in the manifest covers the same fact, open a conflict citing both.
- Missing pages: a term mentioned on 3 or more pages without its own page gets a stub, cited from those pages' sources.
- Drift: for 3 of the picked pages, re-read their raw sources and compare each claim; open a conflict for any divergence.

## 3. Finish

Stage, run `python tools/wiki_check.py --staged` until it passes, and append to `wiki/log.md`:
`## [<today>] lint | <scope> | <n> findings` with one line per fix and per conflict opened.
