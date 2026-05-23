# advection-scheme-lab

Pure-Python experiments for one of the oldest numerical-analysis arguments around: if you transport a waveform across a grid, where do diffusion, dispersion, and monotonicity each win?

![Advection scheme tradeoffs](assets/advection-scheme-tradeoffs.png)

This repo opens with a tight first packet instead of a vague promise:

- a small simulation core for 1D linear advection on a periodic grid
- three classic schemes: upwind, Lax-Friedrichs, and Lax-Wendroff
- von Neumann amplitude and phase curves
- one-turn transport comparisons for a Gaussian pulse and a square pulse
- a generated SVG/PNG figure, CSV sidecar, report, notebook, and tests

## Thesis

No single finite-difference scheme wins every lane.

- **Upwind** is monotone and easy to trust, but it blurs structure.
- **Lax-Friedrichs** damps even harder, especially on short waves.
- **Lax-Wendroff** keeps smooth profiles sharper and phase-accurate longer, but it pays for that sharpness with visible ringing near a jump.

That tradeoff is the whole point of the repo. It turns a classroom slogan into something you can inspect, rerun, and extend.

## Quick start

```bash
python3 scripts/generate_gallery.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-overview \
  --output assets/advection-scheme-tradeoffs.svg \
  --png-output assets/advection-scheme-tradeoffs.png
python3 -m advectionlab.cli write-csv --output assets/advection-scheme-transport.csv
```

## Repo layout

- `advectionlab/core.py` builds the periodic-grid simulation path
- `advectionlab/analysis.py` holds amplification factors and transport metrics
- `advectionlab/render.py` renders the public figure as SVG
- `advectionlab/cli.py` exposes rebuild commands
- `scripts/generate_gallery.py` regenerates the figure, CSV, report, and notebook
- `reports/linear-advection-scheme-tradeoffs.md` gives the first bounded read
- `notebooks/advection_scheme_tradeoffs.ipynb` is the companion notebook

## First artifact

The opening figure answers two different questions at once.

1. What does each scheme do to a Fourier mode in one step?
2. What does that choice look like after a full periodic transport of a smooth pulse and a sharp pulse?

The combined result is clean: Lax-Wendroff is the best smooth-wave lane in this first packet, but it is not a free upgrade because the square pulse shows the ripple immediately.

## Why this repo is worth its own home

A lot of numerical-method repos either stop at derivations or stop at pretty plots. This one is meant to sit in the middle: simple enough to read in an evening, but concrete enough to make design choices visible.
