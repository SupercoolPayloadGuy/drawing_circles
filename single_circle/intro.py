"""
intro.py — animated intro screen for single_circle.

Main panel:
  LEFT/RIGHT / A/D  — change point count
  ENTER             — start
  TAB               — open settings

Settings panel (TAB):
  UP/DOWN / W/S     — move cursor
  LEFT/RIGHT / A/D  — change value
  ENTER / TAB       — back to main
"""

import math
import time
import pygame

from config import WIDTH, HEIGHT, Config, COLOR_SCHEMES


BG     = (10,  10,  10)
WHITE  = (215, 215, 215)
GREY   = (95,  95,  95)
ACCENT = (255, 220,  50)
DIM    = (30,  30,  30)
DIM2   = (50,  50,  50)
SOFT   = (140, 140, 140)
GREEN  = ( 80, 220, 120)


def _lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


_STOPS = [
    (0.0,  (255, 130,  40)),
    (0.25, ( 70, 230,  90)),
    (0.5,  ( 40, 190, 255)),
    (0.75, (190,  70, 255)),
    (1.0,  (255,  60, 190)),
]


def _interp_stops(stops, t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        pos, col = stops[i]
        npos, ncol = stops[i + 1]
        if pos <= t <= npos:
            lt = (t - pos) / (npos - pos)
            return tuple(round(col[j] + (ncol[j] - col[j]) * lt) for j in range(3))
    return stops[-1][1]


class _BackgroundAnim:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t0 = time.time()

    def draw(self, surface, point_count):
        t = time.time() - self.t0
        cx, cy = self.cx, self.cy

        r = 180 + 15 * math.sin(t * 0.6)

        pygame.draw.circle(surface, (50, 50, 50), (cx, cy), round(r), 1)

        for i in range(4):
            pygame.draw.circle(surface, (40, 40, 40), (cx, cy),
                               round(r * (1.0 - i * 0.15)), 1)

        pts = [
            (cx + r * math.cos(-math.pi / 2 + 2 * math.pi * i / point_count),
             cy + r * math.sin(-math.pi / 2 + 2 * math.pi * i / point_count))
            for i in range(point_count)
        ]

        for px, py in pts:
            mx, my = (cx + px) / 2, (cy + py) / 2
            mr = math.hypot(px - cx, py - cy) / 2
            pygame.draw.circle(surface, (65, 65, 65), (round(mx), round(my)), round(mr), 1)

            pygame.draw.circle(surface, ACCENT, (round(px), round(py)), 4)

        pygame.draw.circle(surface, ACCENT, (cx, cy), 4)

        phase = (t % 3) / 3
        exp_r = r * (1.0 + phase * 2.0)
        exp_a = round((1.0 - phase) * 40)
        if exp_a > 0:
            tmp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (255, 220, 50, exp_a), (cx, cy), round(exp_r), 1)
            surface.blit(tmp, (0, 0))


class _SettingsPanel:
    MIN_POINTS = 2
    MAX_POINTS = 100

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.cursor = 0
        self._rows = [
            dict(type='choice', label='color scheme', attr='color_scheme',
                 options=COLOR_SCHEMES),
            dict(type='num', label='main radius', attr='main_radius',
                 min=50, max=550, step=10, fmt=lambda v: f"{v}px"),
            dict(type='num', label='speed', attr='speed',
                 min=0.25, max=8.0, step=0.25, fmt=lambda v: f"{v:.2f}x"),
            dict(type='bool', label='show circle count', attr='show_circle_count'),
            dict(type='bool', label='show progress bar', attr='show_progress_bar'),
        ]

    def handle_key(self, key):
        rows = self._rows
        row = rows[self.cursor]

        if key in (pygame.K_UP, pygame.K_w):
            self.cursor = (self.cursor - 1) % len(rows)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.cursor = (self.cursor + 1) % len(rows)
        elif row['type'] == 'choice':
            opts = row['options']
            cur = opts.index(getattr(self.cfg, row['attr']))
            if key in (pygame.K_RIGHT, pygame.K_d):
                setattr(self.cfg, row['attr'], opts[(cur + 1) % len(opts)])
            elif key in (pygame.K_LEFT, pygame.K_a):
                setattr(self.cfg, row['attr'], opts[(cur - 1) % len(opts)])
        elif row['type'] == 'bool' and key in (
                pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d,
                pygame.K_SPACE, pygame.K_RETURN):
            setattr(self.cfg, row['attr'], not getattr(self.cfg, row['attr']))
        elif row['type'] == 'num':
            if key in (pygame.K_RIGHT, pygame.K_d, pygame.K_EQUALS,
                       pygame.K_PLUS, pygame.K_KP_PLUS):
                self._nudge(row, +1)
            elif key in (pygame.K_LEFT, pygame.K_a, pygame.K_MINUS,
                         pygame.K_KP_MINUS):
                self._nudge(row, -1)

    def _nudge(self, row, direction):
        cur = getattr(self.cfg, row['attr'])
        new = cur + direction * row['step']
        new = round(new / row['step']) * row['step']
        new = max(row['min'], min(row['max'], new))
        if row['step'] == int(row['step']):
            new = int(new)
        setattr(self.cfg, row['attr'], new)

    def draw(self, surface, font_small, cx, cy):
        pw, ph = 420, 310
        px, py = cx - pw // 2, cy - ph // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((18, 18, 18, 230))
        surface.blit(panel, (px, py))
        pygame.draw.rect(surface, (60, 60, 60), (px, py, pw, ph), 1,
                         border_radius=10)

        title = font_small.render("SETTINGS", True, ACCENT)
        surface.blit(title, (cx - title.get_width() // 2, py + 10))

        row_h = 40
        start_y = py + 42
        bar_w = 120

        for i, row in enumerate(self._rows):
            ry = start_y + i * row_h
            focused = i == self.cursor
            fg = WHITE if focused else SOFT

            if focused:
                sel = pygame.Surface((pw - 16, row_h - 4), pygame.SRCALPHA)
                sel.fill((255, 220, 50, 22))
                surface.blit(sel, (px + 8, ry - 1))

            lbl = font_small.render(row['label'], True, fg)
            surface.blit(lbl, (px + 20, ry + (row_h - lbl.get_height()) // 2))

            if row['type'] == 'choice':
                val = getattr(self.cfg, row['attr'])
                opts = row['options']
                cur = opts.index(val)
                ind = font_small.render("<", True, ACCENT if focused else GREY)
                ind2 = font_small.render(">", True, ACCENT if focused else GREY)
                vl = font_small.render(val, True, ACCENT if focused else SOFT)
                ix = px + pw - 20 - vl.get_width() - ind.get_width() - ind2.get_width() - 8
                iy = ry + (row_h - vl.get_height()) // 2
                surface.blit(ind, (ix, iy))
                surface.blit(vl, (ix + ind.get_width() + 4, iy))
                surface.blit(ind2, (ix + ind.get_width() + 4 + vl.get_width() + 4, iy))

            elif row['type'] == 'bool':
                val = getattr(self.cfg, row['attr'])
                on_col = GREEN if val else DIM2
                off_col = DIM2 if val else GREY
                on_s = font_small.render("ON", True, on_col)
                off_s = font_small.render("OFF", True, off_col)
                rx = px + pw - 20
                surface.blit(off_s, (rx - off_s.get_width(),
                                     ry + (row_h - off_s.get_height()) // 2))
                surface.blit(on_s, (rx - off_s.get_width() - on_s.get_width() - 12,
                                    ry + (row_h - on_s.get_height()) // 2))
                box_x = rx - off_s.get_width() - on_s.get_width() - 28
                box_r = pygame.Rect(box_x, ry + row_h // 2 - 7, 14, 14)
                pygame.draw.rect(surface, GREEN if val else GREY, box_r,
                                 0 if val else 1, border_radius=3)

            else:
                val = getattr(self.cfg, row['attr'])
                frac = (val - row['min']) / max(row['max'] - row['min'], 1e-9)
                bx = px + pw - bar_w - 20
                by_mid = ry + row_h // 2

                pygame.draw.rect(surface, DIM, (bx, by_mid - 2, bar_w, 4),
                                 border_radius=2)
                filled = round(bar_w * frac)
                if filled > 0:
                    fc = _interp_stops(_STOPS, frac)
                    pygame.draw.rect(surface, fc, (bx, by_mid - 2, filled, 4),
                                     border_radius=2)
                kx = bx + filled
                pygame.draw.circle(surface, WHITE if focused else SOFT,
                                   (kx, by_mid), 6)

                val_s = font_small.render(row['fmt'](val), True,
                                          ACCENT if focused else GREY)
                surface.blit(val_s, (bx - val_s.get_width() - 10,
                                     by_mid - val_s.get_height() // 2))

        hint = font_small.render("[TAB] or [ENTER] back  ·  arrows to adjust",
                                 True, (70, 70, 70))
        surface.blit(hint, (cx - hint.get_width() // 2, py + ph - 22))


def run_intro(screen, clock, prev_config=None):
    w, h = screen.get_size()
    cx, cy = w // 2, h // 2

    pygame.display.set_caption("Circle Flower")

    font_big = pygame.font.SysFont("monospace", 48, bold=True)
    font_med = pygame.font.SysFont("monospace", 24)
    font_small = pygame.font.SysFont("monospace", 18)

    cfg = prev_config if prev_config is not None else Config()
    bg_anim = _BackgroundAnim(cx, cy)
    settings = _SettingsPanel(cfg)
    show_settings = False
    start_time = time.time()

    confirmed_at = None

    btn_up = pygame.Rect(cx + 50, cy - 8, 44, 44)
    btn_dn = pygame.Rect(cx - 94, cy - 8, 44, 44)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    show_settings = not show_settings
                elif show_settings:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        show_settings = False
                    else:
                        settings.handle_key(event.key)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    confirmed_at = time.time()
                elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_UP, pygame.K_w):
                    cfg.point_count = min(settings.MAX_POINTS, cfg.point_count + 1)
                elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_DOWN, pygame.K_s):
                    cfg.point_count = max(settings.MIN_POINTS, cfg.point_count - 1)
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION) and not show_settings:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_up.collidepoint(event.pos):
                        cfg.point_count = min(settings.MAX_POINTS, cfg.point_count + 1)
                    elif btn_dn.collidepoint(event.pos):
                        cfg.point_count = max(settings.MIN_POINTS, cfg.point_count - 1)

        screen.fill(BG)
        bg_anim.draw(screen, cfg.point_count)

        elapsed = time.time() - start_time

        if not show_settings:
            if elapsed > 0.3:
                alpha = min(1.0, (elapsed - 0.3) / 0.7)
                title = font_big.render("CIRCLE FLOWER", True, WHITE)
                title.set_alpha(round(alpha * 255))
                screen.blit(title, (cx - title.get_width() // 2, cy - 140))

            # Point count
            if elapsed > 0.8:
                lbl = font_small.render("POINTS", True, GREY)
                screen.blit(lbl, (cx - lbl.get_width() // 2, cy - 40))

                num_s = font_big.render(str(cfg.point_count), True, ACCENT)
                screen.blit(num_s, (cx - num_s.get_width() // 2, cy + 5))

                # Arrow buttons
                for btn, arrow in [(btn_dn, "◀"), (btn_up, "▶")]:
                    pygame.draw.rect(screen, DIM, btn, border_radius=8)
                    pygame.draw.rect(screen, (60, 60, 60), btn, 1, border_radius=8)
                    a_s = font_med.render(arrow, True, SOFT)
                    screen.blit(a_s, (btn.x + (btn.w - a_s.get_width()) // 2,
                                      btn.y + (btn.h - a_s.get_height()) // 2))

            # Prompt
            if elapsed > 1.5:
                pulse = (math.sin(elapsed * 2.5) + 1) / 2 * 0.5 + 0.3
                prompt = font_small.render(
                    "[ENTER] to start  ·  [TAB] settings", True, GREY)
                prompt.set_alpha(round(pulse * 255))
                screen.blit(prompt, (cx - prompt.get_width() // 2, cy + 90))

        if show_settings:
            settings.draw(screen, font_small, cx, cy)

        pygame.display.flip()
        clock.tick(60)

        if confirmed_at is not None and time.time() - confirmed_at >= 0.25:
            return cfg
