from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class ProfileSpec:
    key: str
    title: str
    sampler: Callable[[float], float]


@dataclass(frozen=True)
class SimulationRun:
    scheme_key: str
    profile_key: str
    grid_size: int
    requested_cfl: float
    actual_cfl: float
    steps: int
    x_values: tuple[float, ...]
    initial: tuple[float, ...]
    exact: tuple[float, ...]
    numerical: tuple[float, ...]


def periodic_distance(x: float, center: float) -> float:
    delta = abs(x - center)
    return min(delta, 1.0 - delta)


GAUSSIAN_PROFILE = ProfileSpec(
    key="gaussian",
    title="Gaussian pulse",
    sampler=lambda x: math.exp(-0.5 * (periodic_distance(x, 0.3) / 0.06) ** 2),
)

SQUARE_PROFILE = ProfileSpec(
    key="square",
    title="Square pulse",
    sampler=lambda x: 1.0 if periodic_distance(x, 0.3) <= 0.09 else 0.0,
)

PROFILE_LIBRARY = {
    GAUSSIAN_PROFILE.key: GAUSSIAN_PROFILE,
    SQUARE_PROFILE.key: SQUARE_PROFILE,
}

SCHEME_TITLES = {
    "upwind": "Upwind",
    "lax-friedrichs": "Lax-Friedrichs",
    "lax-wendroff": "Lax-Wendroff",
}


def grid_points(grid_size: int) -> tuple[float, ...]:
    if grid_size < 8:
        raise ValueError("grid_size must be at least 8")
    return tuple(index / grid_size for index in range(grid_size))


def sample_profile(profile_key: str, grid_size: int, *, shift: float = 0.0) -> tuple[float, ...]:
    try:
        profile = PROFILE_LIBRARY[profile_key]
    except KeyError as exc:
        raise ValueError(f"unknown profile: {profile_key}") from exc
    return tuple(profile.sampler((x - shift) % 1.0) for x in grid_points(grid_size))


def total_variation(samples: tuple[float, ...] | list[float]) -> float:
    values = list(samples)
    return sum(abs(right - left) for left, right in zip(values, values[1:] + values[:1]))


def _periodic(samples: list[float], index: int) -> float:
    return samples[index % len(samples)]


def step_upwind(samples: list[float], cfl: float) -> list[float]:
    return [value - cfl * (value - _periodic(samples, index - 1)) for index, value in enumerate(samples)]


def step_lax_friedrichs(samples: list[float], cfl: float) -> list[float]:
    next_samples: list[float] = []
    for index, _ in enumerate(samples):
        right = _periodic(samples, index + 1)
        left = _periodic(samples, index - 1)
        next_samples.append(0.5 * (right + left) - 0.5 * cfl * (right - left))
    return next_samples


def step_lax_wendroff(samples: list[float], cfl: float) -> list[float]:
    next_samples: list[float] = []
    for index, value in enumerate(samples):
        right = _periodic(samples, index + 1)
        left = _periodic(samples, index - 1)
        next_samples.append(
            value
            - 0.5 * cfl * (right - left)
            + 0.5 * cfl * cfl * (right - 2.0 * value + left)
        )
    return next_samples


SCHEME_STEPS = {
    "upwind": step_upwind,
    "lax-friedrichs": step_lax_friedrichs,
    "lax-wendroff": step_lax_wendroff,
}


def choose_step_count(grid_size: int, requested_cfl: float, *, turns: float = 1.0) -> tuple[int, float]:
    if requested_cfl <= 0.0:
        raise ValueError("requested_cfl must be positive")
    steps = max(1, round(turns * grid_size / requested_cfl))
    actual_cfl = turns * grid_size / steps
    return steps, actual_cfl


def evolve(samples: tuple[float, ...], scheme_key: str, cfl: float, steps: int) -> tuple[float, ...]:
    try:
        stepper = SCHEME_STEPS[scheme_key]
    except KeyError as exc:
        raise ValueError(f"unknown scheme: {scheme_key}") from exc
    current = list(samples)
    for _ in range(steps):
        current = stepper(current, cfl)
    return tuple(current)


def simulate_transport(
    scheme_key: str,
    profile_key: str,
    *,
    grid_size: int = 256,
    requested_cfl: float = 0.9,
    turns: float = 1.0,
) -> SimulationRun:
    x_values = grid_points(grid_size)
    initial = sample_profile(profile_key, grid_size, shift=0.0)
    steps, actual_cfl = choose_step_count(grid_size, requested_cfl, turns=turns)
    numerical = evolve(initial, scheme_key, actual_cfl, steps)
    exact = sample_profile(profile_key, grid_size, shift=turns)
    return SimulationRun(
        scheme_key=scheme_key,
        profile_key=profile_key,
        grid_size=grid_size,
        requested_cfl=requested_cfl,
        actual_cfl=actual_cfl,
        steps=steps,
        x_values=x_values,
        initial=initial,
        exact=exact,
        numerical=numerical,
    )
