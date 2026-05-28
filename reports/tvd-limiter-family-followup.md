# TVD limiter family follow-up for linear advection

The first limiter sidecar proved one useful thing: the bounded lane was real.

It did not prove that all bounded lanes feel the same.

This follow-up tests the next honest question on the same periodic one-turn transport problem: if we stay inside classical TVD limiter form, do different limiter choices merely repaint the same compromise, or do they open distinct bounded personalities?

## Main bounded result at CFL 0.95

They split cleanly enough to matter.

- On the Gaussian pulse, **TVD MC** reaches an L2 error of `0.0003`.
- That beats **Lax-Wendroff** on this bounded smooth test (`0.0005`), with **TVD Superbee** (`0.0007`) and **TVD minmod** (`0.0010`) trailing behind.
- On the square pulse, **TVD Superbee** is the sharpest bounded choice here at `0.0402`.
- **TVD MC** still stays clearly ahead of **TVD minmod** on the same bounded jump lane (`0.0482` versus `0.0559`).
- All three TVD limiters keep overshoot and undershoot at zero in this packet, so the real split is not bounded versus unbounded anymore. It is **which bounded personality you want**.

That is the useful upgrade. The old minmod sidecar introduced a middle lane. This packet shows that the middle lane is still too coarse: **MC is the smoother bounded read, Superbee is the sharper bounded read**.

## Flux form used here

For positive advection speed, the update is still written in conservative form,

\[
u_i^{n+1} = u_i^n - \nu \left(F_{i+1/2} - F_{i-1/2}\right),
\]

with interface flux

\[
F_{i+1/2} = u_i + \tfrac12 (1 - \nu) \phi(r_i) (u_{i+1} - u_i),
\qquad
r_i = \frac{u_i - u_{i-1}}{u_{i+1} - u_i}.
\]

The limiter choices are:

\[
\phi_{\mathrm{minmod}}(r) = \max(0, \min(1, r)),
\]

\[
\phi_{\mathrm{MC}}(r) = \max\left(0, \min\left(2r, \tfrac12(1+r), 2\right)\right),
\]

\[
\phi_{\mathrm{Superbee}}(r) = \max\left(0, \max\left(\min(2r, 1), \min(r, 2)\right)\right).
\]

So the packet stays narrow: same PDE, same periodic grid, same one-turn task, one bounded limiter family comparison.

## Adversarial check

If MC and Superbee had only shaved a few decimals off minmod while telling the same story, this would be filler. If one limiter had won every lane so cleanly that the others became pointless, this would probably be a bad benchmark rather than a good lesson. The useful outcome sits in between: the smooth lane and jump lane now split **inside** the bounded family itself.

## Artifact set

- `assets/advection-limiter-family-followup.svg`
- `assets/advection-limiter-family-followup.png`
- `assets/advection-limiter-family-followup.csv`
- `notebooks/advection_limiter_family_followup.ipynb`

## Rebuild

```bash
python3 scripts/generate_limiter_family_followup.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-limiter-family-followup --output assets/advection-limiter-family-followup.svg --png-output assets/advection-limiter-family-followup.png --cfl 0.95
python3 -m advectionlab.cli write-limiter-family-csv --output assets/advection-limiter-family-followup.csv
```
