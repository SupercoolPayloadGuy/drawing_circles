"""
app.py — animation state machine and main loop for single_circle.
"""

import math
import time

import pygame

from config   import WIDTH, HEIGHT, RADIUS, FPS, LINE_WIDTH, BG
from config   import CIRCLE_DRAW_SPEED, POINT_APPEAR_DELAY, Config
from config   import DRAW_MAIN_CIRCLE, SHOW_POINTS, DRAW_FLOWER, DONE
from geometry import circle_from_points
from renderer import create_mask, render_frame, export_png, export_svg
from renderer import draw_button, draw_hint
from intro    import run_intro


MENU_BTN_W = 130
MENU_BTN_H = 36
MENU_BTN = pygame.Rect(16, 16, MENU_BTN_W, MENU_BTN_H)

BTN_W = 130
BTN_H = 44
BTN_GAP = 16
BTN_Y = HEIGHT - 80
BTN_ACTIONS = ["menu", "look", "png", "svg"]
BTN_LABELS = ["MENU", "LOOK", "EXPORT PNG", "EXPORT SVG"]


def _make_buttons():
    total_w = len(BTN_ACTIONS) * BTN_W + (len(BTN_ACTIONS) - 1) * BTN_GAP
    sx = (WIDTH - total_w) // 2
    btns = []
    for i, (act, lbl) in enumerate(zip(BTN_ACTIONS, BTN_LABELS)):
        x = sx + i * (BTN_W + BTN_GAP)
        btns.append({"rect": pygame.Rect(x, BTN_Y, BTN_W, BTN_H),
                      "action": act, "label": lbl})
    return btns


def _export_png(screen):
    ts = time.strftime("%Y%m%d_%H%M%S")
    fn = f"circle_flower_{ts}.png"
    export_png(screen, fn)
    return fn


def _export_svg(center, points, circles, circle_count, mr, scheme):
    ts = time.strftime("%Y%m%d_%H%M%S")
    fn = f"circle_flower_{ts}.svg"
    export_svg(fn, center, points, circles, list(range(circle_count)),
               mr, circle_count, LINE_WIDTH, scheme)
    return fn


def run_animation(screen, clock, cfg: Config):
    center = (WIDTH // 2, HEIGHT // 2)
    speed = cfg.speed
    mr = cfg.main_radius

    n = cfg.point_count
    points = [
        (
            center[0] + mr * math.cos(-math.pi / 2 + i * (2 * math.pi / n)),
            center[1] + mr * math.sin(-math.pi / 2 + i * (2 * math.pi / n)),
        )
        for i in range(n)
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

    # Camera / look-around
    camera_active = False
    captured = None
    cam_off_x = 0
    cam_off_y = 0
    cam_zoom = 1.0
    dragging = False
    drag_start = None

    buttons = _make_buttons()
    clean_frame = None

    menu_hover = False
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        menu_hover = MENU_BTN.collidepoint(pygame.mouse.get_pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    if camera_active:
                        camera_active = False
                        cam_zoom = 1.0
                        cam_off_x = cam_off_y = 0
                    else:
                        return
                elif event.key == pygame.K_p:
                    print(f"exported {_export_png(screen)}")
                elif event.key == pygame.K_s:
                    print(f"exported {_export_svg(center, points, circles, current_circle, mr, cfg.color_scheme)}")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if MENU_BTN.collidepoint(event.pos):
                    return

            if stage == DONE or camera_active:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if camera_active:
                        dragging = True
                        drag_start = pos
                    else:
                        for btn in buttons:
                            if btn["rect"].collidepoint(pos):
                                act = btn["action"]
                                if act == "menu":
                                    return
                                elif act == "look":
                                    if clean_frame is not None:
                                        captured = clean_frame
                                        camera_active = True
                                        cam_zoom = 1.0
                                        cam_off_x = cam_off_y = 0
                                elif act == "png":
                                    print(f"exported {_export_png(screen)}")
                                elif act == "svg":
                                    print(f"exported {_export_svg(center, points, circles, current_circle, mr, cfg.color_scheme)}")

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging = False

                elif event.type == pygame.MOUSEMOTION and dragging and camera_active:
                    dx = event.pos[0] - drag_start[0]
                    dy = event.pos[1] - drag_start[1]
                    cam_off_x += dx
                    cam_off_y += dy
                    drag_start = event.pos

                elif event.type == pygame.MOUSEWHEEL and camera_active:
                    mx, my = pygame.mouse.get_pos()
                    zf = 1.1 if event.y > 0 else 0.9
                    sw = int(WIDTH * cam_zoom)
                    sh = int(HEIGHT * cam_zoom)
                    img_x = mx - (WIDTH // 2 - sw // 2 + int(cam_off_x))
                    img_y = my - (HEIGHT // 2 - sh // 2 + int(cam_off_y))
                    frac_x = img_x / sw if sw > 0 else 0.5
                    frac_y = img_y / sh if sh > 0 else 0.5
                    cam_zoom = max(0.1, min(10.0, cam_zoom * zf))
                    nsw = int(WIDTH * cam_zoom)
                    nsh = int(HEIGHT * cam_zoom)
                    cam_off_x = mx - (WIDTH // 2 - nsw // 2 + frac_x * nsw)
                    cam_off_y = my - (HEIGHT // 2 - nsh // 2 + frac_y * nsh)

        # ── update ────────────────────────────────────────────────
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

        # ── render ────────────────────────────────────────────────
        if camera_active and captured is not None:
            screen.fill(BG)
            w, h = captured.get_size()
            sw = int(w * cam_zoom)
            sh = int(h * cam_zoom)
            scaled = pygame.transform.smoothscale(captured, (sw, sh))
            screen.blit(scaled, (WIDTH // 2 - sw // 2 + int(cam_off_x),
                                 HEIGHT // 2 - sh // 2 + int(cam_off_y)))
            for btn in buttons:
                draw_button(screen, btn["rect"], btn["label"])
            draw_hint(screen, "drag to pan  ·  scroll to zoom  ·  ESC to exit")
        else:
            render_frame(screen, drawing, mask, center,
                         main_progress, finished_circles,
                         current_circle, circles,
                         current_progress, stage,
                         points, visible_points,
                         cfg.color_scheme, cfg.show_circle_count,
                         cfg.show_progress_bar)

            draw_button(screen, MENU_BTN, "← MENU",
                        bg=(40, 40, 40) if menu_hover else (30, 30, 30),
                        fg=(255, 220, 50) if menu_hover else (200, 200, 200))

            if stage == DONE and not camera_active:
                clean_frame = screen.copy()
                for btn in buttons:
                    draw_button(screen, btn["rect"], btn["label"])

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
