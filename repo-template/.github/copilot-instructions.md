<!-- LLM Wiki block: keep these lines if you merge this file into existing instructions. -->
This repository keeps an agent-maintained knowledge base in `.wiki/`.

- Before changing code in a module, read `.wiki/index.md` and the module's page in `.wiki/entities/`, plus any matching page in `.wiki/playbooks/`.
- Organization-wide knowledge (architecture, platform services, ADRs, postmortems) is in the `llm-wiki` MCP server. Read it; never try to write it except through `propose_edit`.
- Never edit files under `.wiki/raw/`. Only the `wiki-curator` agent edits pages under `.wiki/`.
- When you finish a task, remind the user to run `/wiki-session-end` after committing.
<!-- end LLM Wiki block -->
