"""PNG: hoja HQ con cajas verdes = lo que extrae el build (debe coincidir 1:1 con letras)."""
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from font_forge.config import scale_rows
from font_forge.core import prepare_binary, merge_boxes

OUT = ROOT / "tools" / "sheet_extraction_map.png"


def main():
    cfg = json.loads((ROOT / "configs" / "ethernium.json").read_text(encoding="utf-8"))
    sheet = ROOT / cfg["sheet"]
    img = cv2.imread(str(sheet))
    if img is None:
        print("No sheet")
        return

    h, w = img.shape[:2]
    ps = max(w / cfg["reference_width"], h / cfg["reference_height"])
    thresh = prepare_binary(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 30, True)
    vis = img.copy()

    for row in cfg["rows"]:
        row_sheet = row.get("sheet", cfg["sheet"])
        sp = ROOT / row_sheet
        simg = cv2.imread(str(sp))
        sh = simg.shape[0]
        ps_r = max(simg.shape[1] / cfg["reference_width"], sh / cfg["reference_height"])
        rs = scale_rows([row], sh, cfg["reference_height"])[0]
        y1, y2 = rs["y_start"], rs["y_end"]
        crop = thresh[y1:y2] if row_sheet == cfg["sheet"] else prepare_binary(
            cv2.cvtColor(simg, cv2.COLOR_BGR2GRAY), 30, True
        )[y1:y2]

        contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        mw = int(200 * ps_r)
        for c in contours:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw > mw or bh < 3 * ps_r or bw < 2 * ps_r:
                continue
            boxes.append((x, y, bw, bh))
        merged = merge_boxes(boxes, int(4 * ps_r), int(55 * ps_r))

        for i, (gx, gy, gw, gh) in enumerate(merged):
            if i >= len(row["chars"]):
                break
            cv2.rectangle(vis, (gx, y1 + gy), (gx + gw, y1 + gy + gh), (0, 255, 80), 2)
            cv2.putText(
                vis, row["chars"][i], (gx, max(y1 + gy - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 80), 1, cv2.LINE_AA,
            )

    cv2.imwrite(str(OUT), vis)
    print(f"Saved {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
