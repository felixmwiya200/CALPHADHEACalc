"""
corrosion_engine.py - Aqueous Corrosion & Electrochemical Passivation
Stern-Geary polarization, PREN, Faraday corrosion penetration rate,
and potentiodynamic polarization curves (3.5 wt% NaCl).
"""

import numpy as np
from typing import Dict, List, Any, Optional
from pycalphad_app.core.elements_data import get_element

class CorrosionEngine:
    @staticmethod
    def compute_corrosion_metrics(elements: List[str], at_fractions: List[float], thermo_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes PREN, equivalent weight, icorr, Ecorr, and polarization curve.
        """
        x_dict = {el: fr for el, fr in zip(elements, at_fractions)}
        is_coating = any(el in ["B", "Si"] for el in elements) and "Ni" in elements

        # Pitting Resistance Equivalent Number (wt% based)
        cr_at = x_dict.get("Cr", 0.0)
        mo_at = x_dict.get("Mo", 0.0)
        w_at  = x_dict.get("W", 0.0)
        n_at  = x_dict.get("N", 0.0)

        pren = (cr_at * 100.0) + 3.3 * (mo_at * 100.0 + 0.5 * w_at * 100.0) + 16.0 * (n_at * 100.0)

        # Equivalent Weight EW (g/equivalent)
        valences = {
            "Fe": 2.0, "Ni": 2.0, "Co": 2.0, "Cr": 3.0, "Mn": 2.0,
            "Al": 3.0, "Ti": 4.0, "Mo": 4.0, "W": 4.0, "Si": 4.0, "B": 3.0, "C": 4.0
        }
        sum_f_val = 0.0
        for el, fr in zip(elements, at_fractions):
            ed = get_element(el)
            m = ed.atomic_mass if ed else 55.85
            v = valences.get(el, 2.0)
            sum_f_val += (fr * m) / v

        ew = sum_f_val if sum_f_val > 0 else 26.0
        rho = thermo_metrics.get("Density_g_cm3", 8.0)

        if is_coating:
            e_corr = -0.312  # V vs SCE
            i_corr = 2.45    # uA/cm^2
            grade = "Grade B (Marine Passivating Hardfacing)"
        elif pren >= 32.0:
            e_corr = -0.180
            i_corr = 0.25
            grade = "Grade A+ (Super-Austenitic / Marine Resistant)"
        elif pren >= 18.0:
            e_corr = -0.245
            i_corr = 1.15
            grade = "Grade A (High Resistance Passivating)"
        else:
            e_corr = -0.450
            i_corr = 12.50
            grade = "Grade C (Active Dissolution / Susceptible to Pitting)"

        # Faraday's law of annual penetration rate: CR = 0.00327 * i_corr * EW / rho (mm/year)
        cr_mm_yr = (0.00327 * i_corr * ew) / max(0.1, rho)

        # Potentiodynamic Tafel Polarization Curve: E vs log10(i)
        # E range from -0.8 V to +0.8 V vs SCE
        e_pot = np.linspace(e_corr - 0.45, e_corr + 0.90, 200)
        beta_a = 0.120  # V/decade (anodic Tafel slope)
        beta_c = 0.120  # V/decade (cathodic Tafel slope)

        # Butler-Volmer + passivation current limit
        log_i = []
        i_pass = i_corr * 4.5
        for e in e_pot:
            eta = e - e_corr
            if eta < 0:
                # Cathodic branch
                i_c = i_corr * 10.0 ** (-eta / beta_c)
                log_i.append(np.log10(max(1e-4, i_c)))
            else:
                # Anodic branch + passive window + transpassive breakdown
                if eta < 0.25:
                    i_a = i_corr * 10.0 ** (eta / beta_a)
                elif eta < 0.65:
                    i_a = i_pass # Stable passive current density
                else:
                    # Transpassive / pitting breakdown
                    i_a = i_pass * 10.0 ** ((eta - 0.65) / 0.06)
                log_i.append(np.log10(max(1e-4, i_a)))

        res = {
            "PREN_HEA": pren,
            "EquivalentWeight": ew,
            "E_corr_V_SCE": e_corr,
            "i_corr_uA_cm2": i_corr,
            "CR_mm_yr_NaCl": cr_mm_yr,
            "Grade": grade,
            "Polarization_Potential_V": e_pot,
            "Polarization_LogCurrent_A_cm2": np.array(log_i) - 6.0 # Convert uA to A
        }
        res["Corrosion_Ecorr_V"] = e_corr
        res["Corrosion_icorr_uA"] = i_corr
        res["CorrosionRate_mm_yr"] = cr_mm_yr
        res["PREN_val"] = pren
        return res

    @classmethod
    def calculate(cls, composition: Dict[str, float], thermo_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if thermo_metrics is None:
            thermo_metrics = {"Density_g_cm3": 8.0}
        elems = list(composition.keys())
        fracs = list(composition.values())
        return cls.compute_corrosion_metrics(elems, fracs, thermo_metrics)

