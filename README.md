<p align="center">
  <img src="ethernium_sheet_hq.png" alt="Ethernium Font Forge Specimen Sheet">
</p>

# 🛠️ FONTS FORGE by Ethernium

[![Font Forge Validator](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/actions/workflows/validate_font.yml/badge.svg)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/actions/workflows/validate_font.yml)
[![Version](https://img.shields.io/badge/version-4.0-blueviolet)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/LICENSE.txt)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Pages](https://img.shields.io/badge/demo-GitHub%20Pages-orange)](https://steveblackbeard.github.io/FONTS-FORGE-by-Ethernium/)

#### Languages

[![ES](https://img.shields.io/badge/ES-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_es.md) [![EN](https://img.shields.io/badge/EN-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/README.md) [![JA](https://img.shields.io/badge/JA-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_ja.md) [![ZH](https://img.shields.io/badge/ZH-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_zh.md) [![RU](https://img.shields.io/badge/RU-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_ru.md) [![FR](https://img.shields.io/badge/FR-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_fr.md) [![IT](https://img.shields.io/badge/IT-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_it.md) [![DE](https://img.shields.io/badge/DE-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_de.md) [![PT](https://img.shields.io/badge/PT-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_pt.md) [![KO](https://img.shields.io/badge/KO-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_ko.md) [![AR](https://img.shields.io/badge/AR-white)](https://github.com/SteveBlackbeard/FONTS-FORGE-by-Ethernium/blob/main/OTHER_LANGUAGES/README_ar.md)

**"Your glyphs, forged into vectors."**

*A professional toolkit to design, compile, and visualize custom vector fonts from hand-drawn or grid-based raster specimen sheets.*

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

> 🔗 **[Try them live on GitHub Pages →](https://steveblackbeard.github.io/FONTS-FORGE-by-Ethernium/)**

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
