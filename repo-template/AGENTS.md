# AGENTS.md (LLM Wiki section)

Module memory for this repository lives in `.wiki/`. Read `.wiki/index.md` and the relevant `.wiki/entities/<module>.md` before changing a module.

- Schema: `.github/instructions/wiki.instructions.md`.
- Operations: `.github/prompts/wiki-*.prompt.md`.
- Validate wiki changes: `git add .wiki/ && python tools/wiki_check.py --staged`.
- Organization-wide knowledge: the `llm-wiki` MCP server (read-only for this repo; use `propose_edit` for corrections).
