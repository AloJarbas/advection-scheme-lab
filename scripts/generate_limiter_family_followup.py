from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from advectionlab.analysis import study_transport
from advectionlab.cli import LIMITER_FAMILY_CFLS, render_limiter_family_followup, write_limiter_family_followup_csv


ASSETS = REPO_ROOT / "assets"
REPORTS = REPO_ROOT / "reports"
NOTEBOOKS = REPO_ROOT / "notebooks"
FOCUS_CFL = 0.95
FOLLOWUP_SCHEMES = ("lax-wendroff", "tvd-minmod", "tvd-mc", "tvd-superbee")


def write_report(rows) -> Path:
    gaussian_rows = {
        row.scheme_key: row
        for row in rows
        if row.profile_key == "gaussian" and abs(row.requested_cfl - FOCUS_CFL) < 1e-9
    }
    square_rows = {
        row.scheme_key: row
        for row in rows
        if row.profile_key == "square" and abs(row.requested_cfl - FOCUS_CFL) < 1e-9
    }
    report = fr"""# TVD limiter family follow-up for linear advection

The first limiter sidecar proved one useful thing: the bounded lane was real.

It did not prove that all bounded lanes feel the same.

This follow-up tests the next honest question on the same periodic one-turn transport problem: if we stay inside classical TVD limiter form, do different limiter choices merely repaint the same compromise, or do they open distinct bounded personalities?

## Main bounded result at CFL {FOCUS_CFL:.2f}

They split cleanly enough to matter.

- On the Gaussian pulse, **TVD MC** reaches an L2 error of `{gaussian_rows['tvd-mc'].l2_error:.4f}`.
- That beats **Lax-Wendroff** on this bounded smooth test (`{gaussian_rows['lax-wendroff'].l2_error:.4f}`), with **TVD Superbee** (`{gaussian_rows['tvd-superbee'].l2_error:.4f}`) and **TVD minmod** (`{gaussian_rows['tvd-minmod'].l2_error:.4f}`) trailing behind.
- On the square pulse, **TVD Superbee** is the sharpest bounded choice here at `{square_rows['tvd-superbee'].l2_error:.4f}`.
- **TVD MC** still stays clearly ahead of **TVD minmod** on the same bounded jump lane (`{square_rows['tvd-mc'].l2_error:.4f}` versus `{square_rows['tvd-minmod'].l2_error:.4f}`).
- All three TVD limiters keep overshoot and undershoot at zero in this packet, so the real split is not bounded versus unbounded anymore. It is **which bounded personality you want**.

That is the useful upgrade. The old minmod sidecar introduced a middle lane. This packet shows that the middle lane is still too coarse: **MC is the smoother bounded read, Superbee is the sharper bounded read**.

## Flux form used here

For positive advection speed, the update is still written in conservative form,

\[
u_i^{{n+1}} = u_i^n - \nu \left(F_{{i+1/2}} - F_{{i-1/2}}\right),
\]

with interface flux

\[
F_{{i+1/2}} = u_i + \tfrac12 (1 - \nu) \phi(r_i) (u_{{i+1}} - u_i),
\qquad
r_i = \frac{{u_i - u_{{i-1}}}}{{u_{{i+1}} - u_i}}.
\]

The limiter choices are:

\[
\phi_{{\mathrm{{minmod}}}}(r) = \max(0, \min(1, r)),
\]

\[
\phi_{{\mathrm{{MC}}}}(r) = \max\left(0, \min\left(2r, \tfrac12(1+r), 2\right)\right),
\]

\[
\phi_{{\mathrm{{Superbee}}}}(r) = \max\left(0, \max\left(\min(2r, 1), \min(r, 2)\right)\right).
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
"""
    path = REPORTS / "tvd-limiter-family-followup.md"
    path.write_text(report)
    return path


def write_notebook() -> Path:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# TVD limiter family follow-up for linear advection\n",
                    "This notebook mirrors the repo's limiter-family sidecar: same periodic transport problem, same bounded flux form, but now enough limiter variety to ask whether the bounded lane itself splits into different personalities.\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Limiter family used here\n",
                    "The conservative update stays the same; only the limiter changes. Minmod is the most cautious, MC is the smoother compromise, and Superbee is the most compressive bounded choice in this packet.\n",
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
                    "    schemes=('lax-wendroff', 'tvd-minmod', 'tvd-mc', 'tvd-superbee'),\n",
                    f"    requested_cfls={LIMITER_FAMILY_CFLS!r},\n",
                    ")\n",
                    "for row in rows:\n",
                    f"    if row.requested_cfl == {FOCUS_CFL}:\n",
                    "        print(row)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Reading the bounded split\n",
                    "At CFL 0.95, MC is the best smooth bounded choice in this packet, while Superbee is the sharpest bounded jump choice. That is the point of the sidecar: after the old minmod result, the next honest question was whether boundedness still hides multiple real personalities. It does.\n",
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
                    "    print(row.scheme_title, row.requested_cfl, row.l2_error, row.overshoot, row.undershoot)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Adversarial check\n",
                    "If the family curves had stayed stacked in the same order on both the Gaussian and the square pulse, there would be no new lesson here. The useful result is the split: MC buys smoother transport, Superbee buys a narrower bounded edge, and minmod remains the conservative baseline rather than the whole bounded story.\n",
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
    path = NOTEBOOKS / "advection_limiter_family_followup.ipynb"
    path.write_text(json.dumps(notebook, indent=2))
    return path


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    render_limiter_family_followup(
        ASSETS / "advection-limiter-family-followup.svg",
        ASSETS / "advection-limiter-family-followup.png",
        cfl=FOCUS_CFL,
    )
    write_limiter_family_followup_csv(ASSETS / "advection-limiter-family-followup.csv")
    rows = study_transport(schemes=FOLLOWUP_SCHEMES, requested_cfls=LIMITER_FAMILY_CFLS)
    write_report(rows)
    write_notebook()


if __name__ == "__main__":
    main()
