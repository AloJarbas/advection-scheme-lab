from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from advectionlab.analysis import study_transport
from advectionlab.cli import DEFAULT_CFL_SWEEP, render_cfl_sweep_followup, write_cfl_sweep_followup_csv


ASSETS = REPO_ROOT / "assets"
REPORTS = REPO_ROOT / "reports"
NOTEBOOKS = REPO_ROOT / "notebooks"


def write_report(rows) -> Path:
    rows_by_key = {(row.profile_key, round(row.requested_cfl, 2), row.scheme_key): row for row in rows}
    gaussian_lw_low = rows_by_key[("gaussian", 0.2, "lax-wendroff")]
    gaussian_lw_high = rows_by_key[("gaussian", 0.95, "lax-wendroff")]
    gaussian_minmod_high = rows_by_key[("gaussian", 0.95, "tvd-minmod")]
    square_lw_low = rows_by_key[("square", 0.4, "lax-wendroff")]
    square_lw_high = rows_by_key[("square", 0.95, "lax-wendroff")]
    square_minmod_low = rows_by_key[("square", 0.4, "tvd-minmod")]
    square_minmod_high = rows_by_key[("square", 0.95, "tvd-minmod")]
    report = f"""# CFL sweep follow-up for linear advection

The limiter follow-up settled one honest question: a bounded TVD update can keep the jump monotone without falling all the way back to upwind blur.

This sidecar closes the next loophole.

The scheme ranking is not fixed if the timestep itself moves toward a one-cell grid shift.

## Main bounded result

Two things stay true across the sweep.

- On the **Gaussian pulse**, **Lax-Wendroff** stays first the whole way.
- On the **square pulse**, **TVD minmod** stays best until the near-unit-CFL collapse.

But the whole packet tightens as CFL approaches 1.

- **Lax-Wendroff** Gaussian L2 error drops from `{gaussian_lw_low.l2_error:.4f}` at CFL 0.2 to `{gaussian_lw_high.l2_error:.4f}` at CFL 0.95.
- **TVD minmod** still sits in the middle on the Gaussian lane at CFL 0.95 with L2 error `{gaussian_minmod_high.l2_error:.4f}`.
- On the square pulse, **Lax-Wendroff** overshoot falls from `{square_lw_low.overshoot:.4f}` at CFL 0.4 to `{square_lw_high.overshoot:.4f}` at CFL 0.95.
- **TVD minmod** keeps overshoot at zero across the whole sweep while its square-pulse L2 error drops from `{square_minmod_low.l2_error:.4f}` at CFL 0.4 to `{square_minmod_high.l2_error:.4f}` at CFL 0.95.

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
"""
    path = REPORTS / "cfl-sweep-followup.md"
    path.write_text(report)
    return path


def write_notebook() -> Path:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# CFL sweep follow-up for linear advection\n",
                    "This notebook asks one tighter question than the earlier scheme cards. If the timestep moves toward a one-cell translation, how much of the old blur-versus-ringing hierarchy is still visible?\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from advectionlab.analysis import study_transport\n",
                    "requested_cfls = tuple(round(0.2 + 0.05 * index, 2) for index in range(17))\n",
                    "rows = study_transport(\n",
                    "    schemes=('upwind', 'lax-friedrichs', 'lax-wendroff', 'tvd-minmod'),\n",
                    "    requested_cfls=requested_cfls,\n",
                    ")\n",
                    "len(rows)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Read the two lanes separately\n",
                    "The Gaussian lane stays smooth enough that Lax-Wendroff keeps first place all the way across. The square lane still rewards the limiter, but the gap starts collapsing as CFL approaches 1 because the update is getting closer to a sampled grid shift.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "for cfl in (0.4, 0.8, 0.95, 1.0):\n",
                    "    square_rows = [row for row in rows if row.profile_key == 'square' and abs(row.requested_cfl - cfl) < 1e-9]\n",
                    "    ranking = sorted(square_rows, key=lambda row: row.l2_error)\n",
                    "    print(cfl, [(row.scheme_key, round(row.l2_error, 4), round(row.overshoot, 4)) for row in ranking])\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Why the endpoint is exact here\n",
                    "At CFL 1 with positive velocity, each explicit update becomes an exact one-cell shift on this periodic grid. After one full turn the sampled profile comes back to itself, so every scheme lands at zero transport error. That is a geometric endpoint of this setup, not a general theorem that scheme choice suddenly stops mattering.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "unit_rows = [row for row in rows if abs(row.requested_cfl - 1.0) < 1e-9]\n",
                    "[(row.scheme_key, row.profile_key, row.l2_error, row.overshoot) for row in unit_rows]\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Adversarial check\n",
                    "If the exact endpoint were the only thing happening, the whole sweep would be a cheap trick. It is not. The non-unit-CFL part still shows the real ordering: Lax-Wendroff owns the smooth lane, TVD minmod owns the bounded jump lane, and the approach to CFL 1 only tells you when that ranking gets compressed by the geometry of the step itself.\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.x",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = NOTEBOOKS / "advection_cfl_sweep_followup.ipynb"
    path.write_text(json.dumps(notebook, indent=2))
    return path


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    render_cfl_sweep_followup(
        ASSETS / "advection-cfl-sweep-followup.svg",
        ASSETS / "advection-cfl-sweep-followup.png",
    )
    write_cfl_sweep_followup_csv(ASSETS / "advection-cfl-sweep-followup.csv")
    rows = study_transport(
        schemes=("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod"),
        requested_cfls=DEFAULT_CFL_SWEEP,
    )
    write_report(rows)
    write_notebook()


if __name__ == "__main__":
    main()
