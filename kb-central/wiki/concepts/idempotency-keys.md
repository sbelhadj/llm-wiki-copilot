---
type: concept
aliases: [idempotency key, idempotent retries]
sources: [5cef8ed51c95]
updated: 2026-10-15
revisions: 1
status: active
---
# Idempotency keys

Every retry from the [[payment-gateway]] reuses the original request's idempotency key, so an acquirer never charges twice. [src:5cef8ed51c95]

## Related

[[request-timeouts]]
