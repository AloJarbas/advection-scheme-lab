from __future__ import annotations

import math
import unittest

from advectionlab.analysis import amplitude_curve, study_transport
from advectionlab.core import SCHEME_STEPS, simulate_transport


class AdvectionTests(unittest.TestCase):
    def test_constant_state_is_preserved(self) -> None:
        samples = [1.25] * 32
        for scheme_key, stepper in SCHEME_STEPS.items():
            updated = stepper(samples, 0.9)
            self.assertTrue(all(abs(value - 1.25) < 1e-12 for value in updated), scheme_key)

    def test_von_neumann_curves_stay_bounded_for_stable_cfl(self) -> None:
        for scheme_key in ("upwind", "lax-friedrichs", "lax-wendroff"):
            for _, amplitude in amplitude_curve(scheme_key, 0.9, steps=96):
                self.assertLessEqual(amplitude, 1.0000001, scheme_key)

    def test_lax_wendroff_wins_gaussian_l2_lane(self) -> None:
        rows = [row for row in study_transport(requested_cfls=(0.9,)) if row.profile_key == "gaussian"]
        ranking = sorted(rows, key=lambda row: row.l2_error)
        self.assertEqual(ranking[0].scheme_key, "lax-wendroff")
        self.assertLess(ranking[0].l2_error, ranking[-1].l2_error)

    def test_lax_wendroff_rings_on_square_pulse(self) -> None:
        rows = {row.scheme_key: row for row in study_transport(requested_cfls=(0.9,)) if row.profile_key == "square"}
        self.assertGreater(rows["lax-wendroff"].overshoot, 0.01)
        self.assertGreater(rows["lax-wendroff"].undershoot, 0.01)
        self.assertLess(rows["upwind"].overshoot, 1e-9)
        self.assertLess(rows["lax-friedrichs"].overshoot, 1e-9)

    def test_tvd_minmod_opens_a_middle_lane(self) -> None:
        rows = {
            (row.profile_key, row.scheme_key): row
            for row in study_transport(
                schemes=("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod"),
                requested_cfls=(0.9,),
            )
        }
        gaussian_minmod = rows[("gaussian", "tvd-minmod")]
        gaussian_upwind = rows[("gaussian", "upwind")]
        gaussian_lw = rows[("gaussian", "lax-wendroff")]
        square_minmod = rows[("square", "tvd-minmod")]
        square_lw = rows[("square", "lax-wendroff")]
        self.assertLess(gaussian_minmod.l2_error, gaussian_upwind.l2_error)
        self.assertGreater(gaussian_minmod.l2_error, gaussian_lw.l2_error)
        self.assertLess(square_minmod.overshoot, 1e-9)
        self.assertLess(square_minmod.undershoot, 1e-9)
        self.assertLess(square_minmod.l2_error, square_lw.l2_error)
        self.assertLess(square_minmod.total_variation_ratio, 1.000001)

    def test_one_turn_keeps_exact_gaussian_shape(self) -> None:
        run = simulate_transport("upwind", "gaussian", requested_cfl=0.9)
        self.assertAlmostEqual(run.initial[0], run.exact[0], places=12)
        self.assertAlmostEqual(run.initial[17], run.exact[17], places=12)


if __name__ == "__main__":
    unittest.main()
