# Drawing Circles

A small creative project for exploring recursive circle constructions with interactive visualization.

The repository contains:

- A desktop Python app powered by `pygame`.
- A self-contained browser demo in `index.html`.
- Export support for SVG and PNG output.
- A separate `single_circle/` demo folder with its own app and browser version.
- A few small script experiments in `little_scripts/`.

---

## Features

- Interactive level and base-point selection.
- Animated construction of circles from point pairs.
- Built-in settings panel for radius, speed, HUD toggles, and theme.
- Export completed constructions as SVG or PNG.
- Browser demo with look-around pan/zoom and export buttons.

---

## Quick Start

### Run the browser demo

Open `index.html` in a modern browser. No install is required.

### Run the Python app

1. Install Python 3.
2. Create and activate a virtual environment (optional but recommended).
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Launch the application:

```bash
python main.py
```

5. Override the base point count with:

```bash
python main.py --points 6
```

---

## Controls

### Top-level app (`main.py`)

- `ENTER` / `TAB` — start or open settings
- `P` — pause / resume
- `B` — toggle dark/light theme
- `[` / `]` — decrease / increase speed
- `ESC` / `M` — return to the main menu
- Mouse wheel — zoom
- Drag — pan

### Intro screen

- `LEFT` / `RIGHT` or `A` / `D` — change point count
- `UP` / `DOWN` or `W` / `S` — change level
- digits `0-9` — type level directly
- `TAB` — open settings panel

### Settings panel

- `UP` / `DOWN` or `W` / `S` — move selection
- `LEFT` / `RIGHT` or `A` / `D` — change values
- `+` / `-` — change values
- `ENTER` / `TAB` — return to main panel

---

## Export

The Python app and browser demo can export completed constructions.

- Python export files are saved to `map/exports/`.
- Supported formats: `SVG` and `PNG`.

---

## Project Structure

### Root files

- `main.py` — desktop app entry point
- `app.py` — application initialization and loop
- `cli.py` — command-line argument parsing
- `config.py` — shared runtime configuration
- `intro.py` — intro and settings UI
- `construction.py` — construction and animation stages
- `geometry.py` — pure geometry helpers
- `renderer.py` — drawing, camera, and HUD
- `animation.py` — easing, timers, and event handling
- `export.py` — export helpers for SVG/PNG
- `index.html` — self-contained browser visualization
- `requirements.txt` — Python dependency list

### Supporting folders

- `little_scripts/` — small experimental scripts for circle-related constructions
- `map/exports/` — default export destination for generated images
- `opencode/` — archived or published output content
- `single_circle/` — separate simplified demo with its own app and browser version

---

## `single_circle/` Demo

This folder contains a standalone variant of the same circle construction concept.

- `single_circle/main.py` — entry point for the simplified app
- `single_circle/app.py` — app loop and state machine
- `single_circle/config.py` — demo-specific configuration
- `single_circle/geometry.py` — math helpers
- `single_circle/renderer.py` — drawing utilities
- `single_circle/intro.py` — animated intro screen
- `single_circle/index.html` — browser demo for the simplified version

---

## Dependencies

- `pygame`

Install with:

```bash
pip install pygame
```

---

## Notes

- The app currently supports only `--points` as a CLI override.
- Most runtime options are configured in `config.py`.
- There is no test suite included in this repo.

---

## Development

1. Open the project in your editor.
2. Install dependencies.
3. Run `python main.py` and verify the visualization.
4. Change defaults in `config.py` or explore the browser demo.

If you want to add tests, create a `tests/` folder and use `pytest`.
