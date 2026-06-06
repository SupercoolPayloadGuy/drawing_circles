"""
main.py — entry point.

Run with:  python main.py
           python main.py --points 6

Controls:
  ENTER            — start from intro
  P                — pause / resume
  B                — toggle dark/light theme
  ESC / M          — return to main menu
  scroll           — zoom
  drag             — pan

File layout:
  main.py          — init, main loop
  construction.py  — stage logic (levels 1–N)
  geometry.py      — pure math
  renderer.py      — camera, drawing, UI
  animation.py     — easing, timing, fade, event pump
  intro.py         — level/point selector screen
"""

import argparse
import pygame

from intro        import run_intro
from construction import run
from animation    import RestartSignal


def parse_args():
    p = argparse.ArgumentParser(description="Circle Construction")
    p.add_argument("-p", "--points", type=int, default=4,
                   help="Number of base points (overrides intro selection)")
    return p.parse_args()


def main():
    args = parse_args()

    pygame.init()
    screen = pygame.display.set_mode((1200, 1200))
    clock  = pygame.time.Clock()

    while True:
        level, pts = run_intro(screen, clock)
        if args.points:
            pts = args.points
        try:
            run(level, screen, clock, point_count=pts)
        except RestartSignal:
            continue


if __name__ == "__main__":
    main()