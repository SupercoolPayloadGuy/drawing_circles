"""
construction.py — circle construction stages (levels 1–N).

Extracted from main.py so that main.py is a thin entry point.
"""

import pygame

from geometry import (
    cardinal_points, circle_from_points, midpoint,
    farthest_extent, project_onto_ring, deduplicate,
)
from renderer import Renderer, Camera
from animation import AnimState, animate_circle, pause, add_points_fade, \
    draw_all_pairs, pump, RestartSignal
from config import Config


WIDTH  = 1200
HEIGHT = 1200

_PAUSE = 0.06
_STAGE = 0.28


def run(cfg: Config, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    """
    Animate the circle construction using the given Config.
    Returns normally on completion. Raises RestartSignal on menu return.
    """
    origin   = (WIDTH / 2, HEIGHT / 2)
    camera   = Camera(WIDTH, HEIGHT, origin)
    renderer = Renderer(screen, camera, cfg)
    renderer.animation_done = False

    pygame.display.set_caption(
        f"Circle Construction  •  Level {cfg.level}  •  {cfg.point_count} pts  •  "
        f"[P] pause  [B] theme  [[ ]] speed  [scroll] zoom"
    )

    state           = AnimState(renderer, clock, cfg.level)
    state.speed_mul = cfg.speed

    _build(state, renderer, origin, cfg)
    _idle(state, renderer, clock)


# ──────────────────────────────────────────────
# STAGE BUILDER
# ──────────────────────────────────────────────

def _build(state, renderer, origin, cfg):
    A           = origin
    level       = cfg.level
    point_count = cfg.point_count
    base_radius = cfg.base_radius

    def ac(center, radius, depth=0.0, from_point=None):
        animate_circle(state, center, radius, depth=depth,
                       from_point=from_point, origin=A)

    def wp(seconds):
        pause(state, seconds)

    def apf(pts, depth=0.0, stagger=0.06):
        add_points_fade(state, pts, depth=depth, stagger=stagger)

    def dap(points, depth=0.0):
        draw_all_pairs(state, points, depth=depth, origin=A)

    def extent():
        return farthest_extent(A, [(c, r) for c, r, _ in state.done_circles])

    # ── Level 1 ──────────────────────────────────────────────────────────────

    renderer.redraw()
    wp(0.3)

    outer = cardinal_points(A, base_radius, count=point_count)

    ac(A, base_radius, depth=0.0, from_point=outer[0])
    wp(_STAGE)

    apf([A] + outer, depth=0.0, stagger=0.07)
    wp(_STAGE)

    for pt in outer:
        c, r = circle_from_points(A, pt)
        ac(c, r, depth=0.0, from_point=A)
        wp(_PAUSE)

    wp(_STAGE)
    dap(outer, depth=0.0)
    wp(_STAGE)

    if level == 1:
        return

    # ── Level 2 ──────────────────────────────────────────────────────────────

    lvl2_dep = 1.0 / (level - 1) if level > 2 else 1.0

    R1 = extent()
    ac(A, R1, depth=lvl2_dep)
    wp(_STAGE)

    inner_mids  = [midpoint(A, pt) for pt in outer]
    projected1  = project_onto_ring(inner_mids, A, R1)
    apf(projected1, depth=lvl2_dep, stagger=0.07)
    wp(_STAGE)

    all_pts = [A] + projected1 + outer
    dap(all_pts, depth=lvl2_dep)
    wp(_STAGE)

    R2 = extent()
    ac(A, R2, depth=lvl2_dep)
    wp(_STAGE)

    if level == 2:
        return

    # ── Level 3+ ─────────────────────────────────────────────────────────────

    ring_r      = R2
    cur_pts     = list(all_pts)
    max_dep     = float(level - 1)   # normalise depth so last level → 1.0

    for lvl in range(3, level + 1):
        dep     = (lvl - 1) / max_dep
        stagger = max(0.005, 0.06 / (lvl - 1))

        new_proj = deduplicate(project_onto_ring(cur_pts, A, ring_r), snap=1)
        apf(new_proj, depth=dep, stagger=stagger)
        wp(_STAGE)

        cur_pts = cur_pts + new_proj
        dap(cur_pts, depth=dep)
        wp(_STAGE)

        ring_r = extent()
        ac(A, ring_r, depth=dep)
        wp(_STAGE)


# ──────────────────────────────────────────────
# IDLE LOOP
# ──────────────────────────────────────────────

def _idle(state, renderer, clock):
    renderer.animation_done = True
    renderer.show_choices   = True
    while True:
        renderer.redraw()
        if pump(state):
            raise RestartSignal()
        clock.tick(30)