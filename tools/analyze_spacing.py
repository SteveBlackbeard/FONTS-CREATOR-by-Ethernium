"""Analyze advance widths vs ink widths to find optimal RSB (right side bearing)."""
from fontTools.ttLib import TTFont
from pathlib import Path

root = Path(__file__).resolve().parent.parent
font = TTFont(str(root / "Ethernium_Sym.ttf"))
glyf = font["glyf"]
hmtx = font["hmtx"]
cmap = font.getBestCmap()

print("=== ETHERNIUM spacing analysis ===\n")
print(f"{'Char':>5} {'Glyph':>10} {'InkW':>5} {'Adv':>5} {'LSB':>4} {'RSB':>5} {'RSB%':>5}")
print("-" * 50)

word = "ETHERNIUM"
total_advance = 0
for ch in word:
    gname = cmap.get(ord(ch))
    if gname and gname in glyf:
        g = glyf[gname]
        adv, lsb = hmtx[gname]
        if hasattr(g, 'xMin'):
            ink_w = g.xMax - g.xMin
            rsb = adv - g.xMax
            rsb_pct = rsb / ink_w * 100 if ink_w > 0 else 0
            print(f"{ch:>5} {gname:>10} {ink_w:>5} {adv:>5} {lsb:>4} {rsb:>5} {rsb_pct:>5.0f}%")
            total_advance += adv

print(f"\nTotal advance for '{word}': {total_advance}")
print(f"Average advance: {total_advance/len(word):.0f}")

# What would tight spacing look like?
# RSB should be ~30-50 for tight, ~60-80 for normal, ~100+ for loose
print("\n\n=== Projected spacing with different RSB values ===\n")
for target_rsb in [20, 30, 40, 50, 80]:
    total = 0
    for ch in word:
        gname = cmap.get(ord(ch))
        if gname and gname in glyf:
            g = glyf[gname]
            if hasattr(g, 'xMin'):
                new_adv = g.xMax + target_rsb
                total += new_adv
    print(f"  RSB={target_rsb:3d} → total advance: {total:5d} (ratio: {total/total_advance:.2f}x)")

# Show ALL uppercase advances
print("\n\n=== All uppercase advances ===\n")
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    gname = cmap.get(ord(ch))
    if gname and gname in glyf:
        g = glyf[gname]
        adv, lsb = hmtx[gname]
        if hasattr(g, 'xMin'):
            ink_w = g.xMax - g.xMin
            rsb = adv - g.xMax
            print(f"  {ch}: ink_w={ink_w:4d}, adv={adv:4d}, rsb={rsb:4d}")
