#!/usr/bin/env python3
"""Run the reviewed RQ3 allocation/migration analysis on the repaired export."""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "agentvis" / "research"))

import plot_rq2  # noqa: E402
import plot_rq5  # noqa: E402


plot_rq2.EXPECTED = {
    "agentsight.json.gz": "29bffeef74683bfb4771c8bc6b4bec659f34bc43183693cd5840de16d435e79b",
    "ActPlane.json.gz": "eb1a718f5560fab2c723a2a1da92b349498b9ff4b5cbeef4ba67c8c9b00290c8",
    "bpf-developer-tutorial.json.gz": "9e9ded72578a322af86adc582f8e8cd5754f630ad8efc44fd0d5cf3345a3cd92",
    "eunomia-dev.json.gz": "4cde11326722cbdfdbe052e87132d60cd91d420f55046bab4050ebaa5ff892fb",
    "agentskill-observability-paper.json.gz": "4b303eec0880d2d3f28eda803d3db19d88695b8ec7c25930a4296c59218d55f6",
    "academic-writing-skills.json.gz": "4d5a255679888e1b4e70e1ee6f9626ff700484b2ed1f7bf1d566a396133a50b6",
    "rq1-mutations.csv": "5832ce7b3212220f25a669481d5cc370050aec231d2476267d9acff609c70a38",
}
plot_rq5.RQ4_ACCESS_SHA256 = (
    "372584e828f1f46b8ae68b5381fcf90042a28397383f8adfa74ec3f638268ab0"
)


if __name__ == "__main__":
    plot_rq5.main()
