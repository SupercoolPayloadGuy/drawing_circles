"""
main.py — entry point.

Run with:  python main.py
           python main.py --points 6
           python main.py -p 8

Controls during animation:
  P or pause button    — pause / resume
  B                    — toggle dark/light theme
  scroll               — zoom in / out
  ↺ RESTART button     — restart after animation finishes

File layout:
  main.py       ← orchestration, construction stages
  geometry.py   ← pure math
  renderer.py   ← pygame drawing, camera, UI buttons
  animation.py  ← animate_circle, pause, add_points_fade, draw_all_pairs
  intro.py      ← animated level-select screen
"""

import argparse
import pygame

from geometry  import (cardinal_points, circle_from_points, midpoint,
                       farthest_extent, project_onto_ring, deduplicate)
from renderer  import Renderer, Camera
from animation import AnimState, animate_circle, pause, add_points_fade, \
                      draw_all_pairs, pump, RestartSignal
from intro     import run_intro


# ──────────────────────────────────────────────
# WINDOW
# ──────────────────────────────────────────────

WIDTH  = 1200
HEIGHT = 1200
BASE_RADIUS = 140

PAUSE_BETWEEN = 0.06
STAGE_PAUSE   = 0.28


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Circle Construction")
parser.add_argument("-p", "--points", type=int, default=0,
                    help="Number of base points (overrides intro selection)")
CLI_POINTS = parser.parse_args().points


# ──────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()


# ──────────────────────────────────────────────
# CONSTRUCTION  (wrapped in a function so restart works)
# ──────────────────────────────────────────────

def run_construction(level, screen, clock, point_count=4):
    """
    Build the circle construction up to `level` using `point_count` base
    points evenly spaced around the circle.
    Returns normally when finished.
    Raises RestartSignal if the user clicks Restart.
    """
    WORLD_CENTER = (WIDTH / 2, HEIGHT / 2)
    camera   = Camera(WIDTH, HEIGHT, WORLD_CENTER)
    renderer = Renderer(screen, camera, level)
    renderer.animation_done = False

    pygame.display.set_caption(
        f"Circle Construction  •  Level {level}  •  {point_count} pts  •  "
        f"[P] pause  [B] theme  [scroll] zoom")

    state = AnimState(renderer, clock, level)
    A     = WORLD_CENTER

    # ── shortcuts ────────────────────────────

    def ac(center, radius, depth=0.0, from_point=None):
        animate_circle(state, center, radius, depth=depth,
                       from_point=from_point, origin=A)

    def wp(seconds):
        pause(state, seconds)

    def apf(pts, depth=0.0, stagger=0.06):
        add_points_fade(state, pts, depth=depth, stagger=stagger)

    def dap(points, depth=0.0):
        draw_all_pairs(state, points, depth=depth, origin=A)

    # ── Level 1 ──────────────────────────────
    # depth = 0.0  (innermost)

    renderer.redraw()
    wp(0.3)

    outer = cardinal_points(A, BASE_RADIUS, count=point_count)

    ac(A, BASE_RADIUS, depth=0.0, from_point=outer[0])
    wp(STAGE_PAUSE)

    apf([A] + outer, depth=0.0, stagger=0.07)
    wp(STAGE_PAUSE)

    for pt in outer:
        c, r = circle_from_points(A, pt)
        ac(c, r, depth=0.0, from_point=A)
        wp(PAUSE_BETWEEN)

    wp(STAGE_PAUSE)

    dap(outer, depth=0.0)
    wp(STAGE_PAUSE)

    if level == 1:
        _idle(state, renderer, clock)
        return

    # ── Level 2 ──────────────────────────────
    # depth = 1.0  (first outer ring)

    R1 = farthest_extent(A, [(c, r) for c, r, _ in state.done_circles])
    ac(A, R1, depth=1.0)
    wp(STAGE_PAUSE)

    inner_mids = [midpoint(A, pt) for pt in outer]
    projected1 = project_onto_ring(inner_mids, A, R1)
    apf(projected1, depth=1.0, stagger=0.07)
    wp(STAGE_PAUSE)

    all_pts = [A] + projected1 + outer
    dap(all_pts, depth=1.0)
    wp(STAGE_PAUSE)

    R2 = farthest_extent(A, [(c, r) for c, r, _ in state.done_circles])
    ac(A, R2, depth=1.0)
    wp(STAGE_PAUSE)

    if level == 2:
        _idle(state, renderer, clock)
        return

    # ── Level 3+ ─────────────────────────────

    current_ring_radius = R2
    current_points      = list(all_pts)
    max_depth_val       = float(level - 1)   # so last level maps to depth=1

    for lvl in range(3, level + 1):
        dep     = (lvl - 1) / max_depth_val   # 0 … 1 across levels

        new_proj = project_onto_ring(current_points, A, current_ring_radius)
        new_proj = deduplicate(new_proj, snap=1)

        stagger = max(0.005, 0.06 / (lvl - 1))
        apf(new_proj, depth=dep, stagger=stagger)
        wp(STAGE_PAUSE)

        current_points = current_points + new_proj
        dap(current_points, depth=dep)
        wp(STAGE_PAUSE)

        current_ring_radius = farthest_extent(
            A, [(c, r) for c, r, _ in state.done_circles])
        ac(A, current_ring_radius, depth=dep)
        wp(STAGE_PAUSE)

    # ── done ─────────────────────────────────
    _idle(state, renderer, clock)


def _idle(state, renderer, clock):
    """Spin in the idle loop; show restart button; raise RestartSignal on click."""
    renderer.animation_done = True
    while True:
        renderer.redraw()
        if pump(state):
            raise RestartSignal()
        clock.tick(30)


# ──────────────────────────────────────────────
# MAIN LOOP  (restart wraps everything)
# ──────────────────────────────────────────────

while True:
    level, pts = run_intro(screen, clock)
    if CLI_POINTS:
        pts = CLI_POINTS
    try:
        run_construction(level, screen, clock, point_count=pts)
    except RestartSignal:
        # Loop back to intro
        continue