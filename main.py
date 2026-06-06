"""
main.py — entry point.

Run with:  python main.py
           python main.py --points 6

Controls:
  ENTER / TAB      — start or open settings (intro)
  P                — pause / resume
  B                — toggle dark/light theme
  [ / ]            — decrease / increase speed
  ESC / M          — return to main menu
  scroll           — zoom
  drag             — pan

File layout:
  main.py          — init, main loop
  config.py        — Config dataclass
  construction.py  — stage logic (levels 1–N)
  geometry.py      — pure math
  renderer.py      — camera, drawing, UI
  animation.py     — easing, timing, fade, event pump
  intro.py         — level/point selector + settings screen
"""

import argparse
import pygame

from intro        import run_intro
from construction import run
from animation    import RestartSignal
from config       import Config


def parse_args():
    p = argparse.ArgumentParser(description="Circle Construction")
    p.add_argument("-p", "--points", type=int, default=0,
                   help="Number of base points (overrides intro selection)")
    return p.parse_args()


def main():
    args = parse_args()

    pygame.init()
    screen = pygame.display.set_mode((1200, 1200))
    clock  = pygame.time.Clock()

    cfg = None
    while True:
        cfg = run_intro(screen, clock, prev_config=cfg)
        if args.points:
            cfg.point_count = args.points
        try:
            run(cfg, screen, clock)
        except RestartSignal:
            continue


if __name__ == "__main__":
    main()