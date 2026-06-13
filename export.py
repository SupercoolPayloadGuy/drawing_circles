"""
export.py — export construction as SVG, PNG, or PDF.
"""

import math
import os
import sys
import time
import pygame


def _interp_stops(stops, t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        pos, col = stops[i]
        npos, ncol = stops[i + 1]
        if pos <= t <= npos:
            lt = (t - pos) / (npos - pos)
            return tuple(round(col[j] + (ncol[j] - col[j]) * lt) for j in range(3))
    return stops[-1][1]


def _depth_color(theme, depth_01, base_alpha=220):
    r, g, b = _interp_stops(theme["circle_stops"], depth_01)
    s = base_alpha / 255
    return (round(r * s), round(g * s), round(b * s))


def _point_color(theme, depth_01, alpha=255):
    r, g, b = _interp_stops(theme["point_stops"], depth_01)
    s = alpha / 255
    return (round(r * s), round(g * s), round(b * s))


def _to_hex(rgb):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'


def _make_svg_string(circles, points, theme):
    depths = [d for _, _, d in circles]
    max_depth = max(depths) if depths else 1.0

    all_x = []
    all_y = []
    for (cx, cy), r, _ in circles:
        all_x.extend([cx - r, cx + r])
        all_y.extend([cy - r, cy + r])
    for x, y, _, _ in points:
        all_x.append(x)
        all_y.append(y)

    if not all_x:
        min_x = min_y = 0.0
        max_x = max_y = 100.0
    else:
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)

    pad = max(max_x - min_x, max_y - min_y) * 0.05 or 50.0
    min_x -= pad
    min_y -= pad
    max_x += pad
    max_y += pad

    w = max_x - min_x
    h = max_y - min_y
    diag = math.hypot(w, h)
    stroke_w = max(0.5, min(3.0, diag * 0.002))

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x:.2f} {min_y:.2f} {w:.2f} {h:.2f}">',
        '  <title>Circle Construction</title>',
        f'  <rect x="{min_x:.2f}" y="{min_y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{_to_hex(theme["background"])}"/>'
    ]

    for (cx, cy), r, dep in circles:
        r_col = _interp_stops(theme["circle_stops"], dep / max_depth)
        hex_col = _to_hex(r_col)
        opacity = 220 / 255
        lines.append(
            f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
            f'fill="none" stroke="{hex_col}" stroke-width="{stroke_w:.2f}" stroke-opacity="{opacity:.3f}"/>'
        )

    for x, y, alpha, dep in points:
        if alpha <= 0:
            continue
        r_col = _interp_stops(theme["point_stops"], dep / max_depth)
        hex_col = _to_hex(r_col)
        opacity = alpha / 255
        lines.append(
            f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="4" '
            f'fill="{hex_col}" fill-opacity="{opacity:.3f}"/>'
        )

    lines.append('</svg>')
    return '\n'.join(lines)


def export_svg(circles, points, theme, filepath):
    svg_str = _make_svg_string(circles, points, theme)
    with open(filepath, 'w') as f:
        f.write(svg_str)


def export_pdf(circles, points, theme, filepath):
    svg_str = _make_svg_string(circles, points, theme)
    try:
        import cairosvg
        cairosvg.svg2pdf(bytestring=svg_str.encode(), write_to=filepath)
    except ImportError:
        svg_path = filepath.rsplit('.', 1)[0] + '.svg'
        with open(svg_path, 'w') as f:
            f.write(svg_str)
        print("cairosvg not installed. Install with: pip install cairosvg", file=sys.stderr)


def export_png(renderer, filepath):
    cam = renderer.camera
    th = renderer.theme

    surf = pygame.Surface((1200, 1200))
    surf.fill(th["background"])

    depths = [d for _, _, d in renderer.done_circles]
    max_depth = max(depths, default=1.0) or 1.0

    for wc, wr, dep in renderer.done_circles:
        sr = round(cam.r2s(wr))
        if sr < 1:
            continue
        alpha = max(60, round(220 - dep * 100))
        col = _depth_color(th, dep / max_depth, base_alpha=alpha)
        sc = cam.w2s(wc)
        pygame.draw.circle(surf, col, (round(sc[0]), round(sc[1])), sr, 1)

    for wx, wy, alpha, dep in renderer.done_points:
        col = _point_color(th, dep / max_depth, alpha=alpha)
        sc = cam.w2s((wx, wy))
        pygame.draw.circle(surf, col, (round(sc[0]), round(sc[1])), 5)

    pygame.image.save(surf, filepath)


def export_highres_png(circles, points, theme, filepath, scale=2):
    from renderer import Camera

    width = round(1200 * scale)
    height = round(1200 * scale)

    all_x = []
    all_y = []
    for (cx, cy), r, _ in circles:
        all_x.extend([cx - r, cx + r])
        all_y.extend([cy - r, cy + r])
    for x, y, _, _ in points:
        all_x.append(x)
        all_y.append(y)

    if not all_x:
        min_x = min_y = 0.0
        max_x = max_y = 100.0
    else:
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)

    pad = max(max_x - min_x, max_y - min_y) * 0.05 or 50.0
    world_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)

    world_radius = 0.0
    for (cx, cy), r, _ in circles:
        d = math.hypot(cx - world_center[0], cy - world_center[1]) + r
        world_radius = max(world_radius, d)
    if world_radius == 0:
        world_radius = 100.0

    cam = Camera(width, height, world_center)
    cam.fit_radius(world_radius)

    surf = pygame.Surface((width, height))
    surf.fill(theme["background"])

    depths = [d for _, _, d in circles]
    max_depth = max(depths, default=1.0) or 1.0

    for wc, wr, dep in circles:
        sr = round(cam.r2s(wr))
        if sr < 1:
            continue
        alpha = max(60, round(220 - dep * 100))
        col = _depth_color(theme, dep / max_depth, base_alpha=alpha)
        sc = cam.w2s(wc)
        pygame.draw.circle(surf, col, (round(sc[0]), round(sc[1])), sr, 1)

    pt_radius = max(3, round(4 * scale))
    for wx, wy, alpha, dep in points:
        if alpha <= 0:
            continue
        col = _point_color(theme, dep / max_depth, alpha=alpha)
        sc = cam.w2s((wx, wy))
        pygame.draw.circle(surf, col, (round(sc[0]), round(sc[1])), pt_radius)

    pygame.image.save(surf, filepath)


def _timestamp_path(ext):
    ts = time.strftime("%Y%m%d_%H%M%S")
    base = os.path.join(os.getcwd(), "map", "exports")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"construction_{ts}.{ext}")
