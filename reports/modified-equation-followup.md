# Modified-equation follow-up for linear advection

The limiter-family sidecar closed one real gap: the bounded lane was not one thing.

This follow-up closes the next one.

It asks whether the old linear schemes and the newer TVD limiters are all just different points on the same diffusion-versus-ringing tradeoff, or whether the limiter family is doing something qualitatively different.

## Low-wavenumber coefficient read

For the three linear schemes, the one-step amplification factor `G(θ)` is expanded near `θ = 0` as

\[
\log G(\theta) \approx -i\nu\theta - D(\nu)\theta^2 + iK(\nu)\theta^3 + O(\theta^4).
\]

Here `D(ν)` is the leading low-wavenumber diffusion coefficient and `K(ν)` is the leading low-wavenumber dispersion coefficient. The card extracts both numerically from the exact linear amplification factor instead of pretending the smooth-wave story can be read from one plot alone.

At CFL `0.95`:

- **Lax-Friedrichs** is the most diffusive linear lane here, with `D ≈ 0.04875` and `K ≈ -0.03087`.
- **Upwind** is still diffusive, but less harsh: `D ≈ 0.02375` and `K ≈ -0.00712`.
- **Lax-Wendroff** is the near-zero-diffusion endpoint: `D ≈ 0.00000` while the leading smooth-wave defect is mostly dispersive at `K ≈ +0.01544`.

That is the clean linear story. The low-diffusion endpoint buys the best smooth Gaussian read, but the price shows up on the square pulse.

## Where the linear story stops

At the same CFL `0.95`:

- **Lax-Wendroff** keeps the linear smooth-wave lead at Gaussian L2 error `0.0005`.
- But it pays square-pulse overshoot `0.1497` and total variation ratio `1.390`.
- **TVD MC** beats that smooth-wave error anyway at `0.0003` while still keeping overshoot exactly zero in this packet.
- **TVD Superbee** is the sharpest bounded jump read at square-pulse L2 error `0.0402`, also with zero overshoot.
- **TVD minmod** remains the conservative bounded baseline at Gaussian L2 `0.0010` and square L2 `0.0559`.

That is the useful upgrade. The linear schemes really do lie on one visible compromise curve: less Gaussian error tends to buy more jump overshoot. The limiter family matters because it can step off that curve instead of merely sliding along it.

## Why this sharpens the repo

Without this sidecar, the limiter-family result could be misread as just one more benchmark scoreboard. The modified-equation read makes the sharper point explicit.

- The old three linear schemes differ in **how much low-wavenumber diffusion and dispersion they inject**.
- That explains why Lax-Friedrichs blurs, why upwind softens, and why Lax-Wendroff stays sharp until the jump rings.
- The TVD family matters because it is **not** just another point on that same linear coefficient curve.
- Once overshoot is pinned to zero, the bounded family still splits: **MC** is the smoother bounded choice, **Superbee** is the sharper bounded jump choice.

So the limiter-family card was not decorative after all. It was the first sign that the linear modified-equation compromise had stopped being the whole story.

## Adversarial check

If the limiter markers had landed right back on the same smooth-error versus overshoot curve as the linear schemes, this would have been algebraic costume. They do not. The bounded family sits on the overshoot floor, and the zero-overshoot family still spreads into a real smooth-versus-sharp ranking instead of collapsing into one answer.

## Artifact set

- `assets/advection-modified-equation-followup.svg`
- `assets/advection-modified-equation-followup.png`
- `assets/advection-modified-equation-followup.csv`
- `notebooks/advection_modified_equation_followup.ipynb`

## Rebuild

```bash
python3 scripts/generate_modified_equation_followup.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-modified-equation-followup --output assets/advection-modified-equation-followup.svg --png-output assets/advection-modified-equation-followup.png --focus-cfl 0.95
python3 -m advectionlab.cli write-modified-equation-csv --output assets/advection-modified-equation-followup.csv
```
