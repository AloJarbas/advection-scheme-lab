from __future__ import annotations

import argparse
import csv
from pathlib import Path
import shutil
import subprocess
import tempfile

from .analysis import amplitude_curve, phase_speed_ratio_curve, study_transport
from .core import simulate_transport
from .render import render_cfl_sweep_followup_svg, render_limiter_followup_svg, render_tradeoff_svg, write_svg


DEFAULT_CFL_SWEEP = tuple(round(0.2 + 0.05 * index, 2) for index in range(17))


def export_png(svg_path: Path, png_path: Path) -> None:
    brave_candidates = [
        Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        Path(shutil.which("brave-browser") or ""),
    ]
    browser = next((candidate for candidate in brave_candidates if candidate and candidate.exists()), None)
    if browser is not None:
        command = [
            str(browser),
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1000",
            f"--screenshot={png_path.resolve()}",
            "--window-size=1760,1220",
            svg_path.resolve().as_uri(),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            if png_path.exists():
                return
            raise
        return
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            ["qlmanage", "-t", "-s", "2200", "-o", temp_dir, str(svg_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rendered = Path(temp_dir) / f"{svg_path.name}.png"
        if not rendered.exists():
            raise FileNotFoundError(f"Quick Look did not render {svg_path.name}")
        png_path.write_bytes(rendered.read_bytes())


def write_transport_csv(output: Path) -> None:
    rows = study_transport()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].as_dict().keys()), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def write_limiter_followup_csv(output: Path) -> None:
    rows = study_transport(
        schemes=("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod"),
        requested_cfls=(0.4, 0.7, 0.9),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].as_dict().keys()), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def write_cfl_sweep_followup_csv(output: Path) -> None:
    rows = study_transport(
        schemes=("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod"),
        requested_cfls=DEFAULT_CFL_SWEEP,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].as_dict().keys()), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def render_overview(svg_output: Path, png_output: Path | None = None, *, cfl: float = 0.9) -> None:
    amplitude_curves = {scheme: amplitude_curve(scheme, cfl) for scheme in ("upwind", "lax-friedrichs", "lax-wendroff")}
    phase_curves = {scheme: phase_speed_ratio_curve(scheme, cfl) for scheme in ("upwind", "lax-friedrichs", "lax-wendroff")}
    gaussian_runs = {scheme: simulate_transport(scheme, "gaussian", requested_cfl=cfl) for scheme in ("upwind", "lax-friedrichs", "lax-wendroff")}
    square_runs = {scheme: simulate_transport(scheme, "square", requested_cfl=cfl) for scheme in ("upwind", "lax-friedrichs", "lax-wendroff")}
    rows = study_transport(requested_cfls=(0.4, 0.7, cfl))
    svg = render_tradeoff_svg(amplitude_curves, phase_curves, gaussian_runs, square_runs, rows)
    write_svg(svg, svg_output)
    if png_output is not None:
        export_png(svg_output, png_output)


def render_limiter_followup(svg_output: Path, png_output: Path | None = None, *, cfl: float = 0.9) -> None:
    followup_schemes = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod")
    gaussian_runs = {scheme: simulate_transport(scheme, "gaussian", requested_cfl=cfl) for scheme in followup_schemes}
    square_runs = {scheme: simulate_transport(scheme, "square", requested_cfl=cfl) for scheme in followup_schemes}
    rows = study_transport(schemes=followup_schemes, requested_cfls=(0.4, 0.7, cfl))
    svg = render_limiter_followup_svg(gaussian_runs, square_runs, rows)
    write_svg(svg, svg_output)
    if png_output is not None:
        export_png(svg_output, png_output)


def render_cfl_sweep_followup(svg_output: Path, png_output: Path | None = None) -> None:
    followup_schemes = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod")
    rows = study_transport(schemes=followup_schemes, requested_cfls=DEFAULT_CFL_SWEEP)
    square_runs = {
        (scheme, cfl): simulate_transport(scheme, "square", requested_cfl=cfl)
        for scheme in ("lax-wendroff", "tvd-minmod")
        for cfl in (0.4, 0.95)
    }
    svg = render_cfl_sweep_followup_svg(rows, square_runs)
    write_svg(svg, svg_output)
    if png_output is not None:
        export_png(svg_output, png_output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Linear advection scheme tradeoff lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render-overview", help="render the overview SVG and optional PNG")
    render_parser.add_argument("--output", required=True)
    render_parser.add_argument("--png-output")
    render_parser.add_argument("--cfl", type=float, default=0.9)

    csv_parser = subparsers.add_parser("write-csv", help="write the transport comparison CSV")
    csv_parser.add_argument("--output", required=True)

    render_limiter_parser = subparsers.add_parser("render-limiter-followup", help="render the TVD limiter follow-up SVG and optional PNG")
    render_limiter_parser.add_argument("--output", required=True)
    render_limiter_parser.add_argument("--png-output")
    render_limiter_parser.add_argument("--cfl", type=float, default=0.9)

    limiter_csv_parser = subparsers.add_parser("write-limiter-csv", help="write the TVD limiter follow-up CSV")
    limiter_csv_parser.add_argument("--output", required=True)

    render_cfl_parser = subparsers.add_parser("render-cfl-sweep-followup", help="render the CFL sweep follow-up SVG and optional PNG")
    render_cfl_parser.add_argument("--output", required=True)
    render_cfl_parser.add_argument("--png-output")

    cfl_csv_parser = subparsers.add_parser("write-cfl-sweep-csv", help="write the CFL sweep follow-up CSV")
    cfl_csv_parser.add_argument("--output", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "render-overview":
        render_overview(Path(args.output), Path(args.png_output) if args.png_output else None, cfl=args.cfl)
        return
    if args.command == "write-csv":
        write_transport_csv(Path(args.output))
        return
    if args.command == "render-limiter-followup":
        render_limiter_followup(Path(args.output), Path(args.png_output) if args.png_output else None, cfl=args.cfl)
        return
    if args.command == "write-limiter-csv":
        write_limiter_followup_csv(Path(args.output))
        return
    if args.command == "render-cfl-sweep-followup":
        render_cfl_sweep_followup(Path(args.output), Path(args.png_output) if args.png_output else None)
        return
    if args.command == "write-cfl-sweep-csv":
        write_cfl_sweep_followup_csv(Path(args.output))
        return
    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
