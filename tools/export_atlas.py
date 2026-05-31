"""Render glyphs with real font metrics (no fixed grid overlap)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TTF = ROOT / "Ethernium_Sym.ttf"
OUT = ROOT / "tools" / "glyph_atlas.png"

ROWS = [
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    ".,:;!?'\"-_/\\",
    "()[]{}<>@#%&*+=~",
    "\u03a9\u2020\u2021\u221e\u0394\u25ca\u2609\u263d\u2318\u273b",
]


def main():
    if not TTF.is_file():
        print(f"Missing {TTF.name} — run build_ethernium.py first")
        return

    size = 64
    font = ImageFont.truetype(str(TTF), size)
    pad = 16
    line_h = 90
    img_w = 1100
    img_h = len(ROWS) * line_h + 50
    img = Image.new("RGB", (img_w, img_h), (8, 8, 10))
    draw = ImageDraw.Draw(img)

    y = 30
    for line in ROWS:
        x = pad
        for ch in line:
            w = int(font.getlength(ch)) + 12
            cell = max(36, w)
            draw.rectangle([x, y, x + cell, y + line_h - 20], outline=(45, 45, 55))
            draw.text((x + 4, y + 4), ch, font=font, fill=(255, 255, 255))
            draw.text((x + 2, y + line_h - 32), f"U+{ord(ch):04X}", fill=(90, 90, 100))
            x += cell + 4
            if x > img_w - 50:
                break
        y += line_h

    img.save(OUT)
    print(f"Saved {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
