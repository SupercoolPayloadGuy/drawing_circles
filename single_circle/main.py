"""
main.py — entry point (no logic, just delegates to app.run).

Controls (intro):
  LEFT/RIGHT / A/D  — change point count
  ENTER             — start animation
  TAB               — toggle settings panel

Controls (settings):
  UP/DOWN / W/S     — move cursor
  LEFT/RIGHT / A/D  — change value
  ENTER / TAB       — back to main panel

Controls (animation):
  ESC               — return to intro
  P                 — export current frame as PNG
  S                 — export flower as SVG
  mouse drag        — pan (in look-around mode)
  mouse scroll      — zoom (in look-around mode)

End screen buttons (clickable):
  MENU              — back to intro
  LOOK              — enter look-around (pan/zoom)
  EXPORT PNG        — save screenshot
  EXPORT SVG        — save vector graphic

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
