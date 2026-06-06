"""
renderer.py — drawing utilities, colour schemes, HUD, and export for single_circle.
"""

import math
import os
import time

import pygame
import colorsys

from config import WIDTH, HEIGHT, RADIUS, BG, WHITE, LINE_WIDTH, DRAW_FLOWER


# ── colour schemes ──────────────────────────────────────────────────

_SCHEMES = {
    "rainbow": lambda h: colorsys.hsv_to_rgb(h, 1.0, 1.0),
    "warm":    lambda h: colorsys.hsv_to_rgb(h * 0.15, 0.9, 1.0),
    "cool":    lambda h: colorsys.hsv_to_rgb(0.5 + h * 0.3, 0.9, 1.0),
    "mono":    lambda h: (0.78, 0.78, 0.78),
    "sunset":  lambda h: colorsys.hsv_to_rgb(h * 0.12,
                                              0.8 + 0.2 * h,
                                              0.8 + 0.2 * h),
}


def get_color(index, total, scheme):
    h = index / max(total, 1)
    fn = _SCHEMES.get(scheme, _SCHEMES["rainbow"])
    r, g, b = fn(h)
    return (int(r * 255), int(g * 255), int(b * 255))


# ── drawing primitives ──────────────────────────────────────────────

def create_mask(center):
    mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), center, RADIUS)
    return mask


def draw_arc(surface, center, radius, progress, color, width=LINE_WIDTH):
    cx, cy = center
    r = radius
    rect = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
    pygame.draw.arc(surface, color, rect, 0, math.radians(progress), width)


def draw_circle(surface, center, radius, color, width=LINE_WIDTH):
    pygame.draw.circle(surface, color,
                       (round(center[0]), round(center[1])),
                       round(radius), width)


def draw_dot(surface, center, radius=6, color=WHITE):
    pygame.draw.circle(surface, color,
                       (round(center[0]), round(center[1])),
                       radius)


# ── HUD ─────────────────────────────────────────────────────────────

_HUD_FONT = None


def _hud_font():
    global _HUD_FONT
    if _HUD_FONT is None:
        _HUD_FONT = pygame.font.SysFont("monospace", 16)
    return _HUD_FONT


def _progress_pct(stage, main_progress, visible_points, total_points,
                  current_circle, total_circles):
    if stage == 0:
        return main_progress / 360 * 5
    if stage == 1:
        return 5 + visible_points / max(total_points, 1) * 10
    if stage == 2:
        return 15 + current_circle / max(total_circles, 1) * 85
    return 100


def draw_hud(surface, stage, main_progress, visible_points, total_points,
             current_circle, total_circles,
             show_count, show_bar):
    if not show_count and not show_bar:
        return

    font = _hud_font()
    lines = []

    if show_count:
        done = current_circle if stage > 1 else 0
        lines.append(f"circles  {done} / {total_circles}")

    if show_bar:
        pct = _progress_pct(stage, main_progress, visible_points,
                            total_points, current_circle, total_circles)
        lines.append(f"progress  {pct:.1f}%")

    if not lines:
        return

    line_h = 20
    box_h = len(lines) * line_h + 16
    box_w = 220
    bx, by = WIDTH - box_w - 16, 16

    bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    surface.blit(bg, (bx, by))
    pygame.draw.rect(surface, (40, 40, 40), (bx, by, box_w, box_h), 1,
                     border_radius=4)

    for i, txt in enumerate(lines):
        c = (180, 180, 180) if "circles" in txt else WHITE
        s = font.render(txt, True, c)
        surface.blit(s, (bx + 10, by + 8 + i * line_h))


# ── main render ─────────────────────────────────────────────────────

def render_frame(screen, drawing, mask, center,
                 main_progress, finished_circles,
                 current_circle, circles,
                 current_progress, stage,
                 points, visible_points,
                 color_scheme, show_circle_count, show_progress_bar):
    total = len(circles)

    drawing.fill((0, 0, 0, 0))

    for i, circle in enumerate(finished_circles):
        color = get_color(i, total, color_scheme)
        draw_circle(drawing, circle["center"], circle["radius"], color)

    if stage == DRAW_FLOWER and current_circle < len(circles):
        circle = circles[current_circle]
        color = get_color(current_circle, total, color_scheme)
        draw_arc(drawing, circle["center"], circle["radius"],
                 current_progress, color)

    drawing.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    screen.fill(BG)
    screen.blit(drawing, (0, 0))

    draw_arc(screen, center, RADIUS, main_progress, WHITE, 3)
    draw_dot(screen, center)

    for p in points[:visible_points]:
        draw_dot(screen, p)

    draw_hud(screen, stage, main_progress, visible_points, len(points),
             current_circle, total, show_circle_count, show_progress_bar)


# ── UI helpers (end-screen buttons, hints) ──────────────────────────

_BTN_FONT = None


def _btn_font():
    global _BTN_FONT
    if _BTN_FONT is None:
        _BTN_FONT = pygame.font.SysFont("monospace", 17)
    return _BTN_FONT


def draw_button(surface, rect, label, bg=(30, 30, 30), fg=(200, 200, 200),
                border=(60, 60, 60)):
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 1, border_radius=8)
    s = _btn_font().render(label, True, fg)
    surface.blit(s, (rect.x + (rect.w - s.get_width()) // 2,
                     rect.y + (rect.h - s.get_height()) // 2))


def draw_hint(surface, text, y=12, color=(150, 150, 150)):
    s = _btn_font().render(text, True, color)
    surface.blit(s, (WIDTH // 2 - s.get_width() // 2, y))


# ── export ──────────────────────────────────────────────────────────

def export_png(screen, filename):
    pygame.image.save(screen, filename)
    return filename


def export_svg(filename, center, points, circles, finished_indices,
               main_radius, circle_count, line_width, scheme):
    cxs, cys = center
    clip_id = "mask0"

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

    with open(filename, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{WIDTH}" height="{HEIGHT}" '
                f'viewBox="0 0 {WIDTH} {HEIGHT}">\n')
        f.write(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#000"/>\n')
        f.write(f'<clipPath id="{clip_id}">\n')
        f.write(f'  <circle cx="{cxs}" cy="{cys}" r="{main_radius}"/>\n')
        f.write(f'</clipPath>\n')
        f.write(f'<g clip-path="url(#{clip_id})">\n')

        for idx in finished_indices:
            c = circles[idx]
            col = get_color(idx, circle_count, scheme)
            cx, cy = c["center"]
            r = c["radius"]
            f.write(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                    f'fill="none" stroke="rgb{col}" '
                    f'stroke-width="{line_width}"/>\n')

        f.write('</g>\n')
        f.write(f'<circle cx="{cxs}" cy="{cys}" r="{main_radius}" '
                f'fill="none" stroke="#fff" stroke-width="3"/>\n')
        f.write(f'<circle cx="{cxs}" cy="{cys}" r="6" fill="#fff"/>\n')

        for p in points:
            f.write(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="6" fill="#fff"/>\n')

        f.write('</svg>\n')

    return filename
