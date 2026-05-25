# advection-scheme-lab

Pure-Python experiments for one of the oldest numerical-analysis arguments around: if you transport a waveform across a grid, where do diffusion, dispersion, and monotonicity each win?

![Advection scheme tradeoffs](assets/advection-scheme-tradeoffs.png)

This repo opens with a tight first packet instead of a vague promise:

- a small simulation core for 1D linear advection on a periodic grid
- three classic schemes: upwind, Lax-Friedrichs, and Lax-Wendroff
- von Neumann amplitude and phase curves
- one-turn transport comparisons for a Gaussian pulse and a square pulse
- a generated SVG/PNG figure, CSV sidecar, report, notebook, and tests
- a TVD minmod follow-up that adds a real middle lane instead of pretending the choice is only blur versus ringing

## Thesis

No single finite-difference scheme wins every lane.

- **Upwind** is monotone and easy to trust, but it blurs structure.
- **Lax-Friedrichs** damps even harder, especially on short waves.
- **Lax-Wendroff** keeps smooth profiles sharper and phase-accurate longer, but it pays for that sharpness with visible ringing near a jump.

The limiter follow-up sharpens that reading instead of replacing it.

- **TVD minmod** keeps the square pulse monotone and much cleaner than Lax-Wendroff.
- It also stays much sharper than upwind on the Gaussian.
- But it still does not beat unrestricted Lax-Wendroff on the smooth-wave lane.

That tradeoff is the whole point of the repo. It turns a classroom slogan into something you can inspect, rerun, and extend.

## Quick start

```bash
python3 scripts/generate_gallery.py
python3 scripts/generate_limiter_followup.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-overview \
  --output assets/advection-scheme-tradeoffs.svg \
  --png-output assets/advection-scheme-tradeoffs.png
python3 -m advectionlab.cli write-csv --output assets/advection-scheme-transport.csv
python3 -m advectionlab.cli render-limiter-followup \
  --output assets/advection-minmod-limiter-followup.svg \
  --png-output assets/advection-minmod-limiter-followup.png
python3 -m advectionlab.cli write-limiter-csv --output assets/advection-minmod-limiter-followup.csv
```

## Repo layout

- `advectionlab/core.py` builds the periodic-grid simulation path
- `advectionlab/analysis.py` holds amplification factors and transport metrics
- `advectionlab/render.py` renders the public figure as SVG
- `advectionlab/cli.py` exposes rebuild commands
- `scripts/generate_gallery.py` regenerates the figure, CSV, report, and notebook
- `scripts/generate_limiter_followup.py` regenerates the limiter follow-up figure, CSV, report, and notebook
- `reports/linear-advection-scheme-tradeoffs.md` gives the first bounded read
- `notebooks/advection_scheme_tradeoffs.ipynb` is the companion notebook

## First artifact

The opening figure answers two different questions at once.

1. What does each scheme do to a Fourier mode in one step?
2. What does that choice look like after a full periodic transport of a smooth pulse and a sharp pulse?

The combined result is clean: Lax-Wendroff is the best smooth-wave lane in this first packet, but it is not a free upgrade because the square pulse shows the ripple immediately.

## Limiter follow-up

![TVD minmod follow-up](assets/advection-minmod-limiter-followup.png)

The follow-up packet adds one bounded escape hatch: a TVD minmod limiter.

It does something the opening three-scheme comparison could not:

- it keeps the jump monotone,
- it stays much sharper than upwind,
- and it makes the monotone-versus-sharp tradeoff feel like a real design curve instead of a binary choice.

The repo still does not pretend the limiter wins every lane. On the smooth Gaussian, unrestricted Lax-Wendroff remains best. That is why the follow-up earns its own artifact instead of silently replacing the first packet.

## Why this repo is worth its own home

A lot of numerical-method repos either stop at derivations or stop at pretty plots. This one is meant to sit in the middle: simple enough to read in an evening, but concrete enough to make design choices visible.
