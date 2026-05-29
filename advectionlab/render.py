from __future__ import annotations

from html import escape
from pathlib import Path

from .analysis import ModifiedEquationRow, TransportRow
from .core import SCHEME_TITLES, SimulationRun


SCHEME_COLORS = {
    "upwind": "#2563eb",
    "lax-friedrichs": "#f97316",
    "lax-wendroff": "#16a34a",
    "tvd-minmod": "#7c3aed",
    "tvd-mc": "#dc2626",
    "tvd-superbee": "#0891b2",
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


def render_limiter_followup_svg(
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
    followup_schemes = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod")

    def panel_rect(col: int, row: int) -> tuple[float, float]:
        return left + col * (panel_width + panel_gap_x), top + row * (panel_height + panel_gap_y)

    def chart_frame(col: int, row: int) -> tuple[float, float, float, float]:
        panel_left, panel_top = panel_rect(col, row)
        return panel_left + 70, panel_top + 118, panel_left + panel_width - 40, panel_top + panel_height - 58

    def map_generic(
        x_value: float,
        y_value: float,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        *,
        y_min: float,
        y_max: float,
    ) -> tuple[float, float]:
        x = x0 + x_value * (x1 - x0)
        y = y1 - (y_value - y_min) / (y_max - y_min) * (y1 - y0)
        return x, y

    rows_by_key = {
        (row.profile_key, round(row.requested_cfl, 1), row.scheme_key): row
        for row in rows
    }
    gaussian_lw = rows_by_key[("gaussian", 0.9, "lax-wendroff")]
    gaussian_minmod = rows_by_key[("gaussian", 0.9, "tvd-minmod")]
    square_lw = rows_by_key[("square", 0.9, "lax-wendroff")]
    square_minmod = rows_by_key[("square", 0.9, "tvd-minmod")]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfcfd"/>',
        _text(width / 2, 46, "TVD minmod follow-up: a real middle lane", size=31, anchor="middle", weight="700"),
        _paragraph(
            width / 2,
            78,
            [
                "The limiter keeps the square pulse monotone while staying much sharper than upwind.",
                f"At CFL 0.9, TVD minmod cuts the Gaussian L2 error to {gaussian_minmod.l2_error:.4f} while Lax-Wendroff stays best on the smooth lane at {gaussian_lw.l2_error:.4f}.",
                f"On the square pulse, TVD minmod holds overshoot at {square_minmod.overshoot:.1f} and keeps total variation at {square_minmod.total_variation_ratio:.3f}, while Lax-Wendroff blows TV up to {square_lw.total_variation_ratio:.3f}.",
            ],
            size=16,
            fill="#475569",
            line_height=21,
            anchor="middle",
        ),
    ]
    legend_y = 166
    legend_items = [
        ("exact", "exact"),
        ("upwind", SCHEME_TITLES["upwind"]),
        ("lax-friedrichs", SCHEME_TITLES["lax-friedrichs"]),
        ("lax-wendroff", SCHEME_TITLES["lax-wendroff"]),
        ("tvd-minmod", SCHEME_TITLES["tvd-minmod"]),
    ]
    x = 236
    for key, label in legend_items:
        dash = "7 5" if key == "exact" else None
        parts.append(_line(x, legend_y, x + 28, legend_y, stroke=SCHEME_COLORS[key], width=3.5, dash=dash))
        parts.append(_text(x + 40, legend_y + 5, label, size=14, fill="#111827"))
        x += 150 if key == "exact" else 220

    for row_index in range(2):
        for col_index in range(2):
            panel_left, panel_top = panel_rect(col_index, row_index)
            parts.append(
                f'<rect x="{panel_left:.1f}" y="{panel_top:.1f}" width="{panel_width:.1f}" height="{panel_height:.1f}" fill="#ffffff" stroke="#e5e7eb" rx="18"/>'
            )

    for col, run_group, title, subtitle in (
        (
            0,
            gaussian_runs,
            "Gaussian after one turn at CFL 0.9",
            [
                "Lax-Wendroff still owns the clean smooth-wave lane.",
                "TVD minmod is the honest compromise: sharper than upwind and Lax-Friedrichs, but still bounded.",
            ],
        ),
        (
            1,
            square_runs,
            "Square pulse after one turn at CFL 0.9",
            [
                "The limiter keeps the edge monotone instead of throwing the Lax-Wendroff ripple.",
                "It is not free, but it buys a much cleaner jump without falling all the way back to upwind blur.",
            ],
        ),
    ):
        plot_left, plot_top, plot_right, plot_bottom = chart_frame(col, 0)
        panel_left, panel_top = panel_rect(col, 0)
        parts.append(_text(panel_left + 24, panel_top + 34, title, size=20, weight="700"))
        parts.append(_paragraph(panel_left + 24, panel_top + 56, subtitle, size=13, line_height=16))
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
            map_generic((x_value - x_min) / (x_max - x_min), y_value, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
            for x_value, y_value in zip(exact_run.x_values, exact_run.exact)
            if x_min <= x_value <= x_max
        ]
        parts.append(_polyline(exact_points, stroke=SCHEME_COLORS["exact"], width=2.5, dash="7 5"))
        for scheme_key in followup_schemes:
            run = run_group[scheme_key]
            mapped = [
                map_generic((x_value - x_min) / (x_max - x_min), y_value, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
                for x_value, y_value in zip(run.x_values, run.numerical)
                if x_min <= x_value <= x_max
            ]
            parts.append(_polyline(mapped, stroke=SCHEME_COLORS[scheme_key], width=2.7))

    gaussian_rows = [row for row in rows if row.profile_key == "gaussian"]
    l2_left, l2_top, l2_right, l2_bottom = chart_frame(0, 1)
    panel_left, panel_top = panel_rect(0, 1)
    parts.append(_text(panel_left + 24, panel_top + 34, "Gaussian L2 error across CFL", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["The limiter opens a middle lane.", "It stays much closer to Lax-Wendroff than to the diffusive schemes on smooth data."], size=13, line_height=16))
    l2_max = max(row.l2_error for row in gaussian_rows) * 1.1
    for tick in (0.0, 0.04, 0.08, 0.12, 0.16):
        _, y = map_generic(0.0, tick, l2_left, l2_top, l2_right, l2_bottom, y_min=0.0, y_max=l2_max)
        parts.append(_line(l2_left, y, l2_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(l2_left - 12, y + 5, f"{tick:.2f}", size=12, anchor="end", fill="#64748b"))
    for tick in (0.4, 0.7, 0.9):
        x_tick = l2_left + (tick - 0.4) / 0.5 * (l2_right - l2_left)
        parts.append(_line(x_tick, l2_top, x_tick, l2_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, l2_bottom + 26, f"{tick:.1f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(l2_left, l2_top, l2_left, l2_bottom, width=1.5))
    parts.append(_line(l2_left, l2_bottom, l2_right, l2_bottom, width=1.5))
    parts.append(_text((l2_left + l2_right) / 2, l2_bottom + 46, "requested CFL", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(l2_left, l2_top - 16, "L2 error", size=13, fill="#334155", weight="600"))
    for scheme_key in followup_schemes:
        curve = [
            map_generic((row.requested_cfl - 0.4) / 0.5, row.l2_error, l2_left, l2_top, l2_right, l2_bottom, y_min=0.0, y_max=l2_max)
            for row in gaussian_rows
            if row.scheme_key == scheme_key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[scheme_key], width=3.0))

    square_rows = [row for row in rows if row.profile_key == "square"]
    tv_left, tv_top, tv_right, tv_bottom = chart_frame(1, 1)
    panel_left, panel_top = panel_rect(1, 1)
    parts.append(_text(panel_left + 24, panel_top + 34, "Square-pulse total variation ratio", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["Exact total variation sits at 1.", "TVD minmod stays on the monotone side of that line while Lax-Wendroff grows extra variation as ringing."], size=13, line_height=16))
    for tick in (0.6, 1.0, 1.4, 1.8, 2.2):
        _, y = map_generic(0.0, tick, tv_left, tv_top, tv_right, tv_bottom, y_min=0.6, y_max=2.2)
        parts.append(_line(tv_left, y, tv_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(tv_left - 12, y + 5, f"{tick:.1f}", size=12, anchor="end", fill="#64748b"))
    for tick in (0.4, 0.7, 0.9):
        x_tick = tv_left + (tick - 0.4) / 0.5 * (tv_right - tv_left)
        parts.append(_line(x_tick, tv_top, x_tick, tv_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, tv_bottom + 26, f"{tick:.1f}", size=12, anchor="middle", fill="#64748b"))
    exact_y = map_generic(0.0, 1.0, tv_left, tv_top, tv_right, tv_bottom, y_min=0.6, y_max=2.2)[1]
    parts.append(_line(tv_left, exact_y, tv_right, exact_y, stroke="#111827", width=1.6, dash="7 5"))
    parts.append(_line(tv_left, tv_top, tv_left, tv_bottom, width=1.5))
    parts.append(_line(tv_left, tv_bottom, tv_right, tv_bottom, width=1.5))
    parts.append(_text((tv_left + tv_right) / 2, tv_bottom + 46, "requested CFL", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(tv_left, tv_top - 16, "TV / exact TV", size=13, fill="#334155", weight="600"))
    for scheme_key in followup_schemes:
        curve = [
            map_generic((row.requested_cfl - 0.4) / 0.5, row.total_variation_ratio, tv_left, tv_top, tv_right, tv_bottom, y_min=0.6, y_max=2.2)
            for row in square_rows
            if row.scheme_key == scheme_key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[scheme_key], width=3.0))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_modified_equation_followup_svg(
    rows: tuple[ModifiedEquationRow, ...],
    *,
    focus_cfl: float = 0.95,
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
    linear_schemes = ("upwind", "lax-friedrichs", "lax-wendroff")
    all_schemes = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod", "tvd-mc", "tvd-superbee")

    def panel_rect(col: int, row: int) -> tuple[float, float]:
        return left + col * (panel_width + panel_gap_x), top + row * (panel_height + panel_gap_y)

    def chart_frame(col: int, row: int) -> tuple[float, float, float, float]:
        panel_left, panel_top = panel_rect(col, row)
        return panel_left + 70, panel_top + 118, panel_left + panel_width - 40, panel_top + panel_height - 58

    def map_generic(
        x_value: float,
        y_value: float,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        *,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
    ) -> tuple[float, float]:
        x = x0 + (x_value - x_min) / (x_max - x_min) * (x1 - x0)
        y = y1 - (y_value - y_min) / (y_max - y_min) * (y1 - y0)
        return x, y

    rows_by_key = {(row.scheme_key, round(row.requested_cfl, 2)): row for row in rows}
    focus_rows = {scheme: rows_by_key[(scheme, round(focus_cfl, 2))] for scheme in all_schemes}
    mc_focus = focus_rows["tvd-mc"]
    superbee_focus = focus_rows["tvd-superbee"]
    lw_focus = focus_rows["lax-wendroff"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfcfd"/>',
        _text(width / 2, 46, "Modified-equation follow-up: where the linear tradeoff stops", size=31, anchor="middle", weight="700"),
        _paragraph(
            width / 2,
            78,
            [
                "The linear schemes sit on one diffusion-versus-dispersion curve. The limiter family matters because it can step off that curve instead of merely sliding along it.",
                f"At CFL {focus_cfl:.2f}, TVD MC reaches Gaussian L2 error {mc_focus.gaussian_l2_error:.4f} with zero overshoot, while Lax-Wendroff reaches {lw_focus.gaussian_l2_error:.4f} but pays square-pulse overshoot {lw_focus.square_overshoot:.3f}.",
                f"Inside the bounded family itself, Superbee is still the sharpest jump read at square-pulse L2 error {superbee_focus.square_l2_error:.4f}.",
            ],
            size=16,
            fill="#475569",
            line_height=21,
            anchor="middle",
        ),
    ]
    legend_y = 168
    x = 190
    for key in all_schemes:
        parts.append(_line(x, legend_y, x + 28, legend_y, stroke=SCHEME_COLORS[key], width=3.5))
        parts.append(_text(x + 40, legend_y + 5, SCHEME_TITLES[key], size=14, fill="#111827"))
        x += 220 if key != "tvd-superbee" else 200

    for row_index in range(2):
        for col_index in range(2):
            panel_left, panel_top = panel_rect(col_index, row_index)
            parts.append(
                f'<rect x="{panel_left:.1f}" y="{panel_top:.1f}" width="{panel_width:.1f}" height="{panel_height:.1f}" fill="#ffffff" stroke="#e5e7eb" rx="18"/>'
            )

    # Panel 1: diffusion coefficients
    plot_left, plot_top, plot_right, plot_bottom = chart_frame(0, 0)
    panel_left, panel_top = panel_rect(0, 0)
    parts.append(_text(panel_left + 24, panel_top + 34, "Low-wavenumber diffusion coefficient D(ν)", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, [
        "Defined from log G(θ) ≈ -iνθ - D(ν)θ² + iK(ν)θ³ near θ = 0.",
        "Lax-Wendroff is the nearly zero-diffusion endpoint; Lax-Friedrichs is the most diffusive.",
    ], size=13, line_height=16))
    for value in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        _, y = map_generic(0.2, value, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=0.0, y_max=0.52)
        parts.append(_line(plot_left, y, plot_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(plot_left - 12, y + 5, f"{value:.1f}", size=12, anchor="end", fill="#64748b"))
    for value in (0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 0.95):
        x_tick, _ = map_generic(value, 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=0.0, y_max=0.52)
        parts.append(_line(x_tick, plot_top, x_tick, plot_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, plot_bottom + 26, f"{value:.2f}" if value == 0.95 else f"{value:.2f}".rstrip("0"), size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(plot_left, plot_top, plot_left, plot_bottom, width=1.5))
    parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, width=1.5))
    parts.append(_text((plot_left + plot_right) / 2, plot_bottom + 46, "CFL ν", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(plot_left, plot_top - 16, "dimensionless D(ν)", size=13, fill="#334155", weight="600"))
    for key in linear_schemes:
        curve = [
            map_generic(row.requested_cfl, row.diffusion_coeff or 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=0.0, y_max=0.52)
            for row in rows
            if row.scheme_key == key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[key], width=3.0))

    # Panel 2: dispersion coefficients
    plot_left, plot_top, plot_right, plot_bottom = chart_frame(1, 0)
    panel_left, panel_top = panel_rect(1, 0)
    parts.append(_text(panel_left + 24, panel_top + 34, "Low-wavenumber dispersion coefficient K(ν)", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, [
        "The sign says which way the third-derivative phase defect bends.",
        "Lax-Wendroff keeps almost no diffusion, so its leading smooth-wave defect is mostly dispersive.",
    ], size=13, line_height=16))
    for value in (-0.12, -0.08, -0.04, 0.0, 0.04, 0.08):
        _, y = map_generic(0.2, value, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=-0.13, y_max=0.08)
        parts.append(_line(plot_left, y, plot_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(plot_left - 12, y + 5, f"{value:+.2f}", size=12, anchor="end", fill="#64748b"))
    for value in (0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 0.95):
        x_tick, _ = map_generic(value, 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=-0.13, y_max=0.08)
        parts.append(_line(x_tick, plot_top, x_tick, plot_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, plot_bottom + 26, f"{value:.2f}" if value == 0.95 else f"{value:.2f}".rstrip("0"), size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(plot_left, plot_top, plot_left, plot_bottom, width=1.5))
    parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, width=1.5))
    zero_y = map_generic(0.2, 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=-0.13, y_max=0.08)[1]
    parts.append(_line(plot_left, zero_y, plot_right, zero_y, stroke="#111827", width=1.2, dash="7 5"))
    parts.append(_text((plot_left + plot_right) / 2, plot_bottom + 46, "CFL ν", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(plot_left, plot_top - 16, "dimensionless K(ν)", size=13, fill="#334155", weight="600"))
    for key in linear_schemes:
        curve = [
            map_generic(row.requested_cfl, row.dispersion_coeff or 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.2, x_max=0.95, y_min=-0.13, y_max=0.08)
            for row in rows
            if row.scheme_key == key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[key], width=3.0))

    # Panel 3: Gaussian error vs square overshoot
    plot_left, plot_top, plot_right, plot_bottom = chart_frame(0, 1)
    panel_left, panel_top = panel_rect(0, 1)
    parts.append(_text(panel_left + 24, panel_top + 34, f"At CFL {focus_cfl:.2f}: smooth accuracy versus jump overshoot", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, [
        "The linear schemes sit on one visible compromise curve: less Gaussian error usually buys more square-pulse overshoot.",
        "The TVD markers matter because they drop to the overshoot floor instead of staying on that linear branch.",
    ], size=13, line_height=16))
    for value in (0.0, 0.03, 0.06, 0.09, 0.12, 0.15):
        _, y = map_generic(0.0, value, plot_left, plot_top, plot_right, plot_bottom, x_min=0.0, x_max=0.016, y_min=0.0, y_max=0.16)
        parts.append(_line(plot_left, y, plot_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(plot_left - 12, y + 5, f"{value:.2f}", size=12, anchor="end", fill="#64748b"))
    for value in (0.0, 0.004, 0.008, 0.012, 0.016):
        x_tick, _ = map_generic(value, 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.0, x_max=0.016, y_min=0.0, y_max=0.16)
        parts.append(_line(x_tick, plot_top, x_tick, plot_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, plot_bottom + 26, f"{value:.3f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(plot_left, plot_top, plot_left, plot_bottom, width=1.5))
    parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, width=1.5))
    parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, stroke="#111827", width=1.2, dash="7 5"))
    parts.append(_text((plot_left + plot_right) / 2, plot_bottom + 46, "Gaussian one-turn L2 error", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(plot_left, plot_top - 16, "square-pulse overshoot", size=13, fill="#334155", weight="600"))
    short_labels = {
        "upwind": "Upwind",
        "lax-friedrichs": "Lax-F",
        "lax-wendroff": "Lax-W",
        "tvd-minmod": "Minmod",
        "tvd-mc": "MC",
        "tvd-superbee": "Superbee",
    }
    for key in all_schemes:
        row = focus_rows[key]
        x, y = map_generic(row.gaussian_l2_error, row.square_overshoot, plot_left, plot_top, plot_right, plot_bottom, x_min=0.0, x_max=0.016, y_min=0.0, y_max=0.16)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{SCHEME_COLORS[key]}" stroke="#ffffff" stroke-width="2"/>')
        label_offsets = {
            "upwind": (-12, -10, "end"),
            "lax-friedrichs": (12, -10, "start"),
            "lax-wendroff": (12, -12, "start"),
            "tvd-minmod": (12, -24, "start"),
            "tvd-mc": (12, 18, "start"),
            "tvd-superbee": (12, -26, "start"),
        }
        dx, dy, anchor = label_offsets[key]
        parts.append(_text(x + dx, y + dy, short_labels[key], size=13, fill="#111827", anchor=anchor, weight="600"))

    # Panel 4: zero-overshoot family split
    plot_left, plot_top, plot_right, plot_bottom = chart_frame(1, 1)
    panel_left, panel_top = panel_rect(1, 1)
    parts.append(_text(panel_left + 24, panel_top + 34, f"Zero-overshoot family at CFL {focus_cfl:.2f}", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, [
        "Once overshoot is pinned to zero, the family still does not collapse to one answer.",
        "MC is the smooth bounded winner here; Superbee is the sharpest bounded jump winner.",
    ], size=13, line_height=16))
    zero_overshoot_rows = [focus_rows[key] for key in ("upwind", "lax-friedrichs", "tvd-minmod", "tvd-mc", "tvd-superbee")]
    for value in (0.0, 0.02, 0.04, 0.06, 0.08, 0.10):
        _, y = map_generic(0.0, value, plot_left, plot_top, plot_right, plot_bottom, x_min=0.0, x_max=0.016, y_min=0.0, y_max=0.105)
        parts.append(_line(plot_left, y, plot_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(plot_left - 12, y + 5, f"{value:.2f}", size=12, anchor="end", fill="#64748b"))
    for value in (0.0, 0.004, 0.008, 0.012, 0.016):
        x_tick, _ = map_generic(value, 0.0, plot_left, plot_top, plot_right, plot_bottom, x_min=0.0, x_max=0.016, y_min=0.0, y_max=0.105)
        parts.append(_line(x_tick, plot_top, x_tick, plot_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, plot_bottom + 26, f"{value:.3f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(plot_left, plot_top, plot_left, plot_bottom, width=1.5))
    parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, width=1.5))
    parts.append(_text((plot_left + plot_right) / 2, plot_bottom + 46, "Gaussian one-turn L2 error", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(plot_left, plot_top - 16, "square-pulse L2 error", size=13, fill="#334155", weight="600"))
    for row in zero_overshoot_rows:
        x, y = map_generic(row.gaussian_l2_error, row.square_l2_error, plot_left, plot_top, plot_right, plot_bottom, x_min=0.0, x_max=0.016, y_min=0.0, y_max=0.105)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{SCHEME_COLORS[row.scheme_key]}" stroke="#ffffff" stroke-width="2"/>')
        label_offsets = {
            "upwind": (-12, -8, "end"),
            "lax-friedrichs": (-12, 18, "end"),
            "tvd-minmod": (12, -10, "start"),
            "tvd-mc": (12, 18, "start"),
            "tvd-superbee": (12, -12, "start"),
        }
        dx, dy, anchor = label_offsets[row.scheme_key]
        parts.append(_text(x + dx, y + dy, short_labels[row.scheme_key], size=13, fill="#111827", anchor=anchor, weight="600"))

    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render_cfl_sweep_followup_svg(
    rows: tuple[TransportRow, ...],
    square_runs: dict[tuple[str, float], SimulationRun],
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
    followup_schemes = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod")

    def panel_rect(col: int, row: int) -> tuple[float, float]:
        return left + col * (panel_width + panel_gap_x), top + row * (panel_height + panel_gap_y)

    def chart_frame(col: int, row: int) -> tuple[float, float, float, float]:
        panel_left, panel_top = panel_rect(col, row)
        return panel_left + 70, panel_top + 118, panel_left + panel_width - 40, panel_top + panel_height - 58

    def map_generic(
        x_value: float,
        y_value: float,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        *,
        y_min: float,
        y_max: float,
    ) -> tuple[float, float]:
        x = x0 + x_value * (x1 - x0)
        y = y1 - (y_value - y_min) / (y_max - y_min) * (y1 - y0)
        return x, y

    rows_by_key = {(row.profile_key, round(row.requested_cfl, 2), row.scheme_key): row for row in rows}
    lw_square_low = rows_by_key[("square", 0.4, "lax-wendroff")]
    lw_square_high = rows_by_key[("square", 0.95, "lax-wendroff")]
    minmod_square_low = rows_by_key[("square", 0.4, "tvd-minmod")]
    minmod_square_high = rows_by_key[("square", 0.95, "tvd-minmod")]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfcfd"/>',
        _text(width / 2, 46, "CFL sweep follow-up: the ranking compresses near a grid shift", size=30, anchor="middle", weight="700"),
        _paragraph(
            width / 2,
            78,
            [
                "Away from CFL 1, the earlier story holds: Lax-Wendroff wins the smooth lane, TVD minmod owns the bounded jump lane.",
                f"At CFL 0.4, Lax-Wendroff square overshoot is {lw_square_low.overshoot:.4f}; by CFL 0.95 it falls to {lw_square_high.overshoot:.4f}.",
                "At CFL 1 on this periodic one-turn problem, every scheme lands on an exact grid translation instead of its usual diffusion-or-ringing personality.",
            ],
            size=16,
            fill="#475569",
            line_height=21,
            anchor="middle",
        ),
    ]
    legend_y = 166
    legend_items = [
        ("upwind", SCHEME_TITLES["upwind"]),
        ("lax-friedrichs", SCHEME_TITLES["lax-friedrichs"]),
        ("lax-wendroff", SCHEME_TITLES["lax-wendroff"]),
        ("tvd-minmod", SCHEME_TITLES["tvd-minmod"]),
        ("exact", "exact"),
    ]
    x = 220
    for key, label in legend_items:
        dash = "7 5" if key == "exact" else None
        parts.append(_line(x, legend_y, x + 28, legend_y, stroke=SCHEME_COLORS[key], width=3.5, dash=dash))
        parts.append(_text(x + 40, legend_y + 5, label, size=14, fill="#111827"))
        x += 210 if key != "exact" else 150

    for row_index in range(2):
        for col_index in range(2):
            panel_left, panel_top = panel_rect(col_index, row_index)
            parts.append(
                f'<rect x="{panel_left:.1f}" y="{panel_top:.1f}" width="{panel_width:.1f}" height="{panel_height:.1f}" fill="#ffffff" stroke="#e5e7eb" rx="18"/>'
            )

    gaussian_rows = [row for row in rows if row.profile_key == "gaussian"]
    gaussian_max = max(row.l2_error for row in gaussian_rows) * 1.08
    gauss_left, gauss_top, gauss_right, gauss_bottom = chart_frame(0, 0)
    panel_left, panel_top = panel_rect(0, 0)
    parts.append(_text(panel_left + 24, panel_top + 34, "Gaussian L2 error across CFL", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["Lax-Wendroff stays first all the way across.", "The middle lane survives, but every scheme sharpens as the step moves toward a one-cell shift."], size=13, line_height=16))
    for tick in range(6):
        y_value = gaussian_max * tick / 5
        _, y = map_generic(0.0, y_value, gauss_left, gauss_top, gauss_right, gauss_bottom, y_min=0.0, y_max=gaussian_max)
        parts.append(_line(gauss_left, y, gauss_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(gauss_left - 12, y + 5, f"{y_value:.3f}", size=12, anchor="end", fill="#64748b"))
    for tick_value in (0.2, 0.4, 0.6, 0.8, 1.0):
        x_tick = gauss_left + (tick_value - 0.2) / 0.8 * (gauss_right - gauss_left)
        parts.append(_line(x_tick, gauss_top, x_tick, gauss_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, gauss_bottom + 26, f"{tick_value:.1f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(gauss_left, gauss_top, gauss_left, gauss_bottom, width=1.5))
    parts.append(_line(gauss_left, gauss_bottom, gauss_right, gauss_bottom, width=1.5))
    parts.append(_text((gauss_left + gauss_right) / 2, gauss_bottom + 46, "requested CFL", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(gauss_left, gauss_top - 16, "L2 error", size=13, fill="#334155", weight="600"))
    for scheme_key in followup_schemes:
        curve = [
            map_generic((row.requested_cfl - 0.2) / 0.8, row.l2_error, gauss_left, gauss_top, gauss_right, gauss_bottom, y_min=0.0, y_max=gaussian_max)
            for row in gaussian_rows
            if row.scheme_key == scheme_key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[scheme_key], width=3.0))

    square_rows = [row for row in rows if row.profile_key == "square"]
    square_l2_max = max(row.l2_error for row in square_rows) * 1.08
    square_left, square_top, square_right, square_bottom = chart_frame(1, 0)
    panel_left, panel_top = panel_rect(1, 0)
    parts.append(_text(panel_left + 24, panel_top + 34, "Square-pulse L2 error across CFL", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["TVD minmod stays best until the near-unit-CFL collapse.", "The square lane still cares about boundedness long after the smooth lane is already nearly perfect."], size=13, line_height=16))
    for tick in range(6):
        y_value = square_l2_max * tick / 5
        _, y = map_generic(0.0, y_value, square_left, square_top, square_right, square_bottom, y_min=0.0, y_max=square_l2_max)
        parts.append(_line(square_left, y, square_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(square_left - 12, y + 5, f"{y_value:.3f}", size=12, anchor="end", fill="#64748b"))
    for tick_value in (0.2, 0.4, 0.6, 0.8, 1.0):
        x_tick = square_left + (tick_value - 0.2) / 0.8 * (square_right - square_left)
        parts.append(_line(x_tick, square_top, x_tick, square_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, square_bottom + 26, f"{tick_value:.1f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(square_left, square_top, square_left, square_bottom, width=1.5))
    parts.append(_line(square_left, square_bottom, square_right, square_bottom, width=1.5))
    parts.append(_text((square_left + square_right) / 2, square_bottom + 46, "requested CFL", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(square_left, square_top - 16, "L2 error", size=13, fill="#334155", weight="600"))
    for scheme_key in followup_schemes:
        curve = [
            map_generic((row.requested_cfl - 0.2) / 0.8, row.l2_error, square_left, square_top, square_right, square_bottom, y_min=0.0, y_max=square_l2_max)
            for row in square_rows
            if row.scheme_key == scheme_key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[scheme_key], width=3.0))

    overshoot_left, overshoot_top, overshoot_right, overshoot_bottom = chart_frame(0, 1)
    panel_left, panel_top = panel_rect(0, 1)
    overshoot_max = max(row.overshoot for row in square_rows) * 1.1
    parts.append(_text(panel_left + 24, panel_top + 34, "Square-pulse overshoot across CFL", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["Only Lax-Wendroff goes above zero here.", "Its ripple fades as CFL approaches 1, but it stays a real penalty until the exact-shift endpoint."], size=13, line_height=16))
    for tick in range(6):
        y_value = overshoot_max * tick / 5
        _, y = map_generic(0.0, y_value, overshoot_left, overshoot_top, overshoot_right, overshoot_bottom, y_min=0.0, y_max=overshoot_max)
        parts.append(_line(overshoot_left, y, overshoot_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(overshoot_left - 12, y + 5, f"{y_value:.2f}", size=12, anchor="end", fill="#64748b"))
    exact_y = map_generic(0.0, 0.0, overshoot_left, overshoot_top, overshoot_right, overshoot_bottom, y_min=0.0, y_max=overshoot_max)[1]
    parts.append(_line(overshoot_left, exact_y, overshoot_right, exact_y, stroke="#111827", width=1.6, dash="7 5"))
    for tick_value in (0.2, 0.4, 0.6, 0.8, 1.0):
        x_tick = overshoot_left + (tick_value - 0.2) / 0.8 * (overshoot_right - overshoot_left)
        parts.append(_line(x_tick, overshoot_top, x_tick, overshoot_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, overshoot_bottom + 26, f"{tick_value:.1f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(overshoot_left, overshoot_top, overshoot_left, overshoot_bottom, width=1.5))
    parts.append(_line(overshoot_left, overshoot_bottom, overshoot_right, overshoot_bottom, width=1.5))
    parts.append(_text((overshoot_left + overshoot_right) / 2, overshoot_bottom + 46, "requested CFL", size=14, anchor="middle", fill="#334155", weight="600"))
    parts.append(_text(overshoot_left, overshoot_top - 16, "overshoot", size=13, fill="#334155", weight="600"))
    for scheme_key in followup_schemes:
        curve = [
            map_generic((row.requested_cfl - 0.2) / 0.8, row.overshoot, overshoot_left, overshoot_top, overshoot_right, overshoot_bottom, y_min=0.0, y_max=overshoot_max)
            for row in square_rows
            if row.scheme_key == scheme_key
        ]
        parts.append(_polyline(curve, stroke=SCHEME_COLORS[scheme_key], width=3.0))

    trace_left, trace_top, trace_right, trace_bottom = chart_frame(1, 1)
    panel_left, panel_top = panel_rect(1, 1)
    parts.append(_text(panel_left + 24, panel_top + 34, "Square pulse snapshots: CFL 0.4 versus 0.95", size=20, weight="700"))
    parts.append(_paragraph(panel_left + 24, panel_top + 56, ["Dashed lines use CFL 0.4. Solid lines use CFL 0.95.", "The jump still prefers the bounded limiter, but both curves tighten sharply as the step nears a one-cell translation."], size=13, line_height=16))
    for step in range(6):
        frac = step / 5
        y_value = -0.2 + frac * 1.4
        _, y = map_generic(0.0, y_value, trace_left, trace_top, trace_right, trace_bottom, y_min=-0.2, y_max=1.2)
        parts.append(_line(trace_left, y, trace_right, y, stroke="#e5e7eb", dash="4 6"))
        parts.append(_text(trace_left - 12, y + 5, f"{y_value:.1f}", size=12, anchor="end", fill="#64748b"))
    x_min = 0.10
    x_max = 0.50
    for step in range(5):
        frac = step / 4
        tick_value = x_min + frac * (x_max - x_min)
        x_tick = trace_left + frac * (trace_right - trace_left)
        parts.append(_line(x_tick, trace_top, x_tick, trace_bottom, stroke="#f1f5f9", dash="4 6"))
        parts.append(_text(x_tick, trace_bottom + 26, f"{tick_value:.2f}", size=12, anchor="middle", fill="#64748b"))
    parts.append(_line(trace_left, trace_top, trace_left, trace_bottom, width=1.5))
    parts.append(_line(trace_left, trace_bottom, trace_right, trace_bottom, width=1.5))
    parts.append(_text((trace_left + trace_right) / 2, trace_bottom + 46, "x on the periodic interval", size=14, anchor="middle", fill="#334155", weight="600"))
    exact_run = square_runs[("lax-wendroff", 0.95)]
    exact_points = [
        map_generic((x_value - x_min) / (x_max - x_min), y_value, trace_left, trace_top, trace_right, trace_bottom, y_min=-0.2, y_max=1.2)
        for x_value, y_value in zip(exact_run.x_values, exact_run.exact)
        if x_min <= x_value <= x_max
    ]
    parts.append(_polyline(exact_points, stroke=SCHEME_COLORS["exact"], width=2.5, dash="7 5"))
    trace_specs = [
        ("lax-wendroff", 0.4, "7 5"),
        ("lax-wendroff", 0.95, None),
        ("tvd-minmod", 0.4, "7 5"),
        ("tvd-minmod", 0.95, None),
    ]
    for scheme_key, cfl, dash in trace_specs:
        run = square_runs[(scheme_key, cfl)]
        mapped = [
            map_generic((x_value - x_min) / (x_max - x_min), y_value, trace_left, trace_top, trace_right, trace_bottom, y_min=-0.2, y_max=1.2)
            for x_value, y_value in zip(run.x_values, run.numerical)
            if x_min <= x_value <= x_max
        ]
        parts.append(_polyline(mapped, stroke=SCHEME_COLORS[scheme_key], width=2.7, dash=dash))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_limiter_family_followup_svg(
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
    focus_cfl = round(next(iter(gaussian_runs.values())).requested_cfl, 2)
    followup_schemes = ("lax-wendroff", "tvd-minmod", "tvd-mc", "tvd-superbee")

    def panel_rect(col: int, row: int) -> tuple[float, float]:
        return left + col * (panel_width + panel_gap_x), top + row * (panel_height + panel_gap_y)

    def chart_frame(col: int, row: int) -> tuple[float, float, float, float]:
        panel_left, panel_top = panel_rect(col, row)
        return panel_left + 70, panel_top + 118, panel_left + panel_width - 40, panel_top + panel_height - 58

    def map_generic(
        x_value: float,
        y_value: float,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        *,
        y_min: float,
        y_max: float,
    ) -> tuple[float, float]:
        x = x0 + x_value * (x1 - x0)
        y = y1 - (y_value - y_min) / (y_max - y_min) * (y1 - y0)
        return x, y

    rows_by_key = {(row.profile_key, round(row.requested_cfl, 2), row.scheme_key): row for row in rows}
    gaussian_focus_rows = {scheme: rows_by_key[("gaussian", focus_cfl, scheme)] for scheme in followup_schemes}
    square_focus_rows = {scheme: rows_by_key[("square", focus_cfl, scheme)] for scheme in followup_schemes}
    mc_gaussian = gaussian_focus_rows["tvd-mc"]
    lw_gaussian = gaussian_focus_rows["lax-wendroff"]
    superbee_square = square_focus_rows["tvd-superbee"]
    mc_square = square_focus_rows["tvd-mc"]
    minmod_square = square_focus_rows["tvd-minmod"]

    gaussian_rows = [row for row in rows if row.profile_key == "gaussian"]
    square_rows = [row for row in rows if row.profile_key == "square"]
    cfl_min = min(row.requested_cfl for row in rows)
    cfl_max = max(row.requested_cfl for row in rows)
    gaussian_l2_max = max(row.l2_error for row in gaussian_rows) * 1.12
    square_l2_max = max(row.l2_error for row in square_rows) * 1.12

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfcfd"/>',
        _text(width / 2, 46, "TVD limiter family follow-up: one bounded lane is not enough", size=31, anchor="middle", weight="700"),
        _paragraph(
            width / 2,
            78,
            [
                f"At CFL {focus_cfl:.2f}, TVD MC cuts the Gaussian L2 error to {mc_gaussian.l2_error:.4f}, beating Lax-Wendroff's {lw_gaussian.l2_error:.4f} on this bounded smooth pulse.",
                f"On the square pulse, TVD Superbee pushes the bounded edge further, dropping L2 error to {superbee_square.l2_error:.4f} versus MC's {mc_square.l2_error:.4f} and minmod's {minmod_square.l2_error:.4f}.",
                "The useful read is the split itself: MC is the calmer smooth-wave limiter, Superbee is the sharper bounded jump limiter.",
            ],
            size=16,
            fill="#475569",
            line_height=21,
            anchor="middle",
        ),
    ]
    legend_y = 166
    legend_items = [("exact", "exact")] + [(scheme, SCHEME_TITLES[scheme]) for scheme in followup_schemes]
    x = 196
    for key, label in legend_items:
        dash = "7 5" if key == "exact" else None
        parts.append(_line(x, legend_y, x + 28, legend_y, stroke=SCHEME_COLORS[key], width=3.5, dash=dash))
        parts.append(_text(x + 40, legend_y + 5, label, size=14, fill="#111827"))
        x += 150 if key == "exact" else 190

    for row_index in range(2):
        for col_index in range(2):
            panel_left, panel_top = panel_rect(col_index, row_index)
            parts.append(
                f'<rect x="{panel_left:.1f}" y="{panel_top:.1f}" width="{panel_width:.1f}" height="{panel_height:.1f}" fill="#ffffff" stroke="#e5e7eb" rx="18"/>'
            )

    for col, run_group, title, subtitle_lines in (
        (
            0,
            gaussian_runs,
            f"Gaussian after one turn at CFL {focus_cfl:.2f}",
            [
                "MC is the bounded smooth-wave winner in this packet.",
                "Superbee stays bounded too, but keeps a slightly rougher smooth profile.",
            ],
        ),
        (
            1,
            square_runs,
            f"Square pulse after one turn at CFL {focus_cfl:.2f}",
            [
                "All three TVD limiters stay monotone here.",
                "Superbee keeps the sharpest bounded edge, while minmod gives away the most width.",
            ],
        ),
    ):
        plot_left, plot_top, plot_right, plot_bottom = chart_frame(col, 0)
        panel_left, panel_top = panel_rect(col, 0)
        parts.append(_text(panel_left + 24, panel_top + 34, title, size=20, weight="700"))
        parts.append(_paragraph(panel_left + 24, panel_top + 56, subtitle_lines, size=13, line_height=16))
        for step in range(6):
            frac = step / 5
            y_value = -0.2 + frac * 1.4
            _, y = map_generic(0.0, y_value, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
            parts.append(_line(plot_left, y, plot_right, y, stroke="#e5e7eb", dash="4 6"))
            parts.append(_text(plot_left - 12, y + 5, f"{y_value:.1f}", size=12, anchor="end", fill="#64748b"))
        x_min = 0.10
        x_max = 0.50
        for step in range(5):
            frac = step / 4
            tick_value = x_min + frac * (x_max - x_min)
            x_tick = plot_left + frac * (plot_right - plot_left)
            parts.append(_line(x_tick, plot_top, x_tick, plot_bottom, stroke="#f1f5f9", dash="4 6"))
            parts.append(_text(x_tick, plot_bottom + 26, f"{tick_value:.2f}", size=12, anchor="middle", fill="#64748b"))
        parts.append(_line(plot_left, plot_top, plot_left, plot_bottom, width=1.5))
        parts.append(_line(plot_left, plot_bottom, plot_right, plot_bottom, width=1.5))
        parts.append(_text((plot_left + plot_right) / 2, plot_bottom + 46, "x on the periodic interval", size=14, anchor="middle", fill="#334155", weight="600"))
        exact_run = next(iter(run_group.values()))
        exact_points = [
            map_generic((x_value - x_min) / (x_max - x_min), y_value, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
            for x_value, y_value in zip(exact_run.x_values, exact_run.exact)
            if x_min <= x_value <= x_max
        ]
        parts.append(_polyline(exact_points, stroke=SCHEME_COLORS["exact"], width=2.5, dash="7 5"))
        for scheme_key in followup_schemes:
            run = run_group[scheme_key]
            mapped = [
                map_generic((x_value - x_min) / (x_max - x_min), y_value, plot_left, plot_top, plot_right, plot_bottom, y_min=-0.2, y_max=1.2)
                for x_value, y_value in zip(run.x_values, run.numerical)
                if x_min <= x_value <= x_max
            ]
            parts.append(_polyline(mapped, stroke=SCHEME_COLORS[scheme_key], width=2.7))

    for col, profile_key, panel_title, subtitle_lines, y_max in (
        (
            0,
            "gaussian",
            "Gaussian L2 error across CFL",
            [
                "MC stays lowest on the smooth lane across this whole bounded sweep.",
                "Superbee buys square-edge sharpness by giving some of that smooth calm back.",
            ],
            gaussian_l2_max,
        ),
        (
            1,
            "square",
            "Square-pulse L2 error across CFL",
            [
                "Superbee leads the bounded jump lane across the sweep.",
                "Minmod stays safest-looking, but it pays with the fattest edge.",
            ],
            square_l2_max,
        ),
    ):
        chart_left, chart_top, chart_right, chart_bottom = chart_frame(col, 1)
        panel_left, panel_top = panel_rect(col, 1)
        parts.append(_text(panel_left + 24, panel_top + 34, panel_title, size=20, weight="700"))
        parts.append(_paragraph(panel_left + 24, panel_top + 56, subtitle_lines, size=13, line_height=16))
        for tick in range(6):
            y_value = y_max * tick / 5
            _, y = map_generic(0.0, y_value, chart_left, chart_top, chart_right, chart_bottom, y_min=0.0, y_max=y_max)
            parts.append(_line(chart_left, y, chart_right, y, stroke="#e5e7eb", dash="4 6"))
            parts.append(_text(chart_left - 12, y + 5, f"{y_value:.3f}", size=12, anchor="end", fill="#64748b"))
        for tick_value in sorted({row.requested_cfl for row in rows}):
            x_tick = chart_left + (tick_value - cfl_min) / (cfl_max - cfl_min) * (chart_right - chart_left)
            parts.append(_line(x_tick, chart_top, x_tick, chart_bottom, stroke="#f1f5f9", dash="4 6"))
            parts.append(_text(x_tick, chart_bottom + 26, f"{tick_value:.2f}", size=12, anchor="middle", fill="#64748b"))
        parts.append(_line(chart_left, chart_top, chart_left, chart_bottom, width=1.5))
        parts.append(_line(chart_left, chart_bottom, chart_right, chart_bottom, width=1.5))
        parts.append(_text((chart_left + chart_right) / 2, chart_bottom + 46, "requested CFL", size=14, anchor="middle", fill="#334155", weight="600"))
        parts.append(_text(chart_left, chart_top - 16, "L2 error", size=13, fill="#334155", weight="600"))
        for scheme_key in followup_schemes:
            curve = [
                map_generic(
                    (row.requested_cfl - cfl_min) / (cfl_max - cfl_min),
                    row.l2_error,
                    chart_left,
                    chart_top,
                    chart_right,
                    chart_bottom,
                    y_min=0.0,
                    y_max=y_max,
                )
                for row in rows
                if row.profile_key == profile_key and row.scheme_key == scheme_key
            ]
            parts.append(_polyline(curve, stroke=SCHEME_COLORS[scheme_key], width=3.0))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"
