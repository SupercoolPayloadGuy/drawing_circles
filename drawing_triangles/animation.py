"""
animation.py — timing, easing, pause/play, animated triangle construction steps.
"""

import os
import time
import pygame
import numpy as np

from geometry import next_generation
from renderer import RESTART_EVENT
from export import _timestamp_path, export_svg, export_png, export_pdf, \
    export_highres_png


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def gen_duration(gen_idx):
    return max(0.2, 0.80 / (1.0 + 0.35 * gen_idx))


class AnimState:
    SPEED_MIN  = 0.25
    SPEED_MAX  = 8.0
    SPEED_STEP = 0.25

    def __init__(self, renderer, clock):
        self.renderer      = renderer
        self.clock         = clock
        self.speed_mul     = 1.0

    @property
    def draw_duration(self):
        return self._base_dur / self.speed_mul

    def set_gen(self, gen_idx):
        self._base_dur = gen_duration(gen_idx)


def pump(state):
    r = state.renderer
    r.update_hover(pygame.mouse.get_pos())
    r.speed_display = state.speed_mul

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                r.toggle_theme()
            elif event.key == pygame.K_p:
                r.paused = not r.paused
            elif event.key == pygame.K_LEFTBRACKET:
                state.speed_mul = max(AnimState.SPEED_MIN,
                                      round(state.speed_mul - AnimState.SPEED_STEP, 10))
            elif event.key == pygame.K_RIGHTBRACKET:
                state.speed_mul = min(AnimState.SPEED_MAX,
                                      round(state.speed_mul + AnimState.SPEED_STEP, 10))
            elif event.key == pygame.K_d:
                r.toggle_dev_mode()
            elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                pygame.event.post(pygame.event.Event(RESTART_EVENT))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.menu_rect.collidepoint(event.pos):
                pygame.event.post(pygame.event.Event(RESTART_EVENT))
            elif r.toggle_rect.collidepoint(event.pos):
                r.toggle_theme()
            elif not r.animation_done and r.pause_rect.collidepoint(event.pos):
                r.paused = not r.paused
            elif r.animation_done and not r.show_choices:
                restart_req = False
                if r.restart_rect.collidepoint(event.pos):
                    restart_req = True
                elif r.export_svg_rect and r.export_svg_rect.collidepoint(event.pos):
                    path = _timestamp_path("svg")
                    export_svg(r.done_triangles, r.done_points, r.theme, path)
                    r.export_message = f"SVG saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                elif r.export_png_rect and r.export_png_rect.collidepoint(event.pos):
                    path = _timestamp_path("png")
                    export_png(r, path)
                    r.export_message = f"PNG saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                elif r.export_pdf_rect and r.export_pdf_rect.collidepoint(event.pos):
                    path = _timestamp_path("pdf")
                    export_pdf(r.done_triangles, r.done_points, r.theme, path)
                    r.export_message = f"PDF saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                elif r.export_hd_rect and r.export_hd_rect.collidepoint(event.pos):
                    path = _timestamp_path("png")
                    export_highres_png(r.done_triangles, r.done_points, r.theme, path, scale=2)
                    r.export_message = f"HD PNG saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                if restart_req:
                    pygame.event.post(pygame.event.Event(RESTART_EVENT))
            elif r.show_choices:
                if r.choice_menu_rect and r.choice_menu_rect.collidepoint(event.pos):
                    pygame.event.post(pygame.event.Event(RESTART_EVENT))
                elif r.choice_look_rect and r.choice_look_rect.collidepoint(event.pos):
                    r.show_choices = False
                elif r.choice_svg_rect and r.choice_svg_rect.collidepoint(event.pos):
                    path = _timestamp_path("svg")
                    export_svg(r.done_triangles, r.done_points, r.theme, path)
                    r.export_message = f"SVG saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                elif r.choice_png_rect and r.choice_png_rect.collidepoint(event.pos):
                    path = _timestamp_path("png")
                    export_png(r, path)
                    r.export_message = f"PNG saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                elif r.choice_pdf_rect and r.choice_pdf_rect.collidepoint(event.pos):
                    path = _timestamp_path("pdf")
                    export_pdf(r.done_triangles, r.done_points, r.theme, path)
                    r.export_message = f"PDF saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()
                elif r.choice_hd_rect and r.choice_hd_rect.collidepoint(event.pos):
                    path = _timestamp_path("png")
                    export_highres_png(r.done_triangles, r.done_points, r.theme, path, scale=2)
                    r.export_message = f"HD PNG saved → {os.path.basename(path)}"
                    r.export_msg_timer = time.time()

        if event.type == pygame.MOUSEWHEEL:
            r.camera.scroll(event.y)

        if event.type == RESTART_EVENT:
            return True

    return False


def _phase_alpha(t, start, end):
    """Compute alpha for an element that appears between start and end."""
    if t < start:
        return 0
    if t >= end:
        return 255
    raw = (t - start) / (end - start)
    return round(ease_in_out(raw) * 255)


def animate_generation(state, current_triangle, gen_idx):
    r = state.renderer
    state.set_gen(gen_idx)

    new_tri, bisectors, perps = next_generation(current_triangle)

    dur = state._base_dur
    prev_ts = time.time()
    elapsed = 0.0

    while True:
        now = time.time()
        if not r.paused:
            elapsed += now - prev_ts
        prev_ts = now

        t = min(elapsed / dur, 1.0)

        r.anim_triangle = current_triangle
        r.anim_bisectors = bisectors
        r.anim_perps = perps
        r.anim_new_tri = new_tri
        r.anim_intersections = new_tri
        r.anim_t = t
        r.redraw()

        if pump(state):
            raise _RestartSignal()
        state.clock.tick(60)

        if t >= 1.0:
            break

    r.done_triangles.append((current_triangle, gen_idx))
    r.construction_history.append({
        "tri": current_triangle,
        "bis": list(zip(current_triangle, bisectors)),
        "perps": list(zip(current_triangle, perps)),
        "ints": new_tri,
    })
    r.anim_triangle = None
    r.anim_bisectors = None
    r.anim_perps = None
    r.anim_new_tri = None
    r.anim_intersections = None
    r.anim_t = 0.0

    return new_tri


class _RestartSignal(Exception):
    pass

RestartSignal = _RestartSignal
