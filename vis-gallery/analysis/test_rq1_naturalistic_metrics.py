import copy
import unittest

from rq1_naturalistic_metrics import validate_truth_association_coverage


def truth_document():
    return {
        "pairs": [
            {
                "case_id": "case-1",
                "vendor": "codex",
                "ts_ms": 1_000,
                "path": "src/lib.rs",
                "target_commit_ids": [],
                "label": "unadjudicable",
                "split": "heldout",
                "scenario": "naturalistic:2026-06-02:edit",
                "adjudicable": False,
            }
        ]
    }


def artifact():
    return {
        "window": {"since": "2026-06-02T07:00:00Z"},
        "events": [
            {
                "id": "event-1",
                "vendor": "codex",
                "ts_ms": 1_020,
                "paths": ["src/lib.rs"],
            }
        ],
        "associations": [
            {
                "id": "association-1",
                "event_id": "event-1",
                "path": "src/lib.rs",
                "candidates": [],
            }
        ],
        "changes": [],
    }


class NaturalisticCoverageTests(unittest.TestCase):
    def test_accepts_exact_injective_current_universe(self):
        validate_truth_association_coverage(truth_document(), [artifact()])

    def test_rejects_stale_truth_and_unannotated_current_associations(self):
        stale = truth_document()
        stale["pairs"][0]["path"] = "removed/fragment"
        with self.assertRaisesRegex(ValueError, "do not resolve"):
            validate_truth_association_coverage(stale, [artifact()])

        expanded = copy.deepcopy(artifact())
        expanded["events"].append(
            {
                "id": "event-2",
                "vendor": "codex",
                "ts_ms": 2_000,
                "paths": ["src/main.rs"],
            }
        )
        expanded["associations"].append(
            {
                "id": "association-2",
                "event_id": "event-2",
                "path": "src/main.rs",
                "candidates": [],
            }
        )
        with self.assertRaisesRegex(ValueError, "without truth labels"):
            validate_truth_association_coverage(truth_document(), [expanded])


if __name__ == "__main__":
    unittest.main()
