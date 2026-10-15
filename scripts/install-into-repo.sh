#!/usr/bin/env bash
# Add the LLM Wiki setup to an existing code repository without overwriting anything.
#
#   scripts/install-into-repo.sh ../payments-service
#   scripts/install-into-repo.sh ../payments-service https://kb.mycorp.example/mcp
#
# Files that already exist are skipped, except copilot-instructions.md and AGENTS.md,
# which get the LLM Wiki block appended once.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
template="$here/repo-template"
target="${1:?usage: $0 <target-repo> [central-mcp-url]}"
mcp_url="${2:-}"
target="$(cd "$target" && pwd)"

[ -d "$target/.git" ] || { echo "$target is not a git repository" >&2; exit 1; }

copied=0; skipped=0
while IFS= read -r -d '' src; do
  rel="${src#"$template"/}"
  dst="$target/$rel"
  case "$rel" in
    .github/copilot-instructions.md|AGENTS.md)
      if [ -f "$dst" ]; then
        if grep -q "LLM Wiki" "$dst"; then
          echo "keep   $rel (LLM Wiki block already present)"
        else
          printf '\n' >> "$dst"; cat "$src" >> "$dst"
          echo "append $rel"
        fi
        continue
      fi
      ;;
  esac
  if [ -e "$dst" ]; then
    echo "skip   $rel (exists)"; skipped=$((skipped + 1)); continue
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  copied=$((copied + 1))
done < <(find "$template" -type f -print0)

chmod +x "$target/tools/"*.py "$target/tools/"*.sh "$target/.githooks/pre-commit" 2>/dev/null || true

if [ -n "$mcp_url" ]; then
  sed -i.bak "s#https://kb.internal.example.com/mcp#${mcp_url}#" "$target/.vscode/mcp.json" && rm -f "$target/.vscode/mcp.json.bak"
fi

cat <<EOF

Installed: $copied file(s) copied, $skipped skipped.
Next steps in $target:
  1. pip install "$here/kb-central/mcp"        # repo-wiki MCP server (or install from your kb-central repo)
  2. git config core.hooksPath .githooks       # local validation on commit
  3. python tools/wiki_check.py                # should report 0 findings
  4. Add the WIKI_CURATOR_TOKEN secret if you want wiki-ingest-pr.yml to run.
  5. Point .vscode/mcp.json at your central kb-central MCP URL if you did not pass one.
EOF
