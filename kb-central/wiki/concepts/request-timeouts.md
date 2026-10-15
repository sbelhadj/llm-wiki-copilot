---
type: concept
aliases: [upstream timeout, acquirer timeout]
sources: [4bde79ba938f, 5cef8ed51c95, 0a594426ef94]
updated: 2026-10-15
revisions: 2
status: active
---
# Request timeouts (payments)

The upstream timeout bounds how long a gateway worker waits on an acquirer. [src:5cef8ed51c95]
It was 30 s in the 2024 runbook and is 12 s since ADR-112. [src:4bde79ba938f, 5cef8ed51c95]
A timeout that is too long lets one slow dependency exhaust a shared worker pool, as [[incident-2026-08-14]] showed. [src:0a594426ef94]

## Related

[[payment-gateway]] · [[idempotency-keys]]
