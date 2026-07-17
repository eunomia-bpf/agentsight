#!/usr/bin/env python3
"""Render paper-readable flamegraph panels from existing exact SVG profiles.

This is a presentation-only transform: x positions and rectangle widths are
copied unchanged, while the redundant title/metadata band is removed and rows
are made tall enough for 9-point labels at the paper's final width.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


SVG = "{http://www.w3.org/2000/svg}"
ROW_HEIGHT = 24.0
ROW_GAP = 1.0
FONT_SIZE = 24.0
TEXT_BASELINE = 19.0
CHAR_WIDTH = 14.4


def render(source: Path, output: Path) -> None:
    tree = ET.parse(source)
    root = tree.getroot()
    width = float(root.attrib["width"])

    groups = [child for child in root if child.tag == f"{SVG}g"]
    source_rows = sorted(
        {
            float(rect.attrib["y"])
            for group in groups
            if (rect := group.find(f"{SVG}rect")) is not None
        }
    )
    row_index = {value: index for index, value in enumerate(source_rows)}
    height = len(source_rows) * (ROW_HEIGHT + ROW_GAP) - ROW_GAP

    for child in list(root):
        if child.tag != f"{SVG}g":
            root.remove(child)

    root.attrib.update(
        {
            "width": str(int(width)),
            "height": str(int(height)),
            "viewBox": f"0 0 {int(width)} {int(height)}",
        }
    )
    root.insert(
        0,
        ET.Element(
            f"{SVG}style",
            {},
        ),
    )
    root[0].text = (
        f"text{{font-family:DejaVu Sans Mono,monospace;font-size:{FONT_SIZE:g}px;"
        "pointer-events:none}"
    )
    background = ET.Element(
        f"{SVG}rect",
        {"width": str(int(width)), "height": str(int(height)), "fill": "#fbfbf7"},
    )
    root.insert(1, background)

    for group in groups:
        rect = group.find(f"{SVG}rect")
        if rect is None:
            continue
        old_y = float(rect.attrib["y"])
        new_y = row_index[old_y] * (ROW_HEIGHT + ROW_GAP)
        rect.attrib["y"] = f"{new_y:.3f}"
        rect.attrib["height"] = str(int(ROW_HEIGHT))

        text = group.find(f"{SVG}text")
        if text is None or not text.text:
            continue
        text.attrib["y"] = f"{new_y + TEXT_BASELINE:.3f}"
        available = max(0, int((float(rect.attrib["width"]) - 8.0) / CHAR_WIDTH))
        if available < 2:
            group.remove(text)
        elif len(text.text) > available:
            text.text = text.text[: max(1, available - 1)] + "."

    output.parent.mkdir(parents=True, exist_ok=True)
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree.write(output, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.source, args.output)


if __name__ == "__main__":
    main()
