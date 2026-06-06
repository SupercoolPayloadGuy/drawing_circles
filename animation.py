"""
animation.py — timing, easing, pause/play, animated circle drawing,
               point fade-in, auto-zoom, draw_all_pairs.
"""

import math
import time
import pygame

from geometry import angle_on_circle, farthest_extent, circle_from_points, all_pairs
from renderer import RESTART_EVENT


# ──────────────────────────────────────────────
# EASING & DURATION
# ──────────────────────────────────────────────

def ease_in_out(t):
    return t * t * (3 - 2 * t)


def draw_duration(level):
    """Hyperbolic scaling: fast at high levels, never below floor."""
    return max(0.025, 0.30 / (1.0 + 0.35 * (level - 1)))


# ──────────────────────────────────────────────
# SHARED STATE
# ──────────────────────────────────────────────

class AnimState:
    _BASE_DURATION = None   # set from level in __init__

    SPEED_MIN  = 0.25
    SPEED_MAX  = 8.0
    SPEED_STEP = 0.25

    def __init__(self, renderer, clock, level):
        self.renderer      = renderer
        self.clock         = clock
        self._base_dur     = draw_duration(level)
        self.speed_mul     = 1.0          # user-adjustable via [ / ]
        self.point_fade    = 0.38
        # Same list objects as renderer — mutations reflected immediately.
        self.done_circles  = renderer.done_circles
        self.done_points   = renderer.done_points

    @property
    def draw_duration(self):
        return self._base_dur / self.speed_mul


# ──────────────────────────────────────────────
# EVENT PUMP
# ──────────────────────────────────────────────

def pump(state):
    """Process events; return True if a restart was requested."""
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
            return True

    return False


# ──────────────────────────────────────────────
# AUTO-ZOOM
# ──────────────────────────────────────────────

def _auto_zoom(state, origin):
    extent = farthest_extent(origin, [(c, r) for c, r, _ in state.done_circles])
    if extent > 0:
        state.renderer.camera.fit_radius(extent, 0.88)


# ──────────────────────────────────────────────
# ANIMATE CIRCLE
# ──────────────────────────────────────────────

def animate_circle(state, center, radius, depth=0.0, from_point=None, origin=None):
    r = state.renderer
    r.anim_circle    = (center, radius, depth)
    r.anim_t         = 0.0
    r.anim_start_ang = (angle_on_circle(center, from_point)
                        if from_point is not None else -math.pi / 2)

    draw_t  = 0.0
    prev_ts = time.time()

    while True:
        now = time.time()
        if not r.paused:
            draw_t += now - prev_ts
        prev_ts = now

        raw      = min(draw_t / state.draw_duration, 1.0)
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
        _auto_zoom(state, origin)


# ──────────────────────────────────────────────
# PAUSE
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

    n       = len(pts)
    timers  = [-(i * stagger) for i in range(n)]
    flags   = [False] * n
    dur     = state.point_fade
    prev_ts = time.time()

    while not all(flags):
        now  = time.time()
        dt   = (now - prev_ts) if not state.renderer.paused else 0.0
        prev_ts = now

        for i in range(n):
            if flags[i]:
                continue
            timers[i] += dt
            if timers[i] < 0:
                continue
            raw = min(timers[i] / dur, 1.0)
            state.done_points[base_idx + i][2] = round(ease_in_out(raw) * 255)
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
    pass

RestartSignal = _RestartSignal