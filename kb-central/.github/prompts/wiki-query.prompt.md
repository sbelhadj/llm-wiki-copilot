---
description: Answer a question from the compiled wiki, with page citations
agent: wiki-reader
argument-hint: your question
---
Question: ${input:question:what do you want to know?}

Answer it from the wiki only, following your agent instructions: index first, at most 8 pages, one-hop link
expansion if needed, every claim cited as [[slug]], open conflicts called out.

End with one line listing the pages you read. If the answer is a new synthesis worth keeping, say so and offer the
"File this answer as a synthesis page" handoff.
