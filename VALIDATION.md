# Validation method

The first release is evidence-led rather than benchmark-led.

1. Every fixture declares the original operation identity, attempt phase, possible mutation boundary, and readback evidence.
2. The expected disposition is fixed before running the implementation.
3. The fixture suite runs twice and its serialized output must be byte-identical.
4. Malformed, stale, conflicting, and unsupported evidence must never produce a retry-safe result.
5. The repository must pass compilation, unit tests, and `git diff --check`.

The validation result must distinguish:

- **verified** — the pure function returned the pre-declared result;
- **unknown** — the fixture does not establish provider behavior;
- **out of scope** — transport execution and external readback are deliberately not tested here.

