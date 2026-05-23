from __future__ import annotations

from html import escape
from pathlib import Path

from .analysis import TransportRow
from .core import SCHEME_TITLES, SimulationRun


SCHEME_COLORS = {
    "upwind": "#2563eb",
    "lax-friedrichs": "#f97316",
    "lax-wendroff": "#16a34a",
    "exact": "#111827",
}


def _text(x: float, y: float, text: str, *, size: int = 16, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
        f'font-family="Inter, Arial, sans-serif" text-anchor="{anchor}" font-weight="{weight}">{escape(text)}</text>'
    )


def _paragraph(
    x: float,
    y: float,
    lines: list[str],
    *,
    size: int = 14,
    fill: str = "#475569",
    line_height: int = 18,
    anchor: str = "start",
) -> str:
    return "".join(_text(x, y + index * line_height, line, size=size, fill=fill, anchor=anchor) for index, line in enumerate(lines))


def _line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#334155", width: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def _polyline(points: list[tuple[float, float]], *, stroke: str, width: float = 2.4, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    payload = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{dash_attr} points="{payload}"/>'


def render_tradeoff_svg(
    amplitude_curves: dict[str, tuple[tuple[float, float], ...]],
    phase_curves: dict[str, tuple[tuple[float, float], ...]],
    gaussian_runs: dict[str, SimulationRun],
    square_runs: dict[str, SimulationRun],
    rows: tuple[TransportRow, ...],
) -> str:
    width = 1760
    height = 1220
    left = 60
    top = 198
    right = width - 160
    bottom = height - 72
    panel_gap_x = 34
    panel_gap_y = 46
    panel_width = (right - left - panel_gap_x) / 2
    panel_height = (bottom - top - panel_gap_y) / 2

    def panel_rect(col: int, row: int) -> tuple[float, float]:
        return left + col * (panel_width + panel_gap_x), top + row * (panel_height + panel_gap_y)

    def chart_frame(col: int, row: int) -> tuple[float, float, float, float]:
        panel_left, panel_top = panel_rect(col, row)
        return panel_left + 70, panel_top + 118, panel_left + panel_width - 40, panel_top + panel_height - 58

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfcfd"/>',
        _text(width / 2, 46, "Advection scheme tradeoffs on one periodic turn", size=31, anchor="middle", weight="700"),
        _paragraph(
            width / 2,
            78,
            [
                "Upwind and Lax-Friedrichs damp high wavenumbers.",
                "Lax-Wendroff keeps smooth waves sharper, but it pays with dispersive ringing near a jump.",
            ],
            size=17,
            fill="#475569",
            line_height=22,
            anchor="middle",
        ),
    ]
    legend_y = 146
    legend_items = [
        ("exact", "exact"),
        ("upwind", SCHEME_TITLES["upwind"]),
        ("lax-friedrichs", SCHEME_TITLES["lax-friedrichs"]),
        ("lax-wendroff", SCHEME_TITLES["lax-wendroff"]),
    ]
    x = 360
    for key, label in legend_items:
        dash = "7 5" if key == "exact" else None
        parts.append(_line(x, legend_y, x + 28, legend_y, stroke=SCHEME_COLORS[key], width=3.5, dash=dash))
        parts.append(_text(x + 40, legend_y + 5, label, size=14, fill="#111827"))
        x += 220

    for row in range(2):
        for col in range(2):
            panel_left, panel_top = panel_rect(col, row)
            parts.append(f'<rect x="{panel_left:.1f}" y="{panel_top:.1f}" width="{panel_width:.1f}" height="{panel_height:.1f}" fill="#ffffff" stroke="#e5e7eb" rx="18"/>')

    amp_left, amp_top, amp_right, amp_bottom = chart_frame(0, 0)
    parts.append(_text(left + 24, top + 34, "Von Neumann amplitude damping at CFL 0.9", size=20, weight="700"))
    parts.append(_paragraph(left + 24, top + 56, ["Values below 1 damp a Fourier mode in one step.", "Lax-Friedrichs is the harshest on short waves."], size=13, line_height=16))

    def map_generic(x_value: float, y_value: float, x0: float, y0: float, x1: float, y1: float, *, y_min: float, y_max: float) -> tuple[float, float]:
        x = x0 + x_value * (x1 - x0)
        y = y1 - (y_value - y_min) / (y_max - y_min) * (y1 - y0)
        return x, y

    for step in range(6):
        frac = step / 5
        y_value = frac
        _, y = map_generic(0.0, y_value, amp_left, amp_top, amp_right, amp_bottom, y_min=0.0, y_max=1.02)
        parts.append(_line(amp_left, y, amp_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(amp_left - 12, y + 5, f"{y_value:.1f}", size=12, anchor="end", fill="#64748b"))
    for step in range(6):
        frac = step / 5
        x_tick = amp_left + frac * (amp_right - amp_left)
        parts.append(_line(x_tick, amp_top, x_tick, amp_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, amp_bottom + 26, f"{frac:.1f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(amp_left, amp_top, amp_left, amp_bottom, width=1.5))
    parts.append(_line(amp_left, amp_bottom, amp_right, amp_bottom, width=1.5))
    parts.append(_text((amp_left + amp_right) / 2, amp_bottom + 46, "wavenumber / π", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(amp_left, amp_top - 16, "|G(θ)|", size=13, fill="#334155", weight="600"))
    for key, curve in amplitude_curves.items():
        mapped = [map_generic(x, y, amp_left, amp_top, amp_right, amp_bottom, y_min=0.0, y_max=1.02) for x, y in curve]
        parts.append(_polyline(mapped, stroke=SCHEME_COLORS[key], width=3.0))

    phase_left, phase_top, phase_right, phase_bottom = chart_frame(1, 0)
    panel_left, panel_top = panel_rect(1, 0)
    parts.append(_text(panel_left + 24, panel_top + 34, "Phase speed ratio at CFL 0.9", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["The exact line is 1.", "Lax-Wendroff stays closest on smooth modes.", "Near the grid scale it bends away fastest."], size=13, line_height=16))
    for step, value in enumerate((0.6, 0.7, 0.8, 0.9, 1.0)):
        _, y = map_generic(0.0, value, phase_left, phase_top, phase_right, phase_bottom, y_min=0.55, y_max=1.02)
        parts.append(_line(phase_left, y, phase_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(phase_left - 12, y + 5, f"{value:.1f}", size=12, anchor="end", fill="#64748b"))
    for step in range(6):
        frac = step / 5
        x_tick = phase_left + frac * (phase_right - phase_left)
        parts.append(_line(x_tick, phase_top, x_tick, phase_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, phase_bottom + 26, f"{frac:.1f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(phase_left, phase_top, phase_left, phase_bottom, width=1.5))
    parts.append(_line(phase_left, phase_bottom, phase_right, phase_bottom, width=1.5))
    parts.append(_text((phase_left + phase_right) / 2, phase_bottom + 46, "wavenumber / π", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(phase_left, phase_top - 16, "phase speed / exact", size=13, fill="#334155", weight="600"))
    parts.append(_line(phase_left, phase_bottom - (1.0 - 0.55) / (1.02 - 0.55) * (phase_bottom - phase_top), phase_right, phase_bottom - (1.0 - 0.55) / (1.02 - 0.55) * (phase_bottom - phase_top), stroke="#111827", width=1.6, dash="7 5"))
    for key, curve in phase_curves.items():
        mapped = [map_generic(x, y, phase_left, phase_top, phase_right, phase_bottom, y_min=0.55, y_max=1.02) for x, y in curve]
        parts.append(_polyline(mapped, stroke=SCHEME_COLORS[key], width=3.0))

    for col, run_group, title, subtitle in (
        (0, gaussian_runs, "Gaussian after one turn", "Smooth data rewards the lower-dispersion scheme. Upwind and Lax-Friedrichs blur the peak and spread the tail."),
        (1, square_runs, "Square pulse after one turn", "The jump is the stress test. Lax-Wendroff stays sharper but throws a Gibbs-style ripple. The diffusive schemes keep the jump monotone by smearing it."),
    ):
        plot_left, plot_top, plot_right, plot_bottom = chart_frame(col, 1)
        panel_left, panel_top = panel_rect(col, 1)
        parts.append(_text(panel_left + 24, panel_top + 34, title, size=20, weight="700"))
        subtitle_lines = {
            "Gaussian after one turn": [
                "Smooth data rewards the lower-dispersion scheme.",
                "Upwind and Lax-Friedrichs blur the peak.",
                "Lax-Wendroff stays closest to the exact return.",
            ],
            "Square pulse after one turn": [
                "The jump is the stress test.",
                "Lax-Wendroff stays sharper but throws a visible ripple.",
                "The diffusive schemes keep the edge monotone by smearing it.",
            ],
        }[title]
        parts.append(_paragraph(panel_left + 24, panel_top + 56, subtitle_lines, size=13, line_height=16))
        for step in range(6):
            frac = step / 5
            y_value = -0.2 + frac * 1.4
            _, y = map_generic(0.0, y_value, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
            parts.append(_line(plot_left, y, plot_right, y, stroke="#e5e7eb", dash="4 6"))
            parts.append(_text(plot_left - 12, y + 5, f"{y_value:.1f}", size=12, anchor="end", fill="#64748b"))
        x_min = 0.05
        x_max = 0.55
        for step in range(6):
            frac = step / 5
            tick_value = x_min + frac * (x_max - x_min)
            x_tick = plot_left + frac * (plot_right - plot_left)
            parts.append(_line(x_tick, plot_top, x_tick, plot_bottom, stroke="#f1f5f9", dash="4 6"))
            parts.append(_text(x_tick, plot_bottom + 26, f"{tick_value:.2f}", size=12, anchor="middle", fill="#64748b"))
        parts.append(_line(plot_left, plot_top, plot_left, plot_bottom, width=1.5))
        parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, width=1.5))
        parts.append(_text((plot_left + plot_right) / 2, plot_bottom + 46, "x on the periodic interval", size=14, anchor="middle", fill="#334155", weight="600"))
        exact_run = next(iter(run_group.values()))
        exact_points = [
            map_generic((x - x_min) / (x_max - x_min), y, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
            for x, y in zip(exact_run.x_values, exact_run.exact)
            if x_min <= x <= x_max
        ]
        parts.append(_polyline(exact_points, stroke=SCHEME_COLORS["exact"], width=2.5, dash="7 5"))
        for key, run in run_group.items():
            mapped = [
                map_generic((x - x_min) / (x_max - x_min), y, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
                for x, y in zip(run.x_values, run.numerical)
                if x_min <= x <= x_max
            ]
            parts.append(_polyline(mapped, stroke=SCHEME_COLORS[key], width=2.7))

    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def write_svg(svg: str, output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    return path
