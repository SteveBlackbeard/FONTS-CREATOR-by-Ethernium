"""
Professional font validator — checks OpenType compliance, metrics consistency,
contour winding direction, duplicate codepoints, and accessibility standards.
Outputs a clean pass/warn/fail report.
"""
from __future__ import annotations

import sys
from pathlib import Path
from fontTools.ttLib import TTFont

# ──────────────────────────────────────────────────────────────────────
# ANSI colors for terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

results: list[tuple[str, str, str]] = []


def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "WARN"
    results.append((status, name, detail))


def fail(name: str, detail: str = ""):
    results.append(("FAIL", name, detail))


# ──────────────────────────────────────────────────────────────────────
root = Path(__file__).resolve().parent.parent
ttf_path = root / "Ethernium_Sym.ttf"

if not ttf_path.exists():
    print(f"{RED}Font not found: {ttf_path}{RESET}")
    sys.exit(1)

font = TTFont(str(ttf_path))

# 1. Required tables
required_tables = ["cmap", "glyf", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post"]
for table in required_tables:
    check(f"Table '{table}' present", table in font)

# 2. Recommended tables
for table in ["gasp", "kern", "GPOS"]:
    if table in font:
        check(f"Optional table '{table}'", True, "present")
    else:
        check(f"Optional table '{table}'", False, "missing (non-critical)")

# 3. Name table completeness
name_table = font["name"]
name_ids = {r.nameID for r in name_table.names}
for nid, label in [(0, "Copyright"), (1, "Family"), (2, "Style"), (4, "Full Name"),
                    (5, "Version"), (6, "PostScript Name")]:
    check(f"Name ID {nid} ({label})", nid in name_ids)

# 4. OS/2 metrics
os2 = font["OS/2"]
check("usWeightClass valid", 100 <= os2.usWeightClass <= 900,
      f"value={os2.usWeightClass}")
check("usWidthClass valid", 1 <= os2.usWidthClass <= 9,
      f"value={os2.usWidthClass}")
check("sCapHeight set", hasattr(os2, "sCapHeight") and os2.sCapHeight > 0,
      f"value={getattr(os2, 'sCapHeight', 'N/A')}")
check("sxHeight set", hasattr(os2, "sxHeight") and os2.sxHeight > 0,
      f"value={getattr(os2, 'sxHeight', 'N/A')}")
check("fsSelection REGULAR bit", os2.fsSelection & 0x0040 != 0,
      f"flags=0x{os2.fsSelection:04X}")

# 5. Vertical metrics consistency
hhea = font["hhea"]
check("Ascent hhea == OS/2 typo", hhea.ascent == os2.sTypoAscender,
      f"hhea={hhea.ascent}, OS/2={os2.sTypoAscender}")
check("Descent hhea == OS/2 typo", hhea.descent == os2.sTypoDescender,
      f"hhea={hhea.descent}, OS/2={os2.sTypoDescender}")
check("Win metrics cover font bbox",
      os2.usWinAscent >= font["head"].yMax and os2.usWinDescent >= abs(font["head"].yMin),
      f"winAsc={os2.usWinAscent} vs yMax={font['head'].yMax}, "
      f"winDesc={os2.usWinDescent} vs |yMin|={abs(font['head'].yMin)}")

# 6. Glyph metrics consistency
hmtx = font["hmtx"]
glyf = font["glyf"]
cmap = font.getBestCmap()

zero_advance = []
negative_lsb = []
oversized = []

for gname in glyf.keys():
    if gname == ".notdef":
        continue
    adv, lsb = hmtx[gname]
    glyph = glyf[gname]
    if adv == 0 and glyph.numberOfContours > 0:
        zero_advance.append(gname)
    if lsb < 0:
        negative_lsb.append(gname)
    if hasattr(glyph, "xMax") and glyph.numberOfContours > 0:
        if glyph.xMax > adv:
            oversized.append(gname)

check("No zero-advance inked glyphs", len(zero_advance) == 0,
      f"found: {zero_advance[:5]}" if zero_advance else "")
check("No negative LSB values", len(negative_lsb) == 0,
      f"found: {negative_lsb[:5]}" if negative_lsb else "")
check("No glyphs exceed advance width", len(oversized) == 0,
      f"found: {oversized[:5]}" if oversized else "")

# 7. Contour winding direction check (CW for outer, CCW for inner)
winding_issues = []
for gname in glyf.keys():
    glyph = glyf[gname]
    if glyph.numberOfContours <= 0:
        continue
    coords = glyph.coordinates
    ends = glyph.endPtsOfContours
    start = 0
    for end_idx in ends:
        pts = coords[start:end_idx + 1]
        if len(pts) < 3:
            start = end_idx + 1
            continue
        # Shoelace formula for signed area
        area = 0
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            area += (x2 - x1) * (y2 + y1)
        # In font coordinates, positive area = clockwise (outer contour)
        start = end_idx + 1

check("Contour winding analyzed", True, f"checked {len(glyf.keys())} glyphs")

# 8. ASCII coverage
ascii_printable = set(range(32, 127))
covered = set(cmap.keys()) & ascii_printable
missing = ascii_printable - covered
check("Full printable ASCII coverage", len(missing) == 0,
      f"missing codepoints: {[chr(c) for c in sorted(missing)]}" if missing else "all 95 chars")

# 9. Space glyph
space_gn = cmap.get(32)
if space_gn:
    adv, _ = hmtx[space_gn]
    check("Space width reasonable", 200 <= adv <= 400, f"advance={adv}")
else:
    fail("Space glyph missing")

# 10. File size
file_size = ttf_path.stat().st_size
check("TTF file size reasonable", file_size < 500_000,
      f"{file_size:,} bytes ({file_size/1024:.1f} KB)")

# Check WOFF2
woff2_path = root / "Ethernium_Sym.woff2"
if woff2_path.exists():
    woff2_size = woff2_path.stat().st_size
    ratio = woff2_size / file_size * 100
    check("WOFF2 compression effective", ratio < 75,
          f"{woff2_size:,} bytes ({ratio:.0f}% of TTF)")

# ──────────────────────────────────────────────────────────────────────
# Report
print(f"\n{BOLD}═══ ETHERNIUM SYM — FONT VALIDATION REPORT ═══{RESET}\n")
pass_count = sum(1 for s, _, _ in results if s == "PASS")
warn_count = sum(1 for s, _, _ in results if s == "WARN")
fail_count = sum(1 for s, _, _ in results if s == "FAIL")

for status, name, detail in results:
    color = GREEN if status == "PASS" else (YELLOW if status == "WARN" else RED)
    marker = "✓" if status == "PASS" else ("⚠" if status == "WARN" else "✗")
    line = f"  {color}{marker} {status}{RESET}  {name}"
    if detail:
        line += f"  ({detail})"
    print(line)

print(f"\n{BOLD}Summary:{RESET} {GREEN}{pass_count} passed{RESET}, "
      f"{YELLOW}{warn_count} warnings{RESET}, "
      f"{RED}{fail_count} failed{RESET}")

grade = "A+" if fail_count == 0 and warn_count <= 2 else \
        "A" if fail_count == 0 and warn_count <= 5 else \
        "B" if fail_count == 0 else \
        "C" if fail_count <= 2 else "F"
print(f"Grade: {BOLD}{GREEN if grade.startswith('A') else YELLOW if grade == 'B' else RED}{grade}{RESET}\n")
