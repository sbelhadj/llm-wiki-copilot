# AGENTS.md

This repository is an LLM Wiki: `raw/` (immutable sources) is compiled into `wiki/` (cross-linked markdown) by an agent.

- Schema and rules: `.github/instructions/wiki.instructions.md`. Read it before writing anything.
- Operations: `.github/prompts/wiki-ingest.prompt.md`, `wiki-query.prompt.md`, `wiki-lint.prompt.md`, `wiki-review-queue.prompt.md`.
- Validate every change: `git add wiki/ && python tools/wiki_check.py --staged`.
- Register sources: `python tools/wiki_manifest.py add <raw path>`.

This file exists so agents other than Copilot (Codex, Claude Code, Copilot CLI) find the same rules.
