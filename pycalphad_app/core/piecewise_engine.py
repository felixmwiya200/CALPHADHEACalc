# -*- coding: utf-8 -*-
"""
piecewise_engine.py - Continuous & Piecewise Material Functions Engine
Ports the 21-property COMSOL Multiphysics Code Vault and continuous Heaviside step formulations
from CALPHADHEACalc.m (lines 4370–4560).

Generates both:
1. Discrete Piecewise Interval Functions (Solid, Mushy Phase-Change, Liquid Melt)
2. Continuous C²-Smoothed Transition Step Formulations using COMSOL's native flc2hs(T - T_trans, scale)
"""

from typing import Dict, Any, List, Optional
import math


PROPERTIES_LIST = [
    "Thermal Conductivity k(T) [W/(m*K)]",
    "Specific Heat Capacity Cp(T) [J/(kg*K)]",
    "Apparent Heat Capacity Cp_app(T) [J/(kg*K)] (Phase Change)",
    "Total Enthalpy H(T) [kJ/kg]",
    "Mass Density rho(T) [g/cm^3]",
    "Thermal Diffusivity alpha(T) [m^2/s]",
    "Linear Thermal Expansion CTE alpha_L(T) [1e-6/K]",
    "Volumetric Thermal Expansion beta(T) [1e-6/K]",
    "Thermal Strain dl/l0(T) [%]",
    "Electrical Resistivity rho_e(T) [uOhm*cm]",
    "Electrical Conductivity sigma_elec(T) [MS/m]",
    "Young's Elastic Modulus E(T) [GPa]",
    "Shear Modulus G(T) [GPa]",
    "Bulk Modulus K(T) [GPa]",
    "Poisson's Ratio nu(T) [-]",
    "Yield Strength sigma_y(T) [MPa]",
    "Dynamic Viscosity mu(T) [Pa*s]",
    "Kinematic Viscosity nu_kin(T) [m^2/s]",
    "Liquid Surface Tension gamma(T) [N/m] (Marangoni)",
    "Laser Optical Absorptivity A(T) [-]",
    "Total Hemispherical Emissivity epsilon(T) [-]"
]


class PiecewiseEngine:
    """
    Thermodynamic and mechanics piecewise function generator for FEA/CFD solvers
    (COMSOL Multiphysics, ANSYS Fluent, ABAQUS, OpenFOAM).
    """

    @classmethod
    def get_available_properties(cls) -> List[str]:
        return list(PROPERTIES_LIST)

    @classmethod
    def generate_property_piecewise(
        cls,
        property_name: str,
        thermo_metrics: Dict[str, Any],
        mech_metrics: Optional[Dict[str, Any]] = None,
        alloy_name: str = "Alloy-System"
    ) -> Dict[str, Any]:
        """
        Generates piecewise interval functions and smooth continuous flc2hs formulations
        anchored directly to CALPHAD solidus (Ts) and liquidus (Tl) temperatures.
        """
        mm = mech_metrics or {}
        tm = thermo_metrics or {}

        # Anchor temperatures from CALPHAD solution
        ts = float(tm.get("T_Solidus", tm.get("Solidus_K", tm.get("solidus", 1243.2))))
        tl = float(tm.get("T_Liquidus", tm.get("Liquidus_K", tm.get("liquidus", 1318.2))))
        if tl <= ts:
            tl = ts + 10.0
        delta_t = max(1.0, tl - ts)
        smooth_w = max(5.0, delta_t / 4.0)

        # Baseline room temperature physical parameters
        rho0 = float(tm.get("Density_g_cm3", tm.get("Density", tm.get("density", 8.24))))
        k0 = float(tm.get("ThermalConductivity_W_mK", tm.get("ThermalConductivity", tm.get("k", 16.5))))
        cp0 = float(tm.get("SpecificHeat_J_kgK", tm.get("Cp", tm.get("cp", 462.0))))
        dh_fus = float(tm.get("dH_fus", tm.get("EnthalpyOfFusion_kJ_kg", 250.0)))
        rho_e0 = float(tm.get("ElectricalResistivity", tm.get("Resistivity_uOhm_cm", 95.0)))
        e0 = float(mm.get("YoungsModulus_GPa", mm.get("EffectiveYoungsModulus", 208.0)))
        sy0 = float(mm.get("YieldStrength_RT_MPa", mm.get("YieldStrength_MPa", 1265.0)))
        nu0 = float(mm.get("PoissonsRatio", mm.get("PoissonRatio", 0.308)))
        g0 = float(mm.get("ShearModulus", e0 / (2.0 * (1.0 + nu0))))
        k_bulk0 = float(mm.get("BulkModulus", e0 / (3.0 * (1.0 - 2.0 * nu0))))
        alpha0 = float(tm.get("CTE_1e6_K", 14.1))

        header_lines = [
            "% =======================================================================",
            "% COMSOL MULTIPHYSICS PIECEWISE & CONTINUOUS MATERIAL FUNCTIONS",
            f"% Property:     {property_name}",
            f"% Alloy System: {alloy_name}",
            f"% Solidus Ts = {ts:.2f} K | Liquidus Tl = {tl:.2f} K | Freezing Window = {delta_t:.2f} K",
            "% =======================================================================",
            ""
        ]

        discrete_intervals: List[Dict[str, Any]] = []
        code_lines: List[str] = list(header_lines)
        smooth_expr = ""

        # 1. Thermal Conductivity
        if "Thermal Conductivity" in property_name:
            k_sol_ts = k0 + 0.0150 * (ts - 293.15)
            k_liq_tl = k_sol_ts * 1.35
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_k(T) [W/(m*K)]",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_k_solid(T)  = {k0:.2f} + 0.0150*(T - 293.15);",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Rule of Mixtures)",
                f"pw_k_mushy(T)  = {k_sol_ts:.2f} + (T - {ts:.1f})/{delta_t:.1f} * ({k_liq_tl:.2f} - {k_sol_ts:.2f});",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K",
                f"pw_k_liquid(T) = {k_liq_tl:.2f} + 0.0065*(T - {tl:.1f});",
                "",
                "% 2. Unified Continuous Step Formulation (flc2hs smoothed transition):",
                f"k_smooth(T) = pw_k_solid(T)*(1 - flc2hs(T - {ts:.1f}, {smooth_w:.1f})) + ...",
                f"              pw_k_mushy(T)*(flc2hs(T - {ts:.1f}, {smooth_w:.1f}) - flc2hs(T - {tl:.1f}, {smooth_w:.1f})) + ...",
                f"              pw_k_liquid(T)*flc2hs(T - {tl:.1f}, {smooth_w:.1f})"
            ])
            smooth_expr = f"pw_k_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_k_mushy(T)*(flc2hs(T-{ts:.1f},{smooth_w:.1f})-flc2hs(T-{tl:.1f},{smooth_w:.1f})) + pw_k_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_k_solid", "t_min": 293.15, "t_max": ts, "expr": f"{k0:.2f} + 0.0150*(T - 293.15)", "desc": "Solid lattice conduction"},
                {"name": "pw_k_mushy", "t_min": ts, "t_max": tl, "expr": f"{k_sol_ts:.2f} + (T - {ts:.1f})/{delta_t:.1f} * {k_liq_tl - k_sol_ts:.2f}", "desc": "Two-phase rule of mixtures"},
                {"name": "pw_k_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{k_liq_tl:.2f} + 0.0065*(T - {tl:.1f})", "desc": "Liquid melt Wiedemann-Franz"}
            ]

        # 2. Specific Heat Capacity
        elif "Specific Heat" in property_name and "Apparent" not in property_name and "Cp_app" not in property_name:
            cp_sol_ts = cp0 + 0.120 * (ts - 293.15)
            cp_liq = cp0 * 1.15
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_Cp(T) [J/(kg*K)] (Sensible Heat)",
                f"% Range 1 (Solid sensible): 293.15 <= T < {ts:.1f} K",
                f"pw_Cp_solid(T)  = {cp0:.1f} + 0.120*(T - 293.15);",
                f"% Range 2 (Mushy transition): {ts:.1f} <= T < {tl:.1f} K",
                f"pw_Cp_mushy(T)  = {cp_sol_ts:.1f} + (T - {ts:.1f})/{delta_t:.1f} * ({cp_liq:.1f} - {cp_sol_ts:.1f});",
                f"% Range 3 (Liquid melt):    {tl:.1f} <= T <= 3000 K",
                f"pw_Cp_liquid(T) = {cp_liq:.1f} + 0.035*(T - {tl:.1f});",
                "",
                "% 2. Continuous Step Blending:",
                f"Cp_smooth(T) = pw_Cp_solid(T)*(1 - flc2hs(T - {ts:.1f}, {smooth_w:.1f})) + pw_Cp_liquid(T)*flc2hs(T - {ts:.1f}, {smooth_w:.1f})"
            ])
            smooth_expr = f"pw_Cp_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_Cp_liquid(T)*flc2hs(T-{ts:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_Cp_solid", "t_min": 293.15, "t_max": ts, "expr": f"{cp0:.1f} + 0.120*(T - 293.15)", "desc": "Solid sensible heat capacity"},
                {"name": "pw_Cp_mushy", "t_min": ts, "t_max": tl, "expr": f"{cp_sol_ts:.1f} + (T - {ts:.1f})/{delta_t:.1f} * {cp_liq - cp_sol_ts:.1f}", "desc": "Mushy transition baseline"},
                {"name": "pw_Cp_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{cp_liq:.1f} + 0.035*(T - {tl:.1f})", "desc": "Liquid melt heat capacity"}
            ]

        # 3. Apparent Heat Capacity (with Latent Heat Peak)
        elif "Cp_app" in property_name or "Apparent Heat Capacity" in property_name:
            cp_app_mushy = cp0 + (dh_fus * 1000.0 / delta_t)
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_Cp_app(T) [J/(kg*K)]",
                "% Apparent Heat Capacity Formulation with Latent Heat Peak",
                f"% Range 1 (Solid sensible): 293.15 <= T < {ts:.1f} K",
                f"pw_Cp_solid(T)  = {cp0:.1f} + 0.120*(T - 293.15);",
                f"% Range 2 (Mushy latent):   {ts:.1f} <= T < {tl:.1f} K (Latent Peak: dH_fus = {dh_fus:.1f} kJ/kg)",
                f"pw_Cp_mushy(T)  = {cp_app_mushy:.1f};   % Base sensible + (dH_fus / delta_T)",
                f"% Range 3 (Liquid melt):    {tl:.1f} <= T <= 3000 K",
                f"pw_Cp_liquid(T) = {cp0 * 1.15:.1f} + 0.035*(T - {tl:.1f});",
                "",
                "% 2. Continuous Gaussian Latent Peak Formulation (COMSOL Heat Transfer Module):",
                f"Cp_app_cont(T) = pw_Cp_solid(T) + ({dh_fus * 1000.0:.1f}/({delta_t:.1f}*sqrt(pi))) * exp(-((T - {(ts+tl)/2.0:.1f})/({smooth_w:.1f}))^2)"
            ])
            smooth_expr = f"pw_Cp_solid(T) + ({dh_fus * 1000.0:.1f}/({delta_t:.1f}*sqrt(pi))) * exp(-((T - {(ts+tl)/2.0:.1f})/({smooth_w:.1f}))^2)"
            discrete_intervals = [
                {"name": "pw_Cp_solid", "t_min": 293.15, "t_max": ts, "expr": f"{cp0:.1f} + 0.120*(T - 293.15)", "desc": "Solid sensible heat capacity"},
                {"name": "pw_Cp_mushy", "t_min": ts, "t_max": tl, "expr": f"{cp_app_mushy:.1f}", "desc": f"Phase change latent peak (dH={dh_fus} kJ/kg)"},
                {"name": "pw_Cp_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{cp0 * 1.15:.1f} + 0.035*(T - {tl:.1f})", "desc": "Liquid melt sensible heat"}
            ]

        # 4. Total Enthalpy
        elif "Total Enthalpy" in property_name or "H(T)" in property_name:
            h_sol_ts = cp0 * (ts - 293.15) * 1e-3
            h_liq_tl = h_sol_ts + dh_fus
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_H(T) [kJ/kg] (Sensible + Latent Enthalpy)",
                f"% Range 1 (Solid state):    293.15 <= T < {ts:.1f} K",
                f"pw_H_solid(T)  = {cp0*1e-3:.3e}*(T - 293.15) + 0.5*1.2e-4*(T - 293.15)^2;",
                f"% Range 2 (Mushy melting):  {ts:.1f} <= T < {tl:.1f} K (Latent Heat Injection)",
                f"pw_H_mushy(T)  = {h_sol_ts:.2f} + (T - {ts:.1f})/{delta_t:.1f} * {dh_fus:.2f};",
                f"% Range 3 (Liquid melt):    {tl:.1f} <= T <= 3000 K",
                f"pw_H_liquid(T) = {h_liq_tl:.2f} + {cp0*1.15*1e-3:.3e}*(T - {tl:.1f});",
                "",
                "% 2. Unified Enthalpy Formulation in COMSOL Heat Transfer Module:",
                f"H_smooth(T) = pw_H_solid(T)*(1 - flc2hs(T - {ts:.1f}, {smooth_w:.1f})) + ...",
                f"              pw_H_mushy(T)*(flc2hs(T - {ts:.1f}, {smooth_w:.1f}) - flc2hs(T - {tl:.1f}, {smooth_w:.1f})) + ...",
                f"              pw_H_liquid(T)*flc2hs(T - {tl:.1f}, {smooth_w:.1f})"
            ])
            smooth_expr = f"pw_H_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_H_mushy(T)*(flc2hs(T-{ts:.1f},{smooth_w:.1f})-flc2hs(T-{tl:.1f},{smooth_w:.1f})) + pw_H_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_H_solid", "t_min": 293.15, "t_max": ts, "expr": f"{cp0*1e-3:.3e}*(T - 293.15) + 6.0e-5*(T - 293.15)^2", "desc": "Solid sensible enthalpy"},
                {"name": "pw_H_mushy", "t_min": ts, "t_max": tl, "expr": f"{h_sol_ts:.2f} + (T - {ts:.1f})/{delta_t:.1f} * {dh_fus:.2f}", "desc": "Mushy latent heat absorption"},
                {"name": "pw_H_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{h_liq_tl:.2f} + {cp0*1.15*1e-3:.3e}*(T - {tl:.1f})", "desc": "Superheated melt enthalpy"}
            ]

        # 5. Mass Density
        elif "Mass Density" in property_name or "rho(T)" in property_name:
            rho_sol_ts = rho0 / (1.0 + 3.0 * 1.4e-5 * (ts - 293.15))
            rho_liq_tl = rho_sol_ts * 0.948
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_rho(T) [g/cm^3]",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K (Thermal Expansion)",
                f"pw_rho_solid(T)  = {rho0:.3f} / (1 + 4.2e-5*(T - 293.15));",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Volume Expansion on Melting)",
                f"pw_rho_mushy(T)  = {rho_sol_ts:.3f} - (T - {ts:.1f})/{delta_t:.1f} * ({rho_sol_ts:.3f} - {rho_liq_tl:.3f});",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K",
                f"pw_rho_liquid(T) = {rho_liq_tl:.3f} * (1 - 8.5e-5*(T - {tl:.1f}));",
                "",
                "% 2. Smooth Blended Formulation:",
                f"rho_smooth(T) = pw_rho_solid(T) + (pw_rho_liquid(T) - pw_rho_solid(T))*flc2hs(T - {(ts+tl)/2.0:.1f}, {smooth_w:.1f})"
            ])
            smooth_expr = f"pw_rho_solid(T) + (pw_rho_liquid(T) - pw_rho_solid(T))*flc2hs(T - {(ts+tl)/2.0:.1f}, {smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_rho_solid", "t_min": 293.15, "t_max": ts, "expr": f"{rho0:.3f} / (1 + 4.2e-5*(T - 293.15))", "desc": "Solid lattice density"},
                {"name": "pw_rho_mushy", "t_min": ts, "t_max": tl, "expr": f"{rho_sol_ts:.3f} - (T - {ts:.1f})/{delta_t:.1f} * {rho_sol_ts - rho_liq_tl:.3f}", "desc": "Phase-change dilation"},
                {"name": "pw_rho_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{rho_liq_tl:.3f} * (1 - 8.5e-5*(T - {tl:.1f}))", "desc": "Liquid melt thermal contraction"}
            ]

        # 6. Thermal Diffusivity
        elif "Thermal Diffusivity" in property_name:
            alpha_diff0 = (k0 / (rho0 * 1e3 * cp0)) * 1e6
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_alpha(T) [mm^2/s]",
                "% Derived via alpha(T) = k(T) / [rho(T) * Cp(T)]",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_alpha_solid(T)  = {alpha_diff0:.3f} - 0.00085*(T - 293.15);",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Apparent Diffusivity Drop)",
                f"pw_alpha_mushy(T)  = {alpha_diff0 * 0.25:.3f};",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K",
                f"pw_alpha_liquid(T) = {alpha_diff0 * 0.65:.3f} + 0.00030*(T - {tl:.1f});"
            ])
            smooth_expr = f"pw_alpha_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_alpha_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_alpha_solid", "t_min": 293.15, "t_max": ts, "expr": f"{alpha_diff0:.3f} - 0.00085*(T - 293.15)", "desc": "Solid phonon diffusivity"},
                {"name": "pw_alpha_mushy", "t_min": ts, "t_max": tl, "expr": f"{alpha_diff0 * 0.25:.3f}", "desc": "Latent plateau suppression"},
                {"name": "pw_alpha_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{alpha_diff0 * 0.65:.3f} + 0.00030*(T - {tl:.1f})", "desc": "Liquid melt thermal diffusivity"}
            ]

        # 7. Linear Thermal Expansion CTE
        elif "Linear Thermal Expansion" in property_name or "CTE" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_alpha_L(T) [1e-6/K] (Coefficient of Thermal Expansion)",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K (Gruneisen Solid Lattice)",
                f"pw_alphaL_solid(T)  = {alpha0:.2f} + 0.0040*(T - 293.15);",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Pre-melting dilation)",
                f"pw_alphaL_mushy(T)  = {alpha0 + 0.0040*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 15.0;",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K (Liquid bulk expansivity / 3)",
                "pw_alphaL_liquid(T) = 36.5 [1e-6/K];",
                "",
                "% 2. Continuous Solid Mechanics Formulation:",
                f"alphaL_eff(T) = pw_alphaL_solid(T)*(1 - flc2hs(T - {ts:.1f}, {smooth_w:.1f})) + pw_alphaL_liquid(T)*flc2hs(T - {ts:.1f}, {smooth_w:.1f})"
            ])
            smooth_expr = f"pw_alphaL_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + 36.5*flc2hs(T-{ts:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_alphaL_solid", "t_min": 293.15, "t_max": ts, "expr": f"{alpha0:.2f} + 0.0040*(T - 293.15)", "desc": "Anharmonic lattice expansion"},
                {"name": "pw_alphaL_mushy", "t_min": ts, "t_max": tl, "expr": f"{alpha0 + 0.0040*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 15.0", "desc": "Premelting volumetric jump"},
                {"name": "pw_alphaL_liquid", "t_min": tl, "t_max": 3000.0, "expr": "36.50", "desc": "Liquid melt expansivity"}
            ]

        # 8. Volumetric Thermal Expansion
        elif "Volumetric" in property_name or "beta(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_beta(T) [1e-6/K] (Volumetric Expansion beta = 3*alpha_L)",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_beta_solid(T)  = 3.0 * ({alpha0:.2f} + 0.0040*(T - 293.15));",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Melting Volumetric Jump)",
                f"pw_beta_mushy(T)  = 3.0 * {alpha0 + 0.0040*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 50.0;",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K (Melt Thermal Expansivity)",
                "pw_beta_liquid(T) = 110.0 [1e-6/K];"
            ])
            smooth_expr = f"3.0*pw_alphaL_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + 110.0*flc2hs(T-{ts:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_beta_solid", "t_min": 293.15, "t_max": ts, "expr": f"3.0 * ({alpha0:.2f} + 0.0040*(T - 293.15))", "desc": "Solid volumetric expansion"},
                {"name": "pw_beta_mushy", "t_min": ts, "t_max": tl, "expr": f"{3.0*(alpha0 + 0.004*(ts-293.15)):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 50.0", "desc": "Melting volume dilation"},
                {"name": "pw_beta_liquid", "t_min": tl, "t_max": 3000.0, "expr": "110.0", "desc": "Superheated melt volumetric expansion"}
            ]

        # 9. Thermal Strain
        elif "Thermal Strain" in property_name or "dl/l0" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_thermal_strain(T) [%] (Delta L / L0)",
                f"% Range 1 (Solid state):    293.15 <= T < {ts:.1f} K (Elastic Thermal Strain)",
                f"pw_thstrain_solid(T)  = ({alpha0:.2f}*1e-4*(T - 293.15) + 0.5*4e-7*(T - 293.15)^2);",
                f"% Range 2 (Mushy softening): {ts:.1f} <= T < {tl:.1f} K",
                f"pw_thstrain_mushy(T)  = ({alpha0:.2f}*1e-4*({ts:.1f}-293.15)) + (T - {ts:.1f})/{delta_t:.1f} * 1.5;",
                f"% Range 3 (Liquid state):   T >= {tl:.1f} K (Hydrodynamic Zero Shear Stress)",
                f"pw_thstrain_liquid(T) = ({alpha0:.2f}*1e-4*({ts:.1f}-293.15)) + 1.5;"
            ])
            smooth_expr = f"pw_thstrain_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_thstrain_liquid(T)*flc2hs(T-{ts:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_thstrain_solid", "t_min": 293.15, "t_max": ts, "expr": f"{alpha0:.2f}*1e-4*(T - 293.15) + 2.0e-7*(T - 293.15)^2", "desc": "Solid elastic thermal strain"},
                {"name": "pw_thstrain_mushy", "t_min": ts, "t_max": tl, "expr": f"{alpha0*1e-4*(ts-293.15):.4f} + (T - {ts:.1f})/{delta_t:.1f} * 1.5", "desc": "Mushy transition dilation"},
                {"name": "pw_thstrain_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{alpha0*1e-4*(ts-293.15) + 1.5:.4f}", "desc": "Liquid melt maximum dilation plateau"}
            ]

        # 10. Electrical Resistivity
        elif "Electrical Resistivity" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_rho_e(T) [uOhm*cm]",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K (Bloch-Gruneisen / Nordheim)",
                f"pw_rhoe_solid(T)  = {rho_e0:.2f} + 0.042*(T - 293.15);",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K",
                f"pw_rhoe_mushy(T)  = {rho_e0 + 0.042*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 25.0;",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K",
                f"pw_rhoe_liquid(T) = {rho_e0 + 0.042*(ts-293.15) + 25.0:.2f} + 0.018*(T - {tl:.1f});"
            ])
            smooth_expr = f"pw_rhoe_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_rhoe_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_rhoe_solid", "t_min": 293.15, "t_max": ts, "expr": f"{rho_e0:.2f} + 0.042*(T - 293.15)", "desc": "Solid electron scattering"},
                {"name": "pw_rhoe_mushy", "t_min": ts, "t_max": tl, "expr": f"{rho_e0 + 0.042*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 25.0", "desc": "Mushy disorder jump"},
                {"name": "pw_rhoe_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{rho_e0 + 0.042*(ts-293.15) + 25.0:.2f} + 0.018*(T - {tl:.1f})", "desc": "Liquid melt resistivity"}
            ]

        # 11. Electrical Conductivity
        elif "Electrical Conductivity" in property_name or "sigma_elec" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_sigma_elec(T) [MS/m] (AC/DC Module)",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_sigma_solid(T)  = 100.0 / ({rho_e0:.2f} + 0.042*(T - 293.15));",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K",
                f"pw_sigma_mushy(T)  = 100.0 / ({rho_e0 + 0.042*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 25.0);",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K",
                f"pw_sigma_liquid(T) = 100.0 / ({rho_e0 + 0.042*(ts-293.15) + 25.0:.2f} + 0.018*(T - {tl:.1f}));"
            ])
            smooth_expr = f"100.0 / (pw_rhoe_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_rhoe_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f}))"
            discrete_intervals = [
                {"name": "pw_sigma_solid", "t_min": 293.15, "t_max": ts, "expr": f"100.0 / ({rho_e0:.2f} + 0.042*(T - 293.15))", "desc": "Solid electrical conductivity"},
                {"name": "pw_sigma_mushy", "t_min": ts, "t_max": tl, "expr": f"100.0 / ({rho_e0 + 0.042*(ts-293.15):.2f} + (T - {ts:.1f})/{delta_t:.1f} * 25.0)", "desc": "Mushy electrical conductivity"},
                {"name": "pw_sigma_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"100.0 / ({rho_e0 + 0.042*(ts-293.15) + 25.0:.2f} + 0.018*(T - {tl:.1f}))", "desc": "Liquid melt conductivity"}
            ]

        # 12. Young's Elastic Modulus
        elif "Young" in property_name or "E(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_E(T) [GPa]",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K (Thermal Softening)",
                f"pw_E_solid(T)  = max(5.0, {e0:.1f} * (1 - 0.45*(T / {ts:.1f})));",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Cohesion Loss)",
                f"pw_E_mushy(T)  = {max(5.0, e0*0.55):.1f} * (1 - (T - {ts:.1f})/{delta_t:.1f});",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K (Hydrodynamic Zero)",
                "pw_E_liquid(T) = 0.0 [GPa];",
                "",
                "% 2. Continuous Solid-Liquid Cutoff:",
                f"E_eff(T) = pw_E_solid(T)*(1 - flc2hs(T - {ts:.1f}, 10.0))"
            ])
            smooth_expr = f"pw_E_solid(T)*(1 - flc2hs(T - {ts:.1f}, 10.0))"
            discrete_intervals = [
                {"name": "pw_E_solid", "t_min": 293.15, "t_max": ts, "expr": f"max(5.0, {e0:.1f} * (1 - 0.45*(T / {ts:.1f})))", "desc": "Lattice thermal softening"},
                {"name": "pw_E_mushy", "t_min": ts, "t_max": tl, "expr": f"{max(5.0, e0*0.55):.1f} * (1 - (T - {ts:.1f})/{delta_t:.1f})", "desc": "Semi-solid cohesion loss"},
                {"name": "pw_E_liquid", "t_min": tl, "t_max": 3000.0, "expr": "0.0", "desc": "Hydrodynamic zero shear stiffness"}
            ]

        # 13. Shear Modulus
        elif "Shear Modulus" in property_name or "G(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_G(T) [GPa] (Shear Modulus G = E / [2*(1+nu)])",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_G_solid(T)  = max(2.0, {g0:.1f} * (1 - 0.48*(T / {ts:.1f})));",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Rigidity Loss)",
                f"pw_G_mushy(T)  = {max(2.0, g0*0.50):.1f} * (1 - (T - {ts:.1f})/{delta_t:.1f});",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K",
                "pw_G_liquid(T) = 0.0 [GPa];",
                "",
                "% 2. Continuous Cutoff:",
                f"G_eff(T) = pw_G_solid(T)*(1 - flc2hs(T - {ts:.1f}, 10.0))"
            ])
            smooth_expr = f"pw_G_solid(T)*(1 - flc2hs(T - {ts:.1f}, 10.0))"
            discrete_intervals = [
                {"name": "pw_G_solid", "t_min": 293.15, "t_max": ts, "expr": f"max(2.0, {g0:.1f} * (1 - 0.48*(T / {ts:.1f})))", "desc": "Solid shear stiffness"},
                {"name": "pw_G_mushy", "t_min": ts, "t_max": tl, "expr": f"{max(2.0, g0*0.50):.1f} * (1 - (T - {ts:.1f})/{delta_t:.1f})", "desc": "Two-phase rigidity degradation"},
                {"name": "pw_G_liquid", "t_min": tl, "t_max": 3000.0, "expr": "0.0", "desc": "Hydrodynamic zero shear modulus"}
            ]

        # 14. Bulk Modulus
        elif "Bulk Modulus" in property_name or "K(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_K(T) [GPa] (Bulk Modulus K = E / [3*(1-2*nu)])",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_K_solid(T)  = {k_bulk0:.1f} * (1 - 0.32*(T / {ts:.1f}));",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K",
                f"pw_K_mushy(T)  = {k_bulk0*0.68:.1f} - (T - {ts:.1f})/{delta_t:.1f} * ({k_bulk0*0.68:.1f} - {k_bulk0*0.50:.1f});",
                f"% Range 3 (Liquid melt):   {tl:.1f} <= T <= 3000 K (Liquid bulk incompressibility)",
                f"pw_K_liquid(T) = {k_bulk0*0.50:.1f} [GPa];"
            ])
            smooth_expr = f"pw_K_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_K_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_K_solid", "t_min": 293.15, "t_max": ts, "expr": f"{k_bulk0:.1f} * (1 - 0.32*(T / {ts:.1f}))", "desc": "Solid incompressibility"},
                {"name": "pw_K_mushy", "t_min": ts, "t_max": tl, "expr": f"{k_bulk0*0.68:.1f} - (T - {ts:.1f})/{delta_t:.1f} * {k_bulk0*0.18:.1f}", "desc": "Phase transition bulk modulus"},
                {"name": "pw_K_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"{k_bulk0*0.50:.1f}", "desc": "Melt acoustic bulk incompressibility"}
            ]

        # 15. Poisson's Ratio
        elif "Poisson" in property_name or "nu(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_nu(T) [-] (Poisson's Ratio)",
                f"% Range 1 (Solid phase):   293.15 <= T < {ts:.1f} K",
                f"pw_nu_solid(T)  = min(0.42, {nu0:.3f} + 3.5e-5*(T - 293.15));",
                f"% Range 2 (Mushy transition): {ts:.1f} <= T < {tl:.1f} K",
                f"pw_nu_mushy(T)  = {min(0.42, nu0 + 3.5e-5*(ts-293.15)):.3f} + (T - {ts:.1f})/{delta_t:.1f} * (0.499 - {min(0.42, nu0 + 3.5e-5*(ts-293.15)):.3f});",
                f"% Range 3 (Liquid melt):    {tl:.1f} <= T <= 3000 K (Nearly Incompressible Fluid)",
                "pw_nu_liquid(T) = 0.499 [-];"
            ])
            smooth_expr = f"pw_nu_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + 0.499*flc2hs(T-{ts:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_nu_solid", "t_min": 293.15, "t_max": ts, "expr": f"min(0.42, {nu0:.3f} + 3.5e-5*(T - 293.15))", "desc": "Solid transverse contraction"},
                {"name": "pw_nu_mushy", "t_min": ts, "t_max": tl, "expr": f"{min(0.42, nu0 + 3.5e-5*(ts-293.15)):.3f} + (T - {ts:.1f})/{delta_t:.1f} * {0.499 - min(0.42, nu0 + 3.5e-5*(ts-293.15)):.3f}", "desc": "Fluidization transition"},
                {"name": "pw_nu_liquid", "t_min": tl, "t_max": 3000.0, "expr": "0.499", "desc": "Incompressible fluid limit"}
            ]

        # 16. Yield Strength
        elif "Yield Strength" in property_name or "sigma_y" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_sigma_y(T) [MPa]",
                f"% Range 1 (Solid thermal regime):  293.15 <= T < {0.5*ts:.1f} K",
                f"pw_sy_athermal(T) = {sy0:.1f} * max(0.04, (1 - ((T/850)^(2/3))));",
                f"% Range 2 (High-T creep regime):   {0.5*ts:.1f} <= T < {ts:.1f} K (Dislocation Climb)",
                f"pw_sy_creep(T)    = {sy0 * 2.5:.1f} * exp(-280e3 / (8.314 * T));",
                f"% Range 3 (Liquid melt):           T >= {ts:.1f} K",
                "pw_sy_liquid(T)   = 0.0 [MPa];"
            ])
            smooth_expr = f"pw_sy_athermal(T)*(1-flc2hs(T-{0.5*ts:.1f},15.0)) + pw_sy_creep(T)*(flc2hs(T-{0.5*ts:.1f},15.0)-flc2hs(T-{ts:.1f},10.0))"
            discrete_intervals = [
                {"name": "pw_sy_athermal", "t_min": 293.15, "t_max": 0.5*ts, "expr": f"{sy0:.1f} * max(0.04, (1 - ((T/850)^(2/3))))", "desc": "Low-T thermal barrier strength"},
                {"name": "pw_sy_creep", "t_min": 0.5*ts, "t_max": ts, "expr": f"{sy0 * 2.5:.1f} * exp(-280e3 / (8.314 * T))", "desc": "High-T thermally activated climb"},
                {"name": "pw_sy_liquid", "t_min": ts, "t_max": 3000.0, "expr": "0.0", "desc": "Melt zero shear yield stress"}
            ]

        # 17. Dynamic Viscosity
        elif "Dynamic Viscosity" in property_name or "mu(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_mu(T) [Pa*s] (Semi-solid & Melt Rheology)",
                f"% Range 1 (Solid state):    T < {ts:.1f} K (Rigid boundary limit)",
                "pw_mu_solid(T)  = 1e6 [Pa*s];",
                f"% Range 2 (Mushy window):   {ts:.1f} <= T < {tl:.1f} K (Krieger-Dougherty Semi-Solid)",
                f"pw_mu_mushy(T)  = 0.0050 * (1 - ({tl:.1f} - T)/{delta_t:.1f} / 0.65)^(-1.625);",
                f"% Range 3 (Liquid melt):    T >= {tl:.1f} K (Arrhenius-Andrade hydrodynamic)",
                "pw_mu_liquid(T) = 0.0050 * exp(3500 / T);"
            ])
            smooth_expr = f"pw_mu_mushy(T)*(1-flc2hs(T-{tl:.1f},{smooth_w:.1f})) + pw_mu_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_mu_solid", "t_min": 293.15, "t_max": ts, "expr": "1.0e6", "desc": "Rigid solid ceiling"},
                {"name": "pw_mu_mushy", "t_min": ts, "t_max": tl, "expr": f"0.0050 * (1 - ({tl:.1f} - T)/{delta_t:.1f} / 0.65)^(-1.625)", "desc": "Krieger-Dougherty semi-solid slurry"},
                {"name": "pw_mu_liquid", "t_min": tl, "t_max": 3000.0, "expr": "0.0050 * exp(3500 / T)", "desc": "Andrade liquid hydrodynamic viscosity"}
            ]

        # 18. Kinematic Viscosity
        elif "Kinematic Viscosity" in property_name or "nu_kin" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_nu_kin(T) [m^2/s] (nu_kin = mu / rho)",
                f"% Range 1 (Solid state):    T < {ts:.1f} K (Rigid boundary limit)",
                "pw_nukin_solid(T)  = 1.0 [m^2/s];",
                f"% Range 2 (Mushy window):   {ts:.1f} <= T < {tl:.1f} K",
                f"pw_nukin_mushy(T)  = (0.0050 * (1 - ({tl:.1f} - T)/{delta_t:.1f} / 0.65)^(-1.625)) / ({rho0:.3f} * 1e3);",
                f"% Range 3 (Liquid melt):    T >= {tl:.1f} K",
                f"pw_nukin_liquid(T) = (0.0050 * exp(3500 / T)) / ({rho0 * 0.948:.3f} * 1e3);"
            ])
            smooth_expr = f"pw_nukin_mushy(T)*(1-flc2hs(T-{tl:.1f},{smooth_w:.1f})) + pw_nukin_liquid(T)*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_nukin_solid", "t_min": 293.15, "t_max": ts, "expr": "1.0", "desc": "Solid boundary kinematic ceiling"},
                {"name": "pw_nukin_mushy", "t_min": ts, "t_max": tl, "expr": f"(0.0050 * (1 - ({tl:.1f}-T)/{delta_t:.1f}/0.65)^(-1.625)) / ({rho0*1e3:.1f})", "desc": "Semi-solid kinematic resistance"},
                {"name": "pw_nukin_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"(0.0050 * exp(3500/T)) / ({rho0*0.948*1e3:.1f})", "desc": "Liquid melt kinematic momentum diffusivity"}
            ]

        # 19. Surface Tension (Marangoni)
        elif "Surface Tension" in property_name or "gamma(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_gamma(T) [N/m] (Melt Surface Tension & Marangoni)",
                f"% Range 1 (Solid phase):   T < {ts:.1f} K",
                "pw_gamma_solid(T)  = 0.0 [N/m];",
                f"% Range 2 (Mushy window):  {ts:.1f} <= T < {tl:.1f} K (Free-surface onset)",
                f"pw_gamma_mushy(T)  = 1.75 * (T - {ts:.1f})/{delta_t:.1f};",
                f"% Range 3 (Liquid melt):   T >= {tl:.1f} K (Marangoni Effect: dgamma/dT = -0.38 mN/(m*K))",
                f"pw_gamma_liquid(T) = 1.75 - 0.00038 * (T - {tl:.1f});",
                "",
                "% 2. Marangoni Shear Stress Boundary Condition for Melt Pool CFD:",
                "sigma_tangential = -0.00038 * d(T, tangential_coord) [N/m^2]"
            ])
            smooth_expr = f"1.75*flc2hs(T-{ts:.1f},{smooth_w:.1f}) - 0.00038*(T-{tl:.1f})*flc2hs(T-{tl:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_gamma_solid", "t_min": 293.15, "t_max": ts, "expr": "0.0", "desc": "Solid internal cohesive state"},
                {"name": "pw_gamma_mushy", "t_min": ts, "t_max": tl, "expr": f"1.75 * (T - {ts:.1f})/{delta_t:.1f}", "desc": "Liquid film meniscus onset"},
                {"name": "pw_gamma_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"1.75 - 0.00038 * (T - {tl:.1f})", "desc": "Negative Marangoni surface tension slope"}
            ]

        # 20. Laser Optical Absorptivity
        elif "Absorptivity" in property_name or "A(T)" in property_name:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_A(T) [-] (Laser Optical Coupling 1064 nm Fiber)",
                f"% Range 1 (Solid room temp): 293.15 <= T < {ts:.1f} K (Hagen-Rubens Conduction Band)",
                "pw_A_solid(T)  = min(0.48, 0.32 * sqrt(T / 293.15));",
                f"% Range 2 (Mushy window):   {ts:.1f} <= T < {tl:.1f} K (Reflectivity drop on melting)",
                f"pw_A_mushy(T)  = 0.32*sqrt({ts:.1f}/293.15) + (T - {ts:.1f})/{delta_t:.1f} * 0.08;",
                f"% Range 3 (Liquid melt):    T >= {tl:.1f} K (Plasma & Keyhole Absorptance)",
                f"pw_A_liquid(T) = 0.44 + 0.00003*(T - {tl:.1f});"
            ])
            smooth_expr = f"pw_A_solid(T)*(1-flc2hs(T-{ts:.1f},{smooth_w:.1f})) + pw_A_liquid(T)*flc2hs(T-{ts:.1f},{smooth_w:.1f})"
            discrete_intervals = [
                {"name": "pw_A_solid", "t_min": 293.15, "t_max": ts, "expr": "min(0.48, 0.32 * sqrt(T / 293.15))", "desc": "Hagen-Rubens electronic absorption"},
                {"name": "pw_A_mushy", "t_min": ts, "t_max": tl, "expr": f"{0.32*math.sqrt(ts/293.15):.3f} + (T - {ts:.1f})/{delta_t:.1f} * 0.08", "desc": "Melting reflectivity decrease"},
                {"name": "pw_A_liquid", "t_min": tl, "t_max": 3000.0, "expr": f"0.44 + 0.00003*(T - {tl:.1f})", "desc": "Melt pool & keyhole laser coupling"}
            ]

        # 21. Total Hemispherical Emissivity
        else:
            code_lines.extend([
                "% 1. COMSOL Piecewise Definition: pw_epsilon(T) [-] (Total Hemispherical Surface Emissivity)",
                f"% Range 1 (Solid clean):    293.15 <= T < {0.6*ts:.1f} K",
                "pw_eps_solid(T)  = 0.28 + 0.00015*(T - 293.15);",
                f"% Range 2 (Oxidation scale): {0.6*ts:.1f} <= T < {ts:.1f} K (Thermal oxide scale growth)",
                f"pw_eps_oxidized(T) = min(0.85, 0.28 + 0.00015*({0.6*ts:.1f}-293.15) + 0.00045*(T - {0.6*ts:.1f}));",
                f"% Range 3 (Liquid melt):    T >= {ts:.1f} K (Liquid metal radiation)",
                f"pw_eps_liquid(T) = 0.38 + 0.00006*(T - {ts:.1f});"
            ])
            smooth_expr = f"pw_eps_solid(T)*(1-flc2hs(T-{0.6*ts:.1f},15.0)) + pw_eps_oxidized(T)*(flc2hs(T-{0.6*ts:.1f},15.0)-flc2hs(T-{ts:.1f},10.0)) + pw_eps_liquid(T)*flc2hs(T-{ts:.1f},10.0)"
            discrete_intervals = [
                {"name": "pw_eps_solid", "t_min": 293.15, "t_max": 0.6*ts, "expr": "0.28 + 0.00015*(T - 293.15)", "desc": "Bare metallic surface radiation"},
                {"name": "pw_eps_oxidized", "t_min": 0.6*ts, "t_max": ts, "expr": f"min(0.85, {0.28 + 0.00015*(0.6*ts-293.15):.3f} + 0.00045*(T - {0.6*ts:.1f}))", "desc": "Chromia/spinel oxide layer growth"},
                {"name": "pw_eps_liquid", "t_min": ts, "t_max": 3000.0, "expr": f"0.38 + 0.00006*(T - {ts:.1f})", "desc": "Liquid metal radiative emission"}
            ]

        return {
            "property_name": property_name,
            "alloy_name": alloy_name,
            "ts": ts,
            "tl": tl,
            "delta_t": delta_t,
            "smooth_width": smooth_w,
            "code_text": "\n".join(code_lines),
            "smooth_expression": smooth_expr,
            "discrete_intervals": discrete_intervals
        }

    @classmethod
    def generate_all_properties(
        cls,
        thermo_metrics: Dict[str, Any],
        mech_metrics: Optional[Dict[str, Any]] = None,
        alloy_name: str = "Alloy-System"
    ) -> Dict[str, Dict[str, Any]]:
        """Generates piecewise definitions for all 21 properties in one batch."""
        res = {}
        for prop in PROPERTIES_LIST:
            res[prop] = cls.generate_property_piecewise(prop, thermo_metrics, mech_metrics, alloy_name)
        return res
