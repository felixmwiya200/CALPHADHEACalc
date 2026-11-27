# -*- coding: utf-8 -*-
"""
steel_engine.py - Dedicated Engine for Steels and Stainless Steels
Provides authentic metallurgical models for:
- Austenite decomposition, Ferrite, Pearlite, Martensite (Ms, Mf), and Bainite (Bs).
- Andrews linear & product Ms formulations and Koistinen-Marburger kinetics.
- Hall-Petch boundary strengthening and carbon interstitial solid-solution hardening.
- PREN pitting corrosion resistance and high-temperature chromia/wustite oxidation.
"""

from typing import Dict, List, Any, Tuple
import math
import numpy as np

from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine


class SteelEngine(BaseAlloyEngine):
    """
    Dedicated calculation engine for carbon steels, alloy steels, tool steels,
    and austenitic/ferritic/martensitic stainless steels.
    """

    PRIMARY_PHASES = [
        "Austenite (FCC)",
        "Ferrite (BCC)",
        "Martensite (BCT)",
        "Pearlite (Ferrite+Fe3C)",
        "Cementite (Fe3C)",
        "Carbides (M23C6/MC)",
        "Delta-Ferrite",
        "Liquid"
    ]

    def get_supported_phases(self) -> List[str]:
        return list(self.PRIMARY_PHASES)

    def _is_austenitic_stainless(self) -> bool:
        """Determines if composition stabilizes austenitic FCC matrix down to room temperature."""
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        if cr < 10.5:
            # Low-alloy and carbon steels are not stainless
            return False
        ni = self.comp_wt.get("Ni", 0.0) * 100.0
        # Schaeffler austenite boundary criterion
        ni_eq = ni + 30.0 * self.comp_wt.get("C", 0.0) * 100.0 + 0.5 * self.comp_wt.get("Mn", 0.0) * 100.0
        cr_eq = cr + self.comp_wt.get("Mo", 0.0) * 100.0 + 1.5 * self.comp_wt.get("Si", 0.0) * 100.0
        return (cr >= 15.0 and ni >= 6.0) or (ni_eq > 0.85 * cr_eq + 8.0)

    def compute_phase_transformations(self) -> Dict[str, Any]:
        """
        Calculates kinetic transformation temperatures:
        - Andrews linear Ms and Mf temperatures.
        - Steven & Haynes Bainite start Bs.
        - Ae3 (austenite upper boundary) and Ae1 (eutectoid) temperatures.
        """
        c = self.comp_wt.get("C", 0.0) * 100.0
        mn = self.comp_wt.get("Mn", 0.0) * 100.0
        si = self.comp_wt.get("Si", 0.0) * 100.0
        ni = self.comp_wt.get("Ni", 0.0) * 100.0
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        mo = self.comp_wt.get("Mo", 0.0) * 100.0
        v = self.comp_wt.get("V", 0.0) * 100.0
        w = self.comp_wt.get("W", 0.0) * 100.0

        # Andrews Linear Formula for Martensite Start (C)
        ms_c = 539.0 - (423.0 * c) - (30.4 * mn) - (17.7 * ni) - (12.1 * cr) - (7.5 * mo)
        # In austenitic stainless, Ms falls below room temp
        if self._is_austenitic_stainless():
            ms_c = min(-50.0, ms_c)

        mf_c = ms_c - 215.0  # 99% athermal martensite completion
        ms_k = ms_c + 273.15
        mf_k = mf_c + 273.15

        # Steven & Haynes Bainite Start (C)
        bs_c = 830.0 - (270.0 * c) - (90.0 * mn) - (37.0 * ni) - (70.0 * cr) - (83.0 * mo)
        bs_k = bs_c + 273.15

        # Andrews Ae3 upper critical temperature (C)
        ae3_c = 910.0 - (203.0 * math.sqrt(max(0.001, c))) - (15.2 * ni) + (44.7 * si) + (104.0 * v) + (31.5 * mo) + (13.1 * w) - (30.0 * mn) - (11.0 * cr)
        ae3_k = ae3_c + 273.15

        # Ae1 eutectoid temperature (C)
        ae1_c = 723.0 - (10.7 * mn) - (16.9 * ni) + (29.1 * si) + (16.9 * cr)
        ae1_k = ae1_c + 273.15

        # Empirical Liquidus and Solidus for Fe-base systems (C)
        t_liq_c = 1538.0 - (88.0 * c) - (5.0 * mn) - (14.0 * si) - (5.0 * ni) - (1.5 * cr) - (2.0 * mo)
        t_sol_c = 1538.0 - (200.0 * c) - (12.0 * mn) - (30.0 * si) - (10.0 * ni) - (3.0 * cr) - (5.0 * mo)
        t_sol_c = min(t_sol_c, t_liq_c - 15.0)

        t_liq_k = t_liq_c + 273.15
        t_sol_k = t_sol_c + 273.15

        return {
            "Ms_C": float(ms_c),
            "Mf_C": float(mf_c),
            "Ms_K": float(ms_k),
            "Mf_K": float(mf_k),
            "Bs_C": float(bs_c),
            "Bs_K": float(bs_k),
            "Ae3_C": float(ae3_c),
            "Ae3_K": float(ae3_k),
            "Ae1_C": float(ae1_c),
            "Ae1_K": float(ae1_k),
            "T_Liquidus_C": float(t_liq_c),
            "T_Solidus_C": float(t_sol_c),
            "T_Liquidus_K": float(t_liq_k),
            "T_Solidus_K": float(t_sol_k),
            "IsAusteniticStainless": self._is_austenitic_stainless()
        }

    def compute_thermodynamics(self) -> Dict[str, Any]:
        """
        Calculates solidus, liquidus, freezing range, and temperature-dependent phase fractions.
        """
        c = self.comp_wt.get("C", 0.0) * 100.0
        mn = self.comp_wt.get("Mn", 0.0) * 100.0
        si = self.comp_wt.get("Si", 0.0) * 100.0
        ni = self.comp_wt.get("Ni", 0.0) * 100.0
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        mo = self.comp_wt.get("Mo", 0.0) * 100.0

        # Empirical Liquidus and Solidus for Fe-base systems
        t_liq_c = 1538.0 - (88.0 * c) - (5.0 * mn) - (14.0 * si) - (5.0 * ni) - (1.5 * cr) - (2.0 * mo)
        t_sol_c = 1538.0 - (200.0 * c) - (12.0 * mn) - (30.0 * si) - (10.0 * ni) - (3.0 * cr) - (5.0 * mo)
        t_sol_c = min(t_sol_c, t_liq_c - 15.0)

        t_liq_k = t_liq_c + 273.15
        t_sol_k = t_sol_c + 273.15

        # Generate continuous temperature curve
        t_k_arr = np.linspace(300.0, 2000.0, 86)
        t_c_arr = t_k_arr - 273.15

        is_austenitic = self._is_austenitic_stainless()
        trans = self.compute_phase_transformations()
        ms_c = trans["Ms_C"]
        ae1_c = trans["Ae1_C"]
        ae3_c = trans["Ae3_C"]

        liquid_frac = np.zeros_like(t_k_arr)
        austenite_frac = np.zeros_like(t_k_arr)
        ferrite_frac = np.zeros_like(t_k_arr)
        martensite_frac = np.zeros_like(t_k_arr)
        carbide_frac = np.zeros_like(t_k_arr)

        is_quenched = self.cooling_rate_k_s >= 30.0

        for i, (tk, tc) in enumerate(zip(t_k_arr, t_c_arr)):
            if tc >= t_liq_c:
                liquid_frac[i] = 1.0
            elif tc > t_sol_c:
                # Mushy zone lever rule
                fl = (tc - t_sol_c) / max(1.0, t_liq_c - t_sol_c)
                liquid_frac[i] = fl
                if is_austenitic:
                    austenite_frac[i] = 1.0 - fl
                else:
                    austenite_frac[i] = (1.0 - fl) * 0.8
                    ferrite_frac[i] = (1.0 - fl) * 0.2
            else:
                liquid_frac[i] = 0.0
                if is_austenitic:
                    # 100% stable FCC austenite
                    austenite_frac[i] = 0.98
                    carbide_frac[i] = 0.02 if cr >= 12.0 and c > 0.03 else 0.0
                else:
                    if tc >= ae3_c:
                        austenite_frac[i] = 1.0
                    elif tc >= ae1_c:
                        # Intercritical zone (Austenite + Ferrite)
                        fa = (tc - ae1_c) / max(1.0, ae3_c - ae1_c)
                        austenite_frac[i] = fa
                        ferrite_frac[i] = 1.0 - fa
                    else:
                        # Below Ae1
                        if is_quenched and tc <= ms_c:
                            # Koistinen-Marburger athermal martensite
                            fm = 1.0 - math.exp(-0.011 * (ms_c - tc))
                            fm = min(1.0, max(0.0, fm))
                            martensite_frac[i] = fm
                            austenite_frac[i] = 1.0 - fm  # Retained austenite
                        elif is_quenched:
                            austenite_frac[i] = 1.0  # Metastable untransformed austenite above Ms
                        else:
                            # Equilibrium Ferrite + Pearlite/Carbides
                            ferrite_frac[i] = max(0.0, 1.0 - min(0.35, c * 0.8))
                            carbide_frac[i] = 1.0 - ferrite_frac[i]

        dominant_phase = "Austenite (FCC)" if is_austenitic else ("Martensite (BCT)" if is_quenched else "Ferrite (BCC) + Pearlite")

        phase_dict = {
            "T_K": t_k_arr.tolist(),
            "T_C": t_c_arr.tolist(),
            "Liquid": liquid_frac.tolist(),
            "Austenite (FCC)": austenite_frac.tolist(),
            "Ferrite (BCC)": ferrite_frac.tolist(),
            "Martensite (BCT)": martensite_frac.tolist(),
            "Carbides (Fe3C/M23C6)": carbide_frac.tolist(),
            # Legacy aliases for GUI backward compatibility
            "FCC": austenite_frac.tolist(),
            "BCC": (ferrite_frac + martensite_frac).tolist(),
            "B2": np.zeros_like(t_k_arr).tolist(),
            "Sigma": np.zeros_like(t_k_arr).tolist(),
        }

        # Room temperature density (g/cm^3)
        density = 7.87 - 0.08 * (c / 100.0) + 0.04 * (ni / 100.0) - 0.03 * (cr / 100.0)

        rt_phases = {
            "Austenite (FCC)": float(austenite_frac[0]),
            "Ferrite (BCC)": float(ferrite_frac[0]),
            "Martensite (BCT)": float(martensite_frac[0]),
            "Carbides (Fe3C/M23C6)": float(carbide_frac[0])
        }
        # Keep non-zero and strictly normalize to 1.0
        rt_phases = {k: v for k, v in rt_phases.items() if v > 0.001}
        if not rt_phases:
            rt_phases = {"Austenite (FCC)": 1.0} if is_austenitic else {"Ferrite (BCC)": 1.0}
        tot_rt = sum(rt_phases.values())
        if tot_rt > 0:
            rt_phases = {k: float(v / tot_rt) for k, v in rt_phases.items()}

        return {
            "Solidus_K": float(t_sol_k),
            "Liquidus_K": float(t_liq_k),
            "T_Solidus": float(t_sol_k),
            "T_Liquidus": float(t_liq_k),
            "FreezingRange_K": float(t_liq_k - t_sol_k),
            "Density_g_cm3": float(density),
            "density": float(density),
            "DominantPhase": dominant_phase,
            "Phase": dominant_phase,
            "Phases": rt_phases,
            "PhaseFractions": phase_dict,
            "VEC": 8.0,
            "VEC_val": 8.0
        }

    def compute_mechanical_properties(self, thermo_state: Dict[str, Any],
                                     transform_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constitutive mechanical properties incorporating:
        - Hall-Petch boundary strengthening: ky / sqrt(d)
        - Solid solution strengthening
        - Martensitic carbon interstitial hardening
        """
        c = self.comp_wt.get("C", 0.0) * 100.0
        mn = self.comp_wt.get("Mn", 0.0) * 100.0
        si = self.comp_wt.get("Si", 0.0) * 100.0
        ni = self.comp_wt.get("Ni", 0.0) * 100.0
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        mo = self.comp_wt.get("Mo", 0.0) * 100.0

        # Hall-Petch boundary contribution
        d_um = max(0.5, self.grain_size_um)
        sigma_hp = 550.0 / math.sqrt(d_um)

        # Solid solution contribution (MPa)
        sigma_ss = (32.0 * mn) + (84.0 * si) + (33.0 * ni) + (11.0 * mo)

        is_austenitic = transform_state.get("IsAusteniticStainless", False)
        is_quenched = self.cooling_rate_k_s >= 30.0

        if is_austenitic:
            # Austenitic stainless steel (e.g. AISI 304, 316)
            sy = 205.0 + (35.0 * si) + (20.0 * mo) + (0.5 * sigma_hp)
            uts = 515.0 + (45.0 * mo) + (30.0 * si) + (0.3 * sigma_hp)
            elong = max(35.0, 58.0 - 2.5 * mo - 1.2 * si)
            hv = uts / 3.2
            k1c = 110.0  # Outstanding fracture toughness of FCC austenite
        elif is_quenched and c > 0.10:
            # Martensitic high-strength state
            sy = 450.0 + (1420.0 * math.sqrt(c)) + sigma_ss + sigma_hp
            uts = sy * 1.28
            elong = max(6.0, 24.0 - 22.0 * c)
            hv = uts / 3.0
            k1c = max(35.0, 95.0 - 80.0 * c)
        else:
            # Normalised or annealed Ferrite-Pearlite
            f_pearlite = min(1.0, c / 0.77)
            sy = 105.0 + (160.0 * c) + sigma_ss + sigma_hp
            uts = 290.0 + (480.0 * c) + sigma_ss + (0.7 * sigma_hp)
            elong = max(12.0, 38.0 - 26.0 * c)
            hv = uts / 3.3
            k1c = 75.0

        youngs = 205.0 if not is_austenitic else 193.0
        poisson = 0.29

        # Temperature-dependent strength curve
        t_arr = np.array([77.0, 298.15, 573.15, 773.15, 973.15, 1173.15])
        sy_t = sy * np.exp(-0.0009 * (t_arr - 298.15))
        uts_t = uts * np.exp(-0.0008 * (t_arr - 298.15))

        return {
            "YieldStrength_MPa": float(sy),
            "YieldStrength_RT_MPa": float(sy),
            "UTS_MPa": float(uts),
            "UTS_RT_MPa": float(uts),
            "Elongation_pct": float(elong),
            "VickersHardness_HV": float(hv),
            "Hardness_HV": float(hv),
            "YoungsModulus_GPa": float(youngs),
            "PoissonsRatio": float(poisson),
            "FractureToughness_MPa_m05": float(k1c),
            "FractureToughness_K1c": float(k1c),
            "PughRatio": float(2.10 if is_austenitic else 1.85),
            "DominantStructure": thermo_state.get("DominantPhase", "Ferrite-Pearlite"),
            "TempDep_Temperature_K": t_arr.tolist(),
            "TempDep_YieldStrength_MPa": np.maximum(40.0, sy_t).tolist(),
            "TempDep_UTS_MPa": np.maximum(70.0, uts_t).tolist(),
        }

    def compute_transport_properties(self, thermo_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates temperature-dependent density, CTE, and thermal conductivity."""
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        ni = self.comp_wt.get("Ni", 0.0) * 100.0
        is_austenitic = self._is_austenitic_stainless()

        rho_0 = thermo_state.get("Density_g_cm3", 7.85)
        # CTE: Austenitic steels have significantly higher CTE than ferritic
        cte_0 = 17.2 if is_austenitic else 11.8
        # Thermal conductivity: Alloy additions and FCC structure reduce k
        k_0 = 15.2 if is_austenitic else max(24.0, 52.0 - 1.2 * cr - 0.8 * ni)

        t_grid = np.linspace(300.0, 1600.0, 100)
        rho_t = rho_0 * (1.0 - 3.0 * (cte_0 * 1e-6) * (t_grid - 300.0))
        k_t = k_0 + 0.008 * (t_grid - 300.0)
        cte_t = cte_0 + 0.0035 * (t_grid - 300.0)

        return {
            "TheoreticalDensity_g_cm3": float(rho_0),
            "Density_RT_g_cm3": float(rho_0),
            "Density_g_cm3": float(rho_0),
            "CTE_1e6_K": float(cte_0),
            "ThermalConductivity_W_mK": float(k_0),
            "Transport": {
                "T_K": t_grid.tolist(),
                "density_kg_m3": (rho_t * 1000.0).tolist(),
                "thermal_conductivity_W_mK": k_t.tolist(),
                "cte_1e6_K": float(cte_0)
            }
        }

    def compute_environmental_properties(self, thermo_state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Calculates Wagner oxidation kinetics and Stern-Geary corrosion polarization."""
        cr = self.comp_wt.get("Cr", 0.0) * 100.0
        mo = self.comp_wt.get("Mo", 0.0) * 100.0
        n = self.comp_wt.get("N", 0.0) * 100.0

        # Pitting Resistance Equivalent Number
        pren = cr + 3.3 * mo + 16.0 * n

        if pren >= 18.0:
            # Passive stainless regime
            ecorr = -0.120
            icorr = 0.08  # uA/cm2
            crate = 0.001
            regime = "Cr2O3 Passive Scale (Stainless)"
            kp = 1.2e-12
        else:
            # Active carbon/low-alloy steel corrosion
            ecorr = -0.450
            icorr = 4.20
            crate = 0.052
            regime = "Fe2O3 / Fe3O4 Non-Protective Scale"
            kp = 4.5e-10

        ox_res = {
            "kp_g2_cm4_s": float(kp),
            "Oxidation_kp": float(kp),
            "Regime": regime,
            "dominantOxide": "Cr2O3" if cr >= 12.0 else "Fe3O4",
            "ProtectiveOxide": "Cr2O3 Passive Film" if cr >= 12.0 else "Fe3O4 Non-Protective Scale",
            "MaxServiceTemperature_C": 850.0 if cr >= 12.0 else 550.0,
            "OxidationKinetics": {
                "Temp_C": [700, 800, 900, 1000],
                "kp_values": [kp * 0.1, kp, kp * 5.0, kp * 25.0]
            }
        }

        corr_res = {
            "CorrosionRate_mpy": float(crate * 39.37),
            "Ecorr_V_vs_SCE": float(ecorr),
            "Icorr_uA_cm2": float(icorr),
            "Corrosion_Ecorr_V": float(ecorr),
            "Corrosion_icorr_uA": float(icorr),
            "CorrosionRate_mm_yr": float(crate),
            "PREN_val": float(pren),
            "PREN": float(pren)
        }

        return (corr_res, ox_res)

    def compute_single_temperature_step(self, temperature_k: float) -> Dict[str, Any]:
        """Calculates single-temperature evaluation for interactive stepper."""
        thermo = self.compute_thermodynamics()
        trans = self.compute_phase_transformations()
        mech = self.compute_mechanical_properties(thermo, trans)

        t_c = temperature_k - 273.15
        is_austenitic = self._is_austenitic_stainless()
        ms_c = trans["Ms_C"]

        if is_austenitic:
            active_phase = "Austenite (FCC)"
        elif t_c <= ms_c and self.cooling_rate_k_s >= 30.0:
            active_phase = "Martensite (BCT)"
        elif t_c >= trans["Ae3_C"]:
            active_phase = "Austenite (FCC)"
        else:
            active_phase = "Ferrite (BCC)"

        return {
            "Temperature_K": float(temperature_k),
            "Temperature_C": float(t_c),
            "Phases": {active_phase: 1.0},
            "DominantPhase": active_phase,
            "temperature": float(temperature_k),
            "temperature_c": float(t_c),
            "active_phase": active_phase,
            "yield_strength_mpa": float(mech["YieldStrength_MPa"]),
            "hardness_hv": float(mech["VickersHardness_HV"])
        }
