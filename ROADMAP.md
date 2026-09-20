# Roadmap

## Phase 0 — bounded core

- [x] Define the operation/attempt/readback vocabulary.
- [x] Implement a pure decision function with typed outcomes.
- [x] Add deterministic fixtures for safe, ambiguous, confirmed, stale, and conflict cases.
- [x] Document what the core cannot know.

## Phase 1 — usable artifact

- [ ] Provide a small JSON-lines CLI for replaying a receipt bundle locally.
- [ ] Add a public conformance fixture format without secrets or payloads.
- [ ] Publish a release candidate only if the validation corpus supports the claims.

## Stop / ship decision

Ship the bounded core if the fixtures demonstrate the ambiguity boundary clearly and the API is useful without a provider integration. Stop if the result requires a queue, database, transport client, or hidden policy engine to be meaningful. The current implementation reaches this stopping point; Phase 1 requires separate consumer evidence.
