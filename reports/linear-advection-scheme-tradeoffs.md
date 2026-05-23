# Linear advection scheme tradeoffs

This repo starts from one blunt question: when you move a waveform across a periodic grid, which finite-difference scheme blurs it, which one shifts it at the wrong speed, and which one rings near a jump?

The day-one answer is already useful.

- **Upwind** stays monotone and simple, but it diffuses both smooth and sharp features.
- **Lax-Friedrichs** is even more damping-heavy on short waves. It is the most forgiving visually, but it pays for that calmness by washing out structure fastest.
- **Lax-Wendroff** keeps the Gaussian pulse closest to the exact profile at high CFL, but it produces the largest overshoot and undershoot on the square pulse.

## Main bounded result at CFL 0.9

For the smooth Gaussian test after one periodic turn, the lowest L2 error comes from **Lax-Wendroff** (`0.0010`). For the discontinuous square pulse, the strongest shape preservation still comes from **Lax-Wendroff** in plain L2 terms (`0.0783`), but that headline hides the real cost: **Lax-Wendroff** keeps the edge sharp by allowing a visible ripple, with overshoot `0.1763` and undershoot `0.1763`.

That split is the point of the repo. No single scheme wins every lane.

## Artifact set

- `assets/advection-scheme-tradeoffs.svg`
- `assets/advection-scheme-tradeoffs.png`
- `assets/advection-scheme-transport.csv`
- `notebooks/advection_scheme_tradeoffs.ipynb`

## Rebuild

```bash
python3 scripts/generate_gallery.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-overview --output assets/advection-scheme-tradeoffs.svg --png-output assets/advection-scheme-tradeoffs.png
```
