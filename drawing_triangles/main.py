"""
main.py — entry point (no logic, just delegates to app.run).

Run with:  python drawing_triangles/main.py
           python drawing_triangles/main.py --generations 20

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
  construction.py  — triangle generation stages
  geometry.py      — pure math (bisectors, intersections)
  renderer.py      — camera, drawing, UI
  animation.py     — easing, timing, generation animation
  intro.py         — generation selector + settings screen
  export.py        — SVG/PNG/PDF export
"""

from app import run

if __name__ == "__main__":
    run()
