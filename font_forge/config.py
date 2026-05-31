"""Load and normalize font project JSON configs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("sheet", "font", "rows", "reference_height")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Config missing keys: {missing}")
    return data


def scale_rows(rows: list[dict], img_height: int, ref_height: int) -> list[dict]:
    """Scale row Y coordinates when sheet resolution differs from reference."""
    if ref_height <= 0 or img_height == ref_height:
        return rows
    factor = img_height / ref_height
    scaled = []
    for row in rows:
        scaled.append(
            {
                **row,
                "y_start": int(round(row["y_start"] * factor)),
                "y_end": int(round(row["y_end"] * factor)),
                "baseline": int(round(row["baseline"] * factor)),
            }
        )
    return scaled
