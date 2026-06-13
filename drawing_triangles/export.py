"""
export.py — export triangle construction as SVG, PNG, or PDF.
"""

import math
import os
import sys
import time
import pygame

from geometry import distance


def _gen_color(theme, gen_01, base_alpha=180):
    r = theme["base_r"]
    g = theme["base_g"]
    b = theme["base_b"]
    s = base_alpha / 255
    return (
        round(min(255, (r + 50 * gen_01)) * s),
        round(min(255, (g + 80 * gen_01)) * s),
        round(min(255, (b + 40 * gen_01)) * s),
    )


def _to_hex(rgb):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'


def _make_svg_string(triangles, points, theme):
    max_gen = len(triangles) if triangles else 1

    all_x = []
    all_y = []
    for tri, _ in triangles:
        for v in tri:
            all_x.append(v[0])
            all_y.append(v[1])
    for x, y in points:
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
        '  <title>Triangle Construction</title>',
        f'  <rect x="{min_x:.2f}" y="{min_y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{_to_hex(theme["background"])}"/>'
    ]

    for tri, gen in triangles:
        frac = gen / max(int(max_gen - 1), 1) if max_gen > 1 else 0.5
        base_a = max(80, round(200 - frac * 60))
        col = _gen_color(theme, gen / max_gen, base_alpha=base_a)
        hex_col = _to_hex(col)
        pts_str = ' '.join(f'{v[0]:.2f},{v[1]:.2f}' for v in tri)
        opacity = base_a / 255
        lines.append(
            f'  <polygon points="{pts_str}" '
            f'fill="none" stroke="{hex_col}" stroke-width="{stroke_w:.2f}" stroke-opacity="{opacity:.3f}"/>'
        )

    lines.append('</svg>')
    return '\n'.join(lines)


def export_svg(triangles, points, theme, filepath):
    svg_str = _make_svg_string(triangles, points, theme)
    with open(filepath, 'w') as f:
        f.write(svg_str)


def export_pdf(triangles, points, theme, filepath):
    svg_str = _make_svg_string(triangles, points, theme)
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

    max_gen = len(renderer.done_triangles) if renderer.done_triangles else 1
    for tri, gen in renderer.done_triangles:
        col = _gen_color(th, gen / max_gen)
        pts = [cam.w2s(v) for v in tri]
        pygame.draw.polygon(surf, col, pts, 1)

    for pt in renderer.done_points:
        sc = cam.w2s(pt)
        pygame.draw.circle(surf, th["point_color"], (round(sc[0]), round(sc[1])), 4)

    pygame.image.save(surf, filepath)


def export_highres_png(triangles, points, theme, filepath, scale=2):
    from renderer import Camera
    width = round(1200 * scale)
    height = round(1200 * scale)

    all_x = []
    all_y = []
    for tri, _ in triangles:
        for v in tri:
            all_x.append(v[0])
            all_y.append(v[1])
    for x, y in points:
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
    for tri, _ in triangles:
        for v in tri:
            d = distance(world_center, v)
            world_radius = max(world_radius, d)
    if world_radius == 0:
        world_radius = 100.0

    cam = Camera(width, height, world_center)
    cam.fit_radius(world_radius)

    surf = pygame.Surface((width, height))
    surf.fill(theme["background"])

    max_gen = len(triangles) if triangles else 1
    for tri, gen in triangles:
        col = _gen_color(theme, gen / max_gen)
        pts = [(round((v[0] - cam.origin[0]) * cam.zoom + width/2),
                round((v[1] - cam.origin[1]) * cam.zoom + height/2)) for v in tri]
        pygame.draw.polygon(surf, col, pts, 1)

    for x, y in points:
        sx = round((x - cam.origin[0]) * cam.zoom + width/2)
        sy = round((y - cam.origin[1]) * cam.zoom + height/2)
        pygame.draw.circle(surf, theme["point_color"], (sx, sy), 4)

    pygame.image.save(surf, filepath)


def _timestamp_path(ext):
    ts = time.strftime("%Y%m%d_%H%M%S")
    base = os.path.join(os.getcwd(), "map", "exports")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"triangle_{ts}.{ext}")
