#!/usr/bin/env bash
# Write a deterministic digest of a merged PR to .wiki/raw/prs/<number>.md and register it.
# The agent calls this instead of writing raw files itself.
#
#   bash tools/wiki_pr_digest.sh 1234
#
# Requires the GitHub CLI (gh), authenticated.
set -euo pipefail

number="${1:?usage: $0 <pr-number>}"
case "$number" in (*[!0-9]*|'') echo "PR number must be numeric" >&2; exit 2;; esac

cd "$(git rev-parse --show-toplevel)"
out=".wiki/raw/prs/${number}.md"
if [ -e "$out" ]; then
  echo "$out already exists (raw files are immutable)" >&2
  python3 tools/wiki_manifest.py add "$out"
  exit 0
fi
mkdir -p .wiki/raw/prs

gh pr view "$number" --json number,title,body,author,mergedAt,mergeCommit,baseRefName,url,files,closingIssuesReferences \
  --template '# PR #{{.number}}: {{.title}}

- URL: {{.url}}
- Author: {{.author.login}}
- Merged: {{.mergedAt}} into {{.baseRefName}}
- Merge commit: {{if .mergeCommit}}{{.mergeCommit.oid}}{{end}}
- Closes: {{range .closingIssuesReferences}}#{{.number}} {{end}}

## Description

{{.body}}

## Files changed

{{range .files}}- {{.path}} (+{{.additions}} -{{.deletions}})
{{end}}' > "$out"

python3 tools/wiki_manifest.py add "$out"
