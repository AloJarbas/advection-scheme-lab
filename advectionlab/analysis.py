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
