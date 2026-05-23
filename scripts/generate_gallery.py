from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from advectionlab.analysis import study_transport
from advectionlab.cli import render_overview, write_transport_csv




REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "assets"
REPORTS = REPO_ROOT / "reports"
NOTEBOOKS = REPO_ROOT / "notebooks"


def write_report(rows) -> Path:
    gaussian_rows = [row for row in rows if row.profile_key == "gaussian" and abs(row.requested_cfl - 0.9) < 1e-9]
    square_rows = [row for row in rows if row.profile_key == "square" and abs(row.requested_cfl - 0.9) < 1e-9]
    gaussian_rows.sort(key=lambda row: row.l2_error)
    square_rows.sort(key=lambda row: row.l2_error)
    report = f"""# Linear advection scheme tradeoffs

This repo starts from one blunt question: when you move a waveform across a periodic grid, which finite-difference scheme blurs it, which one shifts it at the wrong speed, and which one rings near a jump?

The day-one answer is already useful.

- **Upwind** stays monotone and simple, but it diffuses both smooth and sharp features.
- **Lax-Friedrichs** is even more damping-heavy on short waves. It is the most forgiving visually, but it pays for that calmness by washing out structure fastest.
- **Lax-Wendroff** keeps the Gaussian pulse closest to the exact profile at high CFL, but it produces the largest overshoot and undershoot on the square pulse.

## Main bounded result at CFL 0.9

For the smooth Gaussian test after one periodic turn, the lowest L2 error comes from **{gaussian_rows[0].scheme_title}** (`{gaussian_rows[0].l2_error:.4f}`). For the discontinuous square pulse, the strongest shape preservation still comes from **{square_rows[0].scheme_title}** in plain L2 terms (`{square_rows[0].l2_error:.4f}`), but that headline hides the real cost: **Lax-Wendroff** keeps the edge sharp by allowing a visible ripple, with overshoot `{next(row.overshoot for row in square_rows if row.scheme_key == 'lax-wendroff'):.4f}` and undershoot `{next(row.undershoot for row in square_rows if row.scheme_key == 'lax-wendroff'):.4f}`.

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
"""
    path = REPORTS / "linear-advection-scheme-tradeoffs.md"
    path.write_text(report)
    return path


def write_notebook() -> Path:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Advection scheme tradeoffs\\n",
                    "This notebook mirrors the repo's first public artifact: von Neumann damping and phase drift on one side, one-turn waveform transport on the other.\\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from advectionlab.analysis import study_transport\\n",
                    "rows = study_transport()\\n",
                    "for row in rows:\\n",
                    "    if row.requested_cfl == 0.9:\\n",
                    "        print(row)\\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Reading the first result\\n",
                    "For smooth data, dispersion usually matters more than monotonicity, so Lax-Wendroff wins the Gaussian lane. For a jump, monotonicity matters more, so the same scheme pays with overshoot and undershoot.\\n",
                    "\\n",
                    "That is the thesis of the repo: one transport method can look strong on a spectrum plot and still be the wrong choice for a shock-like profile.\\n",
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
    path = NOTEBOOKS / "advection_scheme_tradeoffs.ipynb"
    path.write_text(json.dumps(notebook, indent=2))
    return path


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    render_overview(ASSETS / "advection-scheme-tradeoffs.svg", ASSETS / "advection-scheme-tradeoffs.png")
    write_transport_csv(ASSETS / "advection-scheme-transport.csv")
    rows = study_transport()
    write_report(rows)
    write_notebook()


if __name__ == "__main__":
    main()
