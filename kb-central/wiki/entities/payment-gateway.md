---
type: entity
aliases: [payments-gw, the gateway, gateway]
sources: [4bde79ba938f, 5cef8ed51c95, 0a594426ef94]
updated: 2026-10-15
revisions: 3
status: active
---
# Payment gateway

Internal service that fronts the card acquirers; all checkout traffic passes through it. [src:4bde79ba938f]
Owned by [[team-payments-core]]; routing to a specific acquirer is delegated to [[acquirer-routing]]. [src:4bde79ba938f]

## Operational limits

- Upstream timeout to acquirers: 12 s since ADR-112, see [[request-timeouts]]. [src:5cef8ed51c95]
- The 12 s timeout reached every cluster on 2026-08-15; the EU cluster ran 30 s until then. [src:0a594426ef94]
- Per-merchant rate limit: 800 rps after the Q3 capacity review. [src:5cef8ed51c95]
- Retries reuse the original idempotency key, see [[idempotency-keys]]. [src:5cef8ed51c95]

## Known failure modes

- A slow acquirer can exhaust the worker pool and block healthy acquirers too, as in [[incident-2026-08-14]]. [src:0a594426ef94]
- HTTP 429 from the gateway means a merchant hit the per-merchant rate limit. [src:4bde79ba938f]

## Conflicts

- Rate limit: 500 rps per [src:4bde79ba938f] (runbook, 2024) vs 800 rps per [src:5cef8ed51c95] (ADR-112, 2026). Open: runbook not yet updated.
- Timeout: 30 s per [src:4bde79ba938f] vs 12 s per [src:5cef8ed51c95]. Resolved 2026-08-20 by curator review: ADR-112 supersedes the runbook.

## Related

[[acquirer-routing]] · [[request-timeouts]] · [[incident-2026-08-14]] · [[team-payments-core]]
