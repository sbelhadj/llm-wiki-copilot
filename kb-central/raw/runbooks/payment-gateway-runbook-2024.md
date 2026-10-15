# Payment gateway runbook (2024 edition)

Owner: Payments Core team (#payments-core)
Last reviewed: 2024-11-04

## Service overview

The payment gateway is the internal service that fronts our card acquirers.
All checkout traffic goes through it before being routed to an acquirer by the
acquirer-routing component.

## Operational limits

- Upstream timeout to acquirers: 30 seconds.
- Rate limit: 500 requests per second per merchant.

## Common incidents

- Acquirer latency spikes: check the acquirer status page, then fail over
  through acquirer-routing.
- 429 responses from the gateway: a merchant hit the per-merchant rate limit.
