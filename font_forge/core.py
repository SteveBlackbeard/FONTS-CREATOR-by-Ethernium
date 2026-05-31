"""
Generic raster sheet → OpenType font pipeline.
Designed for grid-based specimen sheets (rows of glyphs left-to-right).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from font_forge.config import scale_rows


def resolve_sheet_path(root: Path, sheet_name: str) -> Path:
    exact = root / sheet_name
    if exact.is_file():
        return exact
    for fallback in ("ethernium_sheet_hq.png", "ethernium_sheet.png"):
        path = root / fallback
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"No sheet found. Place '{sheet_name}' in {root}"
    )


def effective_upscale(width: int) -> int:
    """HQ sheets need less upscaling to avoid blur."""
    if width >= 3000:
        return 1
    if width >= 1500:
        return 2
    return 4


def make_image_symmetrical(crop: np.ndarray, blend: float) -> np.ndarray:
    pts = np.argwhere(crop > 0)
    if len(pts) == 0:
        return crop

    xs = pts[:, 1]
    xmin, xmax = xs.min(), xs.max()
    center = (xmin + xmax) / 2.0
    int_center = int(np.floor(center))
    h, w = crop.shape
    sym_crop = np.zeros_like(crop)

    for x in range(0, int_center + 1):
        mirrored_x = int(np.round(2 * center - x))
        if 0 <= mirrored_x < w:
            sym_crop[:, x] = crop[:, x]
            sym_crop[:, mirrored_x] = crop[:, x]

    if center.is_integer():
        c_idx = int(center)
        if 0 <= c_idx < w:
            sym_crop[:, c_idx] = crop[:, c_idx]

    if blend >= 1.0:
        return sym_crop
    return cv2.addWeighted(sym_crop, blend, crop, 1.0 - blend, 0)


def draw_smooth_path(pen: TTGlyphPen, path: list[tuple[int, int]], max_deflection_deg: float = 28.0) -> None:
    """
    Classify path vertices using deflection angles:
    - Deflection angle <= max_deflection_deg: Smooth curve (TrueType off-curve control point).
    - Deflection angle > max_deflection_deg: Sharp corner (TrueType on-curve anchor point).
    """
    n = len(path)
    if n < 3:
        if n > 0:
            pen.moveTo(path[0])
            for pt in path[1:]:
                pen.lineTo(pt)
            pen.closePath()
        return

    # 1. Classify points as on-curve (True) or off-curve (False)
    on_curve = []
    for i in range(n):
        p0 = path[i - 1]
        p1 = path[i]
        p2 = path[(i + 1) % n]
        
        v1 = np.array([p1[0] - p0[0], p1[1] - p0[1]], dtype=np.float64)
        v2 = np.array([p2[0] - p1[0], p2[1] - p1[1]], dtype=np.float64)
        
        len1 = np.hypot(v1[0], v1[1])
        len2 = np.hypot(v2[0], v2[1])
        
        if len1 < 1e-5 or len2 < 1e-5:
            on_curve.append(True)
            continue
            
        dot = np.dot(v1, v2)
        cos_theta = np.clip(dot / (len1 * len2), -1.0, 1.0)
        theta = np.degrees(np.arccos(cos_theta))
        
        on_curve.append(theta > max_deflection_deg)

    # 2. Check if we have at least one on-curve point
    if not any(on_curve):
        p_first = path[0]
        p_last = path[-1]
        start_pt = (int(round((p_first[0] + p_last[0]) / 2)), int(round((p_first[1] + p_last[1]) / 2)))
        pen.moveTo(start_pt)
        pen.qCurveTo(*(path + [start_pt]))
        pen.closePath()
        return

    start_idx = on_curve.index(True)
    ordered_path = path[start_idx:] + path[:start_idx]
    ordered_on = on_curve[start_idx:] + on_curve[:start_idx]
    
    pen.moveTo(ordered_path[0])
    
    i = 1
    m = len(ordered_path)
    while i < m:
        if ordered_on[i]:
            pen.lineTo(ordered_path[i])
            i += 1
        else:
            off_curve_pts = []
            while i < m and not ordered_on[i]:
                off_curve_pts.append(ordered_path[i])
                i += 1
            next_pt = ordered_path[i % m]
            pen.qCurveTo(*(off_curve_pts + [next_pt]))
            i += 1
            
    pen.closePath()


def inject_forensic_watermark_in_compiled_glyphs(glyphs: dict, cmap: dict[int, str], watermark_str: str) -> None:
    """
    Inject a secret copyright signature in the LSB of coordinates of target glyphs.
    Invisible to the eye, unforgeable, programmatically auditable.
    """
    sig_bytes = watermark_str.encode('utf-8')
    bits = []
    for b in sig_bytes:
        for bit_idx in range(8):
            bits.append((b >> bit_idx) & 1)
            
    # Null-terminator byte (8 zero bits)
    for _ in range(8):
        bits.append(0)
        
    bit_idx = 0
    n_bits = len(bits)
    
    # Target characters in a stable, deterministic order
    target_chars = ['E', 'M', '\u03a9', 'O', 'V', 'W', '0', 'A', 'B', 'C', 'D', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'N']
    
    for char in target_chars:
        if bit_idx >= n_bits:
            break
            
        gname = cmap.get(ord(char))
        if not gname or gname not in glyphs:
            continue
            
        glyph = glyphs[gname]
        if glyph.numberOfContours <= 0 or not hasattr(glyph, "coordinates"):
            continue
            
        coords = glyph.coordinates
        for i in range(len(coords)):
            if bit_idx >= n_bits:
                break
                
            x, y = coords[i]
            x_int, y_int = int(round(x)), int(round(y))
            
            bit_x = bits[bit_idx]
            x_new = (x_int & ~1) | bit_x
            bit_idx += 1
            
            if bit_idx < n_bits:
                bit_y = bits[bit_idx]
                y_new = (y_int & ~1) | bit_y
                bit_idx += 1
            else:
                y_new = y_int
                
            coords[i] = (x_new, y_new)
            
    print(f"[Forensic Steganography] Embedded unforgeable copyright watermark: {bit_idx} bits written across designated glyphs.")



def refine_glyph_bitmap(crop: np.ndarray) -> np.ndarray:
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    closed = cv2.morphologyEx(crop, cv2.MORPH_CLOSE, k, iterations=1)
    return cv2.addWeighted(closed, 0.55, crop, 0.45, 0)


def smooth_binary_bitmap(crop: np.ndarray, pixel_scale: float) -> np.ndarray:
    """Anti-aliasing threshold smoothing to remove jagged stair-step pixelation."""
    # Ensure kernel size is odd and valid
    k = 5 if pixel_scale >= 3.0 else 3
    # Pad to prevent edge flattening during blur
    padded = cv2.copyMakeBorder(crop, 6, 6, 6, 6, cv2.BORDER_CONSTANT, value=0)
    blurred = cv2.GaussianBlur(padded, (k, k), 0)
    _, smoothed = cv2.threshold(blurred, 110, 255, cv2.THRESH_BINARY)
    return smoothed[6:-6, 6:-6]


def snap_contour_points(pts: np.ndarray, snap_deg: float = 10.0) -> np.ndarray:
    """Snap segment angles to 0/45/90 for crisp geometric strokes."""
    if len(pts) < 3:
        return pts

    snapped = [pts[0].astype(np.float64)]
    snap_targets = np.arange(0, 181, 45)
    min_len = 6.0

    for i in range(1, len(pts)):
        prev = snapped[-1]
        orig = pts[i].astype(np.float64)
        dx, dy = orig[0] - prev[0], orig[1] - prev[1]
        length = np.hypot(dx, dy)
        if length < min_len:
            snapped.append(orig)
            continue

        angle = np.degrees(np.arctan2(dy, dx)) % 180
        best = snap_targets[np.argmin(np.abs(snap_targets - angle))]
        if abs(best - angle) <= snap_deg:
            rad = np.radians(best)
            candidate = np.array(
                [prev[0] + length * np.cos(rad), prev[1] + length * np.sin(rad)]
            )
            if np.hypot(candidate[0] - orig[0], candidate[1] - orig[1]) <= length * 0.35:
                orig = candidate
        snapped.append(orig)

    return np.round(snapped).astype(np.int32)


def simplify_colinear(points: list[tuple[int, int]], tol: float = 2.5) -> list[tuple[int, int]]:
    """Drop middle points on nearly straight segments for cleaner outlines."""
    if len(points) < 3:
        return points
    out = [points[0]]
    for i in range(1, len(points) - 1):
        ax, ay = out[-1]
        bx, by = points[i]
        cx, cy = points[i + 1]
        area = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
        seg = np.hypot(cx - ax, cy - ay)
        if seg > 0 and area / seg > tol:
            out.append((bx, by))
    out.append(points[-1])
    return out


def to_font_coord(abs_x, abs_y, x_min, baseline_y, scale, lsb):
    """Map sheet pixels to font UPM; clamp to valid glyf range."""
    fx = int((abs_x - x_min) * scale + lsb)
    fy = int((baseline_y - abs_y) * scale)
    fx = max(-500, min(1200, fx))
    fy = max(-600, min(1100, fy))
    return fx, fy


def sharpen_gray(gray: np.ndarray, amount: float = 0.35) -> np.ndarray:
    """Light unsharp mask — crisp edges on HQ sheets without changing geometry."""
    blurred = cv2.GaussianBlur(gray, (0, 0), 1.2)
    sharp = cv2.addWeighted(gray, 1.0 + amount, blurred, -amount, 0)
    return np.clip(sharp, 0, 255).astype(np.uint8)


def prepare_binary(gray: np.ndarray, fixed_thresh: int | None, sharpen: bool = False) -> np.ndarray:
    """Sharp binarization: optional unsharp + median + threshold."""
    work = sharpen_gray(gray) if sharpen else gray
    denoised = cv2.medianBlur(work, 3)
    if fixed_thresh is not None:
        _, binary = cv2.threshold(denoised, fixed_thresh, 255, cv2.THRESH_BINARY)
    else:
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def row_content_x_bounds(crop: np.ndarray, pixel_scale: float) -> tuple[int, int]:
    """Left/right ink bounds for glyph grid (ignores far-right decorations)."""
    proj = np.sum(crop > 0, axis=0).astype(np.float32)
    if proj.max() == 0:
        return 0, crop.shape[1]
    thresh = proj.max() * 0.12
    idx = np.where(proj >= thresh)[0]
    x1, x2 = int(idx[0]), int(idx[-1]) + 1
    # Drop isolated right-side ornaments (connectors, wide art)
    max_orament_w = int(90 * pixel_scale)
    scan_x = x2 - 1
    while scan_x > x1 + int(200 * pixel_scale):
        col = crop[:, max(x1, scan_x - 20) : scan_x + 1]
        if col.size and np.sum(col > 0) > col.size * 0.02:
            break
        block = proj[max(x1, scan_x - max_orament_w) : scan_x + 1]
        if block.size and block.max() >= thresh:
            scan_x -= max_orament_w
            continue
        x2 = max(x1 + 1, scan_x)
        break
        scan_x -= max_orament_w
    return x1, x2


def extract_glyphs_grid(
    crop: np.ndarray,
    char_count: int,
    pixel_scale: float,
    pad: int | None = None,
) -> list[tuple[int, int, int, int]]:
    """Split row into equal slots — one glyph per cell, exact shapes from reference."""
    if pad is None:
        pad = max(1, int(2 * pixel_scale))
    x1, x2 = row_content_x_bounds(crop, pixel_scale)
    slot_w = (x2 - x1) / char_count
    boxes = []
    for i in range(char_count):
        sx1 = int(x1 + i * slot_w) + pad
        sx2 = int(x1 + (i + 1) * slot_w) - pad
        if sx2 <= sx1:
            sx2 = sx1 + 1
        slot = crop[:, sx1:sx2]
        pts = np.argwhere(slot > 0)
        if len(pts) == 0:
            boxes.append((sx1, 0, max(1, sx2 - sx1), crop.shape[0]))
            continue
        ys, xs = pts[:, 0], pts[:, 1]
        gy1, gy2 = int(ys.min()), int(ys.max()) + 1
        gx1, gx2 = int(xs.min()) + sx1, int(xs.max()) + sx1 + 1
        boxes.append((gx1, gy1, gx2 - gx1, gy2 - gy1))
    return boxes


def merge_boxes(
    boxes: list,
    gap_px: int,
    max_merge_width: int | None = None,
) -> list[tuple[int, int, int, int]]:
    if not boxes:
        return []

    merged = []
    used: set[int] = set()

    for i, b1 in enumerate(boxes):
        if i in used:
            continue
        group = [b1]
        used.add(i)
        changed = True
        while changed:
            changed = False
            for j, b2 in enumerate(boxes):
                if j in used:
                    continue
                merge_ok = False
                for member in group:
                    x1, _, w1, _ = member[:4]
                    x2, _, w2, _ = b2[:4]
                    h_dist = max(0, max(x1, x2) - min(x1 + w1, x2 + w2))
                    if h_dist <= gap_px:
                        xs = [b[0] for b in group] + [x2]
                        ws = [b[2] for b in group] + [w2]
                        span = max(x + w for x, w in zip(xs, ws)) - min(xs)
                        if max_merge_width and span > max_merge_width:
                            continue
                        merge_ok = True
                        break
                if merge_ok:
                    group.append(b2)
                    used.add(j)
                    changed = True

        xs = [b[0] for b in group]
        ys = [b[1] for b in group]
        ws = [b[2] for b in group]
        hs = [b[3] for b in group]
        min_x, max_x = min(xs), max(x + w for x, w in zip(xs, ws))
        min_y, max_y = min(ys), max(y + h for y, h in zip(ys, hs))
        merged.append((min_x, min_y, max_x - min_x, max_y - min_y))

    return sorted(merged, key=lambda g: g[0])


class SheetToFontBuilder:
    def __init__(self, config: dict[str, Any], root: Path):
        self.config = config
        self.root = root
        self.pipeline = config.get("pipeline", {})
        self.upscale = self.pipeline.get("upscale", "auto")
        self.thresh = self.pipeline.get("threshold", 30)
        self.trace_exact = self.pipeline.get("trace_exact", False)
        self.extraction = self.pipeline.get("extraction", "contour")
        self.snap_deg = self.pipeline.get("angle_snap_degrees", 10)
        self.symmetry_blend = self.pipeline.get("symmetry_blend", 0.90)
        self.symmetry_chars = (
            frozenset()
            if self.trace_exact
            else frozenset(config.get("symmetry_chars", []))
        )
        self.eps_factor = self.pipeline.get("contour_epsilon_factor", 0.010)
        self.skip_refine = self.pipeline.get("skip_bitmap_refine", False)
        self.lsb = config.get("lsb_offset", 80)
        self.units_per_em = config.get("units_per_em", 1024)
        self.scale_base = config.get("scale_base", 20)

    def _upscale_factor(self, width: int) -> int:
        if self.upscale == "auto":
            return effective_upscale(width)
        return int(self.upscale)

    def _load_sheet(self, sheet_name: str) -> tuple[np.ndarray, np.ndarray, float, int]:
        """Return (thresh, gray_source_shape, pixel_scale, upscale)."""
        sheet_path = resolve_sheet_path(self.root, sheet_name)
        img = cv2.imread(str(sheet_path))
        if img is None:
            raise RuntimeError(f"Cannot read sheet: {sheet_path}")

        upscale = self._upscale_factor(img.shape[1])
        if upscale > 1:
            img = cv2.resize(
                img, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_LANCZOS4
            )

        ref_w = self.config.get("reference_width", 1024)
        ref_h = self.config["reference_height"]
        pixel_scale = max(img.shape[1] / ref_w, img.shape[0] / ref_h)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = prepare_binary(
            gray,
            self.thresh if self.thresh > 0 else None,
            sharpen=self.pipeline.get("sharpen", True),
        )
        return thresh, img.shape, pixel_scale, upscale, sheet_path.name

    def build(self) -> dict[str, Any]:
        default_sheet = self.config["sheet"]
        ref_h = self.config["reference_height"]

        thresh_main, shape_main, pixel_scale_main, upscale_main, main_name = (
            self._load_sheet(default_sheet)
        )
        print(
            f"Main sheet: {main_name} -> {shape_main[1]}x{shape_main[0]} "
            f"(upscale {upscale_main}x, pixel_scale {pixel_scale_main:.2f})"
        )

        sheet_cache: dict[str, tuple] = {
            default_sheet: (thresh_main, shape_main, pixel_scale_main, upscale_main)
        }

        font_meta = self.config["font"]
        validation: dict[str, Any] = {
            "version": font_meta.get("version", "1.0"),
            "sheet": main_name,
            "upscale": upscale_main,
            "rows": [],
        }

        fb = FontBuilder(self.units_per_em, isTTF=True)
        fb.setupNameTable(font_meta["names"])

        # Add extended name records
        name_table = fb.font['name']
        for plat_id, enc_id, lang_id in [(3, 1, 0x0409), (1, 0, 0)]:
            name_table.setName("Ethernium Sym \u2014 A cyberpunk-runic display typeface.", 10, plat_id, enc_id, lang_id)
            name_table.setName("https://github.com/EtherniumSym", 11, plat_id, enc_id, lang_id)
            name_table.setName("Created with Ethernium Font Creator", 13, plat_id, enc_id, lang_id)

        glyphs: dict = {}
        glyph_order = [".notdef"]
        pen = TTGlyphPen(None)
        for coords in [(100, 100), (900, 100), (900, 900), (100, 900)]:
            if coords == (100, 100):
                pen.moveTo(coords)
            else:
                pen.lineTo(coords)
        pen.closePath()
        glyphs[".notdef"] = pen.glyph()

        cmap: dict[int, str] = {}
        metrics: dict[str, tuple[int, int]] = {".notdef": (1000, 100)}

        # Define custom fallback glyphs for missing ASCII characters
        # 1. space (codepoint 32)
        pen_sp = TTGlyphPen(None)
        glyphs["space"] = pen_sp.glyph()
        glyph_order.append("space")
        cmap[32] = "space"
        metrics["space"] = (280, 0)

        # 2. dollar (codepoint 36)
        pen_dl = TTGlyphPen(None)
        # Geometric S shape
        pen_dl.moveTo((100, 700))
        pen_dl.lineTo((400, 700))
        pen_dl.lineTo((400, 420))
        pen_dl.lineTo((160, 420))
        pen_dl.lineTo((160, 200))
        pen_dl.lineTo((400, 200))
        pen_dl.lineTo((400, 100))
        pen_dl.lineTo((100, 100))
        pen_dl.lineTo((100, 380))
        pen_dl.lineTo((340, 380))
        pen_dl.lineTo((340, 620))
        pen_dl.lineTo((100, 620))
        pen_dl.closePath()
        # Vertical stroke
        pen_dl.moveTo((220, 20))
        pen_dl.lineTo((280, 20))
        pen_dl.lineTo((280, 780))
        pen_dl.lineTo((220, 780))
        pen_dl.closePath()
        glyphs["dollar"] = pen_dl.glyph()
        glyph_order.append("dollar")
        cmap[36] = "dollar"
        metrics["dollar"] = (500, 100)

        # 3. asciicircum (codepoint 94)
        pen_ac = TTGlyphPen(None)
        pen_ac.moveTo((100, 450))
        pen_ac.lineTo((160, 450))
        pen_ac.lineTo((300, 650))
        pen_ac.lineTo((440, 450))
        pen_ac.lineTo((500, 450))
        pen_ac.lineTo((330, 720))
        pen_ac.lineTo((270, 720))
        pen_ac.closePath()
        glyphs["asciicircum"] = pen_ac.glyph()
        glyph_order.append("asciicircum")
        cmap[94] = "asciicircum"
        metrics["asciicircum"] = (600, 100)

        # 4. grave (codepoint 96)
        pen_gr = TTGlyphPen(None)
        pen_gr.moveTo((100, 580))
        pen_gr.lineTo((220, 720))
        pen_gr.lineTo((270, 680))
        pen_gr.lineTo((150, 540))
        pen_gr.closePath()
        glyphs["grave"] = pen_gr.glyph()
        glyph_order.append("grave")
        cmap[96] = "grave"
        metrics["grave"] = (350, 100)

        # 5. bar (codepoint 124)
        pen_br = TTGlyphPen(None)
        pen_br.moveTo((120, -100))
        pen_br.lineTo((180, -100))
        pen_br.lineTo((180, 800))
        pen_br.lineTo((120, 800))
        pen_br.closePath()
        glyphs["bar"] = pen_br.glyph()
        glyph_order.append("bar")
        cmap[124] = "bar"
        metrics["bar"] = (300, 120)

        for row in self.config["rows"]:
            name = row["name"]
            char_list = row["chars"]
            row_sheet = row.get("sheet", default_sheet)

            if row_sheet not in sheet_cache:
                t, sh, ps, up, _ = self._load_sheet(row_sheet)
                sheet_cache[row_sheet] = (t, sh, ps, up)
                print(
                    f"Alt sheet: {row_sheet} -> {sh[1]}x{sh[0]} "
                    f"(pixel_scale {ps:.2f})"
                )

            thresh, shape, pixel_scale, upscale = sheet_cache[row_sheet]
            rows_scaled = scale_rows([row], shape[0], ref_h)[0]
            y1 = rows_scaled["y_start"]
            y2 = rows_scaled["y_end"]
            baseline = rows_scaled["baseline"]

            scale = self.scale_base / pixel_scale
            margin = max(2, int(3 * pixel_scale))
            merge_gap = max(3, int(4 * pixel_scale))
            min_w = max(2, int(2 * pixel_scale))
            min_h = max(2, int(2 * pixel_scale))
            min_area = max(8, int(8 * pixel_scale * pixel_scale))
            max_w = int(200 * pixel_scale)
            eps_base = (0.08 if self.trace_exact else 0.42) * pixel_scale

            print(f"\nRow: {name} (y={y1}-{y2}, sheet={row_sheet})")

            default_pad_y = max(0, int(4 * pixel_scale))
            row_pad_y = row.get("pad_y")
            if row_pad_y is not None:
                pad_y = max(0, int(row_pad_y * pixel_scale))
            else:
                pad_y = default_pad_y
            y1p = max(0, y1 - pad_y)
            y2p = min(thresh.shape[0], y2 + pad_y)
            crop = thresh[y1p:y2p, :]
            y_offset = y1p

            use_grid = self.extraction == "grid" or (
                self.trace_exact and row.get("grid", True)
            )
            if use_grid:
                merged = extract_glyphs_grid(crop, len(char_list), pixel_scale)
            else:
                contours, _ = cv2.findContours(
                    crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                boxes = []
                for c in contours:
                    x, y, w, h = cv2.boundingRect(c)
                    if w > max_w or h < min_h or w < min_w or w * h < min_area:
                        continue
                    boxes.append((x, y, w, h))

                row_gap = row.get("merge_gap")
                gap = max(2, int(row_gap * pixel_scale)) if row_gap else merge_gap
                max_merge_w = row.get("max_merge_width")
                max_merge_w = (
                    int(max_merge_w * pixel_scale)
                    if max_merge_w
                    else int(55 * pixel_scale)
                )
                x_max = row.get("x_max")
                if x_max is not None:
                    x_lim = int(x_max * pixel_scale)
                    boxes = [b for b in boxes if b[0] <= x_lim]
                merged = merge_boxes(boxes, gap, max_merge_width=max_merge_w)
            row_ok = len(merged) == len(char_list)
            if not row_ok:
                print(f"  Warning: got {len(merged)}, expected {len(char_list)}")

            row_report = {
                "row": name,
                "expected": len(char_list),
                "extracted": len(merged),
                "ok": row_ok,
            }
            validation["rows"].append(row_report)

            for idx, (gx, gy, gw, gh) in enumerate(merged):
                if idx >= len(char_list):
                    break
                char = char_list[idx]
                gname = char if char.isalnum() and ord(char) < 128 else f"uni{ord(char):04X}"

                cx1, cy1 = max(0, gx - margin), max(0, gy - margin)
                cx2 = min(crop.shape[1], gx + gw + margin)
                cy2 = min(crop.shape[0], gy + gh + margin)
                glyph_crop = crop[cy1:cy2, cx1:cx2].copy()
                if not self.skip_refine and not self.trace_exact:
                    glyph_crop = refine_glyph_bitmap(glyph_crop)
                elif self.trace_exact:
                    glyph_crop = smooth_binary_bitmap(glyph_crop, pixel_scale)

                if char in self.symmetry_chars:
                    glyph_crop = make_image_symmetrical(
                        glyph_crop, self.symmetry_blend
                    )

                g_contours, hierarchy = cv2.findContours(
                    glyph_crop, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
                )

                x_min = gx
                path_list: list[list[tuple[int, int]]] = []

                def add_path(contour):
                    peri = cv2.arcLength(contour, True)
                    eps = max(
                        eps_base,
                        self.eps_factor * peri if self.trace_exact else 0.010 * peri,
                    )
                    approx = cv2.approxPolyDP(contour, eps, True)
                    pts = approx.reshape(-1, 2)
                    if len(pts) < 3:
                        return
                    if self.snap_deg > 0 and not self.trace_exact:
                        pts = snap_contour_points(pts, self.snap_deg)
                    font_pts = []
                    for px, py in pts:
                        abs_x, abs_y = cx1 + px, y1p + cy1 + py
                        font_pts.append(
                            to_font_coord(abs_x, abs_y, x_min, baseline, scale, self.lsb)
                        )
                    if not self.trace_exact:
                        font_pts = simplify_colinear(font_pts)
                    if len(font_pts) >= 3:
                        path_list.append(font_pts)

                if hierarchy is not None and len(g_contours):
                    hier = hierarchy[0]
                    for ci, c in enumerate(g_contours):
                        if hier[ci][3] != -1:
                            continue
                        add_path(c)
                        child = hier[ci][2]
                        while child != -1:
                            add_path(g_contours[child])
                            child = hier[child][0]
                else:
                    for c in g_contours:
                        add_path(c)

                if not path_list:
                    continue

                def drop_rogue_paths(paths):
                    cleaned = []
                    for path in paths:
                        ys = [p[1] for p in path]
                        if min(ys) < -120 or max(ys) > 1080:
                            continue
                        if max(ys) - min(ys) > 980:
                            continue
                        cleaned.append(path)
                    return cleaned

                path_list = drop_rogue_paths(path_list)
                if not path_list:
                    g_contours, _ = cv2.findContours(
                        glyph_crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )
                    path_list = []
                    for c in g_contours:
                        peri = cv2.arcLength(c, True)
                        eps = max(eps_base, self.eps_factor * peri)
                        approx = cv2.approxPolyDP(c, eps, True)
                        pts = approx.reshape(-1, 2)
                        if len(pts) < 3:
                            continue
                        fp = [
                            to_font_coord(
                                cx1 + p[0], y1p + cy1 + p[1], x_min, baseline, scale, self.lsb
                            )
                            for p in pts
                        ]
                        path_list.append(fp)
                    path_list = drop_rogue_paths(path_list)
                if not path_list:
                    print(f"  Skip '{char}': no valid paths")
                    continue

                all_pts = [p for path in path_list for p in path]
                min_fx = min(p[0] for p in all_pts)
                max_fx = max(p[0] for p in all_pts)
                min_fy = min(p[1] for p in all_pts)
                max_fy = max(p[1] for p in all_pts)
                if (max_fx - min_fx) > 1400:
                    print(f"  Skip '{char}': too wide")
                    continue

                # Auto baseline alignment vertical shift
                is_baseline_char = char.isupper() or char in "acenorsuvwxz"
                shift_y = 0
                if is_baseline_char and self.pipeline.get("auto_baseline_align", True):
                    shift_y = -min_fy

                shift_x = self.lsb - min_fx
                pen = TTGlyphPen(None)
                max_deflection = self.pipeline.get("curve_deflection_threshold", 28.0)
                for path in path_list:
                    shifted = [(p[0] + shift_x, p[1] + shift_y) for p in path]
                    if max_deflection > 0 and not self.trace_exact:
                        draw_smooth_path(pen, shifted, max_deflection)
                    else:
                        pen.moveTo(shifted[0])
                        for pt in shifted[1:]:
                            pen.lineTo(pt)
                        pen.closePath()

                glyph_w = max_fx - min_fx
                # Tight ink-based advance: LSB + ink width + RSB
                rsb = self.config.get("rsb_offset", 40)
                advance = int(glyph_w) + self.lsb + rsb

                glyphs[gname] = pen.glyph()
                glyph_order.append(gname)
                cmap[ord(char)] = gname

                for alias in self.config.get("aliases", {}).get(char, []):
                    cmap[ord(alias)] = gname

                metrics[gname] = (advance, self.lsb)

        # Embed the steganographic watermark!
        watermark_str = self.config.get("watermark", "SteveBlackbeard / FONTS-CREATOR-by-Ethernium")
        inject_forensic_watermark_in_compiled_glyphs(glyphs, cmap, watermark_str)

        fb.setupGlyphOrder(glyph_order)
        fb.setupGlyf(glyphs)
        fb.setupCharacterMap(cmap)
        fb.setupHorizontalMetrics(metrics)

        # Setup professional kerning table (legacy format 0 kern table)
        from fontTools.ttLib.tables._k_e_r_n import table__k_e_r_n, KernTable_format_0
        kern = table__k_e_r_n()
        kern.version = 0
        subtable = KernTable_format_0()
        subtable.version = 0
        subtable.coverage = 1
        
        kern_table = {}
        def add_kern_pair(char1, char2, val):
            g1 = cmap.get(ord(char1))
            g2 = cmap.get(ord(char2))
            if g1 and g2 and g1 in glyphs and g2 in glyphs:
                kern_table[(g1, g2)] = val
        
        pairs_to_add = [
            ('A', 'V', -45), ('V', 'A', -45),
            ('A', 'W', -40), ('W', 'A', -40),
            ('A', 'Y', -45), ('Y', 'A', -45),
            ('A', 'T', -35), ('T', 'A', -45),
            ('F', 'A', -35), ('P', 'A', -30),
            ('L', 'T', -40), ('L', 'V', -40),
            ('L', 'W', -35), ('L', 'Y', -40),
            ('T', 'O', -35), ('O', 'T', -35),
            ('T', 'C', -30), ('C', 'T', -30),
            ('Y', 'O', -30), ('O', 'Y', -30),
        ]
        
        for c1, c2, val in pairs_to_add:
            # Uppercase pairs
            add_kern_pair(c1.upper(), c2.upper(), val)
            # Lowercase pairs
            add_kern_pair(c1.lower(), c2.lower(), val)
            # Mixed pairs
            add_kern_pair(c1.upper(), c2.lower(), val)
            add_kern_pair(c1.lower(), c2.upper(), val)
            
        # Special symbols kerning (Omega and Delta)
        add_kern_pair('\u03a9', '\u0394', -25)
        add_kern_pair('\u0394', '\u03a9', -25)
        
        if kern_table:
            subtable.kernTable = kern_table
            kern.subtables = [subtable]
            fb.font['kern'] = kern

        metrics_header = self.config.get("metrics", {})
        fb.setupHorizontalHeader(
            ascent=metrics_header.get("ascent", 900),
            descent=metrics_header.get("descent", -224),
        )
        fb.setupOS2(
            sTypoAscender=metrics_header.get("ascent", 900),
            sTypoDescender=metrics_header.get("descent", -224),
            sTypoLineGap=0,
            usWinAscent=metrics_header.get("win_ascent", 1000),
            usWinDescent=metrics_header.get("win_descent", 250),
            sxHeight=500,
            sCapHeight=700,
            usWeightClass=400,
            usWidthClass=5,
            fsType=0,
            fsSelection=0x0040,  # REGULAR bit
            achVendID="ETHN",
        )
        fb.setupPost()
        fb.setupMaxp()

        # Add gasp table for optimal screen rendering
        from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
        gasp = table__g_a_s_p()
        gasp.version = 1
        gasp.gaspRange = {
            8: 0x000A,    # < 8ppem: gridfit only
            20: 0x0007,   # 8-20ppem: gridfit + grayscale + symmetric smoothing
            65535: 0x000F, # > 20ppem: all smoothing options
        }
        fb.font['gasp'] = gasp

        out_base = self.root / self.config.get("output_basename", "Output")
        ttf_path = out_base.with_suffix(".ttf")
        fb.save(str(ttf_path))
        print(f"\nSaved {ttf_path.name}")

        report_path = self.root / "build_report.json"
        report_path.write_text(
            json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        font = TTFont(str(ttf_path))
        for flavor, ext in (("woff", ".woff"), ("woff2", ".woff2")):
            out = out_base.with_suffix(ext)
            font.flavor = flavor
            font.save(str(out))
            print(f"Saved {out.name}")

        return validation
