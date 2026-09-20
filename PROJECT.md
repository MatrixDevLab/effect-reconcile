# Project statement

## Audience

Developers building workers, webhooks, queues, or agent tools that can submit a non-idempotent side effect and later lose the acknowledgement.

## Hypothesis

A small typed decision core with an immutable operation identity and explicit reconciliation states can prevent accidental duplicate retries without requiring a full workflow engine.

## First falsifier

If real users need provider-specific transport, durable storage, or policy evaluation before they can use the core, the dependency-free library is too small to be useful and should stop rather than grow into another orchestration framework.

## Design constraints

1. Ambiguous execution is never treated as a transient failure by default.
2. Reconciliation reuses the original operation and request identity.
3. A readback result is evidence, not permission to execute again.
4. Malformed or conflicting evidence produces a typed blocked result.
5. Outputs are deterministic and contain no secrets, payloads, or provider identifiers.

## Stopping point

Stop after a documented, tested pure decision core and a small fixture corpus. Continue only if an external consumer can demonstrate that the core prevents a concrete duplicate or unsafe retry while remaining understandable without a framework.

