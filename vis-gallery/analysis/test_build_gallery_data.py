import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_gallery_data import validate_public_output


def valid_output():
    return {
        "meta": {"right_censored_days": ["2026-07-14"]},
        "sessions": [{"id": "session-1", "days": ["2026-07-14"]}],
        "source_days": [{"day": "2026-07-14", "sessions": 1}],
        "events": [
            {
                "id": "event-1",
                "day": "2026-07-14",
                "path": "src/lib.rs",
                "association_state": "not_eligible",
                "candidate_count": 0,
                "evidence_bin": None,
                "exact_hunk": False,
            }
        ],
    }


class PublicGalleryValidationTests(unittest.TestCase):
    def test_accepts_process_only_censored_event(self):
        validate_public_output(valid_output())

    def test_rejects_home_relative_native_path(self):
        output = valid_output()
        output["events"][0]["path"] = "~/.claude/projects/session.jsonl"
        with self.assertRaisesRegex(ValueError, "non-repository paths"):
            validate_public_output(output)

    def test_rejects_glob_and_command_fragments_as_paths(self):
        for path in ["src/*.rs", "cargo run --manifest-path Cargo.toml"]:
            output = valid_output()
            output["events"][0]["path"] = path
            with self.assertRaisesRegex(ValueError, "non-repository paths"):
                validate_public_output(output)

    def test_rejects_association_on_censored_day(self):
        output = valid_output()
        output["events"][0]["association_state"] = "unique_candidate"
        output["events"][0]["candidate_count"] = 1
        with self.assertRaisesRegex(ValueError, "association evidence"):
            validate_public_output(output)

    def test_rejects_non_deduplicated_day_count(self):
        output = valid_output()
        output["source_days"][0]["sessions"] = 2
        with self.assertRaisesRegex(ValueError, "not deduplicated"):
            validate_public_output(output)


if __name__ == "__main__":
    unittest.main()
