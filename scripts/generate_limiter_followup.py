from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from advectionlab.analysis import study_transport
from advectionlab.cli import render_limiter_followup, write_limiter_followup_csv


ASSETS = REPO_ROOT / "assets"
REPORTS = REPO_ROOT / "reports"
NOTEBOOKS = REPO_ROOT / "notebooks"


def write_report(rows) -> Path:
    gaussian_rows = {
        row.scheme_key: row
        for row in rows
        if row.profile_key == "gaussian" and abs(row.requested_cfl - 0.9) < 1e-9
    }
    square_rows = {
        row.scheme_key: row
        for row in rows
        if row.profile_key == "square" and abs(row.requested_cfl - 0.9) < 1e-9
    }
    report = f"""# TVD minmod follow-up for linear advection

The opening packet left one honest gap behind.

Lax-Wendroff was clearly the best smooth-wave lane, but its square-pulse ripple made the choice feel too binary: either accept diffusion, or accept ringing.

This follow-up adds one bounded escape hatch: a TVD minmod limiter wrapped around the same positive-velocity transport problem.

## Main bounded result at CFL 0.9

The limiter creates a real middle lane.

- On the Gaussian pulse, **TVD minmod** cuts the L2 error to `{gaussian_rows['tvd-minmod'].l2_error:.4f}`.
- That is much better than **Upwind** (`{gaussian_rows['upwind'].l2_error:.4f}`) and **Lax-Friedrichs** (`{gaussian_rows['lax-friedrichs'].l2_error:.4f}`), but still behind **Lax-Wendroff** (`{gaussian_rows['lax-wendroff'].l2_error:.4f}`).
- On the square pulse, **TVD minmod** keeps overshoot and undershoot at zero while dropping the L2 error to `{square_rows['tvd-minmod'].l2_error:.4f}`.
- **Lax-Wendroff** still reaches `{square_rows['lax-wendroff'].l2_error:.4f}` on the square, but it pays with overshoot `{square_rows['lax-wendroff'].overshoot:.4f}`, undershoot `{square_rows['lax-wendroff'].undershoot:.4f}`, and a total-variation ratio of `{square_rows['lax-wendroff'].total_variation_ratio:.4f}`.

That is the whole point of the sidecar.

The limiter does not magically win every lane. It keeps the jump honest without falling all the way back to first-order blur.

## Flux form used here

For positive advection speed, the update is written in conservative form,

\\[
u_i^{{n+1}} = u_i^n - \\nu \\left(F_{{i+1/2}} - F_{{i-1/2}}\\right),
\\]

with the limited interface flux

\\[
F_{{i+1/2}} = u_i + \\tfrac12 (1 - \\nu) \\phi(r_i) (u_{{i+1}} - u_i),
\\qquad
r_i = \\frac{{u_i - u_{{i-1}}}}{{u_{{i+1}} - u_i}},
\\]

and the minmod limiter

\\[
\\phi(r) = \\max(0, \\min(1, r)).
\\]

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
"""
    path = REPORTS / "tvd-minmod-followup.md"
    path.write_text(report)
    return path


def write_notebook() -> Path:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# TVD minmod follow-up for linear advection\n",
                    "This notebook mirrors the repo's limiter sidecar: same periodic transport problem, one extra bounded scheme, and one sharper question. Can a TVD limiter keep the jump monotone without falling all the way back to first-order blur?\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Flux used in the sidecar\n",
                    "For positive advection speed, the update is written as `u_i^{n+1} = u_i^n - nu (F_{i+1/2} - F_{i-1/2})`, with `F_{i+1/2} = u_i + 0.5 (1-nu) phi(r_i) (u_{i+1} - u_i)` and `phi(r) = max(0, min(1, r))`.\n",
                    "\n",
                    "That keeps the follow-up honest: one new scheme, not a whole new solver family.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from advectionlab.analysis import study_transport\n",
                    "rows = study_transport(\n",
                    "    schemes=('upwind', 'lax-friedrichs', 'lax-wendroff', 'tvd-minmod'),\n",
                    "    requested_cfls=(0.4, 0.7, 0.9),\n",
                    ")\n",
                    "for row in rows:\n",
                    "    if row.requested_cfl == 0.9:\n",
                    "        print(row)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Reading the bounded result\n",
                    "At CFL 0.9 the limiter lands exactly where this repo needed it to land. It does not replace Lax-Wendroff on the smooth Gaussian, but it does keep the square pulse monotone while staying far sharper than upwind.\n",
                    "\n",
                    "That makes the monotone-versus-sharp tradeoff feel like a real middle lane instead of a fake all-or-nothing choice.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "square_rows = [row for row in rows if row.profile_key == 'square']\n",
                    "for row in square_rows:\n",
                    "    print(row.scheme_title, row.requested_cfl, row.total_variation_ratio, row.overshoot, row.undershoot)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Adversarial check\n",
                    "If the limiter had only reproduced upwind blur, the sidecar would be filler. If it had beaten every other scheme in every metric, the sidecar would feel suspiciously overclaimed. The useful result is the one in between: better bounded behavior on the jump, but still not a free pass on the smooth lane.\n",
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
    path = NOTEBOOKS / "advection_minmod_limiter_followup.ipynb"
    path.write_text(json.dumps(notebook, indent=2))
    return path


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    render_limiter_followup(
        ASSETS / "advection-minmod-limiter-followup.svg",
        ASSETS / "advection-minmod-limiter-followup.png",
    )
    write_limiter_followup_csv(ASSETS / "advection-minmod-limiter-followup.csv")
    rows = study_transport(
        schemes=("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod"),
        requested_cfls=(0.4, 0.7, 0.9),
    )
    write_report(rows)
    write_notebook()


if __name__ == "__main__":
    main()
