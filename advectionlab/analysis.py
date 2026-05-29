from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Iterable

from .core import PROFILE_LIBRARY, SCHEME_TITLES, SimulationRun, simulate_transport, total_variation


@dataclass(frozen=True)
class TransportRow:
    scheme_key: str
    scheme_title: str
    profile_key: str
    profile_title: str
    requested_cfl: float
    actual_cfl: float
    steps: int
    l1_error: float
    l2_error: float
    max_abs_error: float
    total_variation_ratio: float
    overshoot: float
    undershoot: float

    def as_dict(self) -> dict[str, float | str]:
        return {
            "scheme_key": self.scheme_key,
            "scheme_title": self.scheme_title,
            "profile_key": self.profile_key,
            "profile_title": self.profile_title,
            "requested_cfl": self.requested_cfl,
            "actual_cfl": self.actual_cfl,
            "steps": self.steps,
            "l1_error": self.l1_error,
            "l2_error": self.l2_error,
            "max_abs_error": self.max_abs_error,
            "total_variation_ratio": self.total_variation_ratio,
            "overshoot": self.overshoot,
            "undershoot": self.undershoot,
        }


@dataclass(frozen=True)
class ModifiedEquationRow:
    scheme_key: str
    scheme_title: str
    requested_cfl: float
    actual_cfl: float
    diffusion_coeff: float | None
    dispersion_coeff: float | None
    gaussian_l2_error: float
    square_l2_error: float
    square_overshoot: float
    square_total_variation_ratio: float

    def as_dict(self) -> dict[str, float | str | None]:
        return {
            "scheme_key": self.scheme_key,
            "scheme_title": self.scheme_title,
            "requested_cfl": self.requested_cfl,
            "actual_cfl": self.actual_cfl,
            "diffusion_coeff": self.diffusion_coeff,
            "dispersion_coeff": self.dispersion_coeff,
            "gaussian_l2_error": self.gaussian_l2_error,
            "square_l2_error": self.square_l2_error,
            "square_overshoot": self.square_overshoot,
            "square_total_variation_ratio": self.square_total_variation_ratio,
        }


def amplification_factor(scheme_key: str, theta: float, cfl: float) -> complex:
    phase = cmath.exp(-1j * theta)
    if scheme_key == "upwind":
        return 1.0 - cfl * (1.0 - phase)
    if scheme_key == "lax-friedrichs":
        return math.cos(theta) - 1j * cfl * math.sin(theta)
    if scheme_key == "lax-wendroff":
        return 1.0 - 1j * cfl * math.sin(theta) + cfl * cfl * (math.cos(theta) - 1.0)
    raise ValueError(f"unknown scheme: {scheme_key}")


def amplitude_curve(scheme_key: str, cfl: float, *, steps: int = 256) -> tuple[tuple[float, float], ...]:
    points = []
    for index in range(steps + 1):
        theta = math.pi * index / steps
        points.append((theta / math.pi, abs(amplification_factor(scheme_key, theta, cfl))))
    return tuple(points)


def phase_speed_ratio_curve(scheme_key: str, cfl: float, *, steps: int = 256) -> tuple[tuple[float, float], ...]:
    points = []
    for index in range(1, steps + 1):
        theta = math.pi * index / steps
        factor = amplification_factor(scheme_key, theta, cfl)
        phase = cmath.phase(factor)
        ratio = 1.0 if abs(theta) < 1e-12 else -phase / (cfl * theta)
        points.append((theta / math.pi, ratio))
    points.insert(0, (0.0, 1.0))
    return tuple(points)


def transport_row(run: SimulationRun) -> TransportRow:
    diffs = [approx - exact for approx, exact in zip(run.numerical, run.exact)]
    l1_error = sum(abs(value) for value in diffs) / len(diffs)
    l2_error = math.sqrt(sum(value * value for value in diffs) / len(diffs))
    max_abs_error = max(abs(value) for value in diffs)
    exact_tv = total_variation(run.exact)
    total_variation_ratio = total_variation(run.numerical) / exact_tv if exact_tv > 0.0 else 1.0
    overshoot = max(0.0, max(run.numerical) - max(run.exact))
    undershoot = max(0.0, min(run.exact) - min(run.numerical))
    return TransportRow(
        scheme_key=run.scheme_key,
        scheme_title=SCHEME_TITLES[run.scheme_key],
        profile_key=run.profile_key,
        profile_title=PROFILE_LIBRARY[run.profile_key].title,
        requested_cfl=run.requested_cfl,
        actual_cfl=run.actual_cfl,
        steps=run.steps,
        l1_error=l1_error,
        l2_error=l2_error,
        max_abs_error=max_abs_error,
        total_variation_ratio=total_variation_ratio,
        overshoot=overshoot,
        undershoot=undershoot,
    )


def study_transport(
    *,
    schemes: Iterable[str] = ("upwind", "lax-friedrichs", "lax-wendroff"),
    profiles: Iterable[str] = ("gaussian", "square"),
    requested_cfls: Iterable[float] = (0.4, 0.7, 0.9),
    grid_size: int = 256,
    turns: float = 1.0,
) -> tuple[TransportRow, ...]:
    rows = []
    for profile_key in profiles:
        for requested_cfl in requested_cfls:
            for scheme_key in schemes:
                rows.append(
                    transport_row(
                        simulate_transport(
                            scheme_key,
                            profile_key,
                            grid_size=grid_size,
                            requested_cfl=requested_cfl,
                            turns=turns,
                        )
                    )
                )
    return tuple(rows)


def modified_equation_coefficients(scheme_key: str, cfl: float) -> tuple[float, float]:
    if scheme_key not in ("upwind", "lax-friedrichs", "lax-wendroff"):
        raise ValueError(f"modified-equation coefficients are only defined here for the linear schemes, not {scheme_key!r}")

    diffusion_estimates: list[float] = []
    dispersion_estimates: list[float] = []
    for theta in (8e-4, 4e-4, 2e-4, 1e-4):
        mismatch = cmath.log(amplification_factor(scheme_key, theta, cfl)) + 1j * cfl * theta
        diffusion_estimates.append(-mismatch.real / (theta * theta))
        dispersion_estimates.append(mismatch.imag / (theta * theta * theta))

    diffusion = sum(diffusion_estimates) / len(diffusion_estimates)
    dispersion = sum(dispersion_estimates) / len(dispersion_estimates)
    return diffusion, dispersion


def study_modified_equation_followup(
    *,
    schemes: Iterable[str] = ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod", "tvd-mc", "tvd-superbee"),
    requested_cfls: Iterable[float] = (0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 0.95),
    grid_size: int = 256,
    turns: float = 1.0,
) -> tuple[ModifiedEquationRow, ...]:
    transport_rows = study_transport(
        schemes=schemes,
        profiles=("gaussian", "square"),
        requested_cfls=requested_cfls,
        grid_size=grid_size,
        turns=turns,
    )
    rows_by_key = {
        (row.profile_key, row.scheme_key, row.requested_cfl): row
        for row in transport_rows
    }
    output: list[ModifiedEquationRow] = []
    for requested_cfl in requested_cfls:
        for scheme_key in schemes:
            gaussian_row = rows_by_key[("gaussian", scheme_key, requested_cfl)]
            square_row = rows_by_key[("square", scheme_key, requested_cfl)]
            if scheme_key in ("upwind", "lax-friedrichs", "lax-wendroff"):
                diffusion_coeff, dispersion_coeff = modified_equation_coefficients(scheme_key, requested_cfl)
            else:
                diffusion_coeff, dispersion_coeff = None, None
            output.append(
                ModifiedEquationRow(
                    scheme_key=scheme_key,
                    scheme_title=SCHEME_TITLES[scheme_key],
                    requested_cfl=requested_cfl,
                    actual_cfl=gaussian_row.actual_cfl,
                    diffusion_coeff=diffusion_coeff,
                    dispersion_coeff=dispersion_coeff,
                    gaussian_l2_error=gaussian_row.l2_error,
                    square_l2_error=square_row.l2_error,
                    square_overshoot=square_row.overshoot,
                    square_total_variation_ratio=square_row.total_variation_ratio,
                )
            )
    return tuple(output)
