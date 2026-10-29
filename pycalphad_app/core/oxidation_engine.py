"""
oxidation_engine.py - High-Temperature Oxidation Kinetics
Wagner parabolic rate law (kp), Arrhenius activation energy,
and protective scale growth (Cr2O3, Al2O3, SiO2, Spinel).
"""

import numpy as np
from typing import Dict, List, Any, Optional

class OxidationEngine:
    R = 8.314462618  # J / (mol * K)

    @staticmethod
    def compute_oxidation_kinetics(elements: List[str], at_fractions: List[float], thermo_metrics: Dict[str, Any], temp_c: float = 900.0, exposure_hours: float = 100.0) -> Dict[str, Any]:
        """
        Computes parabolic rate constant kp (g^2/(cm^4*s)), scale regime,
        and parabolic mass gain curve over exposure time.
        """
        temp_k = temp_c + 273.15
        x_dict = {el: fr for el, fr in zip(elements, at_fractions)}

        cr_frac = x_dict.get("Cr", 0.0)
        al_frac = x_dict.get("Al", 0.0)
        si_frac = x_dict.get("Si", 0.0)

        # Determine dominant scale regime and Arrhenius parameters (Q in J/mol, k0 in g^2/(cm^4*s))
        if al_frac >= 0.08:
            regime = "Protective α-Al2O3 Formers (Low kp, Excellent Spallation Resistance)"
            q_ox = 285000.0
            k0 = 1.2e-3
        elif cr_frac >= 0.12 or (si_frac >= 0.04 and cr_frac >= 0.10):
            regime = "Continuous Cr2O3 Chromia Scale (High Temperature Passivation)"
            q_ox = 245000.0
            k0 = 8.5e-4
        elif any(el in ["Ti", "Zr", "Nb", "Ta"] for el in elements):
            regime = "Non-Protective Mixed Refractory Oxides (Pest Oxidation Susceptible)"
            q_ox = 180000.0
            k0 = 5.0e-2
        else:
            regime = "Complex Multi-Component Spinel (Fe-Mn-Co Rich)"
            q_ox = 210000.0
            k0 = 2.4e-3

        # Arrhenius kp calculation
        kp = k0 * np.exp(-q_ox / (OxidationEngine.R * temp_k))

        # Time evolution (exposure hours to seconds)
        t_hours = np.linspace(0.0, max(1.0, exposure_hours), 150)
        t_sec = t_hours * 3600.0
        mass_gain_g_cm2 = np.sqrt(2.0 * kp * t_sec)
        mass_gain_mg_cm2 = mass_gain_g_cm2 * 1000.0

        res = {
            "Regime": regime,
            "kp_g2_cm4_s": kp,
            "ActivationEnergy_kJ_mol": q_ox / 1000.0,
            "MassGain_mg_cm2": mass_gain_mg_cm2[-1],
            "ExposureHours": exposure_hours,
            "Temperature_C": temp_c,
            "Time_Hours": t_hours,
            "MassGainCurve_mg_cm2": mass_gain_mg_cm2
        }
        res["Oxidation_kp"] = kp
        res["primary_oxide"] = regime
        return res

    @classmethod
    def calculate(cls, composition: Dict[str, float], thermo_metrics: Optional[Dict[str, Any]] = None,
                  temp_c: float = 900.0, exposure_hours: float = 100.0) -> Dict[str, Any]:
        if thermo_metrics is None:
            thermo_metrics = {}
        elems = list(composition.keys())
        fracs = list(composition.values())
        return cls.compute_oxidation_kinetics(elems, fracs, thermo_metrics, temp_c, exposure_hours)

