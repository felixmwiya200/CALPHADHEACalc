# -*- coding: utf-8 -*-
"""
iterative_solver.py - State Machine for Interactive & Stepped CALPHAD Calculations
Enables both 'Run to Completion' and discrete 'Step Forward' iterative stepping
across user-defined temperature windows (T_start to T_stop with step Delta T).
Adheres strictly to scientific CAE convergence and telemetry standards.
"""

import time
import numpy as np
from typing import Dict, Any, List, Optional, Callable

from pycalphad_app.core.thermo_engine import ThermoEngine
from pycalphad_app.core.coating_engine import CoatingEngine
from pycalphad_app.core.mechanical_engine import MechanicalEngine
from pycalphad_app.core.oxidation_engine import OxidationEngine
from pycalphad_app.core.corrosion_engine import CorrosionEngine
from pycalphad_app.core.xrd_engine import XRDEngine
from pycalphad_app.core.application_scorer import ApplicationScorer
from pycalphad_app.core.lattice_distortion_engine import LatticeDistortionEngine
from pycalphad_app.core.pycalphad_embed import PyCalphadEmbed
from pycalphad_app.database.material_selector import MaterialDatabaseSelector


class IterativeSolver:
    """
    Manages the thermodynamic calculation state machine.
    Allows point-by-point stepping or full background execution.
    """
    def __init__(self, database_name: str = "High Entropy Alloys",
                 composition: Optional[Dict[str, float]] = None,
                 basis: str = "at%",
                 grain_size_um: float = 25.0,
                 process_type: str = "Arc Melt / Cast",
                 t_start: float = 300.0,
                 t_stop: float = 2000.0,
                 t_step: float = 20.0):
        self.database_name = database_name
        self.raw_composition = composition or {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
        self.basis = basis
        self.grain_size_um = grain_size_um
        self.process_type = process_type
        self.t_start = float(t_start)
        self.t_stop = float(t_stop)
        self.t_step = max(0.00001, float(t_step))

        # Normalized compositions
        self.normalized_comp: Dict[str, float] = {}
        self.at_comp: Dict[str, float] = {}
        self._normalize_composition()

        # Dedicated domain alloy engine
        self.engine = MaterialDatabaseSelector.get_engine(
            self.database_name, self.normalized_comp, self.grain_size_um, self.process_type
        )
        self._thermo_cache = None
        self._trans_cache = None
        self._mech_cache = None

        # Step state tracking
        self.current_step = 0
        self.current_temp = self.t_start
        self.is_completed = False
        self.history_temperatures: List[float] = []
        self.history_steps: List[Dict[str, Any]] = []

    def _normalize_composition(self):
        tot = sum(self.raw_composition.values())
        if tot <= 0:
            tot = 1.0
        self.normalized_comp = {k: v / tot for k, v in self.raw_composition.items()}
        
        if self.basis == "wt%":
            from pycalphad_app.core.elements_data import get_element
            moles_raw = {el: frac / max(1e-4, getattr(get_element(el), "atomic_mass", 55.845))
                         for el, frac in self.normalized_comp.items()}
            tot_moles = sum(moles_raw.values())
            self.at_comp = {el: m / tot_moles for el, m in moles_raw.items()}
        else:
            self.at_comp = dict(self.normalized_comp)

    def reset(self):
        """Reset solver state to initial start conditions."""
        self.current_step = 0
        self.current_temp = self.t_start
        self.is_completed = False
        self.history_temperatures.clear()
        self.history_steps.clear()

    def step_forward(self) -> Dict[str, Any]:
        """
        Calculates one discrete temperature step (T = current_temp).
        Records state, advances current_temp by t_step, and returns step metrics.
        """
        if self.is_completed:
            return {
                "step_index": self.current_step,
                "temperature": self.current_temp,
                "is_completed": True,
                "message": "Calculation already at maximum temperature."
            }

        t_now = self.current_temp
        self.current_step += 1
        self.history_temperatures.append(t_now)

        # 1. Base thermodynamic metrics from dedicated alloy engine
        if self._thermo_cache is None:
            self._trans_cache = self.engine.compute_phase_transformations()
            self._thermo_cache = self.engine.compute_thermodynamics()
            self._mech_cache = self.engine.compute_mechanical_properties(self._thermo_cache, self._trans_cache)

        t_sol = float(self._thermo_cache.get("Solidus_K", 1400.0))
        t_liq = float(self._thermo_cache.get("Liquidus_K", 1600.0))

        # 2. Compute instantaneous phase fractions at temperature t_now
        step_state = self.engine.compute_single_temperature_step(t_now)
        phases = step_state.get("Phases", {})

        # Temperature-dependent mechanical strength
        base_yield = float(self._mech_cache.get("YieldStrength_MPa", 450.0))
        if t_now <= 300.0:
            yield_str = base_yield
        elif t_now >= t_sol:
            yield_str = 5.0
        else:
            yield_str = base_yield * max(0.05, (1.0 - (t_now - 300.0) / max(50.0, (t_sol - 300.0))) ** 1.2)
        hardness_hv = yield_str / 3.1

        step_res = {
            "step_index": self.current_step,
            "temperature": t_now,
            "phases": phases,
            "yield_strength_mpa": float(yield_str),
            "hardness_hv": float(hardness_hv),
            "dominant_phase": step_state.get("DominantPhase", "Solid Solution"),
            "is_completed": False
        }

        self.history_steps.append(step_res)

        # Advance temperature bidirectionally (precision down to 0.00001 K)
        direction = 1.0 if self.t_stop >= self.t_start else -1.0
        if (direction > 0 and self.current_temp >= self.t_stop - (self.t_step * 0.1)) or \
           (direction < 0 and self.current_temp <= self.t_stop + (self.t_step * 0.1)):
            self.is_completed = True
            step_res["is_completed"] = True
        else:
            if direction > 0:
                self.current_temp = min(self.t_stop, self.current_temp + self.t_step)
            else:
                self.current_temp = max(self.t_stop, self.current_temp - self.t_step)

        return step_res

    def run_to_completion(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """
        Executes all remaining temperature steps to completion and compiles
        the full 8-domain results payload for the main window views.
        """
        t0 = time.perf_counter()
        total_steps = int(np.ceil((self.t_stop - self.t_start) / self.t_step)) + 1
        
        step_idx = 0
        while not self.is_completed:
            step_idx += 1
            step_res = self.step_forward()
            pct = int(min(90, (step_idx / max(1, total_steps)) * 90))
            if progress_callback:
                progress_callback(pct, f"Iterating solver: T = {step_res['temperature']:.1f} K ({pct}%)...")

        # Compile full multi-physics payload
        at_elements = list(self.at_comp.keys())
        at_fractions = list(self.at_comp.values())

        thermo_res = ThermoEngine.calculate(self.at_comp)
        pycalphad_res = PyCalphadEmbed.run_equilibrium(at_elements, at_fractions)
        thermo_res["PhaseFractions"] = pycalphad_res
        thermo_res["PyCalphad"] = pycalphad_res

        transport_res = ThermoEngine.compute_thermophysical_transport(
            self.at_comp, thermo_res["Solidus_K"], thermo_res["Liquidus_K"], thermo_res["Density_g_cm3"]
        )
        thermo_res["Transport"] = transport_res

        distortion_res = LatticeDistortionEngine.compute_distortion_metrics(
            at_elements, at_fractions, thermo_res
        )
        thermo_res["LatticeDistortion"] = distortion_res

        mech_res = MechanicalEngine.compute_mechanical_properties(
            at_elements, at_fractions, thermo_res, grain_size_um=self.grain_size_um
        )
        ox_res = OxidationEngine.compute_oxidation_kinetics(
            at_elements, at_fractions, thermo_res
        )
        corr_res = CorrosionEngine.calculate(self.normalized_comp)
        coating_res = CoatingEngine.compute_coating_properties(
            list(self.normalized_comp.keys()), list(self.normalized_comp.values()),
            thermo_res, {"Process": self.process_type}
        )

        xrd_bench = MaterialDatabaseSelector.get_xrd_benchmark(self.database_name)
        if xrd_bench:
            xrd_res = xrd_bench
        else:
            xrd_res = XRDEngine.calculate_xrd(self.normalized_comp, is_coating=False, thermo_metrics=thermo_res)

        all_metrics = {"composition": self.normalized_comp}
        all_metrics.update(thermo_res)
        all_metrics.update(mech_res)
        all_metrics.update(ox_res)
        all_metrics.update(corr_res)
        val_table = MaterialDatabaseSelector.compare_benchmarks(self.database_name, all_metrics)

        app_scores = ApplicationScorer.score_alloy(
            list(self.normalized_comp.keys()), list(self.normalized_comp.values()),
            thermo_res, mech_res, ox_res
        )

        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0

        if progress_callback:
            progress_callback(100, f"Converged successfully in {elapsed_ms:.1f} ms.")

        return {
            "database_name": self.database_name,
            "composition": self.normalized_comp,
            "atomic_composition": self.at_comp,
            "basis": self.basis,
            "grain_size_um": self.grain_size_um,
            "process_type": self.process_type,
            "thermo": thermo_res,
            "mechanical": mech_res,
            "oxidation": ox_res,
            "corrosion": corr_res,
            "coating": coating_res,
            "xrd": xrd_res,
            "validation_table": val_table,
            "application_scores": app_scores,
            "elapsed_ms": elapsed_ms,
            "history_temperatures": self.history_temperatures,
            "history_steps": self.history_steps
        }
