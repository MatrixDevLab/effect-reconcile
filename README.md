# effect-reconcile

`effect-reconcile` is a small, provider-neutral Python library for deciding what to do when a side-effecting request may have reached its destination but its receipt was lost.

## Problem

Timeouts and connection loss after submission are ambiguous: retrying can duplicate a write, while treating the attempt as failed can hide a real effect. Existing systems often encode the distinction in application-specific workers, making the safe boundary hard to test and reuse.

## Smallest useful release

Given a durable operation identity, an attempt outcome, and a provider-independent reconciliation result, return a typed disposition:

- `RETRY_SAFE` only when evidence establishes that mutation was impossible;
- `RECONCILE_REQUIRED` when execution may have crossed the mutation boundary;
- `CONFIRMED_APPLIED` or `CONFIRMED_ABSENT` after an authoritative readback;
- `BLOCKED` for malformed, stale, conflicting, or unsupported evidence.

The library will not execute requests, invent receipts, or silently change an idempotency key.

## Status

Research-backed repository scaffold. The first implementation will remain dependency-free and local, with deterministic fixtures for timeout, lost-acknowledgement, duplicate, stale, and conflicting readback cases.

## Evidence

- [DataTalksClub issue #259](https://github.com/DataTalksClub/website/issues/259) specifies that a timeout after invocation may be `ambiguous`, must reconcile with the identical identity before retry, and must not automatically repeat execution.
- [OpenTelemetry GenAI issue #239](https://github.com/open-telemetry/semantic-conventions-genai/issues/239) describes the need for auditable decision-point references without putting policy payloads into telemetry.

## Non-goals

No HTTP client, provider adapter, credential handling, queue, database, or automatic retry loop in the first release.

