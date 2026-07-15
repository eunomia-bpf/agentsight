import unittest

from adjudicate_rq1_disagreements import adjudicate_null_disagreement


class AdjudicationTests(unittest.TestCase):
    def test_empty_exhaustive_candidate_set_is_path_level_null(self):
        self.assertEqual(
            adjudicate_null_disagreement({"audit_candidates": []})["label"],
            "null",
        )

    def test_candidate_without_content_evidence_remains_unadjudicable(self):
        self.assertEqual(
            adjudicate_null_disagreement(
                {"audit_candidates": [{"commit_id": "candidate"}]}
            )["label"],
            "unadjudicable",
        )


if __name__ == "__main__":
    unittest.main()
