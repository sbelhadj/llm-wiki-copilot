---
type: entity
aliases: [acquirer router, routing]
sources: [4bde79ba938f]
updated: 2026-10-15
revisions: 1
status: active
---
# Acquirer routing

Component that picks the card acquirer for each transaction coming out of the [[payment-gateway]]. [src:4bde79ba938f]
Failover to another acquirer during latency spikes is done through this component. [src:4bde79ba938f]

## Related

[[payment-gateway]] · [[incident-2026-08-14]]
