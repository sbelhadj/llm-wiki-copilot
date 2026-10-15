This repository is an agent-maintained knowledge base (LLM Wiki pattern).

- `raw/` holds immutable source documents. `wiki/` holds compiled, cross-linked markdown pages. `review-queue/` holds edits proposed through MCP.
- To answer a question, read `wiki/index.md` first, then only the pages you need. Cite pages as [[slug]]. Do not answer from `raw/` unless the wiki has no page on the topic, and say so when that happens.
- Only the `wiki-curator` agent writes under `wiki/`. Nobody writes under `raw/` except by adding new files.
- The full schema is in `.github/instructions/wiki.instructions.md`. Read it before any change to `wiki/`.
