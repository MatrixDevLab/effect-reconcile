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

The bounded dependency-free core is implemented. It accepts an operation
identity, attempt evidence, and an optional readback, then returns a typed
decision without performing I/O or authorizing a retry.

```python
from effect_reconcile import (
    AttemptEvidence, AttemptPhase, MutationBoundary, OperationIdentity,
    decide,
)

decision = decide(
    OperationIdentity("operation-42", "request-key-42"),
    AttemptEvidence(
        AttemptPhase.SUBMITTED,
        MutationBoundary.MAY_HAVE_CROSSED,
        "operation-42",
        "request-key-42",
    ),
)
assert decision.disposition.value == "reconcile_required"
assert not decision.retry_permitted
```

`retry_safe` is returned only when the evidence explicitly establishes that
the mutation boundary was not reached. Current authoritative readback settles
as `confirmed_applied` or `confirmed_absent`; neither silently permits a new
execution. Stale, conflicting, unsupported, malformed, or mismatched evidence
returns `blocked`.

The fixture corpus in `fixtures/cases.json` covers pre-mutation rejection,
timeouts, lost acknowledgement, authoritative readback, stale/conflicting
readback, unsupported evidence, and identity mismatch.

## Evidence

- [DataTalksClub issue #259](https://github.com/DataTalksClub/website/issues/259) specifies that a timeout after invocation may be `ambiguous`, must reconcile with the identical identity before retry, and must not automatically repeat execution.
- [OpenTelemetry GenAI issue #239](https://github.com/open-telemetry/semantic-conventions-genai/issues/239) describes the need for auditable decision-point references without putting policy payloads into telemetry.

## Non-goals

No HTTP client, provider adapter, credential handling, queue, database, or automatic retry loop in the first release.
