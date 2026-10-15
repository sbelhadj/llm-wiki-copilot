#!/usr/bin/env bash
# Batch ingest with Copilot CLI: one source per headless run, one commit per source.
#
#   scripts/ingest_batch.sh raw/adrs/*.md
#   scripts/ingest_batch.sh $(git diff --name-only --diff-filter=A origin/main -- raw/)
#
# Requires: copilot CLI (npm install -g @github/copilot), signed in or COPILOT_GITHUB_TOKEN set,
# python3, and wiki_mcp installed if the curator agent uses the llm-wiki tools.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ "$#" -eq 0 ]; then
  echo "usage: $0 raw/<file> [raw/<file> ...]" >&2
  exit 2
fi

failed=()
for src in "$@"; do
  case "$src" in
    raw/*) ;;
    *) echo "skip $src: not under raw/" >&2; continue ;;
  esac
  [ "$(basename "$src")" = "manifest.jsonl" ] && continue

  echo "==> ingest $src"
  if ! copilot -p "Follow .github/prompts/wiki-ingest.prompt.md with source=${src}. Do not commit; stage your changes only." \
      --agent wiki-curator \
      --allow-tool 'write' \
      --allow-tool 'shell(python tools/wiki_check.py:*)' \
      --allow-tool 'shell(python tools/wiki_manifest.py:*)' \
      --allow-tool 'shell(git add:*)' \
      --allow-tool 'shell(git diff:*)' \
      --allow-tool 'llm-wiki' \
      --deny-tool 'shell(git push)' \
      --deny-tool 'shell(git commit)' \
      --deny-tool 'shell(rm:*)' \
      --deny-tool 'shell(curl:*)'; then
    echo "!! copilot failed on $src" >&2
    git restore --staged wiki/ raw/manifest.jsonl 2>/dev/null || true
    git checkout -- wiki/ raw/manifest.jsonl 2>/dev/null || true
    failed+=("$src")
    continue
  fi

  git add wiki/ raw/manifest.jsonl "$src"
  # Trust, but verify outside the agent.
  if ! python3 tools/wiki_check.py --staged; then
    echo "!! validation failed after ingesting $src; changes left staged for review" >&2
    failed+=("$src")
    break
  fi
  git commit -q -m "ingest $(basename "$src")" -- wiki/ raw/manifest.jsonl "$src"
done

if [ "${#failed[@]}" -gt 0 ]; then
  printf 'failed: %s\n' "${failed[@]}" >&2
  exit 1
fi
echo "done"
