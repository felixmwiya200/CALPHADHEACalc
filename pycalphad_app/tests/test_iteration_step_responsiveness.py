# -*- coding: utf-8 -*-
"""
test_iteration_step_responsiveness.py - Unit test suite for JMatPro temperature stepping
and iteration responsiveness.
Ensures user-configured Step ΔT (e.g. 0.5 K, 0.1 K, 10.0 K) and temperature windows
are strictly honored in SolverWorker and IterativeSolver.
"""

import unittest
from unittest.mock import MagicMock
from pycalphad_app.gui.worker import SolverWorker
from pycalphad_app.core.iterative_solver import IterativeSolver


class TestIterationStepResponsiveness(unittest.TestCase):
    def test_worker_stepping_custom_delta(self):
        """Worker must respect custom small t_step (0.5 K) across a specified range."""
        comp = {"Ni": 0.70, "Cr": 0.20, "Al": 0.10}
        t_start = 1253.50
        t_stop = 1251.00
        t_step = 0.50

        worker = SolverWorker(
            database_name="Nickel Based Superalloy",
            composition=comp,
            basis="wt%",
            t_start=t_start,
            t_stop=t_stop,
            t_step=t_step
        )

        recorded_temps = []
        logged_lines = []
        worker.step_progress.connect(lambda d: recorded_temps.append(d["temperature"]))
        worker.step_log.connect(lambda s: logged_lines.append(s))

        worker.run()

        # Expected steps: 1253.50, 1253.00, 1252.50, 1252.00, 1251.50, 1251.00 (6 steps)
        self.assertEqual(len(recorded_temps), 6)
        self.assertAlmostEqual(recorded_temps[0], 1253.50, places=2)
        self.assertAlmostEqual(recorded_temps[1], 1253.00, places=2)
        self.assertAlmostEqual(recorded_temps[2], 1252.50, places=2)
        self.assertAlmostEqual(recorded_temps[-1], 1251.00, places=2)

        # Check exact string format matching JMatPro console screenshot: T(K) = 1253.50
        self.assertEqual(logged_lines[0], "T(K) = 1253.50")
        self.assertEqual(logged_lines[1], "T(K) = 1253.00")
        self.assertEqual(logged_lines[-1], "T(K) = 1251.00")

    def test_worker_interrupt_with_s_key(self):
        """Worker should halt gracefully when request_interrupt() is triggered."""
        comp = {"Fe": 0.98, "C": 0.02}
        worker = SolverWorker(
            database_name="General Steel",
            composition=comp,
            basis="wt%",
            t_start=1500.0,
            t_stop=300.0,
            t_step=1.0
        )

        steps = []
        def on_step(d):
            steps.append(d["temperature"])
            if len(steps) >= 5:
                worker.request_interrupt()

        worker.step_progress.connect(on_step)
        worker.run()

        self.assertLess(len(steps), 50)
        self.assertTrue(worker._is_interrupted)

    def test_iterative_solver_sub_one_degree_stepping(self):
        """IterativeSolver must step forward by exact sub-degree increments."""
        comp = {"Ni": 50.0, "Fe": 50.0}
        solver = IterativeSolver(
            database_name="NiFe Based Superalloy",
            composition=comp,
            basis="wt%",
            t_start=1200.0,
            t_stop=1202.0,
            t_step=0.25
        )

        res1 = solver.step_forward()
        self.assertAlmostEqual(res1["temperature"], 1200.0, places=2)
        self.assertFalse(res1["is_completed"])

        res2 = solver.step_forward()
        self.assertAlmostEqual(res2["temperature"], 1200.25, places=2)

        res3 = solver.step_forward()
        self.assertAlmostEqual(res3["temperature"], 1200.50, places=2)

    def test_stepping_minimum_five_decimals_0_00001(self):
        """Worker and solver must support minimum stepping delta of 0.00001 K."""
        comp = {"Ni": 0.70, "Cr": 0.20, "Al": 0.10}
        t_start = 1250.00005
        t_stop = 1250.00000
        t_step = 0.00001

        worker = SolverWorker(
            database_name="Nickel Based Superalloy",
            composition=comp,
            basis="wt%",
            t_start=t_start,
            t_stop=t_stop,
            t_step=t_step
        )

        recorded_temps = []
        logged_lines = []
        worker.step_progress.connect(lambda d: recorded_temps.append(d["temperature"]))
        worker.step_log.connect(lambda s: logged_lines.append(s))

        worker.run()

        # Expected 6 steps: 1250.00005 down to 1250.00000 by 0.00001
        self.assertEqual(len(recorded_temps), 6)
        self.assertAlmostEqual(recorded_temps[0], 1250.00005, places=5)
        self.assertAlmostEqual(recorded_temps[-1], 1250.00000, places=5)
        self.assertEqual(logged_lines[0], "T(K) = 1250.00005")
        self.assertEqual(logged_lines[-1], "T(K) = 1250.00000")

        # Also test IterativeSolver with 0.00001 K step
        solver = IterativeSolver(
            database_name="Nickel Based Superalloy",
            composition=comp,
            t_start=1250.00000,
            t_stop=1250.00003,
            t_step=0.00001
        )
        s1 = solver.step_forward()
        self.assertAlmostEqual(s1["temperature"], 1250.00000, places=5)
        s2 = solver.step_forward()
        self.assertAlmostEqual(s2["temperature"], 1250.00001, places=5)
        s3 = solver.step_forward()
        self.assertAlmostEqual(s3["temperature"], 1250.00002, places=5)
        s4 = solver.step_forward()
        self.assertAlmostEqual(s4["temperature"], 1250.00003, places=5)
        self.assertTrue(s4["is_completed"])


if __name__ == "__main__":
    unittest.main()
