# -*- coding: utf-8 -*-
"""
base_alloy_engine.py - Abstract Base Foundation for Alloy Family Engines
Defines the polymorphic contract, composition normalization, mass-to-atomic conversion,
process cooling rates, and standard lifecycle hooks for materials simulation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from pycalphad_app.core.elements_data import ELEMENTS_REGISTRY


class BaseAlloyEngine(ABC):
    """
    Abstract base class establishing the standard lifecycle and data contract
    for all specialized alloy-family calculation engines.
    """

    # ASTM E140 reference conversion tables (Vickers HV -> Rockwell HRC / HRB)
    _ASTM_E140_HV_TO_HRC_X = (228.0, 240.0, 260.0, 280.0, 300.0, 340.0, 380.0, 420.0, 460.0, 500.0, 550.0, 600.0, 650.0, 700.0, 800.0, 900.0, 940.0)
    _ASTM_E140_HV_TO_HRC_Y = (18.0, 20.3, 24.0, 27.1, 29.8, 34.4, 38.8, 42.7, 46.1, 49.1, 52.3, 55.2, 57.8, 60.1, 64.0, 67.0, 68.0)

    _ASTM_E140_HV_TO_HRB_X = (60.0, 80.0, 95.0, 110.0, 125.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 250.0)
    _ASTM_E140_HV_TO_HRB_Y = (15.0, 36.0, 52.0, 62.3, 70.0, 75.8, 82.0, 87.3, 91.5, 95.0, 98.1, 99.5)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        orig_mech = cls.__dict__.get("compute_mechanical_properties")
        if orig_mech is not None:
            def _wrapped_mech(self, thermo_state, transform_state, _orig=orig_mech):
                res = _orig(self, thermo_state, transform_state)
                return BaseAlloyEngine.enrich_hardness_metrics(res)
            cls.compute_mechanical_properties = _wrapped_mech  # type: ignore[method-assign]

        orig_step = cls.__dict__.get("compute_single_temperature_step")
        if orig_step is not None:
            def _wrapped_step(self, temperature_k, _orig=orig_step):
                res = _orig(self, temperature_k)
                return BaseAlloyEngine.enrich_single_step_hardness(res)
            cls.compute_single_temperature_step = _wrapped_step  # type: ignore[method-assign]

    @classmethod
    def hv_to_rockwell(cls, hv: float) -> Dict[str, Any]:
        """
        Converts Vickers Hardness (HV) to both Rockwell C (HRC) and Rockwell B (HRB)
        following ASTM E140 tabulated hardness conversions.
        """
        hv_val = max(20.0, float(hv))
        # Continuous HRC correlation: exact ASTM E140 >= 228 HV, extended smooth estimate below 228 HV
        if hv_val >= 228.0:
            if hv_val <= 940.0:
                hrc = float(np.interp(hv_val, cls._ASTM_E140_HV_TO_HRC_X, cls._ASTM_E140_HV_TO_HRC_Y))
            else:
                hrc = min(72.0, 68.0 + 4.0 * np.log10(hv_val / 940.0) / np.log10(1300.0 / 940.0))
        else:
            # Smooth sub-20 HRC equivalent for tabular/plotting consistency
            hrc = max(0.0, 18.0 - 0.14 * (228.0 - hv_val))

        # Rockwell B scale (valid 60-250 HV; saturates at 100 HRB for harder steels)
        if hv_val <= 250.0:
            hrb = float(np.interp(hv_val, cls._ASTM_E140_HV_TO_HRB_X, cls._ASTM_E140_HV_TO_HRB_Y))
        else:
            hrb = 100.0

        primary_scale = "HRC" if hv_val >= 240.0 else "HRB"
        primary_val = hrc if primary_scale == "HRC" else hrb
        formatted = f"{primary_val:.1f} {primary_scale}"

        return {
            "RockwellHardness_HRC": round(hrc, 1),
            "RockwellHardness_HRB": round(hrb, 1),
            "Hardness_HRC": round(hrc, 1),
            "Hardness_HRB": round(hrb, 1),
            "RockwellScale": primary_scale,
            "RockwellHardness": formatted,
        }

    @classmethod
    def enrich_hardness_metrics(cls, mech: Dict[str, Any]) -> Dict[str, Any]:
        """Injects both Vickers (HV) and Rockwell (HRC / HRB) hardness into mechanical output dictionaries."""
        if not isinstance(mech, dict):
            return mech
        hv = mech.get("VickersHardness_HV", mech.get("Hardness_HV"))
        if hv is not None:
            rk = cls.hv_to_rockwell(float(hv))
            mech.setdefault("VickersHardness_HV", round(float(hv), 1))
            mech.setdefault("Hardness_HV", round(float(hv), 1))
            for k, v in rk.items():
                mech[k] = v
        return mech

    @classmethod
    def enrich_single_step_hardness(cls, step: Dict[str, Any]) -> Dict[str, Any]:
        """Injects Rockwell HRC/HRB hardness alongside HV into single-step snapshots."""
        if not isinstance(step, dict):
            return step
        hv = step.get("Hardness_HV", step.get("hardness_hv", step.get("VickersHardness_HV")))
        if hv is not None:
            rk = cls.hv_to_rockwell(float(hv))
            step["Hardness_HRC"] = rk["RockwellHardness_HRC"]
            step["Hardness_HRB"] = rk["RockwellHardness_HRB"]
            step["RockwellHardness"] = rk["RockwellHardness"]
        return step

    # Deterministic Process-to-Cooling-Rate mapping (K/s)
    COOLING_RATES: Dict[str, float] = {
        "Arc Melt / Cast": 1.5,
        "Casting": 1.5,
        "Wrought / Annealed": 0.5,
        "Wrought": 0.5,
        "Forging": 2.0,
        "Heat Treated / Quenched": 80.0,
        "Water Quench": 150.0,
        "HVOF": 1e6,
        "Plasma Spray": 1e6,
        "Laser Clad / DED": 1e3,
        "Fast Cool / Quench": 50.0,
    }

    def __init__(self, database_name: str, composition_wt: Dict[str, float],
                 grain_size_um: float = 25.0, process_type: str = "Wrought"):
        self.database_name = database_name
        self.grain_size_um = max(0.1, float(grain_size_um))
        self.process_type = process_type
        self.comp_wt = self._normalize(composition_wt)
        self.comp_at = self._convert_to_atomic(self.comp_wt)
        self.base_element = self._resolve_base_element()
        self.cooling_rate_k_s = self.COOLING_RATES.get(process_type, 2.5)
        self.dft_input: Optional[Dict[str, Any]] = None

    def set_dft_input(self, dft_data: Optional[Dict[str, Any]]) -> None:
        """Sets first-principles DFT input data to anchor CALPHAD Gibbs energy calculations."""
        self.dft_input = dft_data

    def _normalize(self, comp: Dict[str, float]) -> Dict[str, float]:
        """Normalizes weight composition such that sum(w_i) == 1.0."""
        total = sum(comp.values())
        if total <= 0:
            raise ValueError("Total alloy composition weight fraction must be strictly positive.")
        normalized = {}
        for el, w in comp.items():
            clean_el = el.strip().capitalize()
            # Epsilon clamping for dilute components
            normalized[clean_el] = max(1e-12, float(w) / total)
        # Rescale after clamping
        subtotal = sum(normalized.values())
        return {el: w / subtotal for el, w in normalized.items()}

    def _convert_to_atomic(self, comp_wt: Dict[str, float]) -> Dict[str, float]:
        """Converts normalized weight fractions to atomic mole fractions."""
        moles: Dict[str, float] = {}
        for el, w in comp_wt.items():
            edata = ELEMENTS_REGISTRY.get(el)
            atomic_mass = edata.atomic_mass if edata else 55.845
            moles[el] = max(1e-12, w / atomic_mass)
        total_moles = sum(moles.values())
        return {el: m / total_moles for el, m in moles.items()}

    def _resolve_base_element(self) -> str:
        """Determines the dominant solvent base element."""
        if not self.comp_wt:
            return "Fe"
        return max(self.comp_wt.items(), key=lambda kv: kv[1])[0]

    # -----------------------------------------------------------------------
    # Integrated Thermodynamic Foundation (Derived into All Alloy Engines)
    # -----------------------------------------------------------------------
    def compute_thermodynamic_fundamentals(self, temperature_k: float = 293.15) -> Dict[str, Any]:
        """
        Integrates multi-component CALPHAD thermodynamic calculations directly into the alloy engine:
        - Molar mass and room-temperature/target-temperature density
        - Valence Electron Concentration (VEC)
        - Atomic size mismatch (delta) and electronegativity difference (delta_chi)
        - Enthalpy of mixing (Delta H_mix) via Miedema model
        - Configurational entropy of mixing (Delta S_mix)
        - Gibbs free energy of mixing (Delta G_mix = Delta H_mix - T * Delta S_mix)
        - Thermodynamic stability parameter (Omega = T_m * Delta S_mix / |Delta H_mix|)
        - Molar volume, average melting point (T_m)
        """
        from pycalphad_app.core.thermo_engine import ThermoEngine
        res = ThermoEngine.calculate(self.comp_at)
        res["T_eval_K"] = temperature_k
        return res

    def get_miedema_enthalpy(self, el1: str, el2: str) -> float:
        """Evaluates pairwise Miedema mixing enthalpy in kJ/mol."""
        from pycalphad_app.core.thermo_engine import ThermoEngine
        return ThermoEngine.get_miedema_enthalpy(el1, el2)

    def get_rk_parameters(self, el1: str, el2: str, phase: str = "FCC") -> Tuple[float, float]:
        """Evaluates binary Redlich-Kister excess parameters (L0, L1) for specified phase."""
        from pycalphad_app.core.thermo_engine import ThermoEngine
        rk_data = ThermoEngine.RK_BINARY_PARAMETERS
        e1, e2 = el1.capitalize(), el2.capitalize()
        return rk_data.get((e1, e2, phase), rk_data.get((e2, e1, phase), (0.0, 0.0)))

    def compute_thermophysical_transport(self, temperatures_k: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Evaluates integrated temperature-dependent transport properties:
        density rho(T), linear CTE alpha(T), thermal conductivity kappa(T), and electrical resistivity.
        """
        from pycalphad_app.core.thermo_engine import ThermoEngine
        return ThermoEngine.compute_thermophysical_transport(self.comp_at, temperatures_k)

    def compute_phase_fractions(self, t_min_c: float = 500.0, t_max_c: float = 1600.0,
                                n_points: int = 50) -> Dict[str, Any]:
        """
        Evaluates multi-component temperature-dependent phase fractions across the specified range.
        """
        from pycalphad_app.core.thermo_engine import ThermoEngine
        elements = list(self.comp_at.keys())
        fractions = list(self.comp_at.values())
        return ThermoEngine.compute_phase_fractions(elements, fractions, t_min_c, t_max_c, n_points)

    @abstractmethod
    def get_supported_phases(self) -> List[str]:
        """Returns the primary crystallographic and precipitate phases supported by this family."""
        pass

    @abstractmethod
    def compute_thermodynamics(self) -> Dict[str, Any]:
        """
        Calculates equilibrium phase stability, solidus, liquidus, freezing range,
        and temperature-dependent phase fractions.
        """
        pass

    @abstractmethod
    def compute_phase_transformations(self) -> Dict[str, Any]:
        """
        Calculates kinetic transformation boundaries: martensite start/finish (Ms, Mf),
        bainite start (Bs), allotropic transus (T_beta), solvus precipitation, or eutectics.
        """
        pass

    @abstractmethod
    def compute_mechanical_properties(self, thermo_state: Dict[str, Any],
                                     transform_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates constitutive yield strength, UTS, elongation %, Vickers hardness,
        and fracture toughness based on phase distribution and grain size.
        """
        pass

    @abstractmethod
    def compute_transport_properties(self, thermo_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates temperature-dependent density, CTE, and thermal conductivity."""
        pass

    @abstractmethod
    def compute_environmental_properties(self, thermo_state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Calculates Wagner high-temperature oxidation kinetics and Stern-Geary corrosion polarization."""
        pass

    @abstractmethod
    def compute_single_temperature_step(self, temperature_k: float) -> Dict[str, Any]:
        """Calculates discrete instantaneous state for interactive step execution."""
        pass
