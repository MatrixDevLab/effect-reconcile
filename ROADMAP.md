# Roadmap

## Phase 0 — bounded core

- [ ] Define the operation/attempt/readback vocabulary.
- [ ] Implement a pure decision function with typed outcomes.
- [ ] Add deterministic fixtures for safe, ambiguous, confirmed, stale, and conflict cases.
- [ ] Document what the core cannot know.

## Phase 1 — usable artifact

- [ ] Provide a small JSON-lines CLI for replaying a receipt bundle locally.
- [ ] Add a public conformance fixture format without secrets or payloads.
- [ ] Publish a release candidate only if the validation corpus supports the claims.

## Stop / ship decision

Ship the bounded core if the fixtures demonstrate the ambiguity boundary clearly and the API is useful without a provider integration. Stop if the result requires a queue, database, transport client, or hidden policy engine to be meaningful.

