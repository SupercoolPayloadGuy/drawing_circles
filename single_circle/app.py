"""
app.py — animation state machine and main loop for single_circle.
"""

import math
import pygame

from config   import WIDTH, HEIGHT, N, RADIUS, FPS
from config   import CIRCLE_DRAW_SPEED, POINT_APPEAR_DELAY, Config
from config   import DRAW_MAIN_CIRCLE, SHOW_POINTS, DRAW_FLOWER, DONE
from geometry import circle_from_points
from renderer import create_mask, render_frame
from intro    import run_intro


def run_animation(screen, clock, cfg: Config):
    center = (WIDTH // 2, HEIGHT // 2)
    speed = cfg.speed

    points = [
        (
            center[0] + RADIUS * math.cos(-math.pi / 2 + i * (2 * math.pi / N)),
            center[1] + RADIUS * math.sin(-math.pi / 2 + i * (2 * math.pi / N)),
        )
        for i in range(N)
    ]

    circles = [
        {"center": c, "radius": r}
        for p in points
        for c, r in [circle_from_points(center, p)]
    ]

    mask = create_mask(center)
    drawing = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    stage = DRAW_MAIN_CIRCLE
    main_progress = 0
    visible_points = 0
    point_timer = 0
    current_circle = 0
    current_progress = 0
    finished_circles = []

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        if stage == DRAW_MAIN_CIRCLE:
            main_progress += CIRCLE_DRAW_SPEED * speed * dt
            if main_progress >= 360:
                main_progress = 360
                stage = SHOW_POINTS

        elif stage == SHOW_POINTS:
            point_timer += dt
            if point_timer >= POINT_APPEAR_DELAY / speed:
                point_timer = 0
                visible_points += 1
                if visible_points >= len(points):
                    visible_points = len(points)
                    stage = DRAW_FLOWER

        elif stage == DRAW_FLOWER:
            if current_circle < len(circles):
                current_progress += CIRCLE_DRAW_SPEED * speed * dt
                if current_progress >= 360:
                    finished_circles.append(circles[current_circle])
                    current_circle += 1
                    current_progress = 0
            else:
                stage = DONE

        render_frame(screen, drawing, mask, center,
                     main_progress, finished_circles,
                     current_circle, circles,
                     current_progress, stage,
                     points, visible_points)

        pygame.display.flip()

    pygame.quit()
    raise SystemExit


def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    cfg = Config()
    while True:
        cfg = run_intro(screen, clock, cfg)
        run_animation(screen, clock, cfg)
