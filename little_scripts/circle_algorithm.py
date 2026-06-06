import pygame
import math
import itertools
import time
import sys

# ==================================================
# LEVEL PROMPT
# ==================================================

def ask_level():
    while True:
        try:
            raw = input("Level (1 = base, 2 = default, 3+ = more): ").strip()
            n = int(raw)
            if n >= 1:
                return n
            print("Please enter a positive integer.")
        except ValueError:
            print("Please enter a number.")

LEVEL = ask_level()

# ==================================================
# SETTINGS
# ==================================================

WIDTH  = 1200
HEIGHT = 1200

BASE_RADIUS = 140

# Draw duration scales down with level so it stays watchable
# L1: 0.28s, L2: 0.22s, L3: 0.14s, L4+: 0.07s
_durations   = {1: 0.28, 2: 0.22, 3: 0.14}
DRAW_DURATION = _durations.get(LEVEL, 0.07)

PAUSE_BETWEEN  = 0.06
STAGE_PAUSE    = 0.28
POINT_FADE_DUR = 0.38

# ==================================================
# THEME
# ==================================================

DARK_THEME = {
    "background": (10, 10, 10),
    "circle":     (200, 200, 200),
    "point":      (255, 220, 50),
    "toggle_bg":  (30, 30, 30),
    "toggle_fg":  (200, 200, 200),
    "label":      "DARK",
}

LIGHT_THEME = {
    "background": (245, 245, 242),
    "circle":     (40, 40, 40),
    "point":      (20, 20, 200),
    "toggle_bg":  (220, 220, 215),
    "toggle_fg":  (40, 40, 40),
    "label":      "LIGHT",
}

theme = DARK_THEME

# ==================================================
# PYGAME INIT
# ==================================================

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Circle Construction  •  Level {LEVEL}  •  B = toggle theme")
font   = pygame.font.SysFont("monospace", 16)

CENTER = (WIDTH // 2, HEIGHT // 2)
clock  = pygame.time.Clock()

# ==================================================
# STATE
# ==================================================

done_circles = []           # list of (center, radius)
done_points  = []           # list of [x, y, alpha 0-255]
known_points = []           # plain (x,y) tuples — geometry only

anim_circle    = None
anim_t         = 0.0
anim_start_ang = -math.pi / 2

# ==================================================
# TOGGLE BUTTON
# ==================================================

TOGGLE_RECT = pygame.Rect(WIDTH - 140, 20, 120, 36)

def draw_toggle():
    bg = theme["toggle_bg"]
    fg = theme["toggle_fg"]
    pygame.draw.rect(screen, bg, TOGGLE_RECT, border_radius=8)
    pygame.draw.rect(screen, fg, TOGGLE_RECT, 1, border_radius=8)
    lbl = font.render(f"[B]  {theme['label']}", True, fg)
    screen.blit(lbl, (TOGGLE_RECT.x + 10, TOGGLE_RECT.y + 10))

def draw_level_label():
    lbl = font.render(f"LEVEL {LEVEL}", True, theme["toggle_fg"])
    screen.blit(lbl, (20, 20))

# ==================================================
# DRAW HELPERS
# ==================================================

def lerp_color(c, alpha):
    s = alpha / 255
    return (round(c[0]*s), round(c[1]*s), round(c[2]*s))

def draw_arc(center, radius, start_angle, sweep, color):
    r = round(radius)
    if r < 1 or sweep <= 0:
        return
    n_segs = max(8, round(180 * sweep))
    end_a  = start_angle + 2 * math.pi * sweep
    prev   = None
    for i in range(n_segs + 1):
        a  = start_angle + (end_a - start_angle) * i / n_segs
        px = center[0] + r * math.cos(a)
        py = center[1] + r * math.sin(a)
        if prev:
            pygame.draw.line(screen, color, prev, (round(px), round(py)), 1)
        prev = (round(px), round(py))

def redraw():
    screen.fill(theme["background"])

    for center, radius in done_circles:
        if radius < 1:
            continue
        pygame.draw.circle(
            screen, theme["circle"],
            (round(center[0]), round(center[1])),
            round(radius), 1
        )

    if anim_circle and anim_t > 0:
        draw_arc(anim_circle[0], anim_circle[1], anim_start_ang, anim_t, theme["circle"])

    pc = theme["point"]
    for (px, py, alpha) in done_points:
        pygame.draw.circle(screen, lerp_color(pc, alpha), (round(px), round(py)), 5)

    draw_toggle()
    draw_level_label()
    pygame.display.flip()

# ==================================================
# EVENT PUMP
# ==================================================

def pump():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_b, pygame.K_SPACE):
                toggle_theme()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if TOGGLE_RECT.collidepoint(event.pos):
                toggle_theme()

def toggle_theme():
    global theme
    theme = LIGHT_THEME if theme is DARK_THEME else DARK_THEME
    redraw()

# ==================================================
# GEOMETRY
# ==================================================

def midpoint(a, b):
    return ((a[0]+b[0])/2, (a[1]+b[1])/2)

def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def circle_from_points(a, b):
    return midpoint(a, b), distance(a, b) / 2

def angle_on_circle(center, point):
    return math.atan2(point[1]-center[1], point[0]-center[0])

def farthest_extent(origin):
    """Radius of the smallest circle centred on origin that encloses all drawn circles."""
    best = 0.0
    for center, radius in done_circles:
        best = max(best, distance(origin, center) + radius)
    return best

def project_onto_ring(points, origin, ring_radius):
    """Project each point outward from origin onto a circle of ring_radius."""
    result = []
    for p in points:
        dx, dy = p[0]-origin[0], p[1]-origin[1]
        ang = math.atan2(dy, dx)
        result.append((
            origin[0] + ring_radius * math.cos(ang),
            origin[1] + ring_radius * math.sin(ang),
        ))
    return result

def pts_xy(pts_list):
    """Strip alpha from done_points entries to get plain (x,y)."""
    return [(p[0], p[1]) for p in pts_list]

# ==================================================
# ANIMATION PRIMITIVES
# ==================================================

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def animate_circle(center, radius, from_point=None, duration=None):
    global anim_circle, anim_t, anim_start_ang
    if duration is None:
        duration = DRAW_DURATION

    anim_start_ang = (angle_on_circle(center, from_point)
                      if from_point is not None else -math.pi / 2)
    anim_circle = (center, radius)
    start = time.time()
    while True:
        elapsed = time.time() - start
        raw = min(elapsed / duration, 1.0)
        anim_t = ease_in_out(raw)
        redraw()
        pump()
        clock.tick(60)
        if raw >= 1.0:
            break
    done_circles.append((center, radius))
    anim_circle = None
    anim_t = 0.0

def pause(seconds):
    end = time.time() + seconds
    while time.time() < end:
        redraw()
        pump()
        clock.tick(60)

def add_points_fade(pts, stagger=0.06):
    for pt in pts:
        done_points.append([pt[0], pt[1], 0])
        known_points.append((pt[0], pt[1]))

    idxs   = list(range(len(done_points) - len(pts), len(done_points)))
    starts = [time.time() + i * stagger for i in range(len(pts))]
    flags  = [False] * len(pts)

    while not all(flags):
        now = time.time()
        for i, idx in enumerate(idxs):
            if flags[i]:
                continue
            elapsed = now - starts[i]
            if elapsed < 0:
                continue
            raw = min(elapsed / POINT_FADE_DUR, 1.0)
            done_points[idx][2] = round(ease_in_out(raw) * 255)
            if raw >= 1.0:
                flags[i] = True
        redraw()
        pump()
        clock.tick(60)

def draw_all_pairs(points):
    """Animate a circle for every pair of points."""
    for p1, p2 in itertools.combinations(points, 2):
        c, r = circle_from_points(p1, p2)
        animate_circle(c, r, from_point=p1)
        pump()

# ==================================================
# BASE GEOMETRY
# ==================================================

A = CENTER

cardinal_angles = [-math.pi/2, 0, math.pi/2, math.pi]
outer = []
for ang in cardinal_angles:
    outer.append((A[0] + BASE_RADIUS * math.cos(ang),
                  A[1] + BASE_RADIUS * math.sin(ang)))

TOP, RIGHT, BOTTOM, LEFT = outer

# ==================================================
# LEVEL 1  —  base circle + cardinal points + inner pair circles
# ==================================================

redraw()
pause(0.3)

# Original circle
animate_circle(A, BASE_RADIUS, from_point=outer[0])
pause(STAGE_PAUSE)

# Mark center + cardinal points
add_points_fade([A] + outer, stagger=0.07)
pause(STAGE_PAUSE)

# Center → cardinal circles
for p in [TOP, BOTTOM]:
    c, r = circle_from_points(A, p)
    animate_circle(c, r, from_point=A)
    pause(PAUSE_BETWEEN)

pause(PAUSE_BETWEEN)

for p in [LEFT, RIGHT]:
    c, r = circle_from_points(A, p)
    animate_circle(c, r, from_point=A)
    pause(PAUSE_BETWEEN)

pause(STAGE_PAUSE)

# Outer adjacent-pair circles
pairs_l1 = [
    (TOP, RIGHT), (BOTTOM, LEFT),
    (TOP, LEFT),  (BOTTOM, RIGHT),
    (TOP, BOTTOM),(LEFT, RIGHT),
]
for i in range(0, len(pairs_l1), 2):
    for p1, p2 in pairs_l1[i:i+2]:
        c, r = circle_from_points(p1, p2)
        animate_circle(c, r, from_point=p1)
        pause(PAUSE_BETWEEN)
    pause(PAUSE_BETWEEN)

pause(STAGE_PAUSE)

if LEVEL == 1:
    # Done — just idle
    while True:
        redraw(); pump(); clock.tick(30)

# ==================================================
# LEVEL 2  —  first enclosing ring + projected points + all-pairs
# ==================================================

# Enclosing circle #1
R1 = farthest_extent(A)
animate_circle(A, R1, from_point=None)
pause(STAGE_PAUSE)

# Project inner midpoints onto the enclosing ring
inner_mids = [midpoint(A, p) for p in outer]
projected1 = project_onto_ring(inner_mids, A, R1)
add_points_fade(projected1, stagger=0.07)
pause(STAGE_PAUSE)

# All pairwise circles from the full 9-point set
all_pts = [A] + projected1 + outer
draw_all_pairs(all_pts)
pause(STAGE_PAUSE)

# Final enclosing circle for level 2
R2 = farthest_extent(A)
animate_circle(A, R2, from_point=None)
pause(STAGE_PAUSE)

if LEVEL == 2:
    while True:
        redraw(); pump(); clock.tick(30)

# ==================================================
# LEVEL 3+  —  each additional level repeats the ring expansion
# ==================================================

current_ring_radius = R2
current_points      = list(all_pts)   # accumulate all known geometry points

for lvl in range(3, LEVEL + 1):

    # Project ALL current points outward onto the new enclosing ring
    new_projected = project_onto_ring(current_points, A, current_ring_radius)

    # Deduplicate (snap to 1px grid to catch near-duplicates)
    seen = set()
    unique_new = []
    for p in new_projected:
        key = (round(p[0]), round(p[1]))
        if key not in seen:
            seen.add(key)
            unique_new.append(p)

    add_points_fade(unique_new, stagger=max(0.01, 0.06 / (lvl - 1)))
    pause(STAGE_PAUSE)

    # Grow the combined point set
    current_points = current_points + unique_new

    # Draw all pairwise circles from ALL accumulated points
    draw_all_pairs(current_points)
    pause(STAGE_PAUSE)

    # New enclosing circle
    current_ring_radius = farthest_extent(A)
    animate_circle(A, current_ring_radius, from_point=None)
    pause(STAGE_PAUSE)

# ==================================================
# IDLE LOOP
# ==================================================

while True:
    redraw()
    pump()
    clock.tick(30)