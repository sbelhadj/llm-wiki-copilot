# Wiki log

Append-only. One entry per operation, newest last. Prefixes are fixed so the log stays greppable:
`grep '| ingest |' wiki/log.md`, `grep '| conflict |' wiki/log.md`.

## [2026-10-15] ingest | payment-gateway-runbook-2024.md | 5 pages
created: payment-gateway, acquirer-routing, team-payments-core, request-timeouts, sources/4bde79ba938f

## [2026-10-15] ingest | adr-112-gateway-timeouts.md | 6 pages
created: idempotency-keys, sources/5cef8ed51c95
updated: payment-gateway, request-timeouts, team-payments-core, index

## [2026-10-15] conflict | payment-gateway | rate limit 500 vs 800 rps | open
## [2026-10-15] conflict | payment-gateway | timeout 30 s vs 12 s | resolved: ADR-112 supersedes

## [2026-10-15] ingest | 2026-08-14-gateway-pool-exhaustion.md | 5 pages
created: incident-2026-08-14, sources/0a594426ef94
updated: payment-gateway, request-timeouts, index
