---
description: Maintenance pass over the repo wiki
agent: wiki-curator
argument-hint: scope=all | scope=staged
---
Run a lint pass on `.wiki/`. Scope: ${input:scope:all or staged}.

1. Run `python tools/wiki_check.py --all --json --fail-on raw_modified` and fix every finding mechanically:
   relink broken links, index unindexed pages, link orphans from the pages they relate to, fix uncited lines from the page's own sources.
2. For scope=all, also check staleness: for each entity page, list the files of its module changed since the newest
   `[src:git:<sha>]` it cites (`git log --format=%h <sha>..HEAD -- <module path>`). If behaviour described on the page
   may have changed, open a conflict that names the newer commits. Do not rewrite the claim yourself.
3. Stage, run `python tools/wiki_check.py --staged` until it passes, append `## [<today>] lint | <scope> | <n> findings` to `.wiki/log.md`.
