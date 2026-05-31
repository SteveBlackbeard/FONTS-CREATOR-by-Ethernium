from fontTools.ttLib import TTFont
import sys

font = TTFont('Ethernium_Sym.ttf')
glyf = font['glyf']
cmap = font.getBestCmap()

print("Glyph topology:")
for code in sorted(cmap.keys()):
    if 65 <= code <= 90: # Uppercase A-Z
        char = chr(code)
        gname = cmap[code]
        g = glyf[gname]
        contours = g.numberOfContours
        print(f"  {char} ({gname}): contours={contours}, bounds=({g.xMin},{g.yMin})-({g.xMax},{g.yMax})")
