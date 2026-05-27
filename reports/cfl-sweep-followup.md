# CFL sweep follow-up for linear advection

The limiter follow-up settled one honest question: a bounded TVD update can keep the jump monotone without falling all the way back to upwind blur.

This sidecar closes the next loophole.

The scheme ranking is not fixed if the timestep itself moves toward a one-cell grid shift.

## Main bounded result

Two things stay true across the sweep.

- On the **Gaussian pulse**, **Lax-Wendroff** stays first the whole way.
- On the **square pulse**, **TVD minmod** stays best until the near-unit-CFL collapse.

But the whole packet tightens as CFL approaches 1.

- **Lax-Wendroff** Gaussian L2 error drops from `0.0050` at CFL 0.2 to `0.0005` at CFL 0.95.
- **TVD minmod** still sits in the middle on the Gaussian lane at CFL 0.95 with L2 error `0.0010`.
- On the square pulse, **Lax-Wendroff** overshoot falls from `0.2415` at CFL 0.4 to `0.1497` at CFL 0.95.
- **TVD minmod** keeps overshoot at zero across the whole sweep while its square-pulse L2 error drops from `0.0877` at CFL 0.4 to `0.0559` at CFL 0.95.

At CFL 1.0 on this one-turn periodic problem, every scheme becomes exact.

That does **not** mean the old tradeoff was fake. It means the timestep can temporarily hide it when the update is almost a pure one-cell translation.

## Why the CFL 1 endpoint matters

For positive advection speed on a periodic grid, this experiment advances the profile by one full circuit.

When CFL is exactly 1, each explicit stencil reduces to an exact one-cell shift per step. After one full turn, every scheme lands back on the sampled profile.

That endpoint gives the sweep a sharp boundary condition:

- far from CFL 1, scheme personality dominates;
- near CFL 1, the grid-translation geometry compresses the ranking.

That is the real new sentence from this sidecar.

## Adversarial check

This is a bounded result, not a universal excuse to ignore scheme choice.

- It depends on **positive velocity**, a **uniform periodic grid**, and a **one-turn transport task**.
- It does **not** say Lax-Wendroff becomes monotone in general.
- It does **not** say multi-turn runs, variable coefficients, or boundary-driven problems will inherit the same exact endpoint.

The useful claim is narrower: in this clean transport problem, CFL itself can compress the ranking enough that a scheme comparison without a timestep sweep leaves out a real part of the story.

## Artifact set

- `assets/advection-cfl-sweep-followup.svg`
- `assets/advection-cfl-sweep-followup.png`
- `assets/advection-cfl-sweep-followup.csv`
- `notebooks/advection_cfl_sweep_followup.ipynb`

## Rebuild

```bash
python3 scripts/generate_cfl_sweep_followup.py
python3 -m unittest discover -s tests
python3 -m advectionlab.cli render-cfl-sweep-followup --output assets/advection-cfl-sweep-followup.svg --png-output assets/advection-cfl-sweep-followup.png
python3 -m advectionlab.cli write-cfl-sweep-csv --output assets/advection-cfl-sweep-followup.csv
```
