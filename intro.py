"""
intro.py — animated level-select screen with a Settings panel.

Main panel  (default)
  UP/DOWN / W/S / scroll  — level
  LEFT/RIGHT / A/D        — point count
  digits 0-9              — type level directly (1.2 s timeout)
  ENTER                   — start
  TAB                     — switch to Settings panel

Settings panel  (TAB to open)
  UP/DOWN                 — move cursor
  LEFT/RIGHT / +/-        — change value
  ENTER / TAB             — back to Main panel
"""

import math
import time
import pygame

from config import Config


# ──────────────────────────────────────────────
# COLOURS
# ──────────────────────────────────────────────

BG     = (10,  10,  10)
DIM    = (30,  30,  30)
ACCENT = (255, 220,  50)
WHITE  = (215, 215, 215)
GREY   = ( 95,  95,  95)
SOFT   = (140, 140, 140)
GREEN  = ( 80, 220, 120)
DIM2   = (50,  50,  50)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

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


def _draw_ring(surface, cx, cy, radius, color, alpha=255, width=1):
    if radius < 1:
        return
    r = round(radius)
    s = r * 2 + width * 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + width, r + width), r, width)
    surface.blit(tmp, (round(cx) - r - width, round(cy) - r - width))


def _draw_dot(surface, cx, cy, color, alpha=255, r=4):
    s = r * 2 + 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + 1, r + 1), r)
    surface.blit(tmp, (round(cx) - r - 1, round(cy) - r - 1))


LEVEL_NAMES = {
    1: "base", 2: "default", 3: "expanded", 4: "deep",
    5: "intense", 6: "extreme", 7: "void", 8: "abyss", 9: "beyond",
}

def level_name(n):
    return LEVEL_NAMES.get(n, f"depth {n}")


# ──────────────────────────────────────────────
# BACKGROUND ANIMATION
# ──────────────────────────────────────────────

class _BackgroundAnim:
    _BASE_R  = 90
    _N_RINGS = 5

    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t0 = time.time()

    def draw(self, surface, chosen_level, point_count=4):
        t  = time.time() - self.t0
        cx, cy = self.cx, self.cy
        r  = self._BASE_R * (1.0 + 0.07 * math.sin(t * 0.85))

        pts = [
            (cx + r * math.cos(-math.pi / 2 + 2 * math.pi * i / point_count),
             cy + r * math.sin(-math.pi / 2 + 2 * math.pi * i / point_count))
            for i in range(point_count)
        ]

        rings = min(chosen_level, self._N_RINGS)
        for i in range(rings):
            dep   = i / max(rings - 1, 1)
            col   = preview_color(dep)
            alpha = max(20, 140 - i * 22)
            _draw_ring(surface, cx, cy, r * (1.0 + i * 0.55), col, alpha=alpha)

        _draw_ring(surface, cx, cy, r, (90, 90, 90), alpha=170)

        for px, py in pts:
            mr = math.hypot(px - cx, py - cy) / 2
            _draw_ring(surface, (px + cx) / 2, (py + cy) / 2, mr, (65, 65, 65), alpha=80)

        n = len(pts)
        for i in range(n):
            p1, p2 = pts[i], pts[(i + 1) % n]
            mr = math.hypot(p1[0] - p2[0], p1[1] - p2[1]) / 2
            _draw_ring(surface, (p1[0]+p2[0])/2, (p1[1]+p2[1])/2, mr, (55, 55, 55), alpha=60)

        phase  = (t % 3.5) / 3.5
        w_col  = preview_color(phase)
        _draw_ring(surface, cx, cy, r * (1.0 + phase * 2.8), w_col,
                   alpha=round((1.0 - phase) * 55))

        for px, py in pts:
            _draw_dot(surface, px, py, ACCENT, alpha=170)
        _draw_dot(surface, cx, cy, ACCENT, alpha=200)


# ──────────────────────────────────────────────
# SETTINGS PANEL
# ──────────────────────────────────────────────

class _SettingsPanel:
    """
    A simple vertical list of rows.  Each row is either:
      - a numeric slider  { type:'num', label, attr, min, max, step, fmt }
      - a boolean toggle  { type:'bool', label, attr }
    Arrow keys / +/- adjust the focused row.
    """

    def __init__(self, cfg: Config):
        self.cfg    = cfg
        self.cursor = 0
        self._rows  = [
            dict(type='num',  label='base radius',      attr='base_radius',
                 min=40, max=400, step=10,  fmt=lambda v: f"{v}px"),
            dict(type='num',  label='speed',            attr='speed',
                 min=0.25, max=8.0, step=0.25, fmt=lambda v: f"{v:.2f}x"),
            dict(type='bool', label='show circle count',attr='show_circle_count'),
            dict(type='bool', label='show level',       attr='show_level'),
            dict(type='bool', label='show total levels',attr='show_total_levels'),
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
        # round to avoid float drift
        new = round(new / row['step']) * row['step']
        new = max(row['min'], min(row['max'], new))
        # store as int if step is whole number
        if row['step'] == int(row['step']):
            new = int(new)
        setattr(self.cfg, row['attr'], new)

    def draw(self, surface, font_med, font_small, cx, cy):
        # Panel background
        pw, ph = 480, 320
        px, py = cx - pw // 2, cy - ph // 2 - 30
        panel  = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((18, 18, 18, 230))
        surface.blit(panel, (px, py))
        pygame.draw.rect(surface, (60, 60, 60), (px, py, pw, ph), 1, border_radius=10)

        # Title
        title = font_med.render("SETTINGS", True, ACCENT)
        surface.blit(title, (cx - title.get_width() // 2, py + 14))

        row_h  = 38
        start_y = py + 52
        bar_w   = 140

        for i, row in enumerate(self._rows):
            ry      = start_y + i * row_h
            focused = i == self.cursor
            fg      = WHITE if focused else SOFT

            # Cursor indicator
            if focused:
                sel = pygame.Surface((pw - 16, row_h - 4), pygame.SRCALPHA)
                sel.fill((255, 220, 50, 22))
                surface.blit(sel, (px + 8, ry - 1))

            # Label
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
                # tick box
                box_x = rx - off_s.get_width() - on_s.get_width() - 28
                box_r = pygame.Rect(box_x, ry + row_h // 2 - 7, 14, 14)
                pygame.draw.rect(surface, GREEN if val else GREY, box_r, 0 if val else 1, border_radius=3)

            else:
                val    = getattr(self.cfg, row['attr'])
                frac   = (val - row['min']) / max(row['max'] - row['min'], 1e-9)
                bx     = px + pw - bar_w - 20
                by_mid = ry + row_h // 2

                # Track
                pygame.draw.rect(surface, DIM, (bx, by_mid - 2, bar_w, 4), border_radius=2)
                # Fill
                filled = round(bar_w * frac)
                if filled > 0:
                    fill_col = _interp_stops(_PREVIEW_STOPS, frac)
                    pygame.draw.rect(surface, fill_col, (bx, by_mid - 2, filled, 4), border_radius=2)
                # Knob
                kx = bx + filled
                pygame.draw.circle(surface, WHITE if focused else SOFT, (kx, by_mid), 6)

                # Value label
                val_s = font_small.render(row['fmt'](val), True, ACCENT if focused else GREY)
                surface.blit(val_s, (bx - val_s.get_width() - 10,
                                     by_mid - val_s.get_height() // 2))

        # Hint
        hint = font_small.render("[TAB] or [ENTER] back  ·  arrows to adjust", True, (70, 70, 70))
        surface.blit(hint, (cx - hint.get_width() // 2, py + ph - 24))


# ──────────────────────────────────────────────
# MAIN SELECTOR
# ──────────────────────────────────────────────

class _Selector:
    MIN_LEVEL  = 1
    MAX_LEVEL  = 99
    MIN_POINTS = 2
    MAX_POINTS = 24
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
        # Settings button rect (drawn lazily, stored for hit-testing)
        self._settings_btn = None

    # ── event handling ────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            k = event.key

            # TAB always toggles panels
            if k == pygame.K_TAB:
                self._panel = (self.PANEL_SETTINGS
                               if self._panel == self.PANEL_MAIN
                               else self.PANEL_MAIN)
                return False

            if self._panel == self.PANEL_SETTINGS:
                # ENTER in settings = back to main (don't start)
                if k == pygame.K_RETURN:
                    self._panel = self.PANEL_MAIN
                else:
                    self._settings.handle_key(k)
                return False

            # ── main panel ──
            if pygame.K_0 <= k <= pygame.K_9:
                now = time.time()
                if now - self._digit_ts > self._DIGIT_TIMEOUT:
                    self._digit_buf = ""
                self._digit_buf += str(k - pygame.K_0)
                self._digit_ts   = now
                val = int(self._digit_buf)
                if val >= self.MIN_LEVEL:
                    self.cfg.level = min(self.MAX_LEVEL, val)
                return False

            if k in (pygame.K_UP, pygame.K_w):
                self._clear_buf()
                self.cfg.level = min(self.MAX_LEVEL, self.cfg.level + 1)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self._clear_buf()
                self.cfg.level = max(self.MIN_LEVEL, self.cfg.level - 1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.cfg.point_count = min(self.MAX_POINTS, self.cfg.point_count + 1)
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.cfg.point_count = max(self.MIN_POINTS, self.cfg.point_count - 1)
            elif k == pygame.K_RETURN:
                self._confirm_t = time.time()
                return True
            elif k == pygame.K_BACKSPACE and self._digit_buf:
                self._digit_buf = self._digit_buf[:-1]
                val = int(self._digit_buf) if self._digit_buf else self.MIN_LEVEL
                self.cfg.level = max(self.MIN_LEVEL, val)

        if event.type == pygame.MOUSEWHEEL and self._panel == self.PANEL_MAIN:
            self._clear_buf()
            self.cfg.level = max(self.MIN_LEVEL,
                                 min(self.MAX_LEVEL, self.cfg.level + event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._panel == self.PANEL_MAIN:
                if self.btn_up.collidepoint(event.pos):
                    self._clear_buf()
                    self.cfg.level = min(self.MAX_LEVEL, self.cfg.level + 1)
                elif self.btn_dn.collidepoint(event.pos):
                    self._clear_buf()
                    self.cfg.level = max(self.MIN_LEVEL, self.cfg.level - 1)
                elif self._settings_btn and self._settings_btn.collidepoint(event.pos):
                    self._panel = self.PANEL_SETTINGS

        if event.type == pygame.MOUSEMOTION and self._panel == self.PANEL_MAIN:
            self.hover_up = self.btn_up.collidepoint(event.pos)
            self.hover_dn = self.btn_dn.collidepoint(event.pos)

        return False

    def _clear_buf(self):
        self._digit_buf = ""

    # ── draw ──────────────────────────────────

    def draw(self, surface):
        if self._panel == self.PANEL_SETTINGS:
            self._draw_settings(surface)
        else:
            self._draw_main(surface)

    def _draw_main(self, surface):
        cx, cy = self.cx, self.cy
        cfg    = self.cfg
        dep_t  = min(1.0, (cfg.level - 1) / 8.0)

        # Title
        title = self.font_big.render("CIRCLE CONSTRUCTION", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, cy - 200))
        sub = self.font_small.render("choose your depth", True, GREY)
        surface.blit(sub, (cx - sub.get_width() // 2, cy - 155))

        # Level number
        num_col = _lerp3((255, 220, 50), (80, 200, 255), dep_t)
        if self._confirm_t is not None:
            flash = (time.time() - self._confirm_t) / 0.25
            num_col = _lerp3(num_col, (255, 255, 255), max(0.0, 1.0 - flash))
            if flash >= 1.0:
                self._confirm_t = None
        num_s = self.font_big.render(str(cfg.level), True, num_col)
        surface.blit(num_s, (cx - num_s.get_width() // 2, cy - 30))

        # Level name
        name_s = self.font_med.render(level_name(cfg.level), True,
                                      _lerp3(SOFT, (100, 180, 240), dep_t))
        surface.blit(name_s, (cx - name_s.get_width() // 2, cy + 52))

        # Arrow buttons
        for btn, lbl, hover in [
            (self.btn_up, "▶", self.hover_up),
            (self.btn_dn, "◀", self.hover_dn),
        ]:
            col = ACCENT if hover else GREY
            s   = self.font_med.render(lbl, True, col)
            surface.blit(s, (btn.x + (btn.w - s.get_width()) // 2,
                             btn.y + (btn.h - s.get_height()) // 2))

        # Point count
        pts_s = self.font_small.render(
            f"POINTS: {cfg.point_count}   [← →] or [A D]",
            True, _lerp3(SOFT, (100, 180, 240), dep_t))
        surface.blit(pts_s, (cx - pts_s.get_width() // 2, cy + 88))

        # Digit buffer hint
        if self._digit_buf:
            buf_s = self.font_small.render(f"typing: {self._digit_buf}_", True, ACCENT)
        else:
            buf_s = self.font_small.render("or type a number directly", True, GREY)
        surface.blit(buf_s, (cx - buf_s.get_width() // 2, cy + 112))

        # Progress bar
        bar_w, bar_h = 300, 4
        bx, by   = cx - bar_w // 2, cy + 138
        filled   = round(bar_w * min(1.0, (cfg.level - 1) / 8.0))
        pygame.draw.rect(surface, DIM, (bx, by, bar_w, bar_h), border_radius=2)
        if filled > 0:
            pygame.draw.rect(surface, _lerp3((255, 220, 50), (80, 200, 255), dep_t),
                             (bx, by, filled, bar_h), border_radius=2)

        # Enter hint
        hint = self.font_small.render("[ENTER] to start", True, GREY)
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 165))

        # Dot progress
        MAX_DOTS = 9
        shown    = min(cfg.level, MAX_DOTS)
        ox       = cx - (MAX_DOTS - 1) * 20 // 2
        oy       = cy + 200
        for i in range(MAX_DOTS):
            col = _lerp3((255, 220, 50), (80, 200, 255), i / (MAX_DOTS - 1)) \
                  if (i + 1) <= shown else DIM
            pygame.draw.circle(surface, col, (ox + i * 20, oy), 4)
        if cfg.level > MAX_DOTS:
            extra = self.font_small.render(f"+{cfg.level - MAX_DOTS}", True, (80, 200, 255))
            surface.blit(extra, (ox + MAX_DOTS * 20 + 4, oy - 7))

        # Settings button
        btn_w, btn_h = 130, 30
        bx2 = cx - btn_w // 2
        by2 = cy + 228
        self._settings_btn = pygame.Rect(bx2, by2, btn_w, btn_h)
        pygame.draw.rect(surface, DIM, self._settings_btn, border_radius=6)
        pygame.draw.rect(surface, (60, 60, 60), self._settings_btn, 1, border_radius=6)
        slbl = self.font_small.render("⚙  SETTINGS  [TAB]", True, GREY)
        surface.blit(slbl, (bx2 + (btn_w - slbl.get_width()) // 2,
                            by2 + (btn_h - slbl.get_height()) // 2))

        # Quick-peek summary of non-default settings
        summary_parts = []
        if cfg.base_radius != 140:
            summary_parts.append(f"r={cfg.base_radius}")
        if cfg.speed != 1.0:
            summary_parts.append(f"spd={cfg.speed:.2f}x")
        if summary_parts:
            peek = self.font_small.render("  ".join(summary_parts), True, (100, 160, 100))
            surface.blit(peek, (cx - peek.get_width() // 2, by2 + btn_h + 6))

    def _draw_settings(self, surface):
        cx, cy = self.cx, self.cy
        self._settings.draw(surface, self.font_med, self.font_small, cx, cy)


# ──────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ──────────────────────────────────────────────

def run_intro(screen, clock, prev_config: Config = None) -> Config:
    """
    Show the animated intro screen.
    Returns a Config when the user confirms.
    Pass `prev_config` to pre-populate values from the last run.
    """
    w, h   = screen.get_size()
    cx, cy = w // 2, h // 2

    pygame.display.set_caption("Circle Construction  —  Select Level")

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
        bg_anim.draw(screen, cfg.level, cfg.point_count)
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)

        if confirmed_at is not None and time.time() - confirmed_at >= 0.28:
            return cfg