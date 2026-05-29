#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from advectionlab.analysis import study_modified_equation_followup
from advectionlab.cli import MODIFIED_EQUATION_CFLS, render_modified_equation_followup, write_modified_equation_followup_csv


ASSETS = REPO_ROOT / "assets"
REPORTS = REPO_ROOT / "reports"
NOTEBOOKS = REPO_ROOT / "notebooks"
FOCUS_CFL = 0.95
ALL_SCHEMES = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod", "tvd-mc", "tvd-superbee")
LINEAR_SCHEMES = ("upwind", "lax-friedrichs", "lax-wendroff")


def write_report(rows) -> Path:
    rows_by_key = {(row.scheme_key, round(row.requested_cfl, 2)): row for row in rows}
    focus_rows = {scheme: rows_by_key[(scheme, FOCUS_CFL)] for scheme in ALL_SCHEMES}
    lw = focus_rows["lax-wendroff"]
    upwind = focus_rows["upwind"]
    lf = focus_rows["lax-friedrichs"]
    mc = focus_rows["tvd-mc"]
    superbee = focus_rows["tvd-superbee"]
    minmod = focus_rows["tvd-minmod"]

    report = fr"""# Modified-equation follow-up for linear advection

The limiter-family sidecar closed one real gap: the bounded lane was not one thing.

This follow-up closes the next one.

It asks whether the old linear schemes and the newer TVD limiters are all just different points on the same diffusion-versus-ringing tradeoff, or whether the limiter family is doing something qualitatively different.

## Low-wavenumber coefficient read

For the three linear schemes, the one-step amplification factor `G(θ)` is expanded near `θ = 0` as

\[
\log G(\theta) \approx -i\nu\theta - D(\nu)\theta^2 + iK(\nu)\theta^3 + O(\theta^4).
\]

Here `D(ν)` is the leading low-wavenumber diffusion coefficient and `K(ν)` is the leading low-wavenumber dispersion coefficient. The card extracts both numerically from the exact linear amplification factor instead of pretending the smooth-wave story can be read from one plot alone.

At CFL `{FOCUS_CFL:.2f}`:

- **Lax-Friedrichs** is the most diffusive linear lane here, with `D ≈ {lf.diffusion_coeff:.5f}` and `K ≈ {lf.dispersion_coeff:+.5f}`.
- **Upwind** is still diffusive, but less harsh: `D ≈ {upwind.diffusion_coeff:.5f}` and `K ≈ {upwind.dispersion_coeff:+.5f}`.
- **Lax-Wendroff** is the near-zero-diffusion endpoint: `D ≈ {lw.diffusion_coeff:.5f}` while the leading smooth-wave defect is mostly dispersive at `K ≈ {lw.dispersion_coeff:+.5f}`.

That is the clean linear story. The low-diffusion endpoint buys the best smooth Gaussian read, but the price shows up on the square pulse.

## Where the linear story stops

At the same CFL `{FOCUS_CFL:.2f}`:

- **Lax-Wendroff** keeps the linear smooth-wave lead at Gaussian L2 error `{lw.gaussian_l2_error:.4f}`.
- But it pays square-pulse overshoot `{lw.square_overshoot:.4f}` and total variation ratio `{lw.square_total_variation_ratio:.3f}`.
- **TVD MC** beats that smooth-wave error anyway at `{mc.gaussian_l2_error:.4f}` while still keeping overshoot exactly zero in this packet.
- **TVD Superbee** is the sharpest bounded jump read at square-pulse L2 error `{superbee.square_l2_error:.4f}`, also with zero overshoot.
- **TVD minmod** remains the conservative bounded baseline at Gaussian L2 `{minmod.gaussian_l2_error:.4f}` and square L2 `{minmod.square_l2_error:.4f}`.

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
"""
    path = REPORTS / "modified-equation-followup.md"
    path.write_text(report)
    return path


def write_notebook() -> Path:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Modified-equation follow-up for linear advection\n",
                    "This notebook is the slower companion to the repo's modified-equation sidecar. It asks where the linear diffusion-versus-dispersion story really explains the transport behavior, and where the bounded limiter family breaks away from it.\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Low-wavenumber coefficient definition\n",
                    "For the linear schemes, the one-step amplification factor is expanded as `log G(θ) ≈ -iνθ - D(ν)θ² + iK(ν)θ³`. The card estimates `D` and `K` directly from the exact amplification factor instead of assuming the smooth-wave story speaks for itself.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from advectionlab.analysis import study_modified_equation_followup\n",
                    f"rows = study_modified_equation_followup(requested_cfls={MODIFIED_EQUATION_CFLS!r})\n",
                    "[row for row in rows if row.requested_cfl == 0.95 and row.diffusion_coeff is not None]\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Where the limiter family leaves the linear curve\n",
                    "At CFL 0.95, Lax-Wendroff is the low-diffusion linear endpoint, but it buys that with visible square-pulse overshoot. The TVD markers matter because they stay on the overshoot floor instead of sitting on the same linear compromise line.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "focus_rows = [row for row in rows if row.requested_cfl == 0.95]\n",
                    "[(row.scheme_key, round(row.gaussian_l2_error, 4), round(row.square_l2_error, 4), round(row.square_overshoot, 4)) for row in focus_rows]\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Adversarial check\n",
                    "If the bounded family had merely reproduced the same smooth-error versus overshoot curve as the linear schemes, there would be no new lesson here. The useful outcome is that MC and Superbee sit on the zero-overshoot floor while still separating into different smooth and jump preferences.\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.x"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = NOTEBOOKS / "advection_modified_equation_followup.ipynb"
    path.write_text(json.dumps(notebook, indent=2))
    return path


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    render_modified_equation_followup(
        ASSETS / "advection-modified-equation-followup.svg",
        ASSETS / "advection-modified-equation-followup.png",
        focus_cfl=FOCUS_CFL,
    )
    write_modified_equation_followup_csv(ASSETS / "advection-modified-equation-followup.csv")
    rows = study_modified_equation_followup(requested_cfls=MODIFIED_EQUATION_CFLS)
    write_report(rows)
    write_notebook()


if __name__ == "__main__":
    main()
