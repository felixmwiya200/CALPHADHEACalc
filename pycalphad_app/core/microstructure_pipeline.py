"""
pycalphad_app.core.microstructure_pipeline
==========================================
Second-Layer Microstructural Mesoscale Pipeline.

Coordinates:
  Layer 1 (CALPHAD Thermodynamics & Solute Stability)
       ↓
  Layer 2A (Population Balance Model / KWN Particle Size Distribution Kinetics)
       ↓
  Layer 2B (Potts Monte Carlo Grain Growth with Dynamic Zener Pinning)
       ↓
  Layer 2C (Coupled Mechanical Strengthening Resolution: Hall-Petch + Orowan)
       ↓
  Layer 2D (Property Enhancements: Hardness, UTS, Toughness, Creep, Transport)
       ↓
  Layer 2E (Phase Diagram Enhancements: Gibbs-Thomson Solvus & TTT/CCT Kinetics)
"""

import math
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pycalphad_app.core.population_balance_engine import PopulationBalanceEngine
from pycalphad_app.core.monte_carlo_engine import MonteCarloEngine


class MicrostructurePipeline:
    """
    Executes the second-stage mesoscale simulation layer downstream of CALPHAD,
    enriching not only microstructural PSD and grain morphology, but also enhancing
    mechanical, thermal, and electrical transport properties, alongside non-equilibrium
    kinetic phase stability diagrams (Gibbs-Thomson solvus shift and TTT/CCT transformation envelopes).
    """

    R_GAS = 8.314462618  # J / (mol*K)

    @classmethod
    def execute(
        cls,
        thermo_res: Dict[str, Any],
        trans_res: Dict[str, Any],
        phase_curves: Dict[str, Any],
        mech_res: Dict[str, Any],
        user_opts: Optional[Dict[str, Any]] = None,
        temp_series: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main pipeline entry point.
        """
        if user_opts is None:
            user_opts = {}

        # 1. Extract CALPHAD outputs
        t_sol_k = float(thermo_res.get("Solidus_K", thermo_res.get("T_Solidus", 1400.0)))
        t_liq_k = float(thermo_res.get("Liquidus_K", thermo_res.get("T_Liquidus", 1550.0)))
        at_comp = thermo_res.get("atomic_composition", thermo_res.get("composition", {}))
        phases = thermo_res.get("Phases", {})
        grain_size_um = float(user_opts.get("grain_size_um", 25.0))

        # Aging / heat treatment temperature for second-stage simulation
        t_service_k = float(user_opts.get("heat_treatment_temp_k", min(1223.15, max(773.15, t_sol_k * 0.70))))
        exposure_hours = float(user_opts.get("heat_treatment_hours", 20.0))
        total_seconds = exposure_hours * 3600.0

        # Detect primary precipitating phase from CALPHAD phase dictionary
        precip_phase = "Secondary Precipitate"
        precip_fraction_eq = 0.08
        interfacial_energy = 0.035  # J/m²

        candidate_phases = [
            ("GAMMA_PRIME", 0.030),
            ("B2_ORDERED", 0.045),
            ("SIGMA", 0.120),
            ("LAVES", 0.140),
            ("M23C6", 0.180),
            ("CARBIDE", 0.180),
            ("BCC_A2", 0.050),
            ("FCC_A1", 0.050)
        ]

        found_candidates = []
        for p_name, p_frac in phases.items():
            p_up = p_name.upper()
            if "LIQUID" not in p_up and p_frac > 0.005:
                for cand_prefix, gamma_val in candidate_phases:
                    if cand_prefix in p_up:
                        found_candidates.append((p_name, float(p_frac), gamma_val))
                        break

        if found_candidates:
            found_candidates.sort(key=lambda x: -x[1])
            if len(found_candidates) > 1 and found_candidates[0][1] > 0.55:
                precip_phase, precip_fraction_eq, interfacial_energy = found_candidates[1]
            else:
                precip_phase, precip_fraction_eq, interfacial_energy = found_candidates[0]
        else:
            precip_phase = "Intermetallic / Dispersoid"
            precip_fraction_eq = 0.05
            interfacial_energy = 0.040

        # Solute concentration estimation (e.g. Al, Ti, Nb, Ta, Cr, Mo, W, C)
        solute_keys = ["Al", "Ti", "Nb", "Ta", "Cr", "Mo", "W", "C"]
        c0_solute = sum(float(at_comp.get(k, 0.0)) for k in solute_keys)
        if c0_solute <= 0.01:
            c0_solute = 0.15
        ce_solute = max(0.005, c0_solute * (1.0 - precip_fraction_eq * 1.5))
        cp_solute = min(0.95, c0_solute + 0.25)

        # 2. Layer 2A: Population Balance Model (KWN Precipitation)
        pbm = PopulationBalanceEngine(
            phase_name=precip_phase,
            t_kelvin=t_service_k,
            matrix_c0=c0_solute,
            matrix_ce=ce_solute,
            precip_cp=cp_solute,
            gamma_interfacial=interfacial_energy,
            eq_phase_fraction=precip_fraction_eq
        )
        pbm_results = pbm.solve(
            total_time_seconds=total_seconds,
            n_bins=120,
            n_time_steps=250
        )

        final_fv = pbm_results["volume_fraction_final"]
        final_r_nm = pbm_results["mean_radius_nm_final"]

        # 3. Layer 2B: Potts Monte Carlo Grain Evolution with Zener Pinning
        mc = MonteCarloEngine(
            initial_grain_size_um=grain_size_um,
            temp_kelvin=t_service_k,
            gb_energy_j_m2=0.62,
            hall_petch_k=0.55,
            lattice_dimension=96,
            num_q_states=64
        )
        mc_results = mc.solve(
            total_time_seconds=total_seconds,
            precip_volume_fraction=final_fv,
            precip_mean_radius_nm=final_r_nm,
            n_time_steps=200
        )

        final_grain_d_um = mc_results["final_grain_size_um"]

        # 4. Layer 2C: Coupled Multi-Scale Strengthening Resolution
        sigma_base_raw = float(mech_res.get("YieldStrength_MPa", 280.0))
        sigma_base = sigma_base_raw * 0.45
        sigma_ss = float(mech_res.get("SolidSolutionHardening_MPa", 120.0))
        sigma_hp = mc_results["hall_petch_strength_final_mpa"]
        sigma_precip = pbm_results["total_precip_strengthening_mpa"]

        # Experimental & Additive Manufacturing parameters (Hatch Pitch, Laser Scan, Cold Work)
        hatch_pitch_um = float(user_opts.get("hatch_pitch_um", 80.0))
        laser_power_w = float(user_opts.get("laser_power_w", 275.0))
        scan_speed_mm_s = float(user_opts.get("scan_speed_mm_s", 800.0))
        layer_thickness_um = float(user_opts.get("layer_thickness_um", 30.0))
        cold_work_pct = float(user_opts.get("cold_work_pct", 0.0))

        ved = float(user_opts.get("volumetric_energy_density_j_mm3", 0.0))
        if ved <= 0.0 and scan_speed_mm_s > 0 and hatch_pitch_um > 0 and layer_thickness_um > 0:
            ved = laser_power_w / (scan_speed_mm_s * (hatch_pitch_um * 1e-3) * (layer_thickness_um * 1e-3))

        cooling_rate = float(user_opts.get("cooling_rate_k_s", 0.0))
        if cooling_rate <= 0.0:
            cooling_rate = min(1e7, max(1e3, 2.5e5 * (scan_speed_mm_s / 800.0) * (80.0 / max(10.0, hatch_pitch_um))))

        cell_spacing_um = 50.0 * math.pow(max(100.0, cooling_rate), -0.33)
        # Cellular subgrain dislocation boundary strengthening in AM
        sigma_cell = 0.0
        if hatch_pitch_um > 0 and scan_speed_mm_s > 100.0:
            sigma_cell = 185.0 / math.sqrt(max(0.1, cell_spacing_um))

        # Cold work dislocation forest hardening (Taylor hardening)
        sigma_cw = 8.5 * math.pow(max(0.0, cold_work_pct), 0.65) if cold_work_pct > 0 else 0.0

        sigma_y_resolved = sigma_base + sigma_ss + sigma_hp + sigma_precip + sigma_cell + sigma_cw

        strengthening_breakdown = {
            "matrix_friction_stress_mpa": float(round(sigma_base, 1)),
            "solid_solution_strengthening_mpa": float(round(sigma_ss, 1)),
            "hall_petch_grain_boundary_mpa": float(round(sigma_hp, 1)),
            "orowan_precipitation_hardening_mpa": float(round(sigma_precip, 1)),
            "cellular_subgrain_boundary_mpa": float(round(sigma_cell, 1)),
            "cold_work_dislocation_mpa": float(round(sigma_cw, 1)),
            "total_resolved_yield_strength_mpa": float(round(sigma_y_resolved, 1))
        }

        # 5. Layer 2D: Multi-Property Enhancement Engine (Hardness, UTS, Toughness, Creep, Transport)
        delta_sig_y = max(0.0, sigma_y_resolved - sigma_base_raw)
        base_hv = float(mech_res.get("Hardness_HV", mech_res.get("VickersHardness_HV", 220.0)))
        enhanced_hv = base_hv + (delta_sig_y / 3.27)

        base_uts = float(mech_res.get("UTS_MPa", sigma_base_raw * 1.35))
        enhanced_uts = base_uts + 0.82 * delta_sig_y

        base_el = float(mech_res.get("Elongation_pct", 18.0))
        # Strength-ductility trade-off (Ashby banana curve)
        enhanced_el = max(1.5, base_el * math.pow(sigma_base_raw / max(1.0, sigma_y_resolved), 0.55))

        base_k1c = float(mech_res.get("FractureToughness_MPa_m05", 45.0))
        # Grain refinement increases toughness (crack deflection), while high particle fraction reduces it slightly
        delta_k1c_grain = 0.10 * sigma_hp
        delta_k1c_precip = -12.0 * final_fv
        enhanced_k1c = max(12.0, base_k1c + delta_k1c_grain + delta_k1c_precip)

        base_creep = float(mech_res.get("CreepRupture_Hours", 120.0))
        # Dislocation climb threshold stress Orowan elevation
        creep_multiplier = 1.0 + 3.5 * (sigma_precip / max(50.0, sigma_base))
        enhanced_creep = base_creep * creep_multiplier

        enhanced_fatigue = 0.45 * enhanced_uts

        # Transport properties: Mayadas-Shatzkes grain boundary scattering & interfacial phonon resistance
        base_rho = float(trans_res.get("Resistivity_uOhm_cm", trans_res.get("ElectricalResistivity_uOhm_cm", 95.0)))
        # delta_rho_GB = 1.5 * rho_0 * (lambda / d) * (R / (1 - R))
        delta_rho_gb = 1.5 * base_rho * (0.040 / max(0.5, final_grain_d_um)) * 0.45
        delta_rho_precip = 3.5 * final_fv * (15.0 / max(1.0, final_r_nm))
        enhanced_rho = base_rho + delta_rho_gb + delta_rho_precip

        base_k = float(trans_res.get("ThermalConductivity_W_mK", 14.5))
        # Coupled Wiedemann-Franz reduction due to boundary electron and phonon scattering
        enhanced_k = base_k * math.pow(base_rho / max(1.0, enhanced_rho), 0.85)

        enhanced_properties = {
            "base_yield_strength_mpa": float(round(sigma_base_raw, 1)),
            "enhanced_yield_strength_mpa": float(round(sigma_y_resolved, 1)),
            "delta_yield_strength_mpa": float(round(delta_sig_y, 1)),
            "base_hardness_hv": float(round(base_hv, 1)),
            "enhanced_hardness_hv": float(round(enhanced_hv, 1)),
            "delta_hardness_hv": float(round(enhanced_hv - base_hv, 1)),
            "base_uts_mpa": float(round(base_uts, 1)),
            "enhanced_uts_mpa": float(round(enhanced_uts, 1)),
            "delta_uts_mpa": float(round(enhanced_uts - base_uts, 1)),
            "base_elongation_pct": float(round(base_el, 2)),
            "enhanced_elongation_pct": float(round(enhanced_el, 2)),
            "base_fracture_toughness_mpa_m05": float(round(base_k1c, 1)),
            "enhanced_fracture_toughness_mpa_m05": float(round(enhanced_k1c, 1)),
            "base_creep_rupture_hours": float(round(base_creep, 1)),
            "enhanced_creep_rupture_hours": float(round(enhanced_creep, 1)),
            "enhanced_fatigue_limit_mpa": float(round(enhanced_fatigue, 1)),
            "base_electrical_resistivity_uohm_cm": float(round(base_rho, 2)),
            "enhanced_electrical_resistivity_uohm_cm": float(round(enhanced_rho, 2)),
            "delta_electrical_resistivity_uohm_cm": float(round(enhanced_rho - base_rho, 2)),
            "base_thermal_conductivity_w_mk": float(round(base_k, 2)),
            "enhanced_thermal_conductivity_w_mk": float(round(enhanced_k, 2)),
            "delta_thermal_conductivity_w_mk": float(round(enhanced_k - base_k, 2)),
            "volumetric_energy_density_j_mm3": float(round(ved, 1)),
            "porosity_regime": (
                "Lack-of-Fusion Risk (Insufficient Overlap)" if ved < 50.0
                else "Optimal Conduction Window (>99.8% Relative Density)" if ved <= 160.0
                else "Keyhole Porosity Risk (Excessive Vaporization)"
            ),
            "cooling_rate_k_s": float(round(cooling_rate, 0)),
            "cellular_spacing_um": float(round(cell_spacing_um, 3)),
            "cellular_strengthening_mpa": float(round(sigma_cell, 1)),
            "cold_work_strengthening_mpa": float(round(sigma_cw, 1)),
            "hatch_pitch_um": float(round(hatch_pitch_um, 1)),
            "grain_size_um": float(round(final_grain_d_um, 1))
        }

        # 6. Layer 2E: Phase Diagram Enhancements (Gibbs-Thomson Solvus Shift & TTT / CCT Kinetics)
        kinetic_phase_diagram = cls._compute_kinetic_phase_diagram(
            phase_curves=phase_curves,
            precip_phase=precip_phase,
            t_sol_k=t_sol_k,
            final_r_nm=final_r_nm,
            interfacial_energy=interfacial_energy,
            final_fv=final_fv,
            c0_solute=c0_solute,
            ce_solute=ce_solute,
            cp_solute=cp_solute
        )

        # 7. Layer 2F: Temperature-Dependent Series Enhancements
        enhanced_temp_series = cls._compute_enhanced_temperature_series(
            temp_series=temp_series,
            sigma_base_raw=sigma_base_raw,
            sigma_y_resolved=sigma_y_resolved,
            delta_sig_y=delta_sig_y,
            enhanced_hv=enhanced_hv,
            base_hv=base_hv,
            enhanced_uts=enhanced_uts,
            base_uts=base_uts,
            enhanced_rho=enhanced_rho,
            base_rho=base_rho,
            enhanced_k=enhanced_k,
            base_k=base_k,
            t_solvus_k=kinetic_phase_diagram.get("equilibrium_solvus_k", t_service_k + 150.0)
        )

        return {
            "heat_treatment_temp_k": t_service_k,
            "heat_treatment_hours": exposure_hours,
            "primary_precipitate_phase": precip_phase,
            "population_balance": pbm_results,
            "monte_carlo_grain_growth": mc_results,
            "strengthening_breakdown": strengthening_breakdown,
            "enhanced_properties": enhanced_properties,
            "kinetic_phase_diagram": kinetic_phase_diagram,
            "enhanced_temp_series": enhanced_temp_series
        }

    @classmethod
    def _compute_kinetic_phase_diagram(
        cls,
        phase_curves: Dict[str, Any],
        precip_phase: str,
        t_sol_k: float,
        final_r_nm: float,
        interfacial_energy: float,
        final_fv: float,
        c0_solute: float,
        ce_solute: float,
        cp_solute: float
    ) -> Dict[str, Any]:
        """
        Evaluates:
        1. Gibbs-Thomson capillary solvus depression Delta T_solvus for nanoscale precipitates
        2. Time-Temperature-Transformation (TTT) C-curves (t_1%, t_50%, t_99%)
        3. Non-equilibrium Continuous Cooling Transformation (CCT) phase stability envelopes
        """
        # Determine equilibrium solvus temperature from phase_curves
        t_k_list = phase_curves.get("t_k", [])
        series = phase_curves.get("series", {})
        precip_series = series.get(precip_phase, [])

        t_solvus_eq_k = t_sol_k * 0.88  # Physical default
        if t_k_list and precip_series and len(t_k_list) == len(precip_series):
            # Find temperature where precipitate fraction drops to ~0
            for i in range(len(t_k_list) - 1, -1, -1):
                if precip_series[i] > 0.003:
                    t_solvus_eq_k = float(t_k_list[i])
                    break

        t_solvus_eq_k = max(700.0, min(t_sol_k - 15.0, t_solvus_eq_k))

        # Gibbs-Thomson capillary solvus shift:
        # Delta T_cap = (2 * gamma * V_m * T_solvus) / (r_bar * Delta H_diss)
        # where Delta H_diss ~ 42 kJ/mol
        v_molar = 1.05e-5  # m³/mol
        delta_h_diss = 42000.0  # J/mol
        r_bar_m = max(0.5e-9, final_r_nm * 1e-9)

        delta_t_cap = (2.0 * interfacial_energy * v_molar * t_solvus_eq_k) / (r_bar_m * delta_h_diss)
        # Bounded between 5 K and 85 K for physical reality
        delta_t_cap = float(max(5.0, min(85.0, delta_t_cap)))
        t_solvus_kin_k = t_solvus_eq_k - delta_t_cap

        # Build TTT Transformation C-Curves
        t_nose_k = 0.76 * t_solvus_eq_k
        t_nose_c = t_nose_k - 273.15
        t_nose_s = 4.8  # Typical rapid nose transformation time (seconds)
        crit_cooling = (t_solvus_eq_k - t_nose_k) / max(0.5, t_nose_s)

        # 25 temperature points for the TTT C-curve from 250 °C to T_solvus - 10 °C
        t_min_c = 250.0
        t_max_c = (t_solvus_eq_k - 273.15) - 10.0
        if t_max_c <= t_min_c + 50.0:
            t_max_c = t_min_c + 300.0

        ttt_temps_c = np.linspace(t_min_c, t_max_c, 26).tolist()
        ttt_t1_s = []
        ttt_t50_s = []
        ttt_t99_s = []

        q_diff = 245000.0  # J/mol

        for tc in ttt_temps_c:
            tk = tc + 273.15
            under = max(1.0, t_solvus_eq_k - tk)

            # Classical TTT C-shape: driving force ~ undercooling, mobility ~ Arrhenius diffusion
            # ln(t) ~ Q / (R*T) + C / (T * under^2)
            d_term = q_diff / (cls.R_GAS * tk) - q_diff / (cls.R_GAS * t_nose_k)
            thermo_term = 4.5 * math.pow((t_solvus_eq_k - t_nose_k) / under, 1.8)
            log_time_factor = math.exp(min(18.0, max(-3.0, 0.5 * d_term + 0.5 * thermo_term - 1.0)))

            t1 = max(0.05, t_nose_s * log_time_factor * 0.15)
            t50 = max(0.2, t_nose_s * log_time_factor * 1.0)
            t99 = max(0.8, t_nose_s * log_time_factor * 3.8)

            ttt_t1_s.append(float(round(t1, 2)))
            ttt_t50_s.append(float(round(t50, 2)))
            ttt_t99_s.append(float(round(t99, 2)))

        # Continuous Cooling Phase Fractions (Equilibrium vs Moderate 10 K/s vs Fast 100 K/s)
        temp_sweep_c = np.linspace(25.0, t_solvus_eq_k - 273.15 + 40.0, 45).tolist()
        eq_phase_traj = []
        kin_frac_mod = []
        kin_frac_fast = []

        for tc in temp_sweep_c:
            tk = tc + 273.15
            # Equilibrium CALPHAD solvus trajectory
            if tk >= t_solvus_eq_k:
                f_eq = 0.0
            else:
                f_eq = final_fv * math.pow(max(0.0, (t_solvus_eq_k - tk) / (t_solvus_eq_k - 298.15)), 0.65)
            eq_phase_traj.append(float(round(f_eq, 4)))

            # Kinetic phase fraction with Gibbs-Thomson capillary depression:
            # Solvus shifted to t_solvus_kin_k, plus diffusion time lag at high cooling rates
            if tk >= t_solvus_kin_k:
                f_mod = 0.0
                f_fast = 0.0
            else:
                # Moderate cooling (10 K/s): ~85% of equilibrium precipitate fraction formed
                f_mod = f_eq * 0.88 * math.pow(max(0.0, (t_solvus_kin_k - tk) / (t_solvus_kin_k - 298.15)), 0.70)
                # Fast cooling (100 K/s SLM / laser quench): solute trapping suppresses precipitation to ~25%
                f_fast = f_eq * 0.28 * math.pow(max(0.0, (t_solvus_kin_k - tk) / (t_solvus_kin_k - 298.15)), 0.85)

            kin_frac_mod.append(float(round(f_mod, 4)))
            kin_frac_fast.append(float(round(f_fast, 4)))

        return {
            "phase_name": precip_phase,
            "equilibrium_solvus_k": float(round(t_solvus_eq_k, 1)),
            "equilibrium_solvus_c": float(round(t_solvus_eq_k - 273.15, 1)),
            "kinetic_solvus_k": float(round(t_solvus_kin_k, 1)),
            "kinetic_solvus_c": float(round(t_solvus_kin_k - 273.15, 1)),
            "gibbs_thomson_shift_c": float(round(delta_t_cap, 1)),
            "ttt_nose_temperature_c": float(round(t_nose_c, 1)),
            "ttt_nose_time_seconds": float(round(t_nose_s, 2)),
            "critical_cooling_rate_k_s": float(round(crit_cooling, 1)),
            "ttt_temperatures_c": ttt_temps_c,
            "ttt_time_1pct_seconds": ttt_t1_s,
            "ttt_time_50pct_seconds": ttt_t50_s,
            "ttt_time_99pct_seconds": ttt_t99_s,
            "temperature_sweep_c": temp_sweep_c,
            "equilibrium_phase_fraction": eq_phase_traj,
            "kinetic_phase_fraction_moderate_cool": kin_frac_mod,
            "kinetic_phase_fraction_fast_cool": kin_frac_fast
        }

    @classmethod
    def _compute_enhanced_temperature_series(
        cls,
        temp_series: Optional[Dict[str, Any]],
        sigma_base_raw: float,
        sigma_y_resolved: float,
        delta_sig_y: float,
        enhanced_hv: float,
        base_hv: float,
        enhanced_uts: float,
        base_uts: float,
        enhanced_rho: float,
        base_rho: float,
        enhanced_k: float,
        base_k: float,
        t_solvus_k: float
    ) -> Dict[str, Any]:
        """
        Enhances temperature-dependent curves for Yield Strength, UTS, Hardness,
        Thermal Conductivity, and Electrical Resistivity across thermal steps.
        """
        if not temp_series:
            return {}

        t_mech_k = temp_series.get("t_mech_k", [])
        ys_raw = temp_series.get("yield_strength", [])
        uts_raw = temp_series.get("uts", [])
        hv_raw = temp_series.get("hardness_hv", [])

        enhanced_ys = []
        enhanced_uts_list = []
        enhanced_hv_list = []

        for i, tk in enumerate(t_mech_k):
            # Thermal dissolution scaling: enhancement is full at RT, decays toward solvus
            decay = max(0.0, min(1.0, (t_solvus_k - tk) / max(50.0, t_solvus_k - 298.15)))
            elev = delta_sig_y * math.pow(decay, 1.4)

            base_y = ys_raw[i] if i < len(ys_raw) else sigma_base_raw
            base_u = uts_raw[i] if i < len(uts_raw) else base_uts
            base_h = hv_raw[i] if i < len(hv_raw) else base_hv

            enhanced_ys.append(float(round(base_y + elev, 1)))
            enhanced_uts_list.append(float(round(base_u + 0.82 * elev, 1)))
            enhanced_hv_list.append(float(round(base_h + elev / 3.27, 1)))

        t_k = temp_series.get("t_k", [])
        k_raw = temp_series.get("thermal_cond", [])
        rho_raw = temp_series.get("resistivity", [])

        enhanced_k_list = []
        enhanced_rho_list = []

        delta_rho = max(0.0, enhanced_rho - base_rho)
        k_ratio = enhanced_k / max(0.1, base_k)

        for i, tk in enumerate(t_k):
            base_r = rho_raw[i] if i < len(rho_raw) else base_rho
            base_c = k_raw[i] if i < len(k_raw) else base_k

            # Boundary electron scattering adds temperature-independent Matthiessen component
            enhanced_rho_list.append(float(round(base_r + delta_rho, 2)))
            enhanced_k_list.append(float(round(base_c * k_ratio, 2)))

        return {
            "t_mech_k": t_mech_k,
            "yield_strength_enhanced": enhanced_ys,
            "uts_enhanced": enhanced_uts_list,
            "hardness_hv_enhanced": enhanced_hv_list,
            "t_k": t_k,
            "thermal_cond_enhanced": enhanced_k_list,
            "resistivity_enhanced": enhanced_rho_list
        }
