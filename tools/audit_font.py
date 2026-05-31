"""Full audit of the Ethernium font."""
from fontTools.ttLib import TTFont
from pathlib import Path

root = Path(__file__).resolve().parent.parent
f = TTFont(str(root / "Ethernium_Sym.ttf"))
cmap = f.getBestCmap()
g = f["glyf"]
h = f["hmtx"]
os2 = f["OS/2"]

print(f"Total glyphs: {len(g.keys())}")
print(f"Total cmap entries: {len(cmap)}")
print()

# Missing ASCII
expected = set(range(32, 127))
mapped = set(cmap.keys())
missing = sorted(expected - mapped)
if missing:
    print(f"Missing ASCII ({len(missing)}): {[chr(c) for c in missing]}")
else:
    print("All printable ASCII covered!")
print()

# Space glyph
if 32 in cmap:
    sp = cmap[32]
    print(f"Space glyph: {sp}, advance={h[sp][0]}")
else:
    print("!! NO SPACE GLYPH !!")
print()

# Vertical metrics
ys_min, ys_max = [], []
for gn in g.keys():
    gl = g[gn]
    if hasattr(gl, "yMin") and gl.numberOfContours > 0:
        ys_min.append(gl.yMin)
        ys_max.append(gl.yMax)

if ys_min:
    print(f"yMin range: {min(ys_min)} to {max(ys_min)}")
    print(f"yMax range: {min(ys_max)} to {max(ys_max)}")

print(f"OS/2 sTypoAscender: {os2.sTypoAscender}")
print(f"OS/2 sTypoDescender: {os2.sTypoDescender}")
print(f"OS/2 usWinAscent: {os2.usWinAscent}")
print(f"OS/2 usWinDescent: {os2.usWinDescent}")
print()

# Check consistency: any glyphs outside metrics bounds?
clipped = []
for cp, gn in sorted(cmap.items()):
    gl = g.get(gn)
    if gl and hasattr(gl, "yMin") and gl.numberOfContours > 0:
        if gl.yMax > os2.usWinAscent:
            clipped.append((chr(cp), gn, "yMax", gl.yMax, os2.usWinAscent))
        if gl.yMin < -os2.usWinDescent:
            clipped.append((chr(cp), gn, "yMin", gl.yMin, -os2.usWinDescent))

if clipped:
    print(f"!! {len(clipped)} glyphs clipped by metrics bounds:")
    for ch, gn, metric, val, bound in clipped:
        print(f"  {ch} ({gn}): {metric}={val} vs bound={bound}")
else:
    print("No glyphs clipped by vertical metrics bounds.")
