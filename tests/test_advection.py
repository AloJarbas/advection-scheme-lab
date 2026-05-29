from __future__ import annotations

import math
import unittest

from advectionlab.analysis import amplitude_curve, modified_equation_coefficients, study_modified_equation_followup, study_transport
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

    def test_tvd_limiter_family_splits_smooth_and_jump_lanes(self) -> None:
        rows = {
            (row.profile_key, row.scheme_key): row
            for row in study_transport(
                schemes=("lax-wendroff", "tvd-minmod", "tvd-mc", "tvd-superbee"),
                requested_cfls=(0.95,),
            )
        }
        gaussian_lw = rows[("gaussian", "lax-wendroff")]
        gaussian_minmod = rows[("gaussian", "tvd-minmod")]
        gaussian_mc = rows[("gaussian", "tvd-mc")]
        gaussian_superbee = rows[("gaussian", "tvd-superbee")]
        square_minmod = rows[("square", "tvd-minmod")]
        square_mc = rows[("square", "tvd-mc")]
        square_superbee = rows[("square", "tvd-superbee")]

        self.assertLess(gaussian_mc.l2_error, gaussian_lw.l2_error)
        self.assertLess(gaussian_lw.l2_error, gaussian_superbee.l2_error)
        self.assertLess(gaussian_superbee.l2_error, gaussian_minmod.l2_error)

        self.assertLess(square_superbee.l2_error, square_mc.l2_error)
        self.assertLess(square_mc.l2_error, square_minmod.l2_error)
        for row in (square_minmod, square_mc, square_superbee):
            self.assertLess(row.overshoot, 1e-9)
            self.assertLess(row.undershoot, 1e-9)
            self.assertLess(abs(row.total_variation_ratio - 1.0), 1e-6)

    def test_one_turn_keeps_exact_gaussian_shape(self) -> None:
        run = simulate_transport("upwind", "gaussian", requested_cfl=0.9)
        self.assertAlmostEqual(run.initial[0], run.exact[0], places=12)
        self.assertAlmostEqual(run.initial[17], run.exact[17], places=12)

    def test_unit_cfl_is_exact_grid_shift_for_every_scheme_here(self) -> None:
        for scheme_key in ("upwind", "lax-friedrichs", "lax-wendroff", "tvd-minmod"):
            for profile_key in ("gaussian", "square"):
                run = simulate_transport(scheme_key, profile_key, requested_cfl=1.0)
                max_error = max(abs(approx - exact) for approx, exact in zip(run.numerical, run.exact))
                self.assertLess(max_error, 1e-12, (scheme_key, profile_key))

    def test_lax_wendroff_square_ripple_shrinks_toward_unit_cfl(self) -> None:
        low = simulate_transport("lax-wendroff", "square", requested_cfl=0.4)
        high = simulate_transport("lax-wendroff", "square", requested_cfl=0.95)
        low_overshoot = max(0.0, max(low.numerical) - max(low.exact))
        high_overshoot = max(0.0, max(high.numerical) - max(high.exact))
        self.assertGreater(low_overshoot, high_overshoot)
        self.assertGreater(high_overshoot, 0.0)

    def test_modified_equation_coefficients_split_diffusion_and_dispersion(self) -> None:
        upwind_diffusion, upwind_dispersion = modified_equation_coefficients("upwind", 0.95)
        lf_diffusion, lf_dispersion = modified_equation_coefficients("lax-friedrichs", 0.95)
        lw_diffusion, lw_dispersion = modified_equation_coefficients("lax-wendroff", 0.95)

        self.assertGreater(lf_diffusion, upwind_diffusion)
        self.assertGreater(upwind_diffusion, 0.0)
        self.assertLess(abs(lw_diffusion), 1e-5)
        self.assertGreater(lw_dispersion, 0.0)
        self.assertLess(lf_dispersion, 0.0)

    def test_modified_equation_followup_shows_limiter_escape_hatch(self) -> None:
        rows = {
            (row.scheme_key, row.requested_cfl): row
            for row in study_modified_equation_followup(requested_cfls=(0.95,))
        }
        lw = rows[("lax-wendroff", 0.95)]
        mc = rows[("tvd-mc", 0.95)]
        superbee = rows[("tvd-superbee", 0.95)]

        self.assertGreater(lw.square_overshoot, 0.1)
        self.assertLess(mc.square_overshoot, 1e-9)
        self.assertLess(mc.gaussian_l2_error, lw.gaussian_l2_error)
        self.assertLess(superbee.square_l2_error, mc.square_l2_error)


if __name__ == "__main__":
    unittest.main()
