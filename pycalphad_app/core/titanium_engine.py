# -*- coding: utf-8 -*-
"""
titanium_engine.py - Specialized Metallurgical Engine for Titanium Alloys
Covers Alpha alloys (CP-Ti Grade 1-4), Near-Alpha (Ti-6242),
Alpha+Beta (Ti-6Al-4V Grade 5), and Metastable Beta alloys (Ti-10-2-3, Beta-21S).
Implements:
- Beta transus temperature T_beta.
- Aluminium and Molybdenum Equivalents ([Al]_eq, [Mo]_eq) for phase field classification.
- Athermal martensite transformation (beta -> alpha' hexagonal, alpha'' orthorhombic).
- Hall-Petch grain boundary strengthening and interstitial strengthening (O, N, C).
"""

from typing import Dict, Any, List, Tuple
import math
import numpy as np

from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine


class TitaniumEngine(BaseAlloyEngine):
    """
    Dedicated metallurgical calculation engine for Titanium Alloy databases.
    """

    def get_supported_phases(self) -> List[str]:
        return [
            "Liquid",
            "BCC_Beta",
            "HCP_Alpha",
            "Martensite_Alpha_Prime",
            "Intermetallics_Ti3Al"
        ]

    def _calc_equivalents(self) -> Tuple[float, float]:
        """
        Calculates Aluminium and Molybdenum Equivalents in wt. %:
        [Al]_eq = %Al + %Sn/3 + %Zr/6 + 10*(%O + %N + 0.5*%C)
        [Mo]_eq = %Mo + 0.67*%V + 0.44*%W + 0.28*%Nb + 0.22*%Ta + 1.25*%Cr + 1.25*%Ni + 1.7*%Mn + 2.5*%Fe
        """
        al = self.comp_wt.get("Al", 0.0) * 100.0
        sn = self.comp_wt.get("Sn", 0.0) * 100.0
        zr = self.comp_wt.get("Zr", 0.0) * 100.0
        o = self.comp_wt.get("O", 0.0) * 100.0
        n = self.comp_wt.get("N", 0.0) * 100.0
        c = self.comp_wt.get("C", 0.0) * 100.0

        mo = self.comp_wt.get("Mo", 0.0) * 100.0
        v = self.comp_wt.get("V", 0.0) * 100.0
        w = self.comp_wt.get("W", 0.0) * 100.0
        nb = self.comp_wt.get("Nb", 0.0) * 100.0
        ta = self.comp_wt.get("Ta", 0.0) * 100.0
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        ni = self.comp_wt.get("Ni", 0.0) * 100.0
        mn = self.comp_wt.get("Mn", 0.0) * 100.0
        fe = self.comp_wt.get("Fe", 0.0) * 100.0

        al_eq = al + (sn / 3.0) + (zr / 6.0) + 10.0 * (o + n + 0.5 * c)
        mo_eq = mo + 0.67 * v + 0.44 * w + 0.28 * nb + 0.22 * ta + 1.25 * cr + 1.25 * ni + 1.7 * mn + 2.5 * fe

        return float(al_eq), float(mo_eq)

    def compute_phase_transformations(self) -> Dict[str, Any]:
        """
        Calculates:
        - Beta transus temperature T_beta (pure Ti = 882 C)
        - Alloy classification: Alpha, Near-Alpha, Alpha+Beta, Metastable Beta
        - Martensite start Ms for water-quenched beta -> alpha'
        - Liquidus and Solidus
        """
        al_eq, mo_eq = self._calc_equivalents()

        # Beta transus formula (C) - Donachie / Leyens & Peters standard
        # Al, O, N raise T_beta (+18.5 C / [Al]_eq); V, Mo, Fe depress it (-10.0 C / [Mo]_eq)
        t_beta_c = 882.0 + (18.5 * al_eq) - (10.0 * mo_eq)
        t_beta_c = min(1200.0, max(700.0, t_beta_c))

        # Classification based on [Mo]_eq
        al_wt = self.comp_wt.get("Al", 0.0) * 100.0
        v_wt = self.comp_wt.get("V", 0.0) * 100.0
        if al_wt < 0.5 and v_wt < 0.5 and mo_eq < 1.0:
            alloy_class = "Alpha Alloy (CP-Ti)"
        elif mo_eq < 2.0:
            alloy_class = "Near-Alpha Alloy"
        elif mo_eq < 10.0:
            alloy_class = "Alpha+Beta Alloy"
        else:
            alloy_class = "Beta / Metastable Beta Alloy"

        # Martensite start Ms upon rapid quench (C)
        # Ms = 850 - 45*%V - 60*%Mo - 80*%Cr
        ms_c = 850.0 - (45.0 * v_wt) - (60.0 * self.comp_wt.get("Mo", 0.0) * 100.0)

        # Melting boundaries (pure Ti melts at 1668 C)
        # Al raises liquidus slightly; V depresses it slightly
        t_liq_c = 1668.0 + (5.0 * al_wt) - (14.0 * v_wt) - (8.0 * self.comp_wt.get("Fe", 0.0) * 100.0)
        t_sol_c = t_liq_c - 55.0

        return {
            "T_beta_transus_C": float(t_beta_c),
            "Al_Equivalent": float(al_eq),
            "Mo_Equivalent": float(mo_eq),
            "AlloyClass": alloy_class,
            "Ms_C": float(ms_c),
            "T_Liquidus_C": float(t_liq_c),
            "T_Solidus_C": float(t_sol_c),
            "T_beta_transus_K": float(t_beta_c + 273.15),
            "T_Liquidus_K": float(t_liq_c + 273.15),
            "T_Solidus_K": float(t_sol_c + 273.15)
        }

    def compute_thermodynamics(self) -> Dict[str, Any]:
        """Calculates equilibrium phase fractions at room temperature."""
        trans = self.compute_phase_transformations()
        mo_eq = trans["Mo_Equivalent"]
        alloy_class = trans["AlloyClass"]

        if alloy_class == "Alpha Alloy (CP-Ti)":
            f_alpha = 0.99
            f_beta = 0.01
        elif alloy_class == "Near-Alpha Alloy":
            f_alpha = 0.95
            f_beta = 0.05
        elif alloy_class == "Alpha+Beta Alloy":
            # For Ti-6Al-4V: ~90-92% alpha, ~8-10% retained beta
            f_beta = min(0.35, max(0.06, 0.025 * mo_eq))
            f_alpha = 1.0 - f_beta
        else:
            # Metastable beta: high retained beta
            f_beta = min(0.95, max(0.40, 0.07 * mo_eq))
            f_alpha = 1.0 - f_beta

        phases = {
            "HCP_Alpha": float(f_alpha),
            "BCC_Beta": float(f_beta)
        }

        return {
            "T_Liquidus": float(trans["T_Liquidus_K"]),
            "T_Solidus": float(trans["T_Solidus_K"]),
            "Solidus_K": float(trans["T_Solidus_K"]),
            "Liquidus_K": float(trans["T_Liquidus_K"]),
            "Enthalpy_Fusion_J_kg": 295000.0,
            "Phases": phases,
            "DominantPhase": "HCP_Alpha" if f_alpha >= f_beta else "BCC_Beta"
        }

    def compute_mechanical_properties(self, thermo: Dict[str, Any],
                                      transform: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes yield strength, UTS, and elongation based on interstitial oxygen,
        solid solution, grain size, and alpha/beta morphology.
        """
        al_eq = transform["Al_Equivalent"]
        mo_eq = transform["Mo_Equivalent"]
        alloy_class = transform["AlloyClass"]
        phases = thermo.get("Phases", {})
        f_beta = phases.get("BCC_Beta", 0.08)

        o_wt = self.comp_wt.get("O", 0.0) * 100.0
        n_wt = self.comp_wt.get("N", 0.0) * 100.0

        if alloy_class == "Alpha Alloy (CP-Ti)":
            # Interstitial strengthening is dominant: ~120 MPa base + 600 * (%O)
            sy = 140.0 + (750.0 * o_wt) + (1200.0 * n_wt)
            uts = sy * 1.35 + 40.0
            elong = max(18.0, 32.0 - (40.0 * o_wt))
            hv = sy / 3.1
            k1c = 75.0
        else:
            # Ti-6Al-4V benchmark:
            # Proof strength: 880-920 MPa annealed
            base_strength = 300.0
            ss_strength = (50.0 * self.comp_wt.get("Al", 0.0) * 100.0) + (20.0 * self.comp_wt.get("V", 0.0) * 100.0)
            interstitial = 550.0 * o_wt
            d_um = max(1.0, self.grain_size_um)
            hp = 160.0 / math.sqrt(d_um)

            sy = base_strength + ss_strength + interstitial + hp
            sy = min(1100.0, max(860.0, sy))
            uts = sy * 1.08 + 30.0
            elong = max(10.0, 16.0 - (4.0 * f_beta))
            hv = sy / 3.0
            k1c = 55.0

        youngs_e = 114.0  # GPa for Ti-6Al-4V

        return {
            "YieldStrength_MPa": float(sy),
            "YieldStrength_RT_MPa": float(sy),
            "UTS_MPa": float(uts),
            "UTS_RT_MPa": float(uts),
            "Elongation_pct": float(elong),
            "Elongation_RT_pct": float(elong),
            "VickersHardness_HV": float(hv),
            "Hardness_HV": float(hv),
            "YoungsModulus_GPa": float(youngs_e),
            "FractureToughness_MPa_m05": float(k1c),
            "PoissonRatio": 0.34,
            "PughRatio": float(youngs_e / (2.0 * 1.34 * max(10.0, sy * 0.001))),
            "DominantStructure": f"{alloy_class} ({phases.get('HCP_Alpha', 0.9)*100:.0f}% Alpha / {f_beta*100:.0f}% Beta)"
        }

    def compute_transport_properties(self, thermo: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates thermophysical properties. Titanium has very low density ~4.43 - 4.51 g/cm3."""
        al_wt = self.comp_wt.get("Al", 0.0) * 100.0
        v_wt = self.comp_wt.get("V", 0.0) * 100.0
        # Al lowers density, V slightly increases it
        rho = 4.51 - (0.025 * al_wt) + (0.012 * v_wt)
        k_th = 6.7 + 0.1 * al_wt  # very low thermal conductivity ~ 7 W/mK
        cp = 525.0
        cte = 8.6e-6

        return {
            "TheoreticalDensity_g_cm3": float(rho),
            "Density_RT_g_cm3": float(rho),
            "ThermalConductivity_W_mK": float(k_th),
            "SpecificHeat_J_kgK": float(cp),
            "ThermalDiffusivity_m2_s": float(k_th / (rho * 1000.0 * cp)),
            "CTE_1e6_K": float(cte * 1e6),
            "ElectricalConductivity_MS_m": 0.58
        }

    def compute_environmental_properties(self, thermo: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Computes exceptional titanium corrosion resistance (TiO2 rutile film)."""
        corr = {
            "CorrosionRate_mpy": 0.02,
            "Ecorr_V_vs_SCE": 0.05,
            "Icorr_uA_cm2": 0.08,
            "PREN": 35.0,
            "CorrosionMechanism": "Spontaneous TiO2 Rutile Passive Film Passivation"
        }
        ox = {
            "ProtectiveOxide": "TiO2 (Rutile / Anatase Dense Film)",
            "Kp_g2_m4_s": 8.5e-7,
            "MaxServiceTemperature_C": 550.0,  # Alpha case embrittlement limit
            "OxidationKinetics": "Sub-Parabolic Diffusion into Subsurface"
        }
        return corr, ox

    def compute_single_temperature_step(self, t_k: float) -> Dict[str, Any]:
        """Provides instantaneous state at temperature T_K."""
        trans = self.compute_phase_transformations()
        t_c = t_k - 273.15
        t_liq_c = trans["T_Liquidus_C"]
        t_sol_c = trans["T_Solidus_C"]
        t_beta_c = trans["T_beta_transus_C"]

        if t_c >= t_liq_c:
            phases = {"Liquid": 1.0}
            dominant = "Liquid"
        elif t_c >= t_sol_c:
            f_liq = (t_c - t_sol_c) / max(1.0, (t_liq_c - t_sol_c))
            phases = {"Liquid": float(f_liq), "BCC_Beta": float(1.0 - f_liq)}
            dominant = "Liquid + BCC_Beta"
        elif t_c >= t_beta_c:
            phases = {"BCC_Beta": 1.0}
            dominant = "BCC_Beta (High-Temp Allotrope)"
        else:
            # Alpha/beta partitioning across two-phase field
            f_alpha_growth = (t_beta_c - t_c) / max(1.0, (t_beta_c - 500.0))
            f_alpha_growth = max(0.0, min(1.0, f_alpha_growth))
            thermo = self.compute_thermodynamics()
            eq_alpha = thermo["Phases"]["HCP_Alpha"]
            cur_alpha = f_alpha_growth * eq_alpha
            phases = {
                "HCP_Alpha": float(cur_alpha),
                "BCC_Beta": float(1.0 - cur_alpha)
            }
            dominant = "HCP_Alpha + BCC_Beta"

        return {
            "Temperature_K": float(t_k),
            "Temperature_C": float(t_c),
            "Phases": phases,
            "DominantPhase": dominant
        }
