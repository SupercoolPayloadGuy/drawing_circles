"""
main.py — entry point (no logic, just delegates to app.run).

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
  main.py          — entry point (delegates to app.run)
  app.py           — init, main loop
  cli.py           — argument parsing
  config.py        — Config dataclass
  construction.py  — stage logic (levels 1–N)
  geometry.py      — pure math
  renderer.py      — camera, drawing, UI
  animation.py     — easing, timing, fade, event pump
  intro.py         — level/point selector + settings screen
"""

from app import run

if __name__ == "__main__":
    run()