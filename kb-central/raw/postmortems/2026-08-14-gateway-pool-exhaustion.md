# Postmortem: gateway worker pool exhaustion, 2026-08-14

Severity: SEV-2, 41 minutes of degraded checkout

## Summary

One acquirer degraded and answered slowly. Gateway workers waited on it up to
the configured timeout, the worker pool filled, and healthy acquirers could not
be reached either.

## Root cause

The 12 s timeout from ADR-112 had not yet been rolled out to the EU cluster,
which still ran with 30 s.

## Action items

- Roll out the 12 s timeout to every cluster (done 2026-08-15).
- Add an alert on worker pool saturation above 80 %.
