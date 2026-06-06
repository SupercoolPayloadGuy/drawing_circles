"""
main.py — entry point (no logic, just delegates to app.run).

Controls:
  ENTER     — start the animation (from intro)
  ESC       — return to intro (during animation)
  TAB       — toggle settings panel (in intro)
  arrows    — adjust speed (in settings panel)

File layout:
  main.py     — entry point (delegates to app.run)
  app.py      — init, main loop, animation state machine
  config.py   — constants and Config dataclass
  geometry.py — pure math helpers
  renderer.py — drawing utilities
  intro.py    — animated intro screen
"""

from app import run

if __name__ == "__main__":
    run()
