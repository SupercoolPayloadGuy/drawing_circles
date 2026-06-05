import pygame
import math
import itertools
import time

# ==================================================
# SETTINGS
# ==================================================

WIDTH  = 1200
HEIGHT = 1200

BASE_RADIUS = 140

# Animation speed: seconds for each circle to be drawn
DRAW_DURATION = 0.28   # per circle (uniform for all stages)
PAUSE_BETWEEN = 0.08   # gap between circles in the same stage
STAGE_PAUSE   = 0.30   # gap between stages

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

theme = DARK_THEME   # start dark

# ==================================================
# PYGAME INIT
# ==================================================

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circle Construction  •  B / Space = toggle theme")
font = pygame.font.SysFont("monospace", 16)

CENTER = (WIDTH // 2, HEIGHT // 2)
clock  = pygame.time.Clock()

# ==================================================
# STATE
# ==================================================

done_circles = []   # list of (center, radius)
done_points  = []   # list of (x, y)

# Currently animating circle: drawn arc progress 0‥1
anim_circle  = None   # (center, radius)
anim_t       = 0.0

# ==================================================
# DRAWING
# ==================================================

TOGGLE_RECT = pygame.Rect(WIDTH - 140, 20, 120, 36)

def draw_toggle():
    bg  = theme["toggle_bg"]
    fg  = theme["toggle_fg"]
    pygame.draw.rect(screen, bg, TOGGLE_RECT, border_radius=8)
    pygame.draw.rect(screen, fg, TOGGLE_RECT, 1, border_radius=8)
    label = font.render(f"[B]  {theme['label']}", True, fg)
    screen.blit(label, (TOGGLE_RECT.x + 10, TOGGLE_RECT.y + 10))

def redraw(extra_circle=None, extra_t=1.0):
    screen.fill(theme["background"])

    # Completed circles
    for center, radius in done_circles:
        if radius < 1:
            continue
        pygame.draw.circle(
            screen, theme["circle"],
            (round(center[0]), round(center[1])),
            round(radius), 1
        )

    # Partially drawn animating circle
    c = extra_circle or anim_circle
    t = extra_t      if extra_circle else anim_t
    if c and t > 0:
        cx, cy = c[0], c[1]
        r = round(c[1]) if isinstance(c, tuple) and len(c) == 2 and not hasattr(c[0], '__len__') else None
        # unpack properly
        center2, radius2 = c
        r2 = round(radius2)
        if r2 >= 1:
            # draw arc as many short line segments
            n_segs = max(12, round(120 * t))
            end_angle = -math.pi/2 + 2 * math.pi * t   # start from top
            start_angle = -math.pi/2
            prev = None
            for i in range(n_segs + 1):
                a = start_angle + (end_angle - start_angle) * i / n_segs
                px = center2[0] + r2 * math.cos(a)
                py = center2[1] + r2 * math.sin(a)
                if prev:
                    pygame.draw.line(screen, theme["circle"], prev, (round(px), round(py)), 1)
                prev = (round(px), round(py))

    # Points (on top)
    for pt in done_points:
        pygame.draw.circle(screen, theme["point"],
                           (round(pt[0]), round(pt[1])), 5)

    draw_toggle()
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
# ANIMATED CIRCLE
# ==================================================

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def animate_circle(center, radius, duration=DRAW_DURATION):
    global anim_circle, anim_t
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

def add_point(pt):
    done_points.append(pt)
    redraw()
    pump()

# ==================================================
# GEOMETRY HELPERS
# ==================================================

def midpoint(a, b):
    return ((a[0]+b[0])/2, (a[1]+b[1])/2)

def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def circle_from_points(a, b):
    return midpoint(a, b), distance(a, b)/2

# ==================================================
# BASE GEOMETRY
# ==================================================

A = CENTER

angles = [-math.pi/2, 0, math.pi/2, math.pi]
outer  = []
for ang in angles:
    outer.append((A[0] + BASE_RADIUS*math.cos(ang),
                  A[1] + BASE_RADIUS*math.sin(ang)))

TOP, RIGHT, BOTTOM, LEFT = outer

# ==================================================
# CONSTRUCTION STAGES
# ==================================================

# ── Stage 1: original circle
redraw()
pause(0.3)
animate_circle(A, BASE_RADIUS)
pause(STAGE_PAUSE)

# ── Stage 2: mark points
add_point(A)
for p in outer:
    add_point(p)
pause(STAGE_PAUSE)

# ── Stage 3: center→outer circles (vertical then horizontal)
for p in [TOP, BOTTOM]:
    c, r = circle_from_points(A, p)
    animate_circle(c, r)
    pause(PAUSE_BETWEEN)

pause(PAUSE_BETWEEN)

for p in [LEFT, RIGHT]:
    c, r = circle_from_points(A, p)
    animate_circle(c, r)
    pause(PAUSE_BETWEEN)

pause(STAGE_PAUSE)

# ── Stage 4: outer pair circles
pairs = [
    (TOP, RIGHT), (BOTTOM, LEFT),
    (TOP, LEFT),  (BOTTOM, RIGHT),
    (TOP, BOTTOM),(LEFT, RIGHT),
]

for i in range(0, len(pairs), 2):
    for p1, p2 in pairs[i:i+2]:
        c, r = circle_from_points(p1, p2)
        animate_circle(c, r)
        pause(PAUSE_BETWEEN)
    pause(PAUSE_BETWEEN)

pause(STAGE_PAUSE)

# ── Enclosing circle #1
max_extent = BASE_RADIUS
for center, radius in done_circles:
    extent = distance(A, center) + radius
    if extent > max_extent:
        max_extent = extent

FIRST_OUTER_RADIUS = max_extent
animate_circle(A, FIRST_OUTER_RADIUS)
pause(STAGE_PAUSE)

# ── Level-1 projected points
inner_midpoints = [midpoint(A, p) for p in outer]
projected = []
for p in inner_midpoints:
    dx, dy = p[0]-A[0], p[1]-A[1]
    angle = math.atan2(dy, dx)
    projected.append((
        A[0] + FIRST_OUTER_RADIUS * math.cos(angle),
        A[1] + FIRST_OUTER_RADIUS * math.sin(angle),
    ))

for p in projected:
    add_point(p)

pause(STAGE_PAUSE)

# ── All 9 points → all circle pairs
all_points = [A] + projected + outer
all_pairs  = list(itertools.combinations(all_points, 2))

for p1, p2 in all_pairs:
    c, r = circle_from_points(p1, p2)
    animate_circle(c, r)
    # tiny gap
    pump()

pause(STAGE_PAUSE)

# ── Final enclosing circle
max_extent2 = 0
for center, radius in done_circles:
    extent = distance(A, center) + radius
    if extent > max_extent2:
        max_extent2 = extent

animate_circle(A, max_extent2)

# ==================================================
# IDLE LOOP
# ==================================================

while True:
    redraw()
    pump()
    clock.tick(30)