import unittest

from agentcap_task_aggregation_case import ROOT_TASK, TRACE_SPECS, path_at, semantic_action


class TaskAggregationCaseTest(unittest.TestCase):
    def test_transition_is_inclusive(self):
        spec = TRACE_SPECS["019f2996-ffd0-74d0-a591-4e04501fa093"]
        self.assertEqual(path_at(spec, 1946), (ROOT_TASK, "Establish review scope"))
        self.assertEqual(path_at(spec, 1947), (ROOT_TASK, "Inspect implementation"))

    def test_depth_is_variable(self):
        paths = {
            transition.path
            for spec in TRACE_SPECS.values()
            for transition in spec.transitions
        }
        self.assertEqual({len(path) for path in paths}, {2, 3})

    def test_every_trace_has_shared_root_and_resolution(self):
        for spec in TRACE_SPECS.values():
            self.assertTrue(all(t.path[0] == ROOT_TASK for t in spec.transitions))
            self.assertIn("Confirm resolution", spec.transitions[-1].path)

    def test_read_only_git_inspection_is_not_called_an_update(self):
        self.assertEqual(
            semantic_action({"action": "Update repository"}),
            "Inspect repository state",
        )


if __name__ == "__main__":
    unittest.main()
