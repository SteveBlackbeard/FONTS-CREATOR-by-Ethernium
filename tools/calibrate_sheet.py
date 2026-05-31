"""
Detect glyph row bands on a specimen sheet and suggest config JSON coordinates.
Usage: python tools/calibrate_sheet.py [sheet.png]
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def find_bands(projection: np.ndarray, min_height: int = 20, gap: int = 15):
    active = projection > projection.max() * 0.08
    bands = []
    start = None
    for i, on in enumerate(active):
        if on and start is None:
            start = i
        elif not on and start is not None:
            if i - start >= min_height:
                bands.append((start, i))
            start = None
    if start is not None and len(active) - start >= min_height:
        bands.append((start, len(active)))
    return bands


def merge_close_bands(bands, max_gap: int = 40):
    if not bands:
        return []
    merged = [bands[0]]
    for y1, y2 in bands[1:]:
        py1, py2 = merged[-1]
        if y1 - py2 <= max_gap:
            merged[-1] = (py1, y2)
        else:
            merged.append((y1, y2))
    return merged


def main():
    sheet = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "ethernium_sheet.png"
    if not sheet.is_file():
        sheet = ROOT / "ethernium_sheet_hq.png"
    if not sheet.is_file():
        print(f"No sheet at {sheet}")
        sys.exit(1)

    img = cv2.imread(str(sheet), cv2.IMREAD_GRAYSCALE)
    h, w = img.shape[:2]
    ref_h = 682
    scale_back = ref_h / h

    _, thresh = cv2.threshold(cv2.medianBlur(img, 3), 30, 255, cv2.THRESH_BINARY)
    proj = np.sum(thresh > 0, axis=1)
    bands = merge_close_bands(find_bands(proj, min_height=max(12, h // 80)))
    # Skip header/logo band — glyph rows usually start below ~25% height
    min_y = int(h * 0.22)
    bands = [(a, b) for a, b in bands if a >= min_y and (b - a) <= h * 0.12]

    print(f"Sheet: {sheet.name} ({w}x{h})")
    print(f"reference_height for config: {ref_h}")
    print(f"Detected {len(bands)} bands (map to your rows in order):\n")

    rows = []
    for i, (y1, y2) in enumerate(bands):
        baseline = int(y2 - (y2 - y1) * 0.12)
        y1s, y2s, bls = int(y1 * scale_back), int(y2 * scale_back), int(baseline * scale_back)
        print(f"  Band {i + 1}: y_start={y1s}, y_end={y2s}, baseline={bls}  (raw px {y1}-{y2})")
        rows.append({"y_start": y1s, "y_end": y2s, "baseline": bls})

    out = ROOT / "tools" / "detected_rows.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nSaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
