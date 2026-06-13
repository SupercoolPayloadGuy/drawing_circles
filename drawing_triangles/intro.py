"""
intro.py — animated level-select screen with a Settings panel.
"""

import math
import time
import pygame

from config import Config


BG     = (10,  10,  10)
DIM    = (30,  30,  30)
ACCENT = (255, 220,  50)
WHITE  = (215, 215, 215)
GREY   = ( 95,  95,  95)
SOFT   = (140, 140, 140)
GREEN  = ( 80, 220, 120)
DIM2   = (50,  50,  50)


def _lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _interp_stops(stops, t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        pos, col   = stops[i]
        npos, ncol = stops[i + 1]
        if pos <= t <= npos:
            lt = (t - pos) / (npos - pos)
            return tuple(round(col[j] + (ncol[j] - col[j]) * lt) for j in range(3))
    return stops[-1][1]


_PREVIEW_STOPS = [
    (0.0,  (255, 130,  40)),
    (0.25, ( 70, 230,  90)),
    (0.5,  ( 40, 190, 255)),
    (0.75, (190,  70, 255)),
    (1.0,  (255,  60, 190)),
]

def preview_color(t):
    return _interp_stops(_PREVIEW_STOPS, t)


def _draw_triangle(surface, pts, color, alpha=255, width=1):
    tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, (*color, alpha), pts, width)
    surface.blit(tmp, (0, 0))


def _draw_dot(surface, cx, cy, color, alpha=255, r=4):
    s = r * 2 + 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + 1, r + 1), r)
    surface.blit(tmp, (round(cx) - r - 1, round(cy) - r - 1))


GEN_NAMES = {
    1: "seed", 2: "shallow", 3: "deepening", 4: "nested",
    5: "intricate", 6: "woven", 7: "dense", 8: "recursive",
    9: "infinite", 10: "beyond",
}

def gen_name(n):
    return GEN_NAMES.get(n, f"depth {n}")


class _BackgroundAnim:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t0 = time.time()

    def draw(self, surface, chosen_gen):
        t  = time.time() - self.t0
        cx, cy = self.cx, self.cy
        breath = 1.0 + 0.05 * math.sin(t * 0.7)
        base_r = 120

        rings = min(chosen_gen, 6)
        for i in range(rings):
            dep = i / max(rings - 1, 1)
            col = preview_color(dep)
            alpha = max(15, 110 - i * 16)
            rr = base_r * (1.0 + i * 0.45) * breath
            # draw a equilateral triangle instead of circle
            h = math.sqrt(3) / 2 * rr
            tri = [
                (cx, cy - 2*h/3),
                (cx - rr/2, cy + h - 2*h/3),
                (cx + rr/2, cy + h - 2*h/3),
            ]
            _draw_triangle(surface, tri, col, alpha=alpha)

        phase = (t % 4.0) / 4.0
        w_col = preview_color(phase)
        rr = base_r * (1.0 + phase * 2.5) * breath
        h = math.sqrt(3) / 2 * rr
        tri = [
            (cx, cy - 2*h/3),
            (cx - rr/2, cy + h - 2*h/3),
            (cx + rr/2, cy + h - 2*h/3),
        ]
        _draw_triangle(surface, tri, w_col, alpha=round((1.0 - phase) * 50))

        _draw_dot(surface, cx, cy, ACCENT, alpha=200)


class _SettingsPanel:
    def __init__(self, cfg: Config):
        self.cfg    = cfg
        self.cursor = 0
        self._rows  = [
            dict(type='num',  label='side length',      attr='side_length',
                 min=100, max=600, step=20, fmt=lambda v: f"{v}px"),
            dict(type='num',  label='speed',            attr='speed',
                 min=0.25, max=8.0, step=0.25, fmt=lambda v: f"{v:.2f}x"),
            dict(type='bool', label='show triangle count', attr='show_triangle_count'),
            dict(type='bool', label='show generation',     attr='show_generation'),
            dict(type='bool', label='show total generations', attr='show_total_generations'),
            dict(type='bool', label='show zoom',        attr='show_zoom'),
            dict(type='bool', label='show speed',       attr='show_speed'),
        ]

    def handle_key(self, key):
        rows = self._rows
        row  = rows[self.cursor]
        if key in (pygame.K_UP, pygame.K_w):
            self.cursor = (self.cursor - 1) % len(rows)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.cursor = (self.cursor + 1) % len(rows)
        elif row['type'] == 'bool' and key in (
                pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d,
                pygame.K_SPACE, pygame.K_RETURN):
            setattr(self.cfg, row['attr'], not getattr(self.cfg, row['attr']))
        elif row['type'] == 'num':
            if key in (pygame.K_RIGHT, pygame.K_d, pygame.K_EQUALS, pygame.K_PLUS,
                       pygame.K_KP_PLUS):
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

    def draw(self, surface, font_med, font_small, cx, cy):
        pw, ph = 480, 320
        px, py = cx - pw // 2, cy - ph // 2 - 30
        panel  = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((18, 18, 18, 230))
        surface.blit(panel, (px, py))
        pygame.draw.rect(surface, (60, 60, 60), (px, py, pw, ph), 1, border_radius=10)

        title = font_med.render("SETTINGS", True, ACCENT)
        surface.blit(title, (cx - title.get_width() // 2, py + 14))

        row_h  = 38
        start_y = py + 52
        bar_w   = 140

        for i, row in enumerate(self._rows):
            ry      = start_y + i * row_h
            focused = i == self.cursor
            fg      = WHITE if focused else SOFT
            if focused:
                sel = pygame.Surface((pw - 16, row_h - 4), pygame.SRCALPHA)
                sel.fill((255, 220, 50, 22))
                surface.blit(sel, (px + 8, ry - 1))
            lbl = font_small.render(row['label'], True, fg)
            surface.blit(lbl, (px + 20, ry + (row_h - lbl.get_height()) // 2))
            if row['type'] == 'bool':
                val = getattr(self.cfg, row['attr'])
                on_col  = GREEN if val else DIM2
                off_col = DIM2  if val else GREY
                on_s  = font_small.render("ON",  True, on_col)
                off_s = font_small.render("OFF", True, off_col)
                rx = px + pw - 20
                surface.blit(off_s, (rx - off_s.get_width(), ry + (row_h - off_s.get_height()) // 2))
                surface.blit(on_s,  (rx - off_s.get_width() - on_s.get_width() - 12,
                                     ry + (row_h - on_s.get_height()) // 2))
                box_x = rx - off_s.get_width() - on_s.get_width() - 28
                box_r = pygame.Rect(box_x, ry + row_h // 2 - 7, 14, 14)
                pygame.draw.rect(surface, GREEN if val else GREY, box_r, 0 if val else 1, border_radius=3)
            else:
                val    = getattr(self.cfg, row['attr'])
                frac   = (val - row['min']) / max(row['max'] - row['min'], 1e-9)
                bx     = px + pw - bar_w - 20
                by_mid = ry + row_h // 2
                pygame.draw.rect(surface, DIM, (bx, by_mid - 2, bar_w, 4), border_radius=2)
                filled = round(bar_w * frac)
                if filled > 0:
                    fill_col = _interp_stops(_PREVIEW_STOPS, frac)
                    pygame.draw.rect(surface, fill_col, (bx, by_mid - 2, filled, 4), border_radius=2)
                kx = bx + filled
                pygame.draw.circle(surface, WHITE if focused else SOFT, (kx, by_mid), 6)
                val_s = font_small.render(row['fmt'](val), True, ACCENT if focused else GREY)
                surface.blit(val_s, (bx - val_s.get_width() - 10,
                                     by_mid - val_s.get_height() // 2))

        hint = font_small.render("[TAB] or [ENTER] back  ·  arrows to adjust", True, (70, 70, 70))
        surface.blit(hint, (cx - hint.get_width() // 2, py + ph - 24))


class _Selector:
    MIN_GEN    = 1
    MAX_GEN    = 99
    _DIGIT_TIMEOUT = 1.2

    PANEL_MAIN     = 'main'
    PANEL_SETTINGS = 'settings'

    def __init__(self, cx, cy, fonts, cfg: Config):
        self.cx, self.cy   = cx, cy
        self.font_big, self.font_med, self.font_small = fonts
        self.cfg           = cfg
        self._panel        = self.PANEL_MAIN
        self._settings     = _SettingsPanel(cfg)
        self._confirm_t    = None
        self._digit_buf    = ""
        self._digit_ts     = 0.0
        self.hover_up      = False
        self.hover_dn      = False
        self.btn_up        = pygame.Rect(cx + 60,  cy + 5, 44, 44)
        self.btn_dn        = pygame.Rect(cx - 104, cy + 5, 44, 44)
        self._settings_btn = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_TAB:
                self._panel = (self.PANEL_SETTINGS
                               if self._panel == self.PANEL_MAIN
                               else self.PANEL_MAIN)
                return False
            if self._panel == self.PANEL_SETTINGS:
                if k == pygame.K_RETURN:
                    self._panel = self.PANEL_MAIN
                else:
                    self._settings.handle_key(k)
                return False
            if pygame.K_0 <= k <= pygame.K_9:
                now = time.time()
                if now - self._digit_ts > self._DIGIT_TIMEOUT:
                    self._digit_buf = ""
                self._digit_buf += str(k - pygame.K_0)
                self._digit_ts   = now
                val = int(self._digit_buf)
                if val >= self.MIN_GEN:
                    self.cfg.generations = min(self.MAX_GEN, val)
                return False
            if k in (pygame.K_UP, pygame.K_w):
                self._clear_buf()
                self.cfg.generations = min(self.MAX_GEN, self.cfg.generations + 1)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self._clear_buf()
                self.cfg.generations = max(self.MIN_GEN, self.cfg.generations - 1)
            elif k == pygame.K_RETURN:
                self._confirm_t = time.time()
                return True
            elif k == pygame.K_BACKSPACE and self._digit_buf:
                self._digit_buf = self._digit_buf[:-1]
                val = int(self._digit_buf) if self._digit_buf else self.MIN_GEN
                self.cfg.generations = max(self.MIN_GEN, val)

        if event.type == pygame.MOUSEWHEEL and self._panel == self.PANEL_MAIN:
            self._clear_buf()
            self.cfg.generations = max(self.MIN_GEN,
                                       min(self.MAX_GEN, self.cfg.generations + event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._panel == self.PANEL_MAIN:
                if self.btn_up.collidepoint(event.pos):
                    self._clear_buf()
                    self.cfg.generations = min(self.MAX_GEN, self.cfg.generations + 1)
                elif self.btn_dn.collidepoint(event.pos):
                    self._clear_buf()
                    self.cfg.generations = max(self.MIN_GEN, self.cfg.generations - 1)
                elif self._settings_btn and self._settings_btn.collidepoint(event.pos):
                    self._panel = self.PANEL_SETTINGS

        if event.type == pygame.MOUSEMOTION and self._panel == self.PANEL_MAIN:
            self.hover_up = self.btn_up.collidepoint(event.pos)
            self.hover_dn = self.btn_dn.collidepoint(event.pos)

        return False

    def _clear_buf(self):
        self._digit_buf = ""

    def draw(self, surface):
        if self._panel == self.PANEL_SETTINGS:
            self._draw_settings(surface)
        else:
            self._draw_main(surface)

    def _draw_main(self, surface):
        cx, cy = self.cx, self.cy
        cfg    = self.cfg
        dep_t  = min(1.0, (cfg.generations - 1) / 8.0)

        title = self.font_big.render("TRIANGLE CONSTRUCTION", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, cy - 200))
        sub = self.font_small.render("choose your depth", True, GREY)
        surface.blit(sub, (cx - sub.get_width() // 2, cy - 155))

        num_col = _lerp3((255, 220, 50), (80, 200, 255), dep_t)
        if self._confirm_t is not None:
            flash = (time.time() - self._confirm_t) / 0.25
            num_col = _lerp3(num_col, (255, 255, 255), max(0.0, 1.0 - flash))
            if flash >= 1.0:
                self._confirm_t = None
        num_s = self.font_big.render(str(cfg.generations), True, num_col)
        surface.blit(num_s, (cx - num_s.get_width() // 2, cy - 30))

        name_s = self.font_med.render(gen_name(cfg.generations), True,
                                      _lerp3(SOFT, (100, 180, 240), dep_t))
        surface.blit(name_s, (cx - name_s.get_width() // 2, cy + 52))

        for btn, lbl, hover in [
            (self.btn_up, "▶", self.hover_up),
            (self.btn_dn, "◀", self.hover_dn),
        ]:
            col = ACCENT if hover else GREY
            s   = self.font_med.render(lbl, True, col)
            surface.blit(s, (btn.x + (btn.w - s.get_width()) // 2,
                             btn.y + (btn.h - s.get_height()) // 2))

        if self._digit_buf:
            buf_s = self.font_small.render(f"typing: {self._digit_buf}_", True, ACCENT)
        else:
            buf_s = self.font_small.render("or type a number directly", True, GREY)
        surface.blit(buf_s, (cx - buf_s.get_width() // 2, cy + 112))

        bar_w, bar_h = 300, 4
        bx, by   = cx - bar_w // 2, cy + 138
        filled   = round(bar_w * min(1.0, (cfg.generations - 1) / 8.0))
        pygame.draw.rect(surface, DIM, (bx, by, bar_w, bar_h), border_radius=2)
        if filled > 0:
            pygame.draw.rect(surface, _lerp3((255, 220, 50), (80, 200, 255), dep_t),
                             (bx, by, filled, bar_h), border_radius=2)

        hint = self.font_small.render("[ENTER] to start", True, GREY)
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 165))

        MAX_DOTS = 9
        shown    = min(cfg.generations, MAX_DOTS)
        ox       = cx - (MAX_DOTS - 1) * 20 // 2
        oy       = cy + 200
        for i in range(MAX_DOTS):
            col = _lerp3((255, 220, 50), (80, 200, 255), i / (MAX_DOTS - 1)) \
                  if (i + 1) <= shown else DIM
            pygame.draw.circle(surface, col, (ox + i * 20, oy), 4)
        if cfg.generations > MAX_DOTS:
            extra = self.font_small.render(f"+{cfg.generations - MAX_DOTS}", True, (80, 200, 255))
            surface.blit(extra, (ox + MAX_DOTS * 20 + 4, oy - 7))

        btn_w, btn_h = 130, 30
        bx2 = cx - btn_w // 2
        by2 = cy + 228
        self._settings_btn = pygame.Rect(bx2, by2, btn_w, btn_h)
        pygame.draw.rect(surface, DIM, self._settings_btn, border_radius=6)
        pygame.draw.rect(surface, (60, 60, 60), self._settings_btn, 1, border_radius=6)
        slbl = self.font_small.render("⚙  SETTINGS  [TAB]", True, GREY)
        surface.blit(slbl, (bx2 + (btn_w - slbl.get_width()) // 2,
                            by2 + (btn_h - slbl.get_height()) // 2))

        summary_parts = []
        if cfg.side_length != 300:
            summary_parts.append(f"s={cfg.side_length}")
        if cfg.speed != 1.0:
            summary_parts.append(f"spd={cfg.speed:.2f}x")
        if summary_parts:
            peek = self.font_small.render("  ".join(summary_parts), True, (100, 160, 100))
            surface.blit(peek, (cx - peek.get_width() // 2, by2 + btn_h + 6))

    def _draw_settings(self, surface):
        cx, cy = self.cx, self.cy
        self._settings.draw(surface, self.font_med, self.font_small, cx, cy)


def run_intro(screen, clock, prev_config: Config = None) -> Config:
    w, h   = screen.get_size()
    cx, cy = w // 2, h // 2

    pygame.display.set_caption("Triangle Construction  —  Select Generations")

    font_big   = pygame.font.SysFont("monospace", 54, bold=True)
    font_med   = pygame.font.SysFont("monospace", 24)
    font_small = pygame.font.SysFont("monospace", 18)

    cfg      = prev_config if prev_config is not None else Config()
    bg_anim  = _BackgroundAnim(cx, cy)
    selector = _Selector(cx, cy, (font_big, font_med, font_small), cfg)

    confirmed_at = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if selector.handle_event(event):
                confirmed_at = time.time()

        if selector._digit_buf and time.time() - selector._digit_ts > selector._DIGIT_TIMEOUT:
            selector._digit_buf = ""

        screen.fill(BG)
        bg_anim.draw(screen, cfg.generations)
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)

        if confirmed_at is not None and time.time() - confirmed_at >= 0.28:
            return cfg
