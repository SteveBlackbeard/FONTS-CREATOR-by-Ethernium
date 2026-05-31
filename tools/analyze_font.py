"""Deep analysis of Ethernium Sym font from Desktop."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from fontTools.ttLib import TTFont
import numpy as np

font = TTFont('Ethernium_Sym.ttf')
glyf = font['glyf']
cmap = font.getBestCmap()

def analyze_symmetry(glyph_name, char_label):
    g = glyf[glyph_name]
    coords = list(g.coordinates)
    flags = list(g.flags)
    cx = (g.xMin + g.xMax) / 2.0
    cy = (g.yMin + g.yMax) / 2.0
    
    print(f"\n{'='*60}")
    print(f" {char_label} -> {glyph_name}")
    print(f" BBox: ({g.xMin},{g.yMin})-({g.xMax},{g.yMax})  Center=({cx:.1f},{cy:.1f})")
    print(f" Points: {len(coords)}")
    print(f"{'='*60}")
    
    # Print all coordinates
    for i, (pt, fl) in enumerate(zip(coords, flags)):
        x, y = pt
        dist_from_cx = x - cx
        on_curve = "ON" if fl & 1 else "OFF"
        print(f"  [{i:2d}] ({x:5d}, {y:5d})  dist_cx={dist_from_cx:+7.1f}  {on_curve}")
    
    # Symmetry check: pair left and right points
    left = [(i, x, y) for i, (x, y) in enumerate(coords) if x < cx - 3]
    right = [(i, x, y) for i, (x, y) in enumerate(coords) if x > cx + 3]
    center = [(i, x, y) for i, (x, y) in enumerate(coords) if abs(x - cx) <= 3]
    
    print(f"\n  Left points: {len(left)}, Right points: {len(right)}, Center: {len(center)}")
    
    if len(left) == len(right):
        print("  Count: SYMMETRIC ✓")
    else:
        print(f"  Count: ASYMMETRIC ✗ ({len(left)} vs {len(right)})")
    
    # Check Y-coordinate matching
    left_ys = sorted([y for _,_,y in left])
    right_ys = sorted([y for _,_,y in right])
    
    matched = 0
    for ly in left_ys:
        for ry in right_ys:
            if abs(ly - ry) <= 3:
                matched += 1
                break
    
    total = max(len(left_ys), 1)
    print(f"  Y-match rate: {matched}/{len(left_ys)} ({100*matched/total:.0f}%)")
    
    # Check X-distance pairing
    left_dists = sorted([cx - x for _,x,_ in left])
    right_dists = sorted([x - cx for _,x,_ in right])
    
    x_matched = 0
    for ld in left_dists:
        for rd in right_dists:
            if abs(ld - rd) <= 5:
                x_matched += 1
                break
    
    print(f"  X-mirror rate: {x_matched}/{len(left_dists)} ({100*x_matched/max(len(left_dists),1):.0f}%)")

# Analyze key symmetrical characters
test_chars = [
    (0x4D, 'M'),
    (0x56, 'V'),
    (0x4F, 'O'),
    (0x49, 'I'),
    (0x03A9, 'Omega Ω'),
    (0x45, 'E (Runic)'),
    (0x65, 'e (lowercase)'),
]

for code, label in test_chars:
    if code in cmap:
        analyze_symmetry(cmap[code], label)

# General quality metrics
print(f"\n{'='*60}")
print(f" GENERAL METRICS")
print(f"{'='*60}")
print(f" Total glyphs in glyf: {len(glyf.keys())}")
print(f" Total cmap entries: {len(cmap)}")

# Check for zero-area or degenerate glyphs
degen = []
for gname in glyf.keys():
    if gname == '.notdef':
        continue
    g = glyf[gname]
    if g.numberOfContours == 0:
        degen.append(gname)
    elif g.xMax - g.xMin < 5 or g.yMax - g.yMin < 5:
        degen.append(gname)

if degen:
    print(f" Degenerate/tiny glyphs: {degen}")
else:
    print(f" No degenerate glyphs ✓")

# Check advance widths
hmtx = font['hmtx']
widths = [hmtx[gname][0] for gname in glyf.keys() if gname != '.notdef']
print(f" Advance width range: {min(widths)}-{max(widths)}")
print(f" Average width: {sum(widths)/len(widths):.0f}")
