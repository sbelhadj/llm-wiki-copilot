---
description: Record what this coding session learned into the module wiki (commit your code first)
agent: wiki-curator
argument-hint: commit the session started from, e.g. main or a SHA
---
Session start: ${input:base:commit or branch the session started from (default: main)}.

Precondition: the code changes of this session are committed. If `git status --porcelain` shows modified files
outside `.wiki/`, stop and ask the user to commit first, because every claim must cite a commit.

1. List the session's commits: `git log --format='%h %s' <base>..HEAD`, and read `git diff <base>..HEAD --stat`.
2. Write a session note to `.wiki/raw/sessions/<today>-<branch>.md`: goal, commits, decisions, and dead ends from this chat
   (what was tried, what happened, the command output that proved it). Register it with `python tools/wiki_manifest.py add`.
3. For each module touched:
   - Update `.wiki/entities/<module>.md` with new or changed invariants and pitfalls, citing `[src:git:<sha>]`.
   - Add anything that failed, and why, under `## Tried and failed` in the matching `.wiki/playbooks/<task>.md`,
     citing the session note `[src:<hash>]`.
4. Write nothing that the diff, the commits or a command output from this session does not support.
5. Update `.wiki/index.md`, stage, run `python tools/wiki_check.py --staged`, append
   `## [<today>] session | <branch> | <n> pages` to `.wiki/log.md`.

Then tell the user to review `git diff --cached .wiki/` and commit it as `wiki: session notes <branch>`.
