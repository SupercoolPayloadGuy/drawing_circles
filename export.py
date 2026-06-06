"""
export.py — export construction as SVG or PNG.
"""

import os
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


def export_svg(circles, points, theme, filepath):
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

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {w} {h}">',
        f'  <rect x="{min_x}" y="{min_y}" width="{w}" height="{h}" fill="{_to_hex(theme["background"])}"/>'
    ]

    for (cx, cy), r, dep in circles:
        col = _depth_color(theme, dep / max_depth)
        lines.append(
            f'  <circle cx="{cx}" cy="{cy}" r="{r}" '
            f'fill="none" stroke="{_to_hex(col)}" stroke-width="1"/>'
        )

    for x, y, alpha, dep in points:
        if alpha <= 0:
            continue
        col = _point_color(theme, dep / max_depth, alpha=alpha)
        lines.append(f'  <circle cx="{x}" cy="{y}" r="4" fill="{_to_hex(col)}"/>')

    lines.append('</svg>')

    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))


def export_png(renderer, filepath):
    cam = renderer.camera
    th = renderer.theme
    sw, sh = renderer.screen.get_size()

    surf = pygame.Surface((sw, sh))
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


def _timestamp_path(ext):
    ts = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(os.getcwd(), f"construction_{ts}.{ext}")
