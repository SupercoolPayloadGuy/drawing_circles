"""
renderer.py — camera, depth-coloured drawing, theme toggle, HUD, UI buttons.
"""

import math
import time
import pygame
import numpy as np


DARK_THEME = {
    "background":  (8, 8, 12),
    "toggle_bg":   (25, 25, 30),
    "toggle_fg":   (180, 180, 185),
    "hud_fg":      (130, 130, 140),
    "label":       "DARK",
    "bisect_color": (120, 200, 255),
    "perp_color":  (150, 220, 255),
    "point_color": (200, 235, 255),
    "base_r": 60,
    "base_g": 160,
    "base_b": 255,
}

LIGHT_THEME = {
    "background":  (240, 240, 245),
    "toggle_bg":   (225, 225, 230),
    "toggle_fg":   (50,  50,  55),
    "hud_fg":      (100, 100, 110),
    "label":       "LIGHT",
    "bisect_color": (40, 100, 180),
    "perp_color":  (70, 120, 200),
    "point_color": (30, 60, 120),
    "base_r": 30,
    "base_g": 80,
    "base_b": 200,
}


def gen_color(theme, gen_01, base_alpha=180):
    """Single blue/cyan color family, varying lightness by generation."""
    r = theme["base_r"]
    g = theme["base_g"]
    b = theme["base_b"]
    brighten = 0.3 * gen_01
    s = base_alpha / 255
    return (
        round(min(255, (r + 50 * gen_01)) * s),
        round(min(255, (g + 80 * gen_01)) * s),
        round(min(255, (b + 40 * gen_01)) * s),
    )


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


RESTART_EVENT = pygame.USEREVENT + 1


class Renderer:
    _BTN_W = 130
    _BTN_H = 36
    _PAD   = 20

    def __init__(self, screen, camera, cfg):
        self.screen  = screen
        self.camera  = camera
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

        self.done_triangles   = []
        self.done_points      = []
        self.anim_triangle    = None
        self.anim_bisectors   = None
        self.anim_perps       = None
        self.anim_new_tri     = None
        self.anim_intersections = None
        self.anim_t           = 0.0

        self._static_surface = None
        self._static_zoom    = None
        self._static_count   = 0

        self.paused         = False
        self.animation_done = False
        self.speed_display  = 1.0
        self._total_generations = 0

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
        self._static_surface = None

    def _draw_segment(self, p1, p2, color, width=1, alpha=255):
        s1 = self.camera.w2s(p1)
        s2 = self.camera.w2s(p2)
        c = (*color, alpha) if alpha < 255 else color
        if alpha < 255:
            tmp = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            pygame.draw.line(tmp, c, s1, s2, width)
            self.screen.blit(tmp, (0, 0))
        else:
            pygame.draw.line(self.screen, c, s1, s2, width)

    def _draw_triangle(self, tri, color, width=1, alpha=255):
        pts = [self.camera.w2s(v) for v in tri]
        pts = [(round(x), round(y)) for x, y in pts]
        c = (*color, alpha) if alpha < 255 else color
        if alpha < 255:
            tmp = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(tmp, c, pts, width)
            self.screen.blit(tmp, (0, 0))
        else:
            pygame.draw.polygon(self.screen, c, pts, width)

    def _draw_infinite_line(self, point, direction, color, width=1, alpha=255, length=2000):
        p = np.array(point)
        d = np.array(direction)
        p1 = self.camera.w2s(p - d * length)
        p2 = self.camera.w2s(p + d * length)
        c = (*color, alpha) if alpha < 255 else color
        if alpha < 255:
            tmp = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            pygame.draw.line(tmp, c, p1, p2, width)
            self.screen.blit(tmp, (0, 0))
        else:
            pygame.draw.line(self.screen, c, p1, p2, width)

    def _draw_dot(self, pt, color, r=5):
        s = self.camera.w2s(pt)
        pygame.draw.circle(self.screen, color, (round(s[0]), round(s[1])), r)

    def _btn(self, rect, label, hover):
        th = self.theme
        fg = (255, 220, 50) if hover else th["toggle_fg"]
        pygame.draw.rect(self.screen, th["toggle_bg"], rect, border_radius=8)
        pygame.draw.rect(self.screen, fg, rect, 1, border_radius=8)
        lbl = self.font.render(label, True, fg)
        self.screen.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2,
                               rect.y + (rect.h - lbl.get_height()) // 2))

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
        fg  = self.theme["hud_fg"]
        cfg = self.cfg
        count = len(self.done_triangles) + (1 if self.anim_new_tri else 0)
        lines = []
        if cfg.show_generation:
            suffix = f" / {self._total_generations}" if cfg.show_total_generations else ""
            lines.append(f"generation  {len(self.done_triangles)}{suffix}")
        elif cfg.show_total_generations:
            lines.append(f"/ {self._total_generations} generations")
        if cfg.show_triangle_count:
            lines.append(f"triangles  {count}")
        if cfg.show_speed:
            lines.append(f"speed  {self.speed_display:.2f}x  [[ ]]")
        if cfg.show_zoom:
            lines.append(f"zoom  {self.camera.zoom:.2f}x  [scroll]")
        if self.paused:
            lines.append("— PAUSED —")
        for i, line in enumerate(lines):
            lbl = self.font_sm.render(line, True, fg)
            self.screen.blit(lbl, (self._PAD, self._PAD + self._BTN_H + 8 + i * 18))

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

    def _ensure_static(self):
        sw, sh = self.screen.get_size()
        cam = self.camera
        th  = self.theme
        if (self._static_surface is None or
                self._static_surface.get_size() != (sw, sh) or
                self._static_zoom != cam.zoom):
            self._static_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
            self._static_surface.fill((*th["background"], 255))
            self._static_zoom  = cam.zoom
            self._static_count = 0
        if self._static_count < len(self.done_triangles):
            new_ones   = self.done_triangles[self._static_count:]
            max_gen    = max(len(self.done_triangles), 1)
            for tri, gen_num in new_ones:
                frac = gen_num / max(int(max_gen - 1), 1) if max_gen > 1 else 0.5
                alpha = max(80, round(200 - frac * 60))
                col = gen_color(th, gen_num / max_gen, base_alpha=alpha)
                pts = [cam.w2s(v) for v in tri]
                pygame.draw.polygon(self._static_surface, col, pts, 1)
            self._static_count = len(self.done_triangles)

    @staticmethod
    def _phase_alpha(t, start, end):
        if t < start:
            return 0
        if t >= end:
            return 200
        raw = (t - start) / (end - start)
        return round((raw * raw * (3 - 2 * raw)) * 200)

    def redraw(self):
        cam = self.camera
        th  = self.theme
        self._ensure_static()
        self.screen.blit(self._static_surface, (0, 0))

        max_gen = max(len(self.done_triangles), 1)
        t = self.anim_t

        # Phase 1: Current triangle (t: 0.00 – 0.15)
        if self.anim_triangle is not None:
            alpha = self._phase_alpha(t, 0.00, 0.15)
            if alpha > 0:
                col = gen_color(th, len(self.done_triangles) / max_gen, base_alpha=alpha)
                self._draw_triangle(self.anim_triangle, col, width=2)

        # Phase 2: Angle bisectors appear one by one (t: 0.15 – 0.40)
        if self.anim_bisectors is not None:
            tri = self.anim_triangle
            for i, (v, d) in enumerate(zip(tri, self.anim_bisectors)):
                s = 0.15 + 0.08 * i
                e = s + 0.10
                alpha = self._phase_alpha(t, s, e)
                if alpha > 0:
                    self._draw_infinite_line(v, d, th["bisect_color"],
                                             width=1, alpha=alpha, length=500)

        # Phase 3: Perpendicular lines (t: 0.40 – 0.65)
        if self.anim_perps is not None:
            tri = self.anim_triangle
            for i, (v, d) in enumerate(zip(tri, self.anim_perps)):
                s = 0.40 + 0.08 * i
                e = s + 0.10
                alpha = self._phase_alpha(t, s, e)
                if alpha > 0:
                    self._draw_infinite_line(v, d, th["perp_color"],
                                             width=1, alpha=alpha, length=500)

        # Phase 4: Intersection points (t: 0.65 – 0.80)
        if self.anim_intersections is not None:
            alpha = self._phase_alpha(t, 0.65, 0.80)
            if alpha > 0:
                for pt in self.anim_intersections:
                    fade = min(255, alpha + 55)
                    self._draw_dot(pt, (*th["point_color"], fade), r=5)

        # Phase 5: New triangle (t: 0.80 – 1.00)
        if self.anim_new_tri is not None:
            alpha = self._phase_alpha(t, 0.80, 1.00)
            if alpha > 0:
                col = gen_color(th, (len(self.done_triangles) + 1) / max_gen, base_alpha=alpha)
                self._draw_triangle(self.anim_new_tri, col, width=2)

        for pt in self.done_points:
            self._draw_dot(pt, th["point_color"], r=4)

        self._draw_buttons()
        self._draw_hud()
        pygame.display.flip()
