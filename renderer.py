"""
renderer.py — camera, depth-coloured drawing, theme toggle, HUD, UI buttons.
"""

import math
import time
import pygame


# ──────────────────────────────────────────────
# THEMES
# ──────────────────────────────────────────────

DARK_THEME = {
    "background":  (10, 10, 10),
    "toggle_bg":   (25, 25, 25),
    "toggle_fg":   (180, 180, 180),
    "hud_fg":      (130, 130, 130),
    "label":       "DARK",
    "alt_colors": [
        (180, 60, 220),   # purple
        (255, 140, 40),   # orange
        (40, 200, 220),   # cyan
        (230, 80, 160),   # pink
    ],
}

LIGHT_THEME = {
    "background":  (245, 240, 235),
    "toggle_bg":   (230, 225, 220),
    "toggle_fg":   ( 50,  50,  50),
    "hud_fg":      (100, 100, 100),
    "label":       "LIGHT",
    "alt_colors": [
        (130, 40, 170),   # purple
        (210, 110, 25),   # orange
        (30, 150, 170),   # cyan
        (180, 55, 120),   # pink
    ],
}


def depth_color(theme, depth_01, base_alpha=220):
    palette = theme["alt_colors"]
    r, g, b = palette[int(depth_01 * len(palette)) % len(palette)]
    s = base_alpha / 255
    return (round(r * s), round(g * s), round(b * s))


def point_color(theme, depth_01, alpha=255):
    palette = theme["alt_colors"]
    r, g, b = palette[int(depth_01 * len(palette)) % len(palette)]
    s = alpha / 255
    return (round(r * s), round(g * s), round(b * s))


# ──────────────────────────────────────────────
# CAMERA
# ──────────────────────────────────────────────

class Camera:
    _ZOOM_STEP = 1.15

    def __init__(self, screen_w, screen_h, world_center):
        self.sc     = (screen_w / 2, screen_h / 2)
        self.origin = world_center
        self.zoom   = 1.0

    def w2s(self, pt):
        return (
            (pt[0] - self.origin[0]) * self.zoom + self.sc[0],
            (pt[1] - self.origin[1]) * self.zoom + self.sc[1],
        )

    def r2s(self, r):
        return r * self.zoom

    def fit_radius(self, world_radius, margin=0.88):
        half = min(self.sc[0], self.sc[1]) * 2 / 2
        self.zoom = half * margin / max(world_radius, 0.001)

    def scroll(self, direction):
        self.zoom *= self._ZOOM_STEP if direction > 0 else 1 / self._ZOOM_STEP


# ──────────────────────────────────────────────
# RENDERER
# ──────────────────────────────────────────────

RESTART_EVENT = pygame.USEREVENT + 1


class Renderer:
    _BTN_W = 130
    _BTN_H = 36
    _PAD   = 20

    def __init__(self, screen, camera, cfg):
        from config import Config
        self.screen  = screen
        self.camera  = camera
        self.level   = cfg.level
        self.cfg     = cfg
        self.theme   = DARK_THEME
        self.font    = pygame.font.SysFont("monospace", 16)
        self.font_sm = pygame.font.SysFont("monospace", 13)

        sw, sh = screen.get_size()
        pad, bw, bh = self._PAD, self._BTN_W, self._BTN_H

        self.toggle_rect  = pygame.Rect(sw - bw - pad, pad, bw, bh)
        self.pause_rect   = pygame.Rect(sw - bw - pad, pad * 2 + bh, bw, bh)
        self.restart_rect = pygame.Rect(sw // 2 - 90, sh - pad - bh, 180, bh)
        self.menu_rect    = pygame.Rect(pad, pad, bw, bh)

        self.show_choices     = False
        self.choice_menu_rect = None
        self.choice_look_rect = None
        self.choice_svg_rect  = None
        self.choice_png_rect  = None
        self.choice_pdf_rect  = None
        self.choice_hd_rect   = None

        self.export_message   = None
        self.export_msg_timer = 0.0

        self.done_circles   = []   # [(world_center, world_radius, depth), …]
        self.done_points    = []   # [[wx, wy, alpha, depth], …]
        self.anim_circle    = None
        self.anim_t         = 0.0
        self.anim_start_ang = -math.pi / 2

        self._static_surface = None
        self._static_zoom    = None
        self._static_count   = 0

        self.paused         = False
        self.animation_done = False
        self.speed_display  = 1.0   # updated each frame by AnimState

        self._hover_pause        = False
        self._hover_restart      = False
        self._hover_toggle       = False
        self._hover_menu         = False
        self._hover_choice_menu  = False
        self._hover_choice_look  = False
        self._hover_choice_svg   = False
        self._hover_choice_png   = False
        self._hover_export_svg   = False
        self._hover_export_png   = False
        self._hover_export_pdf   = False
        self._hover_export_hd    = False
        self._hover_choice_pdf   = False
        self._hover_choice_hd    = False

        self.export_svg_rect = None
        self.export_png_rect = None
        self.export_pdf_rect = None
        self.export_hd_rect  = None

    def toggle_theme(self):
        self.theme = LIGHT_THEME if self.theme is DARK_THEME else DARK_THEME
        self._static_surface = None  # force full redraw

    # ── drawing helpers ───────────────────────

    def _draw_arc(self, world_center, world_radius, start_angle, sweep, color):
        sr = round(self.camera.r2s(world_radius))
        if sr < 1 or sweep <= 0:
            return
        scx, scy = self.camera.w2s(world_center)
        n_segs   = max(8, round(180 * sweep))
        end_a    = start_angle + 2 * math.pi * sweep
        prev     = None
        for i in range(n_segs + 1):
            a  = start_angle + (end_a - start_angle) * i / n_segs
            pt = (round(scx + sr * math.cos(a)), round(scy + sr * math.sin(a)))
            if prev:
                pygame.draw.line(self.screen, color, prev, pt, 1)
            prev = pt

    def _btn(self, rect, label, hover):
        th = self.theme
        fg = (255, 220, 50) if hover else th["toggle_fg"]
        pygame.draw.rect(self.screen, th["toggle_bg"], rect, border_radius=8)
        pygame.draw.rect(self.screen, fg, rect, 1, border_radius=8)
        lbl = self.font.render(label, True, fg)
        self.screen.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2,
                               rect.y + (rect.h - lbl.get_height()) // 2))

    # ── overlays ──────────────────────────────

    def _draw_buttons(self):
        self._btn(self.menu_rect, "← MENU", self._hover_menu)
        self._btn(self.toggle_rect, f"[B] {self.theme['label']}", self._hover_toggle)

        if not self.animation_done:
            icon = "▐▐ PAUSE" if not self.paused else "▶  PLAY"
            self._btn(self.pause_rect, f"[P] {icon}", self._hover_pause)

        if self.animation_done and not self.show_choices:
            sw, sh = self.screen.get_size()
            pad, bh = self._PAD, self._BTN_H

            bw = 120
            rw = 180
            gap = 12
            total = bw + gap + bw + gap + rw + gap + bw
            left = sw // 2 - total // 2

            self.export_svg_rect = pygame.Rect(left, sh - pad - bh, bw, bh)
            self.export_pdf_rect = pygame.Rect(left + bw + gap, sh - pad - bh, bw, bh)
            self.restart_rect    = pygame.Rect(left + bw + gap + bw + gap, sh - pad - bh, rw, bh)
            self.export_hd_rect  = pygame.Rect(left + bw + gap + bw + gap + rw + gap, sh - pad - bh, bw, bh)

            self._btn(self.export_svg_rect, "EXPORT SVG", self._hover_export_svg)
            self._btn(self.export_pdf_rect, "EXPORT PDF", self._hover_export_pdf)
            self._btn(self.restart_rect, "↺  RESTART", self._hover_restart)
            self._btn(self.export_hd_rect, "EXPORT HD", self._hover_export_hd)

            if self.export_message:
                elapsed = time.time() - self.export_msg_timer
                if elapsed < 2.0:
                    alpha = max(0, round(255 * (1.0 - elapsed / 2.0)))
                    msg = self.font.render(self.export_message, True, (140, 255, 140))
                    msg.set_alpha(alpha)
                    mx = sw // 2 - msg.get_width() // 2
                    my = sh - pad - bh - 24
                    self.screen.blit(msg, (mx, my))

        if self.animation_done and self.show_choices:
            self._draw_completion_choices()

    def _draw_completion_choices(self):
        sw, sh = self.screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        lbl = self.font.render("CONSTRUCTION COMPLETE", True, (255, 220, 50))
        self.screen.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh // 2 - 100))

        btn_w, btn_h, gap = 200, 46, 24
        cx, cy = sw // 2, sh // 2 + 6
        row1_y = cy - btn_h // 2
        total  = btn_w * 2 + gap

        self.choice_menu_rect = pygame.Rect(cx - total // 2, row1_y, btn_w, btn_h)
        self.choice_look_rect = pygame.Rect(cx - total // 2 + btn_w + gap, row1_y, btn_w, btn_h)

        self._btn(self.choice_menu_rect, "← MAIN MENU", self._hover_choice_menu)
        self._btn(self.choice_look_rect, "LOOK AROUND",  self._hover_choice_look)

        total  = btn_w * 2 + gap

        row2_y = row1_y + btn_h + gap
        self.choice_svg_rect = pygame.Rect(cx - total // 2, row2_y, btn_w, btn_h)
        self.choice_pdf_rect = pygame.Rect(cx - total // 2 + btn_w + gap, row2_y, btn_w, btn_h)

        self._btn(self.choice_svg_rect, "EXPORT SVG", self._hover_choice_svg)
        self._btn(self.choice_pdf_rect, "EXPORT PDF", self._hover_choice_pdf)

        row3_y = row2_y + btn_h + gap
        self.choice_hd_rect = pygame.Rect(cx - total // 2, row3_y, total, btn_h)
        self._btn(self.choice_hd_rect, "EXPORT HD PNG", self._hover_choice_hd)

        if self.export_message:
            elapsed = time.time() - self.export_msg_timer
            if elapsed < 2.0:
                alpha = max(0, round(255 * (1.0 - elapsed / 2.0)))
                msg = self.font.render(self.export_message, True, (140, 255, 140))
                msg.set_alpha(alpha)
                self.screen.blit(msg, (sw // 2 - msg.get_width() // 2, row3_y + btn_h + 20))

    def _draw_hud(self):
        fg    = self.theme["hud_fg"]
        cfg   = self.cfg
        count = len(self.done_circles) + (1 if self.anim_circle else 0)
        lines = []

        if cfg.show_level:
            suffix = f" / {self.level}" if cfg.show_total_levels else ""
            lines.append(f"level  {self.level}{suffix}")
        elif cfg.show_total_levels:
            lines.append(f"/ {self.level} levels")

        if cfg.show_circle_count:
            lines.append(f"circles  {count}")

        if cfg.show_speed:
            lines.append(f"speed  {self.speed_display:.2f}x  [[ ]]")

        if cfg.show_zoom:
            lines.append(f"zoom  {self.camera.zoom:.2f}x  [scroll]")

        if self.paused:
            lines.append("— PAUSED —")

        for i, line in enumerate(lines):
            lbl = self.font_sm.render(line, True, fg)
            self.screen.blit(lbl, (self._PAD, self._PAD + self._BTN_H + 8 + i * 18))

    # ── hover ─────────────────────────────────

    def update_hover(self, mouse_pos):
        self._hover_toggle  = self.toggle_rect.collidepoint(mouse_pos)
        self._hover_pause   = not self.animation_done and self.pause_rect.collidepoint(mouse_pos)
        self._hover_restart = self.animation_done and not self.show_choices and \
                              self.restart_rect.collidepoint(mouse_pos)
        self._hover_menu    = self.menu_rect.collidepoint(mouse_pos)
        if self.show_choices:
            self._hover_choice_menu = bool(self.choice_menu_rect and
                                           self.choice_menu_rect.collidepoint(mouse_pos))
            self._hover_choice_look = bool(self.choice_look_rect and
                                           self.choice_look_rect.collidepoint(mouse_pos))
            self._hover_choice_svg  = bool(self.choice_svg_rect and
                                           self.choice_svg_rect.collidepoint(mouse_pos))
            self._hover_choice_png  = bool(self.choice_png_rect and
                                           self.choice_png_rect.collidepoint(mouse_pos))
            self._hover_choice_pdf  = bool(self.choice_pdf_rect and
                                           self.choice_pdf_rect.collidepoint(mouse_pos))
            self._hover_choice_hd   = bool(self.choice_hd_rect and
                                           self.choice_hd_rect.collidepoint(mouse_pos))
            self._hover_export_svg  = False
            self._hover_export_png  = False
            self._hover_export_pdf  = False
            self._hover_export_hd   = False
        else:
            self._hover_choice_menu = self._hover_choice_look = False
            self._hover_choice_svg  = self._hover_choice_png  = False
            self._hover_choice_pdf  = False
            self._hover_choice_hd   = False
            self._hover_export_svg  = self.animation_done and bool(self.export_svg_rect and
                                            self.export_svg_rect.collidepoint(mouse_pos))
            self._hover_export_png  = self.animation_done and bool(self.export_png_rect and
                                            self.export_png_rect.collidepoint(mouse_pos))
            self._hover_export_pdf  = self.animation_done and bool(self.export_pdf_rect and
                                            self.export_pdf_rect.collidepoint(mouse_pos))
            self._hover_export_hd   = self.animation_done and bool(self.export_hd_rect and
                                            self.export_hd_rect.collidepoint(mouse_pos))

    # ── static background surface ─────────────

    def _ensure_static(self):
        """Create or resize the opaque static surface that holds bg + finished circles."""
        sw, sh = self.screen.get_size()
        cam    = self.camera
        th     = self.theme

        if (self._static_surface is None or
                self._static_surface.get_size() != (sw, sh) or
                self._static_zoom != cam.zoom):
            self._static_surface = pygame.Surface((sw, sh))
            self._static_surface.fill(th["background"])
            self._static_zoom  = cam.zoom
            self._static_count = 0

        if self._static_count < len(self.done_circles):
            new_ones  = self.done_circles[self._static_count:]
            depths    = [d for _, _, d in self.done_circles]
            max_depth = max(depths, default=1.0) or 1.0

            for wc, wr, dep in new_ones:
                sr = round(cam.r2s(wr))
                if sr < 1:
                    continue
                alpha = max(60, round(220 - dep * 100))
                col   = depth_color(th, dep / max_depth, base_alpha=alpha)
                sc    = cam.w2s(wc)
                pygame.draw.circle(self._static_surface, col,
                                   (round(sc[0]), round(sc[1])), sr, 1)

            self._static_count = len(self.done_circles)

    # ── main redraw ───────────────────────────

    def redraw(self):
        cam = self.camera
        th  = self.theme

        self._ensure_static()
        self.screen.blit(self._static_surface, (0, 0))

        depths    = [d for _, _, d in self.done_circles]
        max_depth = max(depths, default=1.0) or 1.0

        if self.anim_circle and self.anim_t > 0:
            wc, wr, dep = self.anim_circle
            col = depth_color(th, dep / max_depth)
            self._draw_arc(wc, wr, self.anim_start_ang, self.anim_t, col)

        for wx, wy, alpha, dep in self.done_points:
            col = point_color(th, dep / max_depth, alpha=alpha)
            sc  = cam.w2s((wx, wy))
            pygame.draw.circle(self.screen, col, (round(sc[0]), round(sc[1])), 5)

        self._draw_buttons()
        self._draw_hud()
        pygame.display.flip()