#!/usr/bin/env python3
"""Render an existing paper plot with anonymous case labels.

The scientific plotting scripts and their numeric inputs remain unchanged.
This wrapper imports one script, replaces display-only project labels, and
then invokes its normal CLI.  The Skill-footprint renderer has no display
mapping, so its loaded project names are replaced before analysis; grouping
and all numeric rows are otherwise unchanged.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
from pathlib import Path


CASE_LABELS = {
    "agentsight": "Case A",
    "ActPlane": "Case B",
    "bpf-developer-tutorial": "Case C",
    "eunomia.dev": "Case D",
    "eunomia-dev": "Case D",
    "agentskill-observability-paper": "Case E",
    "academic-writing-skills": "Case F",
}

TINY_LABELS = {
    project: label.removeprefix("Case ") for project, label in CASE_LABELS.items()
}


def load_script(path: Path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(
        f"_anonymous_{path.stem}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    script = args.script.resolve()
    module = load_script(script)
    if hasattr(module, "SHORT"):
        module.SHORT.update(CASE_LABELS)
    if hasattr(module, "TINY"):
        module.TINY.update(TINY_LABELS)
    if hasattr(module, "LANE_SHORT"):
        module.LANE_SHORT.update(TINY_LABELS)

    if script.name == "plot_rq5_skill_footprints.py":
        original_plot_skill = module.plot_skill
        original_plot_instruction = module.plot_instruction

        def anonymous_rows(rows):
            result = copy.deepcopy(rows)
            for row in result:
                row["project"] = CASE_LABELS[row["project"]]
            return result

        def anonymous_plot_skill(coverage, footprints, distances, output):
            original_plot_skill(
                anonymous_rows(coverage),
                anonymous_rows(footprints),
                anonymous_rows(distances),
                output,
            )

        def anonymous_plot_instruction(instructions, output):
            original_plot_instruction(anonymous_rows(instructions), output)

        module.plot_skill = anonymous_plot_skill
        module.plot_instruction = anonymous_plot_instruction

    sys.argv = [str(script), *args.script_args]
    module.main()


if __name__ == "__main__":
    main()
