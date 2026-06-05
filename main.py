"""
main.py — entry point.

Runs the intro screen, then orchestrates the circle construction
through the requested number of levels.

File layout:
  main.py        ← you are here
  geometry.py    ← pure math helpers
  renderer.py    ← pygame drawing + camera
  animation.py   ← animate_circle, pause, add_points_fade, draw_all_pairs
  intro.py       ← animated level-select screen
"""

import pygame

from geometry  import (cardinal_points, circle_from_points, midpoint,
                       farthest_extent, project_onto_ring, deduplicate)
from renderer  import Renderer, Camera
from animation import AnimState, animate_circle, pause, add_points_fade, draw_all_pairs, pump
from intro     import run_intro


# ──────────────────────────────────────────────
# SETTINGS
# ──────────────────────────────────────────────

WIDTH       = 1200
HEIGHT      = 1200
BASE_RADIUS = 140

# Draw speed per level (seconds per circle).  Scales down so higher levels
# remain watchable despite exponentially more circles.
_DUR = {1: 0.28, 2: 0.22, 3: 0.14, 4: 0.08}
def draw_duration(level):
    return _DUR.get(level, 0.05)

PAUSE_BETWEEN  = 0.06
STAGE_PAUSE    = 0.28
POINT_FADE_DUR = 0.38


# ──────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()

# ── Intro / level select ──────────────────────
LEVEL = run_intro(screen, clock)

# ── Renderer + camera ────────────────────────
WORLD_CENTER = (WIDTH / 2, HEIGHT / 2)
camera   = Camera(WIDTH, HEIGHT, WORLD_CENTER)
renderer = Renderer(screen, camera, LEVEL)

pygame.display.set_caption(
    f"Circle Construction  •  Level {LEVEL}  •  B = theme  •  scroll = zoom")

# ── Animation state ──────────────────────────
state = AnimState(
    renderer       = renderer,
    clock          = clock,
    draw_duration  = draw_duration(LEVEL),
    pause_between  = PAUSE_BETWEEN,
    stage_pause    = STAGE_PAUSE,
    point_fade_dur = POINT_FADE_DUR,
)

A = WORLD_CENTER   # origin / world centre


# ──────────────────────────────────────────────
# CONVENIENCE WRAPPERS  (pass origin for auto-zoom)
# ──────────────────────────────────────────────

def ac(center, radius, from_point=None):
    animate_circle(state, center, radius, from_point=from_point, origin=A)

def p(seconds):
    pause(state, seconds)

def apf(pts, stagger=0.06):
    add_points_fade(state, pts, stagger=stagger)

def dap(points):
    draw_all_pairs(state, points, origin=A)


# ──────────────────────────────────────────────
# LEVEL 1  —  base circle, cardinal points, inner pair circles
# ──────────────────────────────────────────────

renderer.redraw()
p(0.3)

outer = cardinal_points(A, BASE_RADIUS)
TOP, RIGHT, BOTTOM, LEFT = outer

# Original circle
ac(A, BASE_RADIUS, from_point=TOP)
p(STAGE_PAUSE)

# Mark center + cardinal points
apf([A] + outer, stagger=0.07)
p(STAGE_PAUSE)

# Center → cardinal circles
for pt in [TOP, BOTTOM]:
    c, r = circle_from_points(A, pt)
    ac(c, r, from_point=A)
    p(PAUSE_BETWEEN)

p(PAUSE_BETWEEN)

for pt in [LEFT, RIGHT]:
    c, r = circle_from_points(A, pt)
    ac(c, r, from_point=A)
    p(PAUSE_BETWEEN)

p(STAGE_PAUSE)

# Outer adjacent-pair circles
pairs_l1 = [
    (TOP, RIGHT), (BOTTOM, LEFT),
    (TOP, LEFT),  (BOTTOM, RIGHT),
    (TOP, BOTTOM),(LEFT, RIGHT),
]
for i in range(0, len(pairs_l1), 2):
    for p1, p2 in pairs_l1[i:i+2]:
        c, r = circle_from_points(p1, p2)
        ac(c, r, from_point=p1)
        p(PAUSE_BETWEEN)
    p(PAUSE_BETWEEN)

p(STAGE_PAUSE)

if LEVEL == 1:
    while True:
        renderer.redraw()
        pump(state)
        clock.tick(30)


# ──────────────────────────────────────────────
# LEVEL 2  —  first enclosing ring, projected points, all-pairs
# ──────────────────────────────────────────────

R1 = farthest_extent(A, state.done_circles)
ac(A, R1)
p(STAGE_PAUSE)

inner_mids = [midpoint(A, pt) for pt in outer]
projected1 = project_onto_ring(inner_mids, A, R1)
apf(projected1, stagger=0.07)
p(STAGE_PAUSE)

all_pts = [A] + projected1 + outer
dap(all_pts)
p(STAGE_PAUSE)

R2 = farthest_extent(A, state.done_circles)
ac(A, R2)
p(STAGE_PAUSE)

if LEVEL == 2:
    while True:
        renderer.redraw()
        pump(state)
        clock.tick(30)


# ──────────────────────────────────────────────
# LEVEL 3+  —  recursive ring expansions
# ──────────────────────────────────────────────

current_ring_radius = R2
current_points      = list(all_pts)

for lvl in range(3, LEVEL + 1):

    new_proj = project_onto_ring(current_points, A, current_ring_radius)
    new_proj = deduplicate(new_proj, snap=1)

    stagger = max(0.01, 0.06 / (lvl - 1))
    apf(new_proj, stagger=stagger)
    p(STAGE_PAUSE)

    current_points = current_points + new_proj

    dap(current_points)
    p(STAGE_PAUSE)

    current_ring_radius = farthest_extent(A, state.done_circles)
    ac(A, current_ring_radius)
    p(STAGE_PAUSE)


# ──────────────────────────────────────────────
# IDLE LOOP  —  scroll to zoom, B to toggle theme
# ──────────────────────────────────────────────

while True:
    renderer.redraw()
    pump(state)
    clock.tick(30)