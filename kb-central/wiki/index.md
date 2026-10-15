# Knowledge base index

One line per page: link, one-line summary, last update. Maintained by the wiki-curator agent on every ingest.

## Entities

- [[payment-gateway]]: internal service fronting card acquirers; 12 s timeout, 800 rps limit (2026-10-15)
- [[acquirer-routing]]: picks the acquirer per transaction, handles failover (2026-10-15)
- [[team-payments-core]]: team owning the payment gateway (2026-10-15)
- [[incident-2026-08-14]]: SEV-2 gateway worker pool exhaustion, EU cluster on old timeout (2026-10-15)

## Concepts

- [[request-timeouts]]: why the gateway timeout went from 30 s to 12 s (2026-10-15)
- [[idempotency-keys]]: retries reuse the original key to avoid double charges (2026-10-15)

## Syntheses

_None yet. Answers worth keeping are filed here by /wiki-query._

## Sources

- [[4bde79ba938f]]: payment gateway runbook, 2024 (2026-10-15)
- [[5cef8ed51c95]]: ADR-112, reduce gateway upstream timeout (2026-10-15)
- [[0a594426ef94]]: postmortem, gateway pool exhaustion 2026-08-14 (2026-10-15)
