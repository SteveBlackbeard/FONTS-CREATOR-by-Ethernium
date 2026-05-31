"""
Ethernium ASCII Art Generator
─────────────────────────────
Converts Ethernium Sym font glyphs into ASCII art.
Generates both a reusable ASCII font map and an interactive converter.

Usage:
    python tools/font_to_ascii.py                    # Generate ASCII font map
    python tools/font_to_ascii.py "HELLO WORLD"      # Convert text to ASCII art
    python tools/font_to_ascii.py --height 12         # Taller glyphs (default: 8)
    python tools/font_to_ascii.py --charset full      # All printable ASCII
    python tools/font_to_ascii.py --export             # Export .flf (FIGlet) font
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# ── Rendering ────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image, ImageDraw, ImageFont

# ASCII density ramps (dark → light)
RAMP_BLOCK  = "█▓▒░ "
RAMP_DETAIL = "@%#*+=-:. "
RAMP_SIMPLE = "#@%=+*:.- "
RAMP_BRAILLE = "⣿⣷⣯⣟⡿⢿⣻⣽⣾⣶⣤⣀⡀ "


def render_glyph_bitmap(char: str, font_path: str, height: int = 8) -> list[list[float]]:
    """Render a single character to a brightness matrix [0..1]."""
    # Render at high resolution then downsample
    render_size = height * 8
    img = Image.new("L", (render_size * 2, render_size * 2), 0)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, render_size)
    except Exception:
        return []

    # Get character bounding box
    bbox = draw.textbbox((0, 0), char, font=font)
    if bbox[2] - bbox[0] <= 0:
        return []

    # Center the character
    x_off = max(0, -bbox[0])
    y_off = max(0, -bbox[1])
    draw.text((x_off, y_off), char, fill=255, font=font)

    # Crop to ink bounds
    img_bbox = img.getbbox()
    if not img_bbox:
        return []
    cropped = img.crop(img_bbox)

    # Calculate target width maintaining aspect ratio
    # ASCII chars are ~2x taller than wide, so we compensate
    aspect = cropped.width / cropped.height
    target_w = max(1, int(height * aspect * 2))  # *2 for char aspect ratio

    # Downsample
    small = cropped.resize((target_w, height), Image.LANCZOS)

    # Convert to brightness matrix [0..1]
    pixels = list(small.getdata())
    matrix = []
    for row in range(height):
        line = []
        for col in range(target_w):
            val = pixels[row * target_w + col] / 255.0
            line.append(val)
        matrix.append(line)

    return matrix


def matrix_to_ascii(matrix: list[list[float]], ramp: str = RAMP_DETAIL) -> list[str]:
    """Convert brightness matrix to ASCII art lines."""
    if not matrix:
        return []
    lines = []
    ramp_len = len(ramp)
    for row in matrix:
        line = ""
        for val in row:
            idx = int((1.0 - val) * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            line += ramp[idx]
        lines.append(line)
    return lines


def generate_ascii_font_map(
    font_path: str,
    height: int = 8,
    ramp: str = RAMP_DETAIL,
    charset: str = "alpha",
) -> dict[str, list[str]]:
    """Generate ASCII art for each character in the font."""
    if charset == "full":
        chars = [chr(i) for i in range(32, 127)]
    elif charset == "alpha":
        chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    elif charset == "upper":
        chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    else:
        chars = list(charset)

    font_map: dict[str, list[str]] = {}

    for char in chars:
        if char == " ":
            # Space: empty block
            space_w = max(3, height // 2)
            font_map[char] = [" " * space_w] * height
            continue

        matrix = render_glyph_bitmap(char, font_path, height)
        ascii_lines = matrix_to_ascii(matrix, ramp)
        if ascii_lines:
            font_map[char] = ascii_lines

    return font_map


def render_text_ascii(
    text: str,
    font_map: dict[str, list[str]],
    spacing: int = 1,
) -> str:
    """Combine individual ASCII glyphs into a multi-line text banner."""
    if not text:
        return ""

    height = max(len(v) for v in font_map.values()) if font_map else 1
    spacer = " " * spacing

    output_lines = [""] * height
    for char in text.upper():
        if char in font_map:
            glyph = font_map[char]
            max_w = max(len(line) for line in glyph)
            for i in range(height):
                line = glyph[i] if i < len(glyph) else ""
                output_lines[i] += line.ljust(max_w) + spacer
        elif char == " ":
            space_w = 3
            for i in range(height):
                output_lines[i] += " " * space_w + spacer
        else:
            # Unknown char: placeholder
            for i in range(height):
                output_lines[i] += "?" + spacer

    # Trim trailing whitespace
    return "\n".join(line.rstrip() for line in output_lines)


def export_figlet_font(font_map: dict[str, list[str]], output_path: Path) -> None:
    """Export as FIGlet .flf font file."""
    height = max(len(v) for v in font_map.values()) if font_map else 1
    max_w = max(max(len(line) for line in v) for v in font_map.values()) if font_map else 1

    lines = []
    # FIGlet header
    lines.append(f"flf2a$ {height} {height} {max_w + 2} -1 0 0 0 0")
    lines.append("Ethernium Sym ASCII Font")
    lines.append(f"Generated from Ethernium_Sym.ttf")

    # Characters 32-126
    for cp in range(32, 127):
        char = chr(cp)
        if char in font_map:
            glyph = font_map[char]
        else:
            # Empty placeholder
            glyph = [" "] * height

        for i, line in enumerate(glyph):
            end_marker = "@" if i < height - 1 else "@@"
            lines.append(line + end_marker)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"FIGlet font exported: {output_path}")


# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ethernium ASCII Art Generator")
    parser.add_argument("text", nargs="?", default=None, help="Text to convert")
    parser.add_argument("--height", type=int, default=8, help="Glyph height in rows (default: 8)")
    parser.add_argument("--ramp", choices=["block", "detail", "simple", "braille"], default="detail")
    parser.add_argument("--charset", default="alpha", help="Character set: full, alpha, upper, or custom string")
    parser.add_argument("--export", action="store_true", help="Export as FIGlet .flf font")
    parser.add_argument("--spacing", type=int, default=1, help="Character spacing (default: 1)")
    parser.add_argument("--save-map", action="store_true", help="Save ASCII map as JSON")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    font_path = str(root / "Ethernium_Sym.ttf")

    ramps = {"block": RAMP_BLOCK, "detail": RAMP_DETAIL, "simple": RAMP_SIMPLE, "braille": RAMP_BRAILLE}
    ramp = ramps[args.ramp]

    print(f"Loading Ethernium Sym ({args.height} rows, ramp={args.ramp})...")
    font_map = generate_ascii_font_map(font_path, args.height, ramp, args.charset)
    print(f"Generated {len(font_map)} ASCII glyphs\n")

    if args.export:
        # Need full charset for FIGlet
        if args.charset != "full":
            font_map = generate_ascii_font_map(font_path, args.height, ramp, "full")
        flf_path = root / "Ethernium_Sym.flf"
        export_figlet_font(font_map, flf_path)

    if args.save_map:
        map_path = root / "tools" / "ascii_font_map.json"
        map_path.write_text(json.dumps(font_map, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved ASCII map: {map_path}\n")

    if args.text:
        banner = render_text_ascii(args.text, font_map, args.spacing)
        print(banner)
    else:
        # Demo: show alphabet + sample text
        print("═══ ETHERNIUM ASCII ART ALPHABET ═══\n")
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if char in font_map:
                glyph = font_map[char]
                max_w = max(len(l) for l in glyph)
                header = f"─── {char} {'─' * (max_w - 2)}"
                print(header)
                for line in glyph:
                    print(f"  {line}")
                print()

        print("\n═══ SAMPLE BANNERS ═══\n")
        for word in ["ETHERNIUM", "HELLO", "CRYPTO"]:
            print(f">>> {word}")
            print(render_text_ascii(word, font_map, args.spacing))
            print()
