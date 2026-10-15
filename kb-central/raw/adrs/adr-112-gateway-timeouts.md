# ADR-112: Reduce payment gateway upstream timeout

Status: Accepted
Date: 2026-07-21
Deciders: Payments Core, SRE

## Context

In a July load test, slow acquirer calls held gateway workers for up to
30 seconds and exhausted the worker pool.

## Decision

- Lower the upstream timeout to acquirers from 30 s to 12 s.
- Raise the per-merchant rate limit to 800 rps, following the Q3 capacity review.
- Retries stay idempotent: every retry reuses the original idempotency key.

## Consequences

The 2024 runbook is superseded on timeouts and rate limits and must be updated.
