# Drawing Circles — Recursive Circle Construction

A small project that visualises a geometric circle-construction algorithm. It includes:

- A self-contained HTML renderer (open `index.html`) for quick demos.
- A Python/pygame animated application (`main.py`) with configurable levels and point counts.

This README explains installation, usage, examples, configuration, and development notes.

**Table of Contents**

- Project overview
- Quick start
- Python (pygame) usage
- HTML usage
- Examples
- Configuration
- Project structure
- Development & tests
- Troubleshooting

## Project Overview

The animation builds circles by repeatedly projecting points and drawing circles through point pairs. It demonstrates recursive geometric constructions with depth-based colouring, auto-zoom, and interactive controls.

## Quick Start

- HTML (no install): open [index.html](index.html) in a browser.
- Python (recommended for the full experience):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On Linux/macOS replace `source .venv/bin/activate` with the appropriate activation command for your shell.

## Python (pygame) Usage

- Run the application: `python main.py`
- Useful CLI flags (if implemented):
	- `-p N` or `--points N` — start with N base points
	- `-l N` or `--level N` — start at level N

Controls (keyboard & mouse):

- `Enter` — start animation from intro
- `P` — pause / resume
- `B` — toggle dark/light theme
- Arrow keys or `W/A/S/D` — adjust level and point count in the UI
- Mouse wheel — zoom
- Click & drag — pan

If you modify settings in `config.py` those changes will affect the behaviour of `main.py`.

## HTML Usage

Open [index.html](index.html) in a modern browser. The HTML build is self-contained and provides the same visual demo without Python or external dependencies.

## Examples

- `examples/simple_circle.py` — minimal Python example using turtle (no extra deps).
- `examples/circle_algorithm.py` — pygame example demonstrating alternate algorithm flows.
- `examples/double_circle.py` — variant that draws two concentric constructions.

## Configuration

Primary runtime options live in `config.py`. Typical configurable values:

- `base_radius` — radius of the initial base circle
- `point_count` — default number of points on the base circle
- `level` — default construction depth
- `speed` — animation speed multiplier

Adjust these values directly or expose them via CLI in `main.py` if you want runtime overrides.

## Project Structure

- `main.py` — app entry point (pygame desktop)
- `index.html` — self-contained browser demo
- `animation.py` — animation helpers, timing, and easing
- `renderer.py` — drawing, camera, HUD and theme handling
- `geometry.py` — geometric primitives and helpers
- `construction.py` — construction orchestration (animation stages)
- `intro.py` — intro/menu UI
- `config.py` — default settings
- `requirements.txt` — Python dependencies
- `examples/` — small example scripts

## Development & Tests

1. Create and activate a virtualenv.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run `python main.py` to test the animation locally.

There are no automated tests included with this repo. Add tests under a `tests/` folder and run with `pytest` if desired.

## Troubleshooting

- If `pygame` fails to import: ensure the virtualenv is active and `pygame` is installed (`pip install pygame`).
- If performance is slow: try lowering `point_count` or `level` in the UI or `config.py`.
- If the HTML demo looks different from Python: browsers and canvas rendering may differ slightly in antialiasing/timing.

## Contributing

Contributions are welcome. Typical workflow:

1. Fork the repo and create a feature branch.
2. Make changes and run the app locally to verify.
3. Open a pull request with a short description of your changes.

Please keep changes focused and include a brief note describing the rationale.

## Contact

If you need help, open an issue in the repository with details about your environment and what you tried.

---

Updated README — enjoy exploring the constructions!
