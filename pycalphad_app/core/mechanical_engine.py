"""
mechanical_engine.py - Mechanical Metallurgy & Strengthening Mechanics
Curtin Solid Solution Strengthening, Hall-Petch grain size dependence,
Tabor Vickers hardness, and Ramberg-Osgood stress-strain relations.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class MechanicalEngine:
    @staticmethod
    def compute_mechanical_properties(elements: List[str], at_fractions: List[float], thermo_metrics: Dict[str, Any], grain_size_um: float = 30.0) -> Dict[str, Any]:
        """
        Computes yield strength, UTS, Vickers hardness, fracture toughness,
        temperature dependence, and true stress-strain curve.
        """
        phase = thermo_metrics.get("Phase", "FCC")
        delta_size = thermo_metrics.get("DeltaSize_pct", 1.5)
        is_coating = any(el in ["B", "Si"] for el in elements) and "Ni" in elements

        # Base frictional stress sigma_0
        if is_coating:
            # Thermal spray NiCrBSi coating composite yield strength
            sigma_0 = 850.0  # MPa
            k_hp = 350.0     # MPa * um^0.5
            delta_ss = 380.0
            toughness = 18.5 # MPa * m^0.5 (brittle hardfacing)
        elif "FCC" in phase:
            sigma_0 = 125.0
            k_hp = 494.0     # Laplanche et al. 2016 for Cantor alloy
            delta_ss = 80.0 * (delta_size / 1.5)
            toughness = 220.0 # Gludovatz et al. 2014 (extreme cryogenic toughness)
        elif "BCC" in phase:
            sigma_0 = 850.0
            k_hp = 280.0
            delta_ss = 450.0 * (delta_size / 3.0)
            toughness = 35.0
        else: # Duplex
            sigma_0 = 420.0
            k_hp = 380.0
            delta_ss = 220.0
            toughness = 85.0

        d_um = max(1.0, grain_size_um)
        sigma_hp = k_hp / np.sqrt(d_um)
        sigma_y = sigma_0 + delta_ss + sigma_hp

        # Ultimate Tensile Strength
        if is_coating:
            uts = sigma_y * 1.15
            el_pct = 1.2
            hv = 745.0
        elif "FCC" in phase:
            uts = sigma_y * 2.45
            el_pct = 52.0
            hv = round(sigma_y / 3.0 / 0.9807 * 1.8) # Tabor approximation
        elif "BCC" in phase:
            uts = sigma_y * 1.35
            el_pct = 12.0
            hv = round(sigma_y / 3.0 / 0.9807 * 1.4)
        else:
            uts = sigma_y * 1.65
            el_pct = 28.0
            hv = round(sigma_y / 3.0 / 0.9807 * 1.5)

        # Generate True Stress-Strain curve (Ramberg-Osgood)
        e_elastic = np.linspace(0.0, sigma_y / 200000.0, 50)
        s_elastic = e_elastic * 200000.0

        n_hardening = 0.35 if "FCC" in phase else (0.12 if is_coating else 0.20)
        e_plastic = np.linspace(0.0, el_pct / 100.0, 100)
        s_plastic = sigma_y + (uts - sigma_y) * (e_plastic / max(1e-4, el_pct / 100.0)) ** n_hardening

        strain_full = np.concatenate([e_elastic, e_plastic + e_elastic[-1]]) * 100.0 # in %
        stress_full = np.concatenate([s_elastic, s_plastic])

        # Generate Temperature Dependence curve (77 K to 1600 K)
        t_range = np.linspace(77.0, 1600.0, 100)
        t_m = thermo_metrics.get("T_Solidus", 1553.0)
        # Yield stress decreases with temperature via thermal activation + softening
        ys_temp = []
        for t in t_range:
            if t < 300.0:
                # Cryogenic strengthening (Peierls-Nabarro barrier)
                factor = 1.0 + 0.65 * ((300.0 - t) / 223.0)
            elif t < t_m * 0.55:
                factor = max(0.4, 1.0 - 0.35 * ((t - 300.0) / (t_m * 0.55 - 300.0)))
            else:
                # High-temperature power law creep softening
                factor = max(0.05, 0.65 * np.exp(-4.5 * ((t - t_m * 0.55) / (t_m - t_m * 0.55))))
            ys_temp.append(sigma_y * factor)

        res = {
            "YieldStrength_RT_MPa": sigma_y,
            "UTS_RT_MPa": uts,
            "Elongation_pct": el_pct,
            "VickersHardness_HV": int(hv),
            "FractureToughness_MPa_m05": toughness,
            "HallPetch_k_MPa_um05": k_hp,
            "FrictionStress_sigma0_MPa": sigma_0,
            "GrainSize_um": d_um,
            "StressStrain_Strain_pct": strain_full,
            "StressStrain_Stress_MPa": stress_full,
            "TempDep_Temperature_K": t_range,
            "TempDep_YieldStrength_MPa": np.array(ys_temp)
        }
        res["YieldStrength_MPa"] = sigma_y
        res["Hardness_HV"] = float(hv)
        res["YoungsModulus_GPa"] = 210.0
        return res

    @classmethod
    def calculate(cls, composition: Dict[str, float], thermo_metrics: Optional[Dict[str, Any]] = None,
                  grain_size_um: float = 25.0) -> Dict[str, Any]:
        if thermo_metrics is None:
            thermo_metrics = {"Phase": "FCC", "DeltaSize_pct": 1.5, "T_Solidus": 1553.0}
        elems = list(composition.keys())
        fracs = list(composition.values())
        return cls.compute_mechanical_properties(elems, fracs, thermo_metrics, grain_size_um)

