# -*- coding: utf-8 -*-
"""
rom_engine.py - Independent Rule of Mixtures (ROM) Metallurgical Calculation Engine

Provides:
  1. Pure volume- and mole-fraction weighted linear Rule of Mixtures baselines.
  2. Voigt (isostrain upper bound), Reuss (isostress lower bound), and Hill harmonic mean
     for elastic moduli (Young's modulus E, Shear modulus G, Bulk modulus K, Poisson's ratio nu).
  3. Linear and series transport properties (thermal conductivity k, electrical resistivity rho_el,
     linear thermal expansion CTE, Turner's constrained expansion).
  4. Ideal thermodynamic mixing baseline (Delta H_mix = 0, Delta S_mix = -R * sum(x_i * ln x_i),
     Delta G_mix(T) = -T * Delta S_mix, and linear elemental melting liquidus/solidus).
  5. Direct analytical comparison against CALPHAD / high-fidelity physics calculations,
     quantifying deviations caused by solid solution lattice distortion, chemical short-range order,
     intermetallic precipitation, Nordheim electron scattering, and mass-variance phonon scattering.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from pycalphad_app.core.elements_data import ELEMENTS_REGISTRY, ElementData


# Authoritative pure annealed elemental electrical resistivity at 293 K - 298 K (microOhm*cm)
ELEMENTAL_RESISTIVITY_UOHM_CM: Dict[str, float] = {
    "H": 1e12, "He": 1e14, "Li": 9.28, "Be": 3.56, "B": 1.8e6, "C": 1375.0,
    "N": 1e14, "O": 1e14, "F": 1e14, "Ne": 1e14, "Na": 4.77, "Mg": 4.39,
    "Al": 2.65, "Si": 1000.0, "P": 1e9, "S": 2e15, "Cl": 1e14, "Ar": 1e14,
    "K": 7.20, "Ca": 3.36, "Sc": 56.2, "Ti": 42.0, "V": 20.0, "Cr": 12.5,
    "Mn": 144.0, "Fe": 9.61, "Co": 5.60, "Ni": 6.99, "Cu": 1.68, "Zn": 5.90,
    "Ga": 17.4, "Ge": 46000.0, "As": 33.3, "Se": 1e6, "Br": 1e12, "Kr": 1e14,
    "Rb": 12.8, "Sr": 13.2, "Y": 59.6, "Zr": 42.1, "Nb": 15.2, "Mo": 5.34,
    "Tc": 20.0, "Ru": 7.10, "Rh": 4.51, "Pd": 10.5, "Ag": 1.59, "Cd": 6.80,
    "In": 8.37, "Sn": 11.5, "Sb": 41.7, "Te": 1.0e4, "I": 1.3e9, "Xe": 1e14,
    "Cs": 20.5, "Ba": 33.2, "La": 61.5, "Ce": 82.8, "Pr": 70.0, "Nd": 64.3,
    "Sm": 94.0, "Eu": 90.0, "Gd": 131.0, "Tb": 115.0, "Dy": 92.6, "Ho": 81.4,
    "Er": 86.0, "Tm": 67.6, "Yb": 25.0, "Lu": 58.2, "Hf": 35.1, "Ta": 13.1,
    "W": 5.28, "Re": 19.3, "Os": 8.12, "Ir": 4.71, "Pt": 10.6, "Au": 2.21,
    "Hg": 96.1, "Tl": 18.0, "Pb": 20.8, "Bi": 129.0, "Th": 14.7, "U": 28.0
}

# Pure elemental room-temperature lattice friction (Peierls-Nabarro) yield stress (MPa)
ELEMENTAL_YIELD_STRESS_MPA: Dict[str, float] = {
    "Al": 20.0, "Ti": 140.0, "V": 200.0, "Cr": 280.0, "Mn": 70.0, "Fe": 50.0,
    "Co": 45.0, "Ni": 30.0, "Cu": 25.0, "Zn": 35.0, "Zr": 95.0, "Nb": 140.0,
    "Mo": 320.0, "Hf": 110.0, "Ta": 180.0, "W": 420.0, "Re": 260.0, "Mg": 20.0,
    "Si": 500.0, "C": 1500.0, "Sc": 35.0, "Y": 40.0, "Sn": 15.0, "Pb": 12.0
}

# Pure elemental room-temperature annealed Vickers hardness (HV)
ELEMENTAL_HARDNESS_HV: Dict[str, float] = {
    "Al": 15.0, "Ti": 60.0, "V": 65.0, "Cr": 110.0, "Mn": 45.0, "Fe": 40.0,
    "Co": 45.0, "Ni": 35.0, "Cu": 30.0, "Zn": 30.0, "Zr": 80.0, "Nb": 75.0,
    "Mo": 150.0, "Hf": 90.0, "Ta": 85.0, "W": 350.0, "Re": 135.0, "Mg": 26.0,
    "Si": 950.0, "C": 1800.0, "Sc": 75.0, "Y": 60.0, "Sn": 10.0, "Pb": 5.0
}


class RuleOfMixturesEngine:
    """
    Independent calculation engine implementing linear Rule of Mixtures (ROM)
    and Voigt-Reuss-Hill continuum composite bounds.
    """

    _R_GAS: float = 8.314462618

    def __init__(self, composition: Dict[str, float], basis: str = "wt%"):
        self.raw_composition = {k.strip().capitalize(): float(v) for k, v in composition.items() if float(v) > 0}
        self.basis = basis.strip().lower()

        # Resolve atomic and weight fractions
        self.comp_at: Dict[str, float] = {}
        self.comp_wt: Dict[str, float] = {}
        self._resolve_compositions()

        # Compute volume fractions
        self.comp_vol: Dict[str, float] = {}
        self._resolve_volume_fractions()

    def _resolve_compositions(self) -> None:
        """Converts input composition into normalized atomic (x_i) and weight (w_i) fractions."""
        if not self.raw_composition:
            self.comp_at = {"Fe": 1.0}
            self.comp_wt = {"Fe": 1.0}
            return

        if "at" in self.basis or "mol" in self.basis:
            tot_at = sum(self.raw_composition.values())
            self.comp_at = {el: val / tot_at for el, val in self.raw_composition.items()}
            # Convert to weight fractions: w_i = x_i * M_i / sum(x_j * M_j)
            mw_dict = {}
            for el, x_i in self.comp_at.items():
                data = ELEMENTS_REGISTRY.get(el)
                mw_dict[el] = getattr(data, "atomic_mass", 55.85) if data else 55.85
            masses = {el: x_i * mw_dict[el] for el, x_i in self.comp_at.items()}
            tot_mass = sum(masses.values())
            self.comp_wt = {el: m / tot_mass for el, m in masses.items()}
        else:
            tot_wt = sum(self.raw_composition.values())
            self.comp_wt = {el: val / tot_wt for el, val in self.raw_composition.items()}
            # Convert to atomic fractions: x_i = (w_i / M_i) / sum(w_j / M_j)
            moles = {}
            for el, w_i in self.comp_wt.items():
                data = ELEMENTS_REGISTRY.get(el)
                mw = getattr(data, "atomic_mass", 55.85) if data else 55.85
                moles[el] = w_i / mw
            tot_moles = sum(moles.values())
            self.comp_at = {el: n / tot_moles for el, n in moles.items()}

    def _resolve_volume_fractions(self) -> None:
        """Calculates elemental volume fractions: v_i = (w_i / rho_i) / sum(w_j / rho_j)."""
        vols = {}
        for el, w_i in self.comp_wt.items():
            data = ELEMENTS_REGISTRY.get(el)
            rho = getattr(data, "density_g_cm3", 7.8) if data else 7.8
            rho = max(0.1, float(rho))
            vols[el] = w_i / rho
        tot_vol = sum(vols.values())
        if tot_vol > 0:
            self.comp_vol = {el: v / tot_vol for el, v in vols.items()}
        else:
            self.comp_vol = dict(self.comp_wt)

    def compute_properties(self) -> Dict[str, Any]:
        """
        Computes the complete suite of Rule of Mixtures baseline properties:
        Physical, Thermodynamic, Elastic, Mechanical, and Transport.
        """
        elements = list(self.comp_at.keys())

        # Elemental properties extraction
        molar_masses = []
        densities = []
        radii_pm = []
        vecs = []
        electronegs = []
        tm_ks = []
        youngs_moduli = []
        shear_moduli = []
        bulk_moduli = []
        poissons_ratios = []
        yield_stresses = []
        hardness_hvs = []
        thermal_conds = []
        resistivities = []
        ctes = []

        for el in elements:
            data = ELEMENTS_REGISTRY.get(el)
            mw = float(getattr(data, "atomic_mass", 55.845) if data else 55.845)
            rho = float(getattr(data, "density_g_cm3", 7.87) if data else 7.87)
            r_pm = float(getattr(data, "radius_pm", 126.0) if data else 126.0)
            vec = float(getattr(data, "vec", 8.0) if data else 8.0)
            chi = float(getattr(data, "electronegativity", 1.83) if data else 1.83)
            tm = float(getattr(data, "tm_k", 1811.0) if data else 1811.0)
            e_mod = float(getattr(data, "youngs_modulus_gpa", 211.0) if data else 211.0)
            g_mod = float(getattr(data, "shear_modulus_gpa", 82.0) if data else 82.0)
            nu = float(getattr(data, "poissons_ratio", 0.29) if data else 0.29)
            k_mod = e_mod / max(0.01, 3.0 * (1.0 - 2.0 * nu))
            sy = float(ELEMENTAL_YIELD_STRESS_MPA.get(el, getattr(data, "friction_stress_mpa", 50.0) if data else 50.0))
            hv = float(ELEMENTAL_HARDNESS_HV.get(el, sy / 2.5))
            k_th = float(getattr(data, "thermal_cond_w_mk", 80.4) if data else 80.4)
            rho_el = float(ELEMENTAL_RESISTIVITY_UOHM_CM.get(el, 10.0))
            cte_val = float(getattr(data, "cte_1e6_k", 11.8) if data else 11.8)

            molar_masses.append(mw)
            densities.append(rho)
            radii_pm.append(r_pm)
            vecs.append(vec)
            electronegs.append(chi)
            tm_ks.append(tm)
            youngs_moduli.append(e_mod)
            shear_moduli.append(g_mod)
            bulk_moduli.append(k_mod)
            poissons_ratios.append(nu)
            yield_stresses.append(sy)
            hardness_hvs.append(hv)
            thermal_conds.append(k_th)
            resistivities.append(rho_el)
            ctes.append(cte_val)

        x_arr = np.array([self.comp_at[el] for el in elements], dtype=float)
        w_arr = np.array([self.comp_wt[el] for el in elements], dtype=float)
        v_arr = np.array([self.comp_vol[el] for el in elements], dtype=float)

        # 1. Crystallographic / Physical
        molar_mass_mean = float(np.dot(x_arr, molar_masses))
        # Volume-conservative displacement density: rho = 1 / sum(w_i / rho_i)
        vol_specific = float(np.sum(w_arr / np.array(densities)))
        density_rom = float(1.0 / max(1e-6, vol_specific))
        linear_density = float(np.dot(v_arr, densities))
        molar_volume = molar_mass_mean / max(1e-6, density_rom)
        r_mean = float(np.dot(x_arr, radii_pm))
        vec_rom = float(np.dot(x_arr, vecs))
        chi_rom = float(np.dot(x_arr, electronegs))

        # 2. Thermodynamic (Ideal ROM)
        t_liq_rom = float(np.dot(x_arr, tm_ks))
        t_sol_rom = float(np.min(tm_ks))
        # Ideal mixing entropy Delta S_mix = -R * sum(x_i * ln(x_i))
        delta_s_mix = -self._R_GAS * float(sum(x * math.log(x) for x in x_arr if x > 1e-12))
        delta_h_mix = 0.0  # By definition in ideal linear solution
        delta_g_mix_300 = float(-300.0 * delta_s_mix)
        delta_g_mix_1000 = float(-1000.0 * delta_s_mix)

        # 3. Elastic Constants (Voigt-Reuss-Hill Bounds)
        e_voigt = float(np.dot(v_arr, youngs_moduli))
        e_reuss = float(1.0 / np.sum(v_arr / np.array(youngs_moduli)))
        e_hill = float(0.5 * (e_voigt + e_reuss))

        g_voigt = float(np.dot(v_arr, shear_moduli))
        g_reuss = float(1.0 / np.sum(v_arr / np.array(shear_moduli)))
        g_hill = float(0.5 * (g_voigt + g_reuss))

        k_voigt = float(np.dot(v_arr, bulk_moduli))
        k_reuss = float(1.0 / np.sum(v_arr / np.array(bulk_moduli)))
        k_hill = float(0.5 * (k_voigt + k_reuss))

        nu_hill = float((3.0 * k_hill - 2.0 * g_hill) / max(1e-4, 2.0 * (3.0 * k_hill + g_hill)))
        pugh_ratio = float(k_hill / max(1e-4, g_hill))

        # 4. Mechanical Strength & Hardness (Pure Uncoupled Baseline)
        yield_strength_rom = float(np.dot(x_arr, yield_stresses))
        uts_rom = float(yield_strength_rom * 1.55)
        hardness_hv_rom = float(np.dot(x_arr, hardness_hvs))
        strain_hardening_n_rom = 0.28

        # 5. Transport Properties
        # Thermal conductivity: Mean, Voigt (parallel), Reuss (series)
        thermal_cond_mean = float(np.dot(x_arr, thermal_conds))
        thermal_cond_voigt = float(np.dot(v_arr, thermal_conds))
        thermal_cond_reuss = float(1.0 / np.sum(v_arr / np.array(thermal_conds)))

        # Electrical resistivity: Linear atomic ROM & Series volume ROM
        resistivity_rom = float(np.dot(x_arr, resistivities))
        resistivity_series = float(np.dot(v_arr, resistivities))

        # Coefficient of Thermal Expansion
        cte_rom = float(np.dot(x_arr, ctes))
        # Turner's formula: alpha_eff = sum(alpha_i * K_i / rho_i * w_i) / sum(K_i / rho_i * w_i)
        turner_num = float(np.sum(np.array(ctes) * np.array(bulk_moduli) / np.array(densities) * w_arr))
        turner_den = float(np.sum(np.array(bulk_moduli) / np.array(densities) * w_arr))
        cte_turner = float(turner_num / max(1e-6, turner_den))

        return {
            "density_g_cm3": density_rom,
            "linear_density_g_cm3": linear_density,
            "molar_mass_g_mol": molar_mass_mean,
            "molar_volume_cm3_mol": molar_volume,
            "atomic_radius_pm": r_mean,
            "atomic_radius_mean_pm": r_mean,
            "vec": vec_rom,
            "valence_electron_concentration": vec_rom,
            "electronegativity": chi_rom,
            "electronegativity_mean": chi_rom,
            "liquidus_k": t_liq_rom,
            "solidus_k": t_sol_rom,
            "melting_point_k": t_liq_rom,
            "melting_temperature_k": t_liq_rom,
            "mean_melting_k": (t_sol_rom + t_liq_rom) / 2.0,
            "freezing_range_k": max(0.0, t_liq_rom - t_sol_rom),
            "delta_s_mix_ideal_j_mol_k": delta_s_mix,
            "delta_smix_j_molk": delta_s_mix,
            "delta_h_mix_kj_mol": delta_h_mix / 1000.0,
            "delta_hmix_j_mol": delta_h_mix,
            "delta_gmix_300k_j_mol": delta_g_mix_300,
            "delta_gmix_1000k_j_mol": delta_g_mix_1000,
            "youngs_modulus_gpa": e_hill,
            "youngs_modulus_voigt_gpa": e_voigt,
            "youngs_modulus_reuss_gpa": e_reuss,
            "shear_modulus_gpa": g_hill,
            "shear_modulus_voigt_gpa": g_voigt,
            "shear_modulus_reuss_gpa": g_reuss,
            "bulk_modulus_gpa": k_hill,
            "bulk_modulus_voigt_gpa": k_voigt,
            "bulk_modulus_reuss_gpa": k_reuss,
            "poissons_ratio": nu_hill,
            "pugh_ratio": pugh_ratio,
            "yield_strength_mpa": yield_strength_rom,
            "uts_mpa": uts_rom,
            "hardness_hv": hardness_hv_rom,
            "strain_hardening_n": strain_hardening_n_rom,
            "thermal_conductivity_w_mk": thermal_cond_mean,
            "thermal_conductivity_voigt_w_mk": thermal_cond_voigt,
            "thermal_conductivity_reuss_w_mk": thermal_cond_reuss,
            "electrical_resistivity_uohm_cm": resistivity_rom,
            "cte_1e6_k": cte_rom,
            "cte_turner_1e6_k": cte_turner,
        }

    def compute_temperature_dependent_curves(self, t_k_arr: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Generates temperature-dependent property series under Rule of Mixtures assumptions.
        Includes thermal softening, Wiedemann-Franz transport, and volumetric expansion.
        """
        props = self.compute_properties()
        t_arr = np.asarray(t_k_arr, dtype=float)

        sy0 = props["yield_strength_mpa"]
        hv0 = props["hardness_hv"]
        e0 = props["youngs_modulus_gpa"]
        rho0 = props["density_g_cm3"]
        k0 = props["thermal_conductivity_w_mk"]
        rho_el0 = props["electrical_resistivity_uohm_cm"]
        cte0 = props["cte_1e6_k"]
        t_liq = props["liquidus_k"]

        # 1. Thermal expansion and density
        cte_t = cte0 + 0.0035 * (t_arr - 300.0)
        density_t = rho0 / (1.0 + 3.0 * cte_t * 1e-6 * (t_arr - 300.0))

        # 2. Young's modulus softening (linear homologous decay)
        e_t = e0 * np.maximum(0.15, 1.0 - 0.45 * (t_arr - 300.0) / max(300.0, t_liq - 300.0))

        # 3. Yield strength & Hardness softening
        sy_t = sy0 * np.maximum(0.08, 1.0 - 0.55 * (t_arr - 300.0) / max(300.0, t_liq - 300.0))
        hv_t = hv0 * np.maximum(0.10, sy_t / max(1.0, sy0))

        # 4. Thermal conductivity: slight phonon decrease, electronic Sommerfeld linear increase
        k_t = k0 + 0.012 * (t_arr - 300.0)

        # 5. Electrical resistivity: Bloch-Gruneisen linear acoustic phonon slope
        rho_el_t = rho_el0 + 0.038 * (t_arr - 300.0)

        return {
            "t_k": t_arr,
            "density": density_t,
            "cte": cte_t,
            "youngs_modulus": e_t,
            "yield_strength": sy_t,
            "hardness_hv": hv_t,
            "thermal_conductivity": k_t,
            "resistivity": rho_el_t,
        }

    def compare_with_calphad(
        self,
        calphad_thermo: Dict[str, Any],
        calphad_mech: Dict[str, Any],
        calphad_trans: Dict[str, Any],
        temp_series: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conducts rigorous side-by-side comparison between high-fidelity CALPHAD/physics
        and Rule of Mixtures (ROM), detailing quantitative deviations and physical mechanisms.
        """
        rom_props = self.compute_properties()

        # Extract CALPHAD properties safely
        c_density = float(calphad_thermo.get("Density_g_cm3", calphad_trans.get("TheoreticalDensity_g_cm3", 8.0)))
        c_sol_k = float(calphad_thermo.get("Solidus_K", calphad_thermo.get("T_Solidus", 1400.0)))
        c_liq_k = float(calphad_thermo.get("Liquidus_K", calphad_thermo.get("T_Liquidus", 1500.0)))
        c_e = float(calphad_mech.get("YoungsModulus_GPa", 200.0))
        c_g = float(calphad_mech.get("ShearModulus_GPa", 78.0))
        c_k = float(calphad_mech.get("BulkModulus_GPa", 155.0))
        c_nu = float(calphad_mech.get("PoissonsRatio", 0.30))
        c_sy = float(calphad_mech.get("YieldStrength_MPa", 350.0))
        c_uts = float(calphad_mech.get("UTS_MPa", c_sy * 1.45))
        c_hv = float(calphad_mech.get("VickersHardness_HV", max(50.0, c_sy / 2.6)))
        c_k_th = float(calphad_trans.get("ThermalConductivity_W_mK", 15.0))
        c_rho_el = float(calphad_trans.get("ElectricalResistivity_uOhm_cm", 118.0))
        c_cte = float(calphad_trans.get("CTE_1e6_K", 14.2))

        # Build property comparison rows
        metrics = [
            {
                "property": "Density",
                "units": "g/cm³",
                "calphad_value": round(c_density, 3),
                "rom_value": round(rom_props["density_g_cm3"], 3),
                "rom_voigt": round(rom_props["linear_density_g_cm3"], 3),
                "rom_reuss": round(rom_props["density_g_cm3"], 3),
                "mechanism": "Lattice distortion strain fields expand the unit cell volume slightly relative to ideal hard-sphere atomic packing."
            },
            {
                "property": "Liquidus Temperature",
                "units": "K",
                "calphad_value": round(c_liq_k, 1),
                "rom_value": round(rom_props["liquidus_k"], 1),
                "rom_voigt": round(rom_props["liquidus_k"], 1),
                "rom_reuss": round(rom_props["solidus_k"], 1),
                "mechanism": "Thermodynamic excess Gibbs energy (negative Redlich-Kister mixing enthalpy) suppresses or stabilizes liquidus relative to linear elemental melting."
            },
            {
                "property": "Solidus Temperature",
                "units": "K",
                "calphad_value": round(c_sol_k, 1),
                "rom_value": round(rom_props["solidus_k"], 1),
                "rom_voigt": round(rom_props["liquidus_k"], 1),
                "rom_reuss": round(rom_props["solidus_k"], 1),
                "mechanism": "Solute partitioning and non-ideal Gibbs energy surfaces dictate solidus freezing intervals far more accurately than elemental lower-bounds."
            },
            {
                "property": "Mean Melting Temperature",
                "units": "K",
                "calphad_value": round((c_sol_k + c_liq_k) / 2.0, 1),
                "rom_value": round(rom_props["liquidus_k"], 1),
                "rom_voigt": round(rom_props["liquidus_k"], 1),
                "rom_reuss": round(rom_props["solidus_k"], 1),
                "mechanism": "Excess mixing enthalpy (ΔH_mix) and configurational entropy (ΔS_mix) depress the multi-component melting point relative to the linear elemental mixture."
            },
            {
                "property": "Solidification Interval (ΔT)",
                "units": "K",
                "calphad_value": round(max(0.0, c_liq_k - c_sol_k), 1),
                "rom_value": round(max(0.0, rom_props["liquidus_k"] - rom_props["solidus_k"]), 1),
                "rom_voigt": round(max(0.0, rom_props["liquidus_k"] - rom_props["solidus_k"]), 1),
                "rom_reuss": 0.0,
                "mechanism": "Equilibrium partition coefficients (k_i = c_s / c_l) determine the real non-isothermal freezing range across the mushy zone."
            },
            {
                "property": "Young's Modulus E",
                "units": "GPa",
                "calphad_value": round(c_e, 1),
                "rom_value": round(rom_props["youngs_modulus_gpa"], 1),
                "rom_voigt": round(rom_props["youngs_modulus_voigt_gpa"], 1),
                "rom_reuss": round(rom_props["youngs_modulus_reuss_gpa"], 1),
                "mechanism": "Voigt isostrain upper bound and Reuss isostress lower bound bracket the polycrystalline Hill average, modulated by short-range ordering."
            },
            {
                "property": "Shear Modulus G",
                "units": "GPa",
                "calphad_value": round(c_g, 1),
                "rom_value": round(rom_props["shear_modulus_gpa"], 1),
                "rom_voigt": round(rom_props["shear_modulus_voigt_gpa"], 1),
                "rom_reuss": round(rom_props["shear_modulus_reuss_gpa"], 1),
                "mechanism": "Dislocation core energy and anisotropic interatomic bonding shift shear resistance toward the polycrystal Hill average."
            },
            {
                "property": "Bulk Modulus K",
                "units": "GPa",
                "calphad_value": round(c_k, 1),
                "rom_value": round(rom_props["bulk_modulus_gpa"], 1),
                "rom_voigt": round(rom_props["bulk_modulus_voigt_gpa"], 1),
                "rom_reuss": round(rom_props["bulk_modulus_reuss_gpa"], 1),
                "mechanism": "Hydrostatic electronic compression response closely aligns with the volume-weighted Voigt-Reuss-Hill envelope."
            },
            {
                "property": "Poisson's Ratio ν",
                "units": "dimensionless",
                "calphad_value": round(c_nu, 3),
                "rom_value": round(rom_props["poissons_ratio"], 3),
                "rom_voigt": round(rom_props["poissons_ratio"], 3),
                "rom_reuss": round(rom_props["poissons_ratio"], 3),
                "mechanism": "Cauchy pressure and electronic d-band filling ratio govern lateral strain contraction."
            },
            {
                "property": "Yield Strength σ_y",
                "units": "MPa",
                "calphad_value": round(c_sy, 1),
                "rom_value": round(rom_props["yield_strength_mpa"], 1),
                "rom_voigt": round(rom_props["yield_strength_mpa"] * 1.3, 1),
                "rom_reuss": round(rom_props["yield_strength_mpa"] * 0.8, 1),
                "mechanism": "Severe solid solution hardening (Varvenne-Curtin), Hall-Petch grain boundary locking, and coherent intermetallic precipitation elevate flow stress massively above pure elemental friction."
            },
            {
                "property": "Ultimate Tensile Strength UTS",
                "units": "MPa",
                "calphad_value": round(c_uts, 1),
                "rom_value": round(rom_props["uts_mpa"], 1),
                "rom_voigt": round(rom_props["uts_mpa"] * 1.25, 1),
                "rom_reuss": round(rom_props["uts_mpa"] * 0.85, 1),
                "mechanism": "Work hardening capacity (dislocation forest accumulation and TWIP/TRIP twins) enhances uniform elongation and ultimate load carrying capacity."
            },
            {
                "property": "Vickers Hardness HV",
                "units": "HV",
                "calphad_value": round(c_hv, 1),
                "rom_value": round(rom_props["hardness_hv"], 1),
                "rom_voigt": round(rom_props["hardness_hv"] * 1.3, 1),
                "rom_reuss": round(rom_props["hardness_hv"] * 0.8, 1),
                "mechanism": "Resistance to plastic indenter penetration is amplified by dense obstacle resistance and shear modulus pinning."
            },
            {
                "property": "Thermal Conductivity k",
                "units": "W/(m·K)",
                "calphad_value": round(c_k_th, 2),
                "rom_value": round(rom_props["thermal_conductivity_w_mk"], 2),
                "rom_voigt": round(rom_props["thermal_conductivity_voigt_w_mk"], 2),
                "rom_reuss": round(rom_props["thermal_conductivity_reuss_w_mk"], 2),
                "mechanism": "Mass-variance and atomic size mismatch point-defect scattering severely shorten phonon mean free paths, depressing thermal conductivity far below elemental ROM."
            },
            {
                "property": "Electrical Resistivity ρ_el",
                "units": "µΩ·cm",
                "calphad_value": round(c_rho_el, 2),
                "rom_value": round(rom_props["electrical_resistivity_uohm_cm"], 2),
                "rom_voigt": round(rom_props["electrical_resistivity_uohm_cm"], 2),
                "rom_reuss": round(rom_props["electrical_resistivity_uohm_cm"] * 0.65, 2),
                "mechanism": "Massive multi-element chemical disorder causes intense electron wave packet scattering (Nordheim's rule and Mott-Ioffe-Regel saturation), dramatically increasing resistivity over elemental ROM."
            },
            {
                "property": "Linear Thermal Expansion CTE",
                "units": "10⁻⁶/K",
                "calphad_value": round(c_cte, 2),
                "rom_value": round(rom_props["cte_1e6_k"], 2),
                "rom_voigt": round(rom_props["cte_1e6_k"], 2),
                "rom_reuss": round(rom_props["cte_turner_1e6_k"], 2),
                "mechanism": "Anharmonic interatomic potential asymmetry is constrained by internal hydrostatic bulk modulus compatibility (Turner's formula)."
            }
        ]

        # Calculate deviations
        comparison_rows = []
        for m in metrics:
            c_val = m["calphad_value"]
            r_val = m["rom_value"]
            diff_abs = c_val - r_val
            diff_pct = ((c_val - r_val) / max(1e-6, abs(r_val))) * 100.0 if abs(r_val) > 1e-6 else 0.0
            comparison_rows.append({
                "property": m["property"],
                "units": m["units"],
                "calphad_value": c_val,
                "rom_value": r_val,
                "rom_voigt": m["rom_voigt"],
                "rom_reuss": m["rom_reuss"],
                "diff_absolute": round(diff_abs, 3),
                "diff_relative_pct": round(diff_pct, 1),
                "mechanism": m["mechanism"]
            })

        # Calculate comparative temperature curves
        t_eval = None
        if temp_series and "t_k" in temp_series:
            t_eval = np.array(temp_series["t_k"], dtype=float)
        else:
            t_eval = np.linspace(300.0, max(1600.0, c_liq_k + 80.0), 100)

        rom_curves = self.compute_temperature_dependent_curves(t_eval)

        # Comparative curves package
        comparative_series = {
            "t_k": t_eval.tolist(),
            "rom_yield_strength": rom_curves["yield_strength"].tolist(),
            "rom_hardness_hv": rom_curves["hardness_hv"].tolist(),
            "rom_thermal_conductivity": rom_curves["thermal_conductivity"].tolist(),
            "rom_electrical_resistivity": rom_curves["resistivity"].tolist(),
            "rom_cte": rom_curves["cte"].tolist(),
            "rom_density": rom_curves["density"].tolist(),
        }

        c_mean_tm = (c_sol_k + c_liq_k) / 2.0
        r_mean_tm = rom_props["liquidus_k"]
        melting_depression = r_mean_tm - c_mean_tm

        return {
            "comparison_table": comparison_rows,
            "comparative_series": comparative_series,
            "summary": {
                "density_deviation_pct": round(((c_density - rom_props["density_g_cm3"]) / rom_props["density_g_cm3"]) * 100.0, 1),
                "yield_strength_elevation_pct": round(((c_sy - rom_props["yield_strength_mpa"]) / max(1.0, rom_props["yield_strength_mpa"])) * 100.0, 1),
                "thermal_conductivity_suppression_pct": round(((c_k_th - rom_props["thermal_conductivity_w_mk"]) / max(1.0, rom_props["thermal_conductivity_w_mk"])) * 100.0, 1),
                "resistivity_elevation_pct": round(((c_rho_el - rom_props["electrical_resistivity_uohm_cm"]) / max(1.0, rom_props["electrical_resistivity_uohm_cm"])) * 100.0, 1),
                "calphad_mean_melting_k": round(c_mean_tm, 1),
                "rom_mean_melting_k": round(r_mean_tm, 1),
                "melting_depression_k": round(melting_depression, 1),
                "melting_depression_pct": round((melting_depression / max(1.0, r_mean_tm)) * 100.0, 1),
                "calphad_freezing_interval_k": round(max(0.0, c_liq_k - c_sol_k), 1),
                "rom_freezing_interval_k": round(max(0.0, rom_props["liquidus_k"] - rom_props["solidus_k"]), 1),
            }
        }
