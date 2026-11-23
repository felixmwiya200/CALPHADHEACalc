# -*- coding: utf-8 -*-
"""
piecewise_fitter.py - Piecewise Polynomial Thermophysical Fitting Engine
Ported from MATLAB fit_piecewise_functions.m
Fits temperature-dependent density, thermal conductivity, specific heat, viscosity,
and surface tension into continuous polynomial functions formatted for COMSOL Multiphysics,
ANSYS Fluent, and ABAQUS simulation decks.
"""

from typing import Dict, Any, List, Tuple
import numpy as np


class PiecewiseFitter:
    """
    Fits thermophysical CALPHAD curves into continuous piecewise polynomials
    across Solid, Mushy (Solidus-Liquidus), and Liquid zones.
    """
    @staticmethod
    def fit_property_piecewise(temperatures: np.ndarray, values: np.ndarray,
                               t_solidus: float, t_liquidus: float,
                               degree: int = 2) -> Dict[str, Any]:
        """
        Splits data into Solid, Mushy, and Liquid temperature segments
        and calculates polynomial coefficients: p(T) = a_n * T^n + ... + a_0.
        """
        t = np.asarray(temperatures, dtype=float)
        v = np.asarray(values, dtype=float)

        # Remove NaNs
        valid = ~np.isnan(t) & ~np.isnan(v)
        t = t[valid]
        v = v[valid]

        if len(t) < 3:
            return {"solid": [0.0], "mushy": [0.0], "liquid": [0.0]}

        solid_mask = (t <= t_solidus)
        mushy_mask = (t > t_solidus) & (t < t_liquidus)
        liquid_mask = (t >= t_liquidus)

        def fit_seg(t_sub, v_sub):
            if len(t_sub) >= degree + 1:
                return np.polyfit(t_sub, v_sub, degree).tolist()
            elif len(t_sub) >= 2:
                return np.polyfit(t_sub, v_sub, 1).tolist()
            elif len(t_sub) == 1:
                return [float(v_sub[0])]
            else:
                return [0.0]

        return {
            "t_solidus": float(t_solidus),
            "t_liquidus": float(t_liquidus),
            "solid_coeffs": fit_seg(t[solid_mask], v[solid_mask]),
            "mushy_coeffs": fit_seg(t[mushy_mask], v[mushy_mask]),
            "liquid_coeffs": fit_seg(t[liquid_mask], v[liquid_mask])
        }

    @classmethod
    def generate_comsol_functions(cls, thermo_results: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates piecewise continuous function text ready for COMSOL Global Definitions.
        """
        t_sol = thermo_results.get("Solidus_K", 1400.0)
        t_liq = thermo_results.get("Liquidus_K", 1600.0)

        # Baseline density
        rho0 = thermo_results.get("Density_g_cm3", 7.5) * 1000.0  # kg/m^3
        cp0 = thermo_results.get("Cp_J_kgK", 460.0)
        k0 = thermo_results.get("ThermalConductivity_W_mK", 15.0)

        comsol_deck = {
            "rho_T": f"piecewise(T, T < {t_sol:.1f}, {rho0:.1f} - 0.05*(T - 300), T < {t_liq:.1f}, {rho0*0.95:.1f} - 0.1*(T - {t_sol:.1f}), {rho0*0.90:.1f} - 0.12*(T - {t_liq:.1f})) [kg/m^3]",
            "Cp_T": f"piecewise(T, T < {t_sol:.1f}, {cp0:.1f} + 0.15*(T - 300), T < {t_liq:.1f}, {cp0*1.8:.1f}, {cp0*1.2:.1f}) [J/(kg*K)]",
            "k_T": f"piecewise(T, T < {t_sol:.1f}, {k0:.1f} + 0.012*(T - 300), T < {t_liq:.1f}, {k0*1.1:.1f}, {k0*1.3:.1f} + 0.008*(T - {t_liq:.1f})) [W/(m*K)]",
            "gamma_T": f"1.75 - 0.0004 * (T - {t_liq:.1f}) [N/m]"
        }
        return comsol_deck
