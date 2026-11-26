# -*- coding: utf-8 -*-
"""
cae_export_manager.py - Commercial CAE / FEA Material Card Exporter.

Generates compliant solver material definitions for:
  1. Transvalor FORGE (.mat) - Hansel-Spittel constitutive rheology and thermal tables
  2. SFTC DEFORM Forming (.dat) - 3D flow-stress interpolation matrix (strain, rate, temperature)
  3. Simufact Forming / MSC Marc (.xml) - MatildA XML material definition
  4. Dassault Abaqus (.inp) - *MATERIAL isotropic elastic/plastic/thermal deck
  5. ANSYS APDL (.txt) - /PREP7 MPDATA temperature-dependent cards
  6. COMSOL Multiphysics (.txt) - Temperature-indexed piecewise interpolation tables
"""

from html import escape as _xml_escape
import math
import os
from typing import Any, Dict, Optional


class CAEExportManager:
    """
    Manages export and preview generation of CALPHAD thermophysical, mechanical,
    and flow-stress predictions for commercial FEA and forming solvers.
    """

    @staticmethod
    def _write_optional_file(filepath: Optional[str], content: str,
                             return_path_when_written: bool = False) -> str:
        """
        Writes card content to disk when a non-empty path is given; otherwise returns
        the generated card text directly for live preview and IPC transport.
        """
        if filepath and str(filepath).strip():
            abs_path = os.path.abspath(filepath)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as handle:
                handle.write(content)
            return filepath if return_path_when_written else content
        return content

    @staticmethod
    def _extract_common_props(thermo: Optional[Dict[str, Any]],
                              mech: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Normalizes shared thermomechanical quantities across solver exporters."""
        th = thermo or {}
        mc = mech or {}
        ys_mpa = float(mc.get("YieldStrength_MPa", mc.get("YieldStrength_RT_MPa", mc.get("sigma_y_rt", 450.0))))
        uts_mpa = float(mc.get("UTS_MPa", mc.get("UTS_RT_MPa", mc.get("sigma_uts_rt", ys_mpa * 1.35))))
        e_gpa = float(mc.get("YoungsModulus_GPa", 210.0))
        nu = float(mc.get("PoissonRatio", 0.30))
        rho_kg_m3 = float(th.get("Density_g_cm3", th.get("TheoreticalDensity_g_cm3", th.get("density", 8.2)))) * 1000.0
        sol_k = float(th.get("Solidus_K", th.get("T_Solidus", 1600.0)))
        liq_k = float(th.get("Liquidus_K", th.get("T_Liquidus", 1700.0)))
        return {
            "ys_mpa": ys_mpa,
            "uts_mpa": max(ys_mpa, uts_mpa),
            "e_gpa": e_gpa,
            "nu": nu,
            "rho_kg_m3": rho_kg_m3,
            "sol_k": sol_k,
            "liq_k": max(sol_k + 10.0, liq_k),
        }

    @staticmethod
    def compute_hansel_spittel_params(alloy_name: str, thermo: Optional[Dict[str, Any]],
                                      mech: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """
        Computes Hansel-Spittel flow-stress parameters:
        sigma = A * exp(m1 * T) * eps^m2 * exp(m4 / eps) * (eps_dot)^m3, where T is in deg C.
        """
        th = thermo or {}
        mc = mech or {}
        base_yield = float(mc.get("YieldStrength_MPa", mc.get("YieldStrength_RT_MPa", 450.0)))
        _ = float(th.get("Solidus_K", th.get("T_Solidus", 1600.0))) - 273.15

        name_lower = (alloy_name or "").lower()
        if "nickel" in name_lower or "inconel" in name_lower:
            a_coeff, m1, m2, m3, m4 = base_yield * 2.8, -0.0028, 0.14, 0.12, -0.008
        elif "steel" in name_lower or "iron" in name_lower:
            a_coeff, m1, m2, m3, m4 = base_yield * 2.2, -0.0032, 0.16, 0.10, -0.005
        elif "titanium" in name_lower:
            a_coeff, m1, m2, m3, m4 = base_yield * 2.5, -0.0035, 0.18, 0.14, -0.010
        elif "aluminium" in name_lower or "aluminum" in name_lower:
            a_coeff, m1, m2, m3, m4 = base_yield * 1.9, -0.0045, 0.12, 0.08, -0.003
        else:
            a_coeff, m1, m2, m3, m4 = base_yield * 2.4, -0.0030, 0.15, 0.11, -0.006

        return {
            "A": round(a_coeff, 2),
            "m1": m1,
            "m2": m2,
            "m3": m3,
            "m4": m4,
            "m5": 0.0,
            "m7": 0.0,
            "m8": 0.0,
            "m9": 0.0,
        }

    @staticmethod
    def export_forge(filepath: Optional[str], alloy_name: str, comp: Dict[str, float],
                     thermo: Optional[Dict[str, Any]] = None,
                     mech: Optional[Dict[str, Any]] = None) -> str:
        """
        Exports material card for Transvalor FORGE (.mat format).
        Returns `filepath` when written to disk, or card text when `filepath` is empty.
        """
        comp = comp or {}
        props = CAEExportManager._extract_common_props(thermo, mech)
        hs = CAEExportManager.compute_hansel_spittel_params(alloy_name, thermo, mech)

        temps_c = [20, 200, 400, 600, 800, 1000, 1100, 1200]
        rho0 = props["rho_kg_m3"]
        densities = [rho0 - 0.35 * tc for tc in temps_c]
        conductivities = [14.0 + 0.012 * tc for tc in temps_c]
        specific_heats = [450.0 + 0.18 * tc for tc in temps_c]

        comp_str = ", ".join(f"{k}: {v:.2f}%" for k, v in comp.items())
        lines = [
            "# ========================================================================",
            "# TRANSVALOR FORGE MATERIAL DATA CARD (.MAT)",
            f"# Material: {alloy_name}",
            f"# Chemical Composition (wt%): {comp_str}",
            "# Generated by PyCALPHAD Scientific Materials Design Suite",
            "# ========================================================================",
            "",
            "[GENERAL]",
            f'MATERIAL_NAME = "{alloy_name}"',
            f"SOLIDUS_TEMPERATURE_C = {props['sol_k'] - 273.15:.2f}",
            f"LIQUIDUS_TEMPERATURE_C = {props['liq_k'] - 273.15:.2f}",
            f"POISSON_RATIO = {props['nu']:.3f}",
            f"YOUNG_MODULUS_GPA = {props['e_gpa']:.1f}",
            "",
            "[RHEOLOGY_HANSEL_SPITTEL]",
            "# sigma = A * exp(m1*T) * eps^m2 * exp(m4/eps) * (eps_dot)^m3",
            f"A  = {hs['A']:.2f}",
            f"m1 = {hs['m1']:.6f}",
            f"m2 = {hs['m2']:.4f}",
            f"m3 = {hs['m3']:.4f}",
            f"m4 = {hs['m4']:.4f}",
            "",
            "[THERMAL_PROPERTIES]",
            "# Temperature [C]\tDensity [kg/m^3]\tConductivity [W/(m*K)]\tSpecific Heat [J/(kg*K)]",
        ]
        for tc, rho, k_val, cp_val in zip(temps_c, densities, conductivities, specific_heats):
            lines.append(f"{tc:8.1f}\t{rho:12.1f}\t{k_val:16.2f}\t{cp_val:16.2f}")

        content = "\n".join(lines) + "\n"
        return CAEExportManager._write_optional_file(filepath, content, return_path_when_written=True)

    @staticmethod
    def export_abaqus(filepath: Optional[str], alloy_name: str, comp: Dict[str, float],
                      thermo: Optional[Dict[str, Any]] = None,
                      mech: Optional[Dict[str, Any]] = None) -> str:
        """Exports Abaqus INP material definition card and returns its text content."""
        comp = comp or {}
        props = CAEExportManager._extract_common_props(thermo, mech)

        lines = [
            "** ===========================================================",
            f"** ABAQUS CAE MATERIAL CARD: {alloy_name}",
            f"** Chemical Composition: {comp}",
            "** Generated by CALPHAD XOC",
            "** ===========================================================",
            f"*MATERIAL, NAME={alloy_name.replace(' ', '_')}",
            "*DENSITY",
            f" {props['rho_kg_m3']:.1f}, 20.0",
            "*ELASTIC, TYPE=ISOTROPIC",
            f" {props['e_gpa'] * 1e9:.3e}, {props['nu']:.3f}, 20.0",
            "*EXPANSION, ZERO=20.0",
            " 1.35e-05, 20.0",
            "*CONDUCTIVITY",
            " 16.5, 20.0",
            "*SPECIFIC HEAT",
            " 460.0, 20.0",
            "*PLASTIC",
            f" {props['ys_mpa'] * 1e6:.3e}, 0.00, 20.0",
            f" {props['uts_mpa'] * 1e6:.3e}, 0.15, 20.0",
        ]
        content = "\n".join(lines) + "\n"
        return CAEExportManager._write_optional_file(filepath, content, return_path_when_written=False)

    @staticmethod
    def export_ansys(filepath: Optional[str], alloy_name: str, comp: Dict[str, float],
                     thermo: Optional[Dict[str, Any]] = None,
                     mech: Optional[Dict[str, Any]] = None) -> str:
        """Exports ANSYS APDL material parameter deck and returns its text content."""
        comp = comp or {}
        props = CAEExportManager._extract_common_props(thermo, mech)
        e_pa = props["e_gpa"] * 1e9
        rho = props["rho_kg_m3"]
        nu = props["nu"]

        lines = [
            "! ===========================================================",
            f"! ANSYS APDL MATERIAL DECK: {alloy_name}",
            f"! Chemical Composition: {comp}",
            "! Generated by CALPHAD XOC",
            "! ===========================================================",
            "/PREP7",
            "MPTEMP,,,,,,,,",
            "MPTEMP,1,20.0,200.0,400.0,600.0,800.0,1000.0",
            f"MPDATA,DENS,1,1,{rho:.1f},{rho*0.99:.1f},{rho*0.98:.1f},{rho*0.97:.1f},{rho*0.95:.1f},{rho*0.93:.1f}",
            f"MPDATA,EX,1,1,{e_pa:.3e},{e_pa*0.95:.3e},{e_pa*0.88:.3e},{e_pa*0.78:.3e},{e_pa*0.65:.3e},{e_pa*0.45:.3e}",
            f"MPDATA,NUXY,1,1,{nu:.3f},{nu:.3f},{min(0.45, nu+0.01):.3f},{min(0.45, nu+0.02):.3f},{min(0.45, nu+0.03):.3f},{min(0.45, nu+0.04):.3f}",
            "MPDATA,ALPX,1,1,1.35e-5,1.42e-5,1.51e-5,1.60e-5,1.72e-5,1.85e-5",
            "MPDATA,KXX,1,1,16.5,18.2,20.4,22.8,25.6,28.5",
            "MPDATA,C,1,1,460,490,525,565,610,660",
        ]
        content = "\n".join(lines) + "\n"
        return CAEExportManager._write_optional_file(filepath, content, return_path_when_written=False)

    @staticmethod
    def export_comsol(filepath: Optional[str], alloy_name: str, comp: Dict[str, float],
                      thermo: Optional[Dict[str, Any]] = None,
                      mech: Optional[Dict[str, Any]] = None) -> str:
        """Exports COMSOL Multiphysics piecewise interpolation table and returns its text content."""
        comp = comp or {}
        props = CAEExportManager._extract_common_props(thermo, mech)
        e_pa = props["e_gpa"] * 1e9
        rho = props["rho_kg_m3"]
        temps = [293.15, 473.15, 673.15, 873.15, 1073.15, 1273.15]

        lines = [
            f"% COMSOL Multiphysics Material Model: {alloy_name}",
            f"% Composition: {comp}",
            "% Generated by CALPHAD XOC",
            "% T[K]\trho[kg/m^3]\tCp[J/(kg*K)]\tk[W/(m*K)]\tE[Pa]\tnu",
        ]
        for temp_k in temps:
            scale = 1.0 - (temp_k - 293.15) / 2000.0
            lines.append(
                f"{temp_k:.2f}\t{rho*scale:.1f}\t{460 + 0.18*(temp_k-293.15):.1f}\t"
                f"{16.5 + 0.012*(temp_k-293.15):.2f}\t{e_pa*scale:.3e}\t{props['nu']:.3f}"
            )

        content = "\n".join(lines) + "\n"
        return CAEExportManager._write_optional_file(filepath, content, return_path_when_written=False)

    @staticmethod
    def export_deform(filepath: Optional[str], alloy_name: str, comp: Dict[str, float],
                      thermo: Optional[Dict[str, Any]] = None,
                      mech: Optional[Dict[str, Any]] = None) -> str:
        """
        Exports material card for SFTC DEFORM Forming / DEFORM-HT (.dat format).
        Returns `filepath` when written to disk, or card text when `filepath` is empty.
        """
        comp = comp or {}
        props = CAEExportManager._extract_common_props(thermo, mech)

        temps_c = [700, 800, 900, 1000, 1100, 1200]
        rates = [0.01, 0.1, 1.0, 10.0]
        strains = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
        comp_str = ", ".join(f"{k}:{v:.2f}" for k, v in comp.items())

        lines = [
            "# SFTC DEFORM-3D / DEFORM-HT MATERIAL DATA DECK",
            f"# Material: {alloy_name}",
            f"# Composition: {comp_str}",
            "# Generated by CALPHAD XOC Materials Engineering Suite",
            "# -------------------------------------------------------------",
            f"MATERIAL_NAME = {alloy_name}",
            f"SOLIDUS_TEMPERATURE_K = {props['sol_k']:.2f}",
            f"LIQUIDUS_TEMPERATURE_K = {props['liq_k']:.2f}",
            f"ELASTIC_MODULUS_GPA = {props['e_gpa']:.1f}",
            f"POISSONS_RATIO = {props['nu']:.3f}",
            f"DENSITY_KG_M3 = {props['rho_kg_m3']:.1f}",
            "THERMAL_EXPANSION_1E6 = 13.8",
            "THERMAL_CONDUCTIVITY_W_MK = 18.2",
            "HEAT_CAPACITY_J_KGK = 460.0",
            "",
            "# FLOW STRESS TABLE [True Strain, True Strain Rate (1/s), Temp (C), Flow Stress (MPa)]",
            f"TABLE_DIMENSIONS = {len(strains)} {len(rates)} {len(temps_c)}",
        ]

        hs = CAEExportManager.compute_hansel_spittel_params(alloy_name, thermo, mech)
        for tc in temps_c:
            for edot in rates:
                for eps in strains:
                    val = (
                        hs["A"]
                        * math.exp(hs["m1"] * tc)
                        * (eps ** hs["m2"])
                        * (edot ** hs["m3"])
                        * math.exp(hs["m4"] / max(0.01, eps))
                    )
                    lines.append(f"{eps:.3f}\t{edot:.3f}\t{tc:.1f}\t{max(15.0, val):.2f}")

        content = "\n".join(lines) + "\n"
        return CAEExportManager._write_optional_file(filepath, content, return_path_when_written=True)

    @staticmethod
    def export_simufact(filepath: Optional[str], alloy_name: str, comp: Dict[str, float],
                        thermo: Optional[Dict[str, Any]] = None,
                        mech: Optional[Dict[str, Any]] = None) -> str:
        """
        Exports material card for Simufact.forming / MSC Marc (.xml MatildA format).
        Returns `filepath` when written to disk, or XML card text when `filepath` is empty.
        """
        comp = comp or {}
        props = CAEExportManager._extract_common_props(thermo, mech)
        hs = CAEExportManager.compute_hansel_spittel_params(alloy_name, thermo, mech)

        temps_c = [20, 400, 800, 1000, 1100]
        strains = [0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
        safe_name = _xml_escape(str(alloy_name or "CALPHAD_Alloy"))

        xml_lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<SimufactMaterial xmlns="http://www.simufact.de/material" version="4.0">',
            '  <Header createdBy="PyCALPHAD Suite" format="MatildA">',
            f"    <MaterialName>{safe_name}</MaterialName>",
            "  </Header>",
            "  <GeneralProperties>",
            f'    <Density unit="kg/m3">{props["rho_kg_m3"]:.1f}</Density>',
            f'    <YoungsModulus unit="GPa">{props["e_gpa"]:.1f}</YoungsModulus>',
            f'    <PoissonsRatio>{props["nu"]:.3f}</PoissonsRatio>',
            '    <ThermalExpansion unit="1/K">1.35e-5</ThermalExpansion>',
            f'    <SolidusTemperature unit="C">{props["sol_k"] - 273.15:.1f}</SolidusTemperature>',
            f'    <LiquidusTemperature unit="C">{props["liq_k"] - 273.15:.1f}</LiquidusTemperature>',
            '    <ChemicalComposition unit="wt%">',
        ]
        for el, pct in comp.items():
            xml_lines.append(f'      <Element name="{_xml_escape(str(el))}" fraction="{float(pct):.3f}"/>')

        xml_lines.extend([
            "    </ChemicalComposition>",
            "  </GeneralProperties>",
            '  <FlowStressCurves method="HanselSpittel">',
        ])
        for tc in temps_c:
            xml_lines.append(f'    <TemperatureCurve temperatureC="{tc}">')
            for eps in strains:
                val = hs["A"] * math.exp(hs["m1"] * tc) * (eps ** hs["m2"]) * math.exp(hs["m4"] / max(0.01, eps))
                xml_lines.append(f'      <Point trueStrain="{eps:.2f}" flowStressMPa="{max(20.0, val):.2f}"/>')
            xml_lines.append("    </TemperatureCurve>")

        xml_lines.extend([
            "  </FlowStressCurves>",
            "</SimufactMaterial>",
        ])

        content = "\n".join(xml_lines) + "\n"
        return CAEExportManager._write_optional_file(filepath, content, return_path_when_written=True)
