# TVD minmod follow-up for linear advection

The opening packet left one honest gap behind.

Lax-Wendroff was clearly the best smooth-wave lane, but its square-pulse ripple made the choice feel too binary: either accept diffusion, or accept ringing.

This follow-up adds one bounded escape hatch: a TVD minmod limiter wrapped around the same positive-velocity transport problem.

## Main bounded result at CFL 0.9

The limiter creates a real middle lane.

- On the Gaussian pulse, **TVD minmod** cuts the L2 error to `0.0018`.
- That is much better than **Upwind** (`0.0142`) and **Lax-Friedrichs** (`0.0280`), but still behind **Lax-Wendroff** (`0.0010`).
- On the square pulse, **TVD minmod** keeps overshoot and undershoot at zero while dropping the L2 error to `0.0639`.
- **Lax-Wendroff** still reaches `0.0783` on the square, but it pays with overshoot `0.1763`, undershoot `0.1763`, and a total-variation ratio of `1.4976`.

That is the whole point of the sidecar.

The limiter does not magically win every lane. It keeps the jump honest without falling all the way back to first-order blur.

## Flux form used here

For positive advection speed, the update is written in conservative form,

\[
u_i^{n+1} = u_i^n - \nu \left(F_{i+1/2} - F_{i-1/2}\right),
\]

with the limited interface flux

\[
F_{i+1/2} = u_i + \tfrac12 (1 - \nu) \phi(r_i) (u_{i+1} - u_i),
\qquad
r_i = \frac{u_i - u_{i-1}}{u_{i+1} - u_i},
\]

and the minmod limiter

\[
\phi(r) = \max(0, \min(1, r)).
\]

That keeps the follow-up narrow: same PDE, same periodic grid, same one-turn experiment, one new bounded scheme.

## Artifact set

- `assets/advection-minmod-limiter-followup.svg`
- `assets/advection-minmod-limiter-followup.png`
- `assets/advection-minmod-limiter-followup.csv`
- `notebooks/advection_minmod_limiter_followup.ipynb`

## Rebuild

```bash
python3 scripts/generate_limiter_followup.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-limiter-followup --output assets/advection-minmod-limiter-followup.svg --png-output assets/advection-minmod-limiter-followup.png
python3 -m advectionlab.cli write-limiter-csv --output assets/advection-minmod-limiter-followup.csv
```
