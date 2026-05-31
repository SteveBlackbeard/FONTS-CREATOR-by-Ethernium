"""Draw row crop boxes on the sheet for visual QA."""
import sys
from pathlib import Path

import cv2
import json

ROOT = Path(__file__).resolve().parent.parent


def main():
    config_path = ROOT / "configs" / "ethernium.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sheet = ROOT / config["sheet"]
    if not sheet.is_file():
        sheet = ROOT / "ethernium_sheet.png"

    img = cv2.imread(str(sheet))
    if img is None:
        print("Cannot load sheet")
        sys.exit(1)

    h = img.shape[0]
    ref = config["reference_height"]
    factor = h / ref

    for row in config["rows"]:
        y1 = int(row["y_start"] * factor)
        y2 = int(row["y_end"] * factor)
        bl = int(row["baseline"] * factor)
        cv2.rectangle(img, (0, y1), (img.shape[1] - 1, y2), (0, 255, 0), 2)
        cv2.line(img, (0, bl), (img.shape[1] - 1, bl), (255, 128, 0), 1)
        cv2.putText(
            img, row["name"], (10, max(y1 + 20, 20)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1,
        )

    out = ROOT / "tools" / "sheet_rows_debug.png"
    cv2.imwrite(str(out), img)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
