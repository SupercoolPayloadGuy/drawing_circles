"""
animation.py — timing, easing, animated circle drawing, point fade-in,
               auto-zoom to keep the construction on screen.

Depends on a shared `state` object that holds:
  state.renderer   — Renderer instance
  state.clock      — pygame.time.Clock
  state.done_circles, state.done_points  (mirrored from renderer)

The pump() function handles events (quit, theme toggle, scroll).
"""

import math
import time
import pygame

from geometry import (
    angle_on_circle, farthest_extent, circle_from_points, all_pairs
)


# ──────────────────────────────────────────────
# EASING
# ──────────────────────────────────────────────

def ease_in_out(t):
    return t * t * (3 - 2 * t)


# ──────────────────────────────────────────────
# SHARED STATE  (filled in by main.py)
# ──────────────────────────────────────────────

class AnimState:
    def __init__(self, renderer, clock, draw_duration, pause_between,
                 stage_pause, point_fade_dur):
        self.renderer       = renderer
        self.clock          = clock
        self.draw_duration  = draw_duration
        self.pause_between  = pause_between
        self.stage_pause    = stage_pause
        self.point_fade_dur = point_fade_dur

        # mirrors of renderer lists (same objects)
        self.done_circles  = renderer.done_circles
        self.done_points   = renderer.done_points


# ──────────────────────────────────────────────
# EVENT PUMP
# ──────────────────────────────────────────────

def pump(state):
    r = state.renderer
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_b, pygame.K_SPACE):
                r.toggle_theme()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if r.toggle_rect.collidepoint(event.pos):
                r.toggle_theme()
        if event.type == pygame.MOUSEWHEEL:
            r.camera.scroll(event.y)


# ──────────────────────────────────────────────
# AUTO-ZOOM  (called after each circle is added)
# ──────────────────────────────────────────────

_MARGIN = 0.88   # fraction of half-screen used

def auto_zoom(state, origin):
    """Fit zoom so the farthest circle extent is visible."""
    extent = farthest_extent(origin, state.done_circles)
    if extent > 0:
        state.renderer.camera.fit_radius(extent, _MARGIN)


# ──────────────────────────────────────────────
# ANIMATE CIRCLE
# ──────────────────────────────────────────────

def animate_circle(state, center, radius, from_point=None, origin=None):
    r = state.renderer
    r.anim_circle = (center, radius)
    r.anim_t      = 0.0

    if from_point is not None:
        r.anim_start_ang = angle_on_circle(center, from_point)
    else:
        r.anim_start_ang = -math.pi / 2

    start = time.time()
    while True:
        elapsed = time.time() - start
        raw     = min(elapsed / state.draw_duration, 1.0)
        r.anim_t = ease_in_out(raw)
        r.redraw()
        pump(state)
        state.clock.tick(60)
        if raw >= 1.0:
            break

    state.done_circles.append((center, radius))
    r.anim_circle = None
    r.anim_t      = 0.0

    # Auto-zoom after every circle so construction stays on screen
    if origin is not None:
        auto_zoom(state, origin)


# ──────────────────────────────────────────────
# PAUSE
# ──────────────────────────────────────────────

def pause(state, seconds):
    end = time.time() + seconds
    while time.time() < end:
        state.renderer.redraw()
        pump(state)
        state.clock.tick(60)


# ──────────────────────────────────────────────
# POINT FADE-IN
# ──────────────────────────────────────────────

def add_points_fade(state, pts, stagger=0.06):
    """
    Add world-space points to the renderer and animate them fading in
    with a stagger between each.
    """
    base_idx = len(state.done_points)
    for pt in pts:
        state.done_points.append([pt[0], pt[1], 0])

    idxs   = list(range(base_idx, base_idx + len(pts)))
    starts = [time.time() + i * stagger for i in range(len(pts))]
    flags  = [False] * len(pts)
    dur    = state.point_fade_dur

    while not all(flags):
        now = time.time()
        for i, idx in enumerate(idxs):
            if flags[i]:
                continue
            elapsed = now - starts[i]
            if elapsed < 0:
                continue
            raw = min(elapsed / dur, 1.0)
            state.done_points[idx][2] = round(ease_in_out(raw) * 255)
            if raw >= 1.0:
                flags[i] = True
        state.renderer.redraw()
        pump(state)
        state.clock.tick(60)


# ──────────────────────────────────────────────
# DRAW ALL PAIRS
# ──────────────────────────────────────────────

def draw_all_pairs(state, points, origin=None):
    for p1, p2 in all_pairs(points):
        c, r = circle_from_points(p1, p2)
        animate_circle(state, c, r, from_point=p1, origin=origin)
        pump(state)