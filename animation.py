"""
animation.py — timing, easing, pause/play, animated circle drawing,
               point fade-in, auto-zoom, draw_all_pairs.

Each circle and point now carries a `depth` value (float ≥ 0) that
the renderer uses for colour grading.
"""

import math
import time
import pygame

from geometry import (
    angle_on_circle, farthest_extent, circle_from_points, all_pairs
)
from renderer import RESTART_EVENT


# ──────────────────────────────────────────────
# EASING
# ──────────────────────────────────────────────

def ease_in_out(t):
    return t * t * (3 - 2 * t)


# ──────────────────────────────────────────────
# DURATION SCALING
# ──────────────────────────────────────────────

def draw_duration(level):
    """
    Hyperbolic scaling: fast at high levels, never below floor.
    L1=0.30  L2=0.22  L3=0.15  L5=0.09  L10=0.05  L20+=0.025
    """
    base  = 0.30
    k     = 0.35
    floor = 0.025
    return max(floor, base / (1.0 + k * (level - 1)))


# ──────────────────────────────────────────────
# SHARED STATE
# ──────────────────────────────────────────────

class AnimState:
    def __init__(self, renderer, clock, level):
        self.renderer      = renderer
        self.clock         = clock
        self.draw_duration = draw_duration(level)
        self.point_fade    = 0.38

        # Same list objects as renderer — mutations are reflected immediately
        self.done_circles = renderer.done_circles   # [(wc, wr, depth), …]
        self.done_points  = renderer.done_points    # [[wx,wy,alpha,depth], …]


# ──────────────────────────────────────────────
# EVENT PUMP
# ──────────────────────────────────────────────

def pump(state):
    r = state.renderer
    r.update_hover(pygame.mouse.get_pos())
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_b,):
                r.toggle_theme()
            elif event.key == pygame.K_p:
                r.paused = not r.paused
            elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                pygame.event.post(pygame.event.Event(RESTART_EVENT))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.menu_rect.collidepoint(event.pos):
                pygame.event.post(pygame.event.Event(RESTART_EVENT))
            elif r.toggle_rect.collidepoint(event.pos):
                r.toggle_theme()
            elif not r.animation_done and r.pause_rect.collidepoint(event.pos):
                r.paused = not r.paused
            elif r.animation_done and not r.show_choices and r.restart_rect.collidepoint(event.pos):
                pygame.event.post(pygame.event.Event(RESTART_EVENT))
            elif r.show_choices:
                if r.choice_menu_rect and r.choice_menu_rect.collidepoint(event.pos):
                    pygame.event.post(pygame.event.Event(RESTART_EVENT))
                elif r.choice_look_rect and r.choice_look_rect.collidepoint(event.pos):
                    r.show_choices = False

        if event.type == pygame.MOUSEWHEEL:
            r.camera.scroll(event.y)

        if event.type == RESTART_EVENT:
            return True   # signal restart to caller

    return False


# ──────────────────────────────────────────────
# AUTO-ZOOM
# ──────────────────────────────────────────────

def auto_zoom(state, origin):
    extent = farthest_extent(origin, [(c, r) for c, r, _ in state.done_circles])
    if extent > 0:
        state.renderer.camera.fit_radius(extent, 0.88)


# ──────────────────────────────────────────────
# ANIMATE CIRCLE
# ──────────────────────────────────────────────

def animate_circle(state, center, radius, depth=0.0,
                   from_point=None, origin=None):
    r = state.renderer
    r.anim_circle    = (center, radius, depth)
    r.anim_t         = 0.0
    r.anim_start_ang = (angle_on_circle(center, from_point)
                        if from_point is not None else -math.pi / 2)

    # Track elapsed excluding paused time
    draw_t  = 0.0
    prev_ts = time.time()

    while True:
        now     = time.time()
        if not r.paused:
            draw_t += now - prev_ts
        prev_ts = now

        raw    = min(draw_t / state.draw_duration, 1.0)
        r.anim_t = ease_in_out(raw)
        r.redraw()
        if pump(state):
            raise _RestartSignal()
        state.clock.tick(60)
        if raw >= 1.0:
            break

    state.done_circles.append((center, radius, depth))
    r.anim_circle = None
    r.anim_t      = 0.0

    if origin is not None:
        auto_zoom(state, origin)


# ──────────────────────────────────────────────
# PAUSE (animation stage gap)
# ──────────────────────────────────────────────

def pause(state, seconds):
    elapsed = 0.0
    prev_ts = time.time()
    while elapsed < seconds:
        now = time.time()
        if not state.renderer.paused:
            elapsed += now - prev_ts
        prev_ts = now
        state.renderer.redraw()
        if pump(state):
            raise _RestartSignal()
        state.clock.tick(60)


# ──────────────────────────────────────────────
# POINT FADE-IN
# ──────────────────────────────────────────────

def add_points_fade(state, pts, depth=0.0, stagger=0.06):
    base_idx = len(state.done_points)
    for pt in pts:
        state.done_points.append([pt[0], pt[1], 0, depth])

    idxs   = list(range(base_idx, base_idx + len(pts)))
    # Each point gets its own elapsed counter (independent of wall clock when paused)
    timers = [-(i * stagger) for i in range(len(pts))]   # negative = not started yet
    flags  = [False] * len(pts)
    dur    = state.point_fade
    prev_ts = time.time()

    while not all(flags):
        now  = time.time()
        dt   = (now - prev_ts) if not state.renderer.paused else 0.0
        prev_ts = now
        for i, idx in enumerate(idxs):
            if flags[i]:
                continue
            timers[i] += dt
            if timers[i] < 0:
                continue
            raw = min(timers[i] / dur, 1.0)
            state.done_points[idx][2] = round(ease_in_out(raw) * 255)
            if raw >= 1.0:
                flags[i] = True
        state.renderer.redraw()
        if pump(state):
            raise _RestartSignal()
        state.clock.tick(60)


# ──────────────────────────────────────────────
# DRAW ALL PAIRS
# ──────────────────────────────────────────────

def draw_all_pairs(state, points, depth=0.0, origin=None):
    for p1, p2 in all_pairs(points):
        c, r = circle_from_points(p1, p2)
        animate_circle(state, c, r, depth=depth, from_point=p1, origin=origin)
        pump(state)


# ──────────────────────────────────────────────
# RESTART SIGNAL
# ──────────────────────────────────────────────

class _RestartSignal(Exception):
    """Raised internally to unwind the call stack on restart."""
    pass

# Re-export so main.py can catch it
RestartSignal = _RestartSignal