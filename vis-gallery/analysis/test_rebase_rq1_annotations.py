import unittest

from rebase_rq1_annotations import carry_mapping, rebase_annotations


def pair(pair_id, timestamp, path="src/lib.rs", commit="commit-1"):
    return {
        "pair_id": pair_id,
        "day": "2026-06-02",
        "vendor": "codex",
        "action": "edit",
        "path": path,
        "event_ts_ms": timestamp,
        "audit_candidates": [{"commit_id": commit}],
    }


class AnnotationRebaseTests(unittest.TestCase):
    def test_carries_by_semantic_key_and_exposes_new_universe(self):
        old = {"pairs": [pair("old", 1_000)]}
        current = {
            "pairs": [pair("current", 1_020), pair("new", 3_000, "src/main.rs")]
        }
        mapping, new_pairs, removed = carry_mapping([old], [current])
        self.assertEqual(mapping, {"old": "current"})
        self.assertEqual([row["pair_id"] for row in new_pairs], ["new"])
        self.assertEqual(removed, [])

        annotations = {
            "annotator_type": "test",
            "annotations": [
                {
                    "pair_id": "old",
                    "label": "target",
                    "target_commit_ids": ["commit-1"],
                }
            ],
        }
        rebased = rebase_annotations(annotations, mapping, new_pairs)
        self.assertEqual(rebased["annotations"][0]["pair_id"], "current")
        self.assertEqual(
            rebased["annotations"][0]["carried_from_pair_id"], "old"
        )

    def test_rejects_ambiguous_or_changed_candidate_evidence(self):
        old = {"pairs": [pair("old", 1_000)]}
        ambiguous = {
            "pairs": [pair("left", 900), pair("right", 1_100)]
        }
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            carry_mapping([old], [ambiguous])

        changed = {"pairs": [pair("changed", 1_000, commit="commit-2")]}
        mapping, new_pairs, removed = carry_mapping([old], [changed])
        self.assertEqual(mapping, {})
        self.assertEqual([row["pair_id"] for row in new_pairs], ["changed"])
        self.assertEqual([row["pair_id"] for row in removed], ["old"])


if __name__ == "__main__":
    unittest.main()
