# 🛠️ FONTS FORGE by Ethernium

![Ethernium Specimen Sheet](ethernium_sheet_hq.png)

A professional, state-of-the-art toolkit to **design, compile, and visualize custom vector fonts** starting from simple hand-drawn or grid-based raster specimen sheets (PNG).

Built with forensic-grade precision and cyberpunk aesthetics.

---

## ✨ Features

- **Generic Raster-to-Vector Pipeline**: Automatically splits grid-based specimens into perfect character bounding boxes, extracts glyph contours, and converts them to vector formats.
- **Geometric Snapping & Smoothing**: Configurable angle-snapping (45° / 90°) and morphological edge filters to remove jaggies while keeping crisp details.
- **Bézier Curve Fitting**: Automatic quadratic/cubic Bézier classification using deflection-angle analysis for professional-grade curves.
- **Dual-Layer Symmetry Engine**: Mirror contours left-to-right for mathematically perfect symmetry at both vector and pixel levels.
- **Forensic Watermarking**: LSB-based steganographic coordinate embedding for authorship proof.
- **Professional OpenType Tables**: Robust OS/2 vertical metrics, `gasp` screen-rendering hinting, copyright records, and legacy kerning maps.
- **Multi-Format Output**: Generates `.ttf`, `.woff`, and `.woff2` in a single build.

---

## 🌐 Interactive Web Tools

| Tool | Description |
|------|-------------|
| `preview_font.html` | Complete character grid with copy-to-clipboard, waterfall specimen (12px–72px), and CSS embedding code |
| `ascii_generator.html` | Real-time canvas-based ASCII art generator with multiple rendering modes |
| `presentation_generator.html` | Premium presentation card renderer for showcase posters |
| `unicode_converter.html` | Runic & special symbol Unicode map and converter |

---

## 🚀 Create Your Custom Font in 4 Steps

### Step 1: Draw Your Specimen Sheet
Draw or construct your font glyphs in a single PNG image (e.g., `my_sheet.png`). Organize characters left to right in rows.

### Step 2: Configure Your Project
Copy `configs/template.json` to `configs/my_font.json` and define:
- `"sheet"`: Your PNG filename
- `"font"`: Copyright, family name, style name
- `"rows"`: Y coordinates (`y_start`, `y_end`, `baseline`) and ordered character list per row

> 💡 **Auto-calibration**: Run `python tools/calibrate_sheet.py my_sheet.png` to detect Y-bounds automatically.

### Step 3: Compile
```bash
pip install -r requirements.txt
python -m font_forge configs/my_font.json
```

### Step 4: Preview & Deploy
Open `preview_font.html` in your browser to inspect the glyph grid, test sizes, and grab embedding code.

---

## 🔬 Developer Tools

| Script | Purpose |
|--------|---------|
| `tools/calibrate_sheet.py` | Automated Y-bounds scanning and band suggestions |
| `tools/debug_rows.py` | Visual verification overlay of coordinate slices |
| `tools/audit_font.py` | Integrity verification of compiled vertical bounds and glyph ranges |
| `tools/validate_font.py` | OpenType specification auditor (pass/warn/fail reports) |
| `tools/font_to_ascii.py` | Converts text to high-resolution terminal ASCII banners |
| `tools/export_atlas.py` | Generates a visual glyph atlas from the compiled TTF |
| `tools/analyze_font.py` | Deep font metrics analysis |
| `tools/analyze_spacing.py` | Inter-character spacing analyzer |

---

## ⚙️ Pipeline v4.0

| Stage | What It Does |
|-------|--------------|
| Auto Upscale | 1× if sheet is large; 2×/4× if small |
| Otsu + Median | Sharper edges than blur + fixed threshold |
| 45° Snap | Cleaner geometric angles |
| 90% Symmetry | Perfect mirrors for M, O, Ω… without distortion |
| CCOMP | Preserves holes in O, 0, 8, @… |
| Bézier Fit | Quadratic/cubic curve classification |
| Forensic Watermark | LSB steganographic authorship proof |

---

## 📦 Requirements

```bash
pip install -r requirements.txt
```

Requires **Python 3.8+** with `opencv-python`, `numpy`, `fonttools`, and `Pillow`.

---

## 📄 License

This toolkit is open source and available under the [MIT License](LICENSE.txt).

---

<p align="center">
  <b>FONTS FORGE</b> — Forged by <a href="https://github.com/SteveBlackbeard">Ethernium</a>
</p>
