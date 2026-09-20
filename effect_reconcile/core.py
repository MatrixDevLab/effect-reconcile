"""Pure, provider-neutral decisions for ambiguous side effects.

The module deliberately does not perform I/O.  Callers supply an immutable
operation identity, the best evidence about the attempt, and (optionally) a
readback.  A readback settles what was observed; it never grants permission
to execute another request.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping


class Disposition(str, Enum):
    """The only actions the bounded core can recommend to a caller."""

    RETRY_SAFE = "retry_safe"
    RECONCILE_REQUIRED = "reconcile_required"
    CONFIRMED_APPLIED = "confirmed_applied"
    CONFIRMED_ABSENT = "confirmed_absent"
    BLOCKED = "blocked"


class AttemptPhase(str, Enum):
    """Provider-neutral phase reported for the original attempt."""

    PREPARED = "prepared"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class MutationBoundary(str, Enum):
    """What the attempt evidence says about crossing the mutation boundary."""

    NOT_REACHED = "not_reached"
    MAY_HAVE_CROSSED = "may_have_crossed"
    CROSSED = "crossed"
    UNKNOWN = "unknown"


class ReadbackStatus(str, Enum):
    """The state observed by a readback, before authority/freshness checks."""

    APPLIED = "applied"
    ABSENT = "absent"
    CONFLICTING = "conflicting"
    UNSUPPORTED = "unsupported"


class ReadbackAuthority(str, Enum):
    AUTHORITATIVE = "authoritative"
    UNKNOWN = "unknown"


class ReadbackFreshness(str, Enum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class OperationIdentity:
    """The durable identity that must be reused during reconciliation."""

    operation_id: str
    request_key: str


@dataclass(frozen=True)
class AttemptEvidence:
    phase: AttemptPhase
    mutation_boundary: MutationBoundary
    operation_id: str
    request_key: str


@dataclass(frozen=True)
class ReadbackEvidence:
    status: ReadbackStatus
    authority: ReadbackAuthority
    freshness: ReadbackFreshness
    operation_id: str
    request_key: str


@dataclass(frozen=True)
class Decision:
    """A deterministic disposition plus a machine-readable reason."""

    disposition: Disposition
    reason_code: str

    @property
    def retry_permitted(self) -> bool:
        """Only explicit mutation-impossible evidence permits a retry."""

        return self.disposition is Disposition.RETRY_SAFE

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition.value,
            "reason_code": self.reason_code,
            "retry_permitted": self.retry_permitted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def _blocked(reason_code: str) -> Decision:
    return Decision(Disposition.BLOCKED, reason_code)


def _valid_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identity_valid(identity: OperationIdentity) -> bool:
    return _valid_text(identity.operation_id) and _valid_text(identity.request_key)


def decide(
    identity: OperationIdentity,
    attempt: AttemptEvidence,
    readback: ReadbackEvidence | None = None,
) -> Decision:
    """Decide from supplied evidence without performing or authorizing I/O.

    Invalid, contradictory, stale, non-authoritative, or conflicting evidence
    fails closed as ``blocked``.  In particular, a current authoritative
    ``absent`` readback settles observation as ``confirmed_absent``; it does
    not become an implicit retry instruction.
    """

    if not isinstance(identity, OperationIdentity) or not _identity_valid(identity):
        return _blocked("malformed_identity")
    if not isinstance(attempt, AttemptEvidence):
        return _blocked("malformed_attempt")
    if not isinstance(attempt.phase, AttemptPhase) or not isinstance(
        attempt.mutation_boundary, MutationBoundary
    ):
        return _blocked("malformed_attempt")
    if not _valid_text(attempt.operation_id) or not _valid_text(attempt.request_key):
        return _blocked("malformed_attempt_identity")
    if (attempt.operation_id, attempt.request_key) != (
        identity.operation_id,
        identity.request_key,
    ):
        return _blocked("attempt_identity_mismatch")

    if attempt.phase is AttemptPhase.PREPARED and attempt.mutation_boundary is not MutationBoundary.NOT_REACHED:
        return _blocked("contradictory_attempt_evidence")
    if attempt.phase is AttemptPhase.REJECTED and attempt.mutation_boundary is not MutationBoundary.NOT_REACHED:
        return _blocked("contradictory_attempt_evidence")

    if readback is not None:
        if not isinstance(readback, ReadbackEvidence):
            return _blocked("malformed_readback")
        if not isinstance(readback.status, ReadbackStatus) or not isinstance(
            readback.authority, ReadbackAuthority
        ) or not isinstance(readback.freshness, ReadbackFreshness):
            return _blocked("malformed_readback")
        if not _valid_text(readback.operation_id) or not _valid_text(readback.request_key):
            return _blocked("malformed_readback_identity")
        if (readback.operation_id, readback.request_key) != (
            identity.operation_id,
            identity.request_key,
        ):
            return _blocked("readback_identity_mismatch")
        if readback.authority is not ReadbackAuthority.AUTHORITATIVE:
            return _blocked("non_authoritative_readback")
        if readback.freshness is not ReadbackFreshness.CURRENT:
            return _blocked("stale_or_unknown_readback")
        if readback.status is ReadbackStatus.APPLIED:
            return Decision(Disposition.CONFIRMED_APPLIED, "authoritative_current_applied")
        if readback.status is ReadbackStatus.ABSENT:
            return Decision(Disposition.CONFIRMED_ABSENT, "authoritative_current_absent")
        if readback.status is ReadbackStatus.CONFLICTING:
            return _blocked("conflicting_readback")
        return _blocked("unsupported_readback")

    if attempt.mutation_boundary is MutationBoundary.NOT_REACHED:
        return Decision(Disposition.RETRY_SAFE, "mutation_impossible")
    return Decision(Disposition.RECONCILE_REQUIRED, "mutation_possibly_reached")


def _enum(enum_type: type[Enum], value: object) -> Enum:
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise ValueError(f"unsupported {enum_type.__name__}")


def decide_from_dict(payload: Mapping[str, object]) -> Decision:
    """Parse a secret-free fixture payload and fail closed on malformed input."""

    if not isinstance(payload, Mapping):
        return _blocked("malformed_fixture")
    try:
        operation = payload["operation"]
        attempt = payload["attempt"]
        if not isinstance(operation, Mapping) or not isinstance(attempt, Mapping):
            return _blocked("malformed_fixture")
        identity = OperationIdentity(
            operation_id=operation["operation_id"],
            request_key=operation["request_key"],
        )
        attempt_evidence = AttemptEvidence(
            phase=_enum(AttemptPhase, attempt["phase"]),
            mutation_boundary=_enum(MutationBoundary, attempt["mutation_boundary"]),
            operation_id=attempt["operation_id"],
            request_key=attempt["request_key"],
        )
        raw_readback = payload.get("readback")
        readback = None
        if raw_readback is not None:
            if not isinstance(raw_readback, Mapping):
                return _blocked("malformed_fixture")
            readback = ReadbackEvidence(
                status=_enum(ReadbackStatus, raw_readback["status"]),
                authority=_enum(ReadbackAuthority, raw_readback["authority"]),
                freshness=_enum(ReadbackFreshness, raw_readback["freshness"]),
                operation_id=raw_readback["operation_id"],
                request_key=raw_readback["request_key"],
            )
    except (KeyError, TypeError, ValueError):
        return _blocked("malformed_fixture")
    return decide(identity, attempt_evidence, readback)


def serialize_cases(cases: list[Mapping[str, object]]) -> str:
    """Return stable JSON for fixture results without embedding request data."""

    results = []
    for case in cases:
        name = case.get("name")
        result = decide_from_dict(case.get("input", {}))
        results.append({"name": name, "decision": result.to_dict()})
    return json.dumps(results, sort_keys=True, separators=(",", ":"))
