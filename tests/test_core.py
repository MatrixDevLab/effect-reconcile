import json
from pathlib import Path
import unittest

from effect_reconcile import (
    AttemptEvidence,
    AttemptPhase,
    Disposition,
    MutationBoundary,
    OperationIdentity,
    ReadbackAuthority,
    ReadbackEvidence,
    ReadbackFreshness,
    ReadbackStatus,
    decide,
    decide_from_dict,
    serialize_cases,
)


ROOT = Path(__file__).resolve().parents[1]


class CoreFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((ROOT / "fixtures" / "cases.json").read_text())

    def test_fixtures_match_declared_outcomes(self):
        for case in self.cases:
            with self.subTest(case=case["name"]):
                decision = decide_from_dict(case["input"])
                self.assertEqual(decision.disposition.value, case["expected"]["disposition"])
                self.assertEqual(decision.reason_code, case["expected"]["reason_code"])
                self.assertEqual(decision.retry_permitted, decision.disposition is Disposition.RETRY_SAFE)

    def test_serialized_fixture_results_are_deterministic(self):
        first = serialize_cases(self.cases)
        second = serialize_cases(self.cases)
        self.assertEqual(first, second)
        self.assertNotIn("request_key", first)
        self.assertNotIn("operation_id", first)

    def test_authoritative_absence_does_not_permit_retry(self):
        identity = OperationIdentity("op", "key")
        attempt = AttemptEvidence(
            AttemptPhase.SUBMITTED,
            MutationBoundary.MAY_HAVE_CROSSED,
            "op",
            "key",
        )
        readback = ReadbackEvidence(
            ReadbackStatus.ABSENT,
            ReadbackAuthority.AUTHORITATIVE,
            ReadbackFreshness.CURRENT,
            "op",
            "key",
        )
        decision = decide(identity, attempt, readback)
        self.assertEqual(decision.disposition, Disposition.CONFIRMED_ABSENT)
        self.assertFalse(decision.retry_permitted)

    def test_malformed_fixture_fails_closed(self):
        decision = decide_from_dict(
            {
                "operation": {"operation_id": "op", "request_key": "key"},
                "attempt": {
                    "phase": "not-a-phase",
                    "mutation_boundary": "not-a-boundary",
                    "operation_id": "op",
                    "request_key": "key",
                },
            }
        )
        self.assertEqual(decision.disposition, Disposition.BLOCKED)

    def test_empty_identity_fails_closed(self):
        decision = decide(
            OperationIdentity("", "key"),
            AttemptEvidence(
                AttemptPhase.PREPARED,
                MutationBoundary.NOT_REACHED,
                "",
                "key",
            ),
        )
        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(decision.reason_code, "malformed_identity")


if __name__ == "__main__":
    unittest.main()
