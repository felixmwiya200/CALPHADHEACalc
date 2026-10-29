"""
oxidation_engine.py - High-Temperature Oxidation Kinetics & Thermodynamics Engine
Comprehensive translation of App/HEAOxidationEngine.m to native Python.

Features:
  1. Wagner parabolic oxidation law (Delta W / A)^2 = k_p(T) * t
  2. Arrhenius parabolic rate constant k_p(T) = k0 * exp(-Q_ox / (R * T))
  3. Oxide scale thickness evolution x_ox(t) = (Delta W / A) / (rho_ox * f_O)
  4. Classification into Alumina-, Chromia-, Spinel-, Refractory Pesting, and Non-Volatile regimes
  5. High-temperature Ellingham Gibbs free energy Delta G_f(T) per mole O2
  6. Wagner critical solute threshold N* for continuous external scale formation
  7. Pilling-Bedworth ratio (PBR) and thermal spallation compressive stress sigma_th
  8. Refractory pest oxidation and MoO3 / WO3 / V2O5 volatile sublimation alerts
  9. High-entropy scale sublattice configurational entropy and sluggish diffusion barriers
"""

import math
import numpy as np
from typing import Dict, List, Any, Optional

class OxidationEngine:
    R_GAS = 8.314462618  # Universal gas constant, J / (mol * K)

    @classmethod
    def compute_oxidation_kinetics(cls, elements: List[str], at_fractions: List[float],
                                  thermo_metrics: Optional[Dict[str, Any]] = None,
                                  user_opts: Optional[Dict[str, Any]] = None,
                                  temp_c: float = 900.0,
                                  exposure_hours: float = 100.0) -> Dict[str, Any]:
        """
        Main entry point returning comprehensive oxidation kinetics dictionary.
        """
        if thermo_metrics is None:
            thermo_metrics = {}
        if user_opts is None:
            user_opts = {}

        # Normalize atomic fractions
        c_raw = np.array(at_fractions, dtype=float)
        c_sum = np.sum(c_raw)
        if c_sum <= 0:
            c = np.ones(len(elements)) / max(1, len(elements))
        else:
            c = c_raw / c_sum

        t_c = float(user_opts.get("Temperature_C", temp_c))
        t_c = max(500.0, min(1400.0, t_c))
        t_k = t_c + 273.15

        exp_hours = float(user_opts.get("ExposureHours", exposure_hours))
        exp_hours = max(1.0, min(2000.0, exp_hours))

        delta_t_cooling = float(user_opts.get("CoolingDeltaT", t_c - 25.0))

        # Elemental composition mapping in at%
        at_pct = {el: c[i] * 100.0 for i, el in enumerate(elements)}
        def get_at(sym: str) -> float:
            return at_pct.get(sym, 0.0)

        al_at = get_at("Al")
        cr_at = get_at("Cr")
        mn_at = get_at("Mn")
        mo_at = get_at("Mo")
        w_at  = get_at("W")
        v_at  = get_at("V")
        ti_at = get_at("Ti")
        zr_at = get_at("Zr")
        hf_at = get_at("Hf")
        nb_at = get_at("Nb")
        ta_at = get_at("Ta")
        fe_at = get_at("Fe")
        co_at = get_at("Co")
        ni_at = get_at("Ni")
        si_at = get_at("Si")

        pesting_alert = False
        volatilization_alert = False
        volatile_msg = ""
        pesting_msg = ""

        refr_volatile_at = mo_at + w_at + v_at
        refr_total_at = mo_at + w_at + v_at + nb_at + ta_at + ti_at + zr_at + hf_at

        # 1. Classification of high-temperature oxidation regime
        if al_at >= 12.0:
            regime = "Alumina Former"
            dominant_oxide = "α-Al2O3"
            oxide_formula = "Al2O3"
            q_ox_kj = 215.0
            k0_val = 7.0e-3
            rho_ox = 3.95
            f_o = 0.4707  # 48 / 101.96
            pbr = 1.28
            protective_rating = "Superior (Hermetic Alpha-Alumina Barrier)"
        elif refr_volatile_at >= 15.0 and cr_at < 16.0:
            regime = "Refractory Volatile / Pesting Risk"
            if mo_at >= 8.0 and w_at >= 8.0:
                dominant_oxide = "MoO3 / WO3 / Nb2O5"
            elif mo_at >= 8.0:
                dominant_oxide = "MoO3 / Nb2O5"
            elif w_at >= 8.0:
                dominant_oxide = "WO3 / Ta2O5"
            elif v_at >= 8.0:
                dominant_oxide = "V2O5 / TiO2 (Molten Fluxing Risk)"
            else:
                dominant_oxide = "Mixed Volatile Refractory Oxides"
            oxide_formula = "Mixed Volatile Oxides"
            q_ox_kj = 110.0
            k0_val = 5.0e-3
            rho_ox = 4.60
            f_o = 0.32
            pbr = 3.25
            protective_rating = "Catastrophic (Pesting & Volatilization)"
            pesting_alert = True
            pesting_msg = "Severe pesting disintegration risk at 500-800 °C: oxygen diffusion along grain boundaries causes catastrophic pulverization."

            if mo_at > 5.0 and t_c >= 600.0:
                volatilization_alert = True
                volatile_msg = "MoO3 sublimes rapidly above 600 °C (P_vap > 10^-3 atm), leaving a porous, unprotective skeleton."
            elif w_at > 5.0 and t_c >= 800.0:
                volatilization_alert = True
                volatile_msg = "WO3 undergoes rapid gas-phase volatilization above 800 °C."
            elif v_at > 5.0 and t_c >= 690.0:
                volatilization_alert = True
                volatile_msg = "V2O5 melts at 690 °C into liquid-phase oxide, inducing catastrophic fluxing attack."
        elif cr_at >= 16.0 and mn_at < 8.0:
            regime = "Chromia Former"
            dominant_oxide = "Cr2O3"
            oxide_formula = "Cr2O3"
            q_ox_kj = 225.0
            k0_val = 4.5e-1
            rho_ox = 5.22
            f_o = 0.3158  # 48 / 151.99
            pbr = 2.07
            protective_rating = "Good (Continuous Chromia Scale)"
            if t_c >= 950.0:
                volatilization_alert = True
                volatile_msg = f"High-temperature CrO3(g) evaporation active at {t_c:.0f} °C: scale thinning accelerates metal loss."
        elif mn_at >= 8.0 and cr_at >= 10.0:
            regime = "Spinel Former (Mn Outward Diffusion)"
            dominant_oxide = "(Mn,Cr)3O4 / Mn2O3"
            oxide_formula = "MnCr2O4 Spinel"
            if t_c <= 800.0:
                q_ox_kj = 128.0
                k0_val = 8.5e-4
            else:
                q_ox_kj = 220.0
                k0_val = 6.4e1
            rho_ox = 4.87
            f_o = 0.2871  # 64 / 222.93
            pbr = 1.95
            protective_rating = "Moderate (Fast Outward Mn Flux Overrides Chromia)"
        elif refr_total_at >= 60.0 and refr_volatile_at < 15.0:
            regime = "Refractory Multi-Oxide (Non-Volatile)"
            dominant_oxide = "(Zr,Hf)6(Nb,Ta)2O17 / TiO2"
            oxide_formula = "Complex Refractory Oxides"
            q_ox_kj = 190.0
            k0_val = 0.12
            rho_ox = 4.85
            f_o = 0.35
            pbr = 2.15
            protective_rating = "Moderate (Alpha-Case Interstitial Embrittlement Risk)"
        else:
            regime = "Transition Metal Oxide"
            dominant_oxide = "(Fe,Co,Ni)O / Mixed Spinels"
            oxide_formula = "Mixed (Fe,Ni,Co) Oxides"
            q_ox_kj = 185.0
            k0_val = 0.05
            rho_ox = 5.20
            f_o = 0.28
            pbr = 1.75
            protective_rating = "Fair / Semi-Protective"

        # High-Entropy scale sublattice entropy & sluggish diffusion effect
        pos_c = c[c > 0]
        delta_s_scale = -cls.R_GAS * np.sum(pos_c * np.log(pos_c))
        if delta_s_scale < 1.0 * cls.R_GAS:
            scale_entropy_regime = "Low Entropy Scale (<1.0 R)"
        elif delta_s_scale <= 1.5 * cls.R_GAS:
            scale_entropy_regime = "Medium Entropy Scale (1.0-1.5 R)"
        else:
            scale_entropy_regime = "High-Entropy Stabilized Scale (>1.5 R)"

        de_sluggish_kj = 2.5 * (delta_s_scale / cls.R_GAS)
        q_ox_eff_kj = q_ox_kj + de_sluggish_kj

        # 2. Parabolic rate constant kp(T)
        kp_g2_cm4_s = k0_val * math.exp(-(q_ox_eff_kj * 1e3) / (cls.R_GAS * t_k))
        if pesting_alert and t_c >= 600.0:
            kp_g2_cm4_s = max(kp_g2_cm4_s, 1.5e-8)

        kp_mg2_cm4_h = kp_g2_cm4_s * 3.6e9

        # 3. Mass gain and scale thickness
        mass_gain_mg_cm2 = math.sqrt(kp_mg2_cm4_h * exp_hours)
        mass_gain_g_cm2 = mass_gain_mg_cm2 * 1e-3
        scale_thickness_um = (mass_gain_g_cm2 / (rho_ox * f_o)) * 1e4

        # 4. Wagner Critical Solute Criterion N*
        if regime == "Alumina Former":
            crit_threshold_at = 13.0
            actual_solute_at = al_at
            solute_element = "Al"
        elif regime == "Chromia Former":
            crit_threshold_at = 18.0
            actual_solute_at = cr_at
            solute_element = "Cr"
        else:
            crit_threshold_at = 15.0
            actual_solute_at = max(al_at, cr_at)
            solute_element = "Al/Cr"

        critical_solute_met = actual_solute_at >= crit_threshold_at
        if critical_solute_met:
            solute_status = f"Threshold Met ({solute_element} = {actual_solute_at:.1f} at% >= {crit_threshold_at:.1f} at%): Continuous external scale established."
        else:
            solute_status = f"Sub-Critical ({solute_element} = {actual_solute_at:.1f} at% < {crit_threshold_at:.1f} at%): Internal oxidation susceptibility."

        # 5. Thermal Spallation Stress (sigma_th)
        if oxide_formula == "Al2O3":
            e_ox_gpa = 390.0
            alpha_ox = 8.0e-6
            nu_ox = 0.25
        elif oxide_formula == "Cr2O3":
            e_ox_gpa = 300.0
            alpha_ox = 7.3e-6
            nu_ox = 0.28
        else:
            e_ox_gpa = 260.0
            alpha_ox = 8.5e-6
            nu_ox = 0.27

        alpha_alloy = float(thermo_metrics.get("alpha", 14.5)) * 1e-6
        delta_alpha = alpha_alloy - alpha_ox
        sigma_th_mpa = - (e_ox_gpa * 1e3 * delta_alpha * delta_t_cooling) / (1.0 - nu_ox)
        sigma_th_mpa = round(sigma_th_mpa, 1)

        spallation_alert = False
        spallation_msg = "Compressive residual stress within scale adherence tolerance."
        if abs(sigma_th_mpa) > 2500.0:
            spallation_alert = True
            spallation_msg = f"Severe compressive stress ({abs(sigma_th_mpa):.0f} MPa) exceeds interfacial adhesion limit; high risk of scale buckling and spallation."
        elif abs(sigma_th_mpa) > 1800.0:
            spallation_alert = True
            spallation_msg = f"Moderate-to-high compressive stress ({abs(sigma_th_mpa):.0f} MPa); spallation may occur during cyclic thermal shock."

        # 6. Iterative Subsurface Solute Depletion Solver
        max_iters = min(500, max(5, int(user_opts.get("MaxIterations", 50))))
        tol = float(user_opts.get("Tolerance", 1e-6))
        rho_alloy = float(thermo_metrics.get("density", 7.5))

        n_bulk = actual_solute_at
        n_int = n_bulk
        d_alloy = 1e-15 * math.exp(-140e3 / (cls.R_GAS * t_k))
        t_sec = exp_hours * 3600.0
        ox_converged = False
        ox_final_iter = max_iters

        for it in range(1, max_iters + 1):
            x_curr_m = max(1e-9, scale_thickness_um * 1e-6)
            j_ox = (kp_g2_cm4_s * 1e4) / (2.0 * x_curr_m * rho_ox * 1e3 * f_o)
            delta_diff = max(1e-7, math.sqrt(math.pi * d_alloy * t_sec))
            j_alloy = (d_alloy * (n_bulk - n_int) * 1e-2 * rho_alloy * 1e3) / delta_diff
            flux_res = abs(j_ox - j_alloy) / max(1e-12, j_ox)

            relax = 0.40
            n_int_new = max(0.2, n_bulk - (j_ox * delta_diff) / (d_alloy * 1e-2 * rho_alloy * 1e3 + 1e-12))
            n_int = (1.0 - relax) * n_int + relax * n_int_new

            if flux_res < tol and it >= 5:
                ox_converged = True
                ox_final_iter = it
                break

        # 7. Ellingham Thermodynamics Hierarchy
        ellingham_energies = cls.get_ellingham_gibbs_free_energies(t_k)

        # 8. Parabolic Curves for plotting
        time_hours_vec = np.linspace(0.1, max(100.0, exp_hours * 1.5), 100)
        mass_gain_t = np.sqrt(kp_mg2_cm4_h * time_hours_vec)
        scale_thick_t = (mass_gain_t * 1e-3 / (rho_ox * f_o)) * 1e4

        # 9. Arrhenius Curve
        t_arrh_c = np.linspace(600.0, 1200.0, 50)
        t_arrh_k = t_arrh_c + 273.15
        inv_t_1000 = 1000.0 / t_arrh_k
        kp_arrh_s = k0_val * np.exp(-(q_ox_kj * 1e3) / (cls.R_GAS * t_arrh_k))
        log10_kp_s = np.log10(np.maximum(1e-18, kp_arrh_s))

        res = {
            "Regime": regime,
            "regime": regime,
            "DominantOxide": dominant_oxide,
            "dominantOxide": dominant_oxide,
            "OxideFormula": oxide_formula,
            "ProtectiveRating": protective_rating,
            "OperatingTemp_C": t_c,
            "OperatingTemp_K": t_k,
            "ExposureHours": exp_hours,
            "kp_g2_cm4_s": kp_g2_cm4_s,
            "kp_mg2_cm4_h": round(kp_mg2_cm4_h, 4),
            "ActivationEnergy_kJ": round(q_ox_kj, 1),
            "ActivationEnergy_kJ_mol": round(q_ox_kj, 1),
            "PreExponential_k0": k0_val,
            "OxideDensity_g_cm3": rho_ox,
            "PBR": pbr,
            "MassGain_mg_cm2": round(mass_gain_mg_cm2, 3),
            "ScaleThickness_um": round(scale_thickness_um, 2),
            "SpallationStress_MPa": sigma_th_mpa,
            "ThermalSpallationStress_MPa": sigma_th_mpa,
            "CriticalSoluteMet": critical_solute_met,
            "CriticalSoluteStatus": solute_status,
            "CriticalSoluteConcentration_Nstar": crit_threshold_at,
            "ActualSoluteConcentration_at": actual_solute_at,
            "SpallationAlert": spallation_alert,
            "SpallationMessage": spallation_msg,
            "VolatilizationAlert": volatilization_alert,
            "VolatilizationMessage": volatile_msg,
            "PestingAlert": pesting_alert,
            "PestingMessage": pesting_msg,
            "SubsurfaceSolute_at": round(n_int, 2),
            "ScaleEntropyRegime": scale_entropy_regime,
            "EllinghamEnergies": ellingham_energies,

            # Aliases for plot views and legacy code
            "Oxidation_kp": kp_g2_cm4_s,
            "kp_T_m2_s": kp_g2_cm4_s * 1e-4,
            "kp_m2_s": kp_g2_cm4_s * 1e-4,
            "primary_oxide": dominant_oxide,
            "Time_Hours": time_hours_vec,
            "Time_hours": time_hours_vec,
            "MassGainCurve_mg_cm2": mass_gain_t,
            "MassGain_mg_cm2": mass_gain_t,
            "ScaleThicknessCurve_um": scale_thick_t,
            "Arrhenius_InvT_1000K": inv_t_1000,
            "Arrhenius_1000_over_T": inv_t_1000,
            "Arrhenius_Log10_kp": log10_kp_s,
            "Arrhenius_log10_kp": log10_kp_s,
            "Arrhenius_Temp_C": t_arrh_c,
            "Ellingham": ellingham_energies
        }
        return res

    @staticmethod
    def get_ellingham_gibbs_free_energies(t_k: float) -> Dict[str, float]:
        """
        Returns standard Gibbs free energies of oxide formation Delta G_f(T) per mole O2
        Delta G = dH - T * dS (kJ / mol O2)
        """
        def calc_g(dh: float, ds: float) -> float:
            return round(dh - t_k * ds, 1)

        return {
            "HfO2": calc_g(-1140.0, -0.200),
            "ZrO2": calc_g(-1095.0, -0.190),
            "Al2O3": calc_g(-1055.0, -0.179),
            "TiO2": calc_g(-944.0, -0.180),
            "SiO2": calc_g(-907.0, -0.180),
            "Ta2O5": calc_g(-810.0, -0.160),
            "Nb2O5": calc_g(-760.0, -0.170),
            "Cr2O3": calc_g(-745.0, -0.170),
            "WO3": calc_g(-560.0, -0.160),
            "FeO": calc_g(-525.0, -0.130),
            "MoO3": calc_g(-500.0, -0.160),
            "CoO": calc_g(-475.0, -0.140),
            "NiO": calc_g(-470.0, -0.170),
            "MnCr2O4_spinel": -45.2,
            "FeCr2O4_spinel": -30.5,
            "CoCr2O4_spinel": -26.1,
            "NiCr2O4_spinel": -20.8
        }

    @classmethod
    def calculate(cls, composition: Dict[str, float], thermo_metrics: Optional[Dict[str, Any]] = None,
                  temp_c: float = 900.0, exposure_hours: float = 100.0) -> Dict[str, Any]:
        """Convenience method matching app convention."""
        if thermo_metrics is None:
            thermo_metrics = {}
        elems = list(composition.keys())
        fracs = list(composition.values())
        return cls.compute_oxidation_kinetics(elems, fracs, thermo_metrics, temp_c=temp_c, exposure_hours=exposure_hours)
