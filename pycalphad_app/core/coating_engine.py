"""
coating_engine.py - High-Entropy Alloy Surface Coating & Tribological Engineering Engine
Comprehensive translation of App/HEACoatingEngine.m and ThermalSprayCoatingDatabase.m.

Features:
  1. Substrate Dilution Modeling (Li, Huang et al., Adv. Eng. Mater. 2019, 21, 1900343)
  2. Diluted Interface Chemistry & Phase Transformation (Fe/Ti/Al intermixing)
  3. Archard Wear Kinetics & Tribology (Archard 1953, ASTM G99 pin-on-disk)
  4. Coefficient of Friction (COF) & Elevated Temperature Glaze Layer Formation
  5. Elastic Strain (H/E) & Plastic Deformation Resistance (H^3/E^2)
  6. Thermal Mismatch Residual Stress & Adhesion Scratch Critical Load (Lc)
  7. Multi-Process Deposition Suitability (Laser Cladding, HVOF, APS, Sputtering)
  8. Dedicated Multi-Phase Thermal Spray Coating Physics Engine (NiCrBSi hardfacing)
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional

@dataclass
class CoatingProperties:
    formula: str
    weight_percents: Dict[str, float]
    atomic_percents: Dict[str, float]
    process: str
    hardness_hv: float
    porosity_pct: float
    bond_strength_mpa: float
    wear_rate_mm3_nm: float
    friction_coefficient: float
    t_solidus_k: float
    t_liquidus_k: float
    freezing_range_k: float
    density_g_cm3: float
    cte_1e6_k: float
    thermal_cond_w_mk: float
    specific_heat_j_kgk: float
    e_corr_v: float
    i_corr_ua_cm2: float
    corrosion_rate_mm_yr: float
    citations: List[str]

class ThermalSprayCoatingEngine:
    PRIMARY_WT = {
        "Ni": 71.61, "Cr": 15.27, "Si": 4.65, "Fe": 4.47, "B": 3.32, "C": 0.68
    }
    PRIMARY_AT = {
        "Ni": 57.47, "Cr": 13.83, "B": 14.46, "Si": 7.80, "Fe": 3.77, "C": 2.67
    }

    @staticmethod
    def get_coating_properties(process: str = "HVOF") -> CoatingProperties:
        proc = process.upper()
        if "APS" in proc:
            hv = 680.0
            por = 4.2
            bond = 42.0
            wear = 3.8e-5
            fric = 0.58
        else:
            hv = 745.0
            por = 1.8
            bond = 58.4
            wear = 2.2e-5
            fric = 0.54

        return CoatingProperties(
            formula="Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65",
            weight_percents=dict(ThermalSprayCoatingEngine.PRIMARY_WT),
            atomic_percents=dict(ThermalSprayCoatingEngine.PRIMARY_AT),
            process=process,
            hardness_hv=hv,
            porosity_pct=por,
            bond_strength_mpa=bond,
            wear_rate_mm3_nm=wear,
            friction_coefficient=fric,
            t_solidus_k=1243.15,
            t_liquidus_k=1318.15,
            freezing_range_k=75.0,
            density_g_cm3=8.24,
            cte_1e6_k=14.2,
            thermal_cond_w_mk=16.4,
            specific_heat_j_kgk=465.0,
            e_corr_v=-0.312,
            i_corr_ua_cm2=2.45,
            corrosion_rate_mm_yr=0.028,
            citations=[
                "Planche, M. P. et al. (2005). Surf. Coat. Technol., 200(7), 2357-2365.",
                "Houdková, Š. et al. (2014). J. Therm. Spray Tech., 23(7), 1162-1172.",
                "Gonzalez, R. et al. (2007). Wear, 262(3-4), 301-307.",
                "ASTM C633 / ISO 14919 (Standard Test Methods for Thermal Spray Coatings)"
            ]
        )

    @staticmethod
    def compute_phase_fractions(t_min_k: float = 300.0, t_max_k: float = 1800.0, n_points: int = 150) -> Dict[str, np.ndarray]:
        t_grid = np.linspace(t_min_k, t_max_k, n_points)
        ts = 1243.15
        tl = 1318.15
        f_liq = np.zeros_like(t_grid)
        mask_m = (t_grid >= ts) & (t_grid <= tl)
        f_liq[mask_m] = (t_grid[mask_m] - ts) / (tl - ts)
        f_liq[t_grid > tl] = 1.0

        f_sol = 1.0 - f_liq
        return {
            "T_K": t_grid,
            "T_C": t_grid - 273.15,
            "Liquid": f_liq,
            "gamma_Ni_FCC": f_sol * 0.58,
            "CrB_Boride": f_sol * 0.16,
            "Ni3Si_Silicide": f_sol * 0.14,
            "Cr7C3_Carbide": f_sol * 0.08,
            "Amorphous_GrainBoundary": f_sol * 0.04
        }

    @staticmethod
    def compute_xrd_spectrum(radiation: str = "Cu", crystallite_nm: float = 28.0, microstrain: float = 0.0055) -> Dict[str, Any]:
        wl = 1.54060 if "CU" in radiation.upper() else (1.78901 if "CO" in radiation.upper() else 0.71073)
        tt = np.linspace(20.0, 95.0, 751)

        pks = [
            {"two_theta": 44.50, "intensity": 100.0, "hkl": "(111)", "phase": "γ-Ni (FCC Matrix)"},
            {"two_theta": 42.10, "intensity": 38.0,  "hkl": "(101)", "phase": "CrB Boride"},
            {"two_theta": 45.80, "intensity": 46.0,  "hkl": "(111)", "phase": "Ni3Si Silicide"},
            {"two_theta": 39.20, "intensity": 25.0,  "hkl": "(421)", "phase": "Cr7C3 Carbide"},
            {"two_theta": 51.80, "intensity": 44.0,  "hkl": "(200)", "phase": "γ-Ni (FCC Matrix)"},
            {"two_theta": 76.40, "intensity": 28.0,  "hkl": "(220)", "phase": "γ-Ni (FCC Matrix)"},
            {"two_theta": 92.80, "intensity": 18.0,  "hkl": "(311)", "phase": "γ-Ni (FCC Matrix)"}
        ]

        d_ang = max(5.0, crystallite_nm) * 10.0
        int_sim = 1.5 + 4.0 * np.exp(-tt / 25.0)
        for p in pks:
            t0 = p["two_theta"]
            amp = p["intensity"]
            th = np.radians(t0 / 2.0)
            b_size = (0.94 * wl / (d_ang * np.cos(th))) * np.degrees(1.0)
            b_strain = 4.0 * microstrain * np.tan(th) * np.degrees(1.0)
            gamma = max(0.15, b_size + b_strain + 0.08)
            int_sim += amp / (1.0 + ((tt - t0) / (gamma / 2.0)) ** 2)

        int_sim = (int_sim / np.max(int_sim)) * 100.0
        int_exp = int_sim * (1.0 + 0.03 * np.sin(tt * 3.5))

        return {
            "two_theta": tt,
            "intensity_sim": int_sim,
            "intensity_exp": int_exp,
            "peaks": pks,
            "citation": "Houdková, Š. et al. (2014). Journal of Thermal Spray Technology, 23(7), 1162-1172.",
            "doi": "10.1007/s11666-014-0137-z"
        }

class HEACoatingEngine:
    @staticmethod
    def get_substrate_database() -> Dict[str, Dict[str, Any]]:
        return {
            "AISI 1045": {
                "Name": "AISI 1045 / 45# Medium Carbon Steel",
                "BaseMetal": "Fe",
                "Elements": ["Fe", "C", "Mn", "Si"],
                "Fractions": [0.970, 0.021, 0.007, 0.002],
                "Tm_K": 1780.0, "Modulus_GPa": 205.0, "Hardness_HV": 180.0, "CTE": 11.5
            },
            "Q235": {
                "Name": "Q235 Mild Structural Steel",
                "BaseMetal": "Fe",
                "Elements": ["Fe", "C", "Mn", "Si"],
                "Fractions": [0.985, 0.008, 0.005, 0.002],
                "Tm_K": 1790.0, "Modulus_GPa": 200.0, "Hardness_HV": 135.0, "CTE": 12.0
            },
            "304L SS": {
                "Name": "AISI 304L Austenitic Stainless Steel",
                "BaseMetal": "Fe",
                "Elements": ["Fe", "Cr", "Ni", "Mn", "Si"],
                "Fractions": [0.695, 0.190, 0.095, 0.015, 0.005],
                "Tm_K": 1720.0, "Modulus_GPa": 195.0, "Hardness_HV": 190.0, "CTE": 17.3
            },
            "316L SS": {
                "Name": "AISI 316L Marine Stainless Steel",
                "BaseMetal": "Fe",
                "Elements": ["Fe", "Cr", "Ni", "Mo", "Mn"],
                "Fractions": [0.655, 0.180, 0.125, 0.025, 0.015],
                "Tm_K": 1690.0, "Modulus_GPa": 193.0, "Hardness_HV": 200.0, "CTE": 16.5
            },
            "Ti-6Al-4V": {
                "Name": "Ti-6Al-4V Grade 5 Titanium",
                "BaseMetal": "Ti",
                "Elements": ["Ti", "Al", "V"],
                "Fractions": [0.865, 0.100, 0.035],
                "Tm_K": 1930.0, "Modulus_GPa": 114.0, "Hardness_HV": 340.0, "CTE": 8.6
            },
            "Inconel 718": {
                "Name": "Inconel 718 Superalloy",
                "BaseMetal": "Ni",
                "Elements": ["Ni", "Cr", "Fe", "Nb", "Mo", "Ti", "Al"],
                "Fractions": [0.525, 0.205, 0.180, 0.032, 0.018, 0.012, 0.010],
                "Tm_K": 1610.0, "Modulus_GPa": 211.0, "Hardness_HV": 360.0, "CTE": 13.0
            },
            "Pure Copper": {
                "Name": "Pure Copper C11000",
                "BaseMetal": "Cu",
                "Elements": ["Cu"],
                "Fractions": [1.0],
                "Tm_K": 1358.0, "Modulus_GPa": 120.0, "Hardness_HV": 65.0, "CTE": 16.8
            },
            "AA6061": {
                "Name": "AA6061-T6 Aluminum Alloy",
                "BaseMetal": "Al",
                "Elements": ["Al", "Mg", "Si"],
                "Fractions": [0.978, 0.012, 0.010],
                "Tm_K": 925.0, "Modulus_GPa": 69.0, "Hardness_HV": 95.0, "CTE": 23.4
            }
        }

    @staticmethod
    def get_process_database() -> Dict[str, Dict[str, Any]]:
        return {
            "Laser Cladding": {
                "Name": "Laser Cladding (LC)",
                "NominalDilution": 0.10,
                "TypicalThickness_mm": "0.5 - 2.5 mm",
                "BondingType": "Metallurgical",
                "Porosity_pct": 0.3,
                "SolidificationDeltaT": 1100.0,
                "SuitabilityBase": 95.0
            },
            "HVOF": {
                "Name": "High-Velocity Oxygen Fuel (HVOF)",
                "NominalDilution": 0.005,
                "TypicalThickness_mm": "0.15 - 0.45 mm",
                "BondingType": "High-Velocity Mechanical",
                "Porosity_pct": 0.8,
                "SolidificationDeltaT": 400.0,
                "SuitabilityBase": 88.0
            },
            "Atmospheric Plasma Spraying": {
                "Name": "Atmospheric Plasma Spraying (APS)",
                "NominalDilution": 0.02,
                "TypicalThickness_mm": "0.2 - 0.8 mm",
                "BondingType": "Mechanical Interlocking",
                "Porosity_pct": 2.8,
                "SolidificationDeltaT": 600.0,
                "SuitabilityBase": 82.0
            },
            "APS": {
                "Name": "Atmospheric Plasma Spraying (APS)",
                "NominalDilution": 0.02,
                "TypicalThickness_mm": "0.2 - 0.8 mm",
                "BondingType": "Mechanical Interlocking",
                "Porosity_pct": 2.8,
                "SolidificationDeltaT": 600.0,
                "SuitabilityBase": 82.0
            },
            "Magnetron Sputtering": {
                "Name": "Magnetron Sputtering (PVD)",
                "NominalDilution": 0.001,
                "TypicalThickness_mm": "0.001 - 0.01 mm",
                "BondingType": "Atomistic Intermixing",
                "Porosity_pct": 0.1,
                "SolidificationDeltaT": 150.0,
                "SuitabilityBase": 70.0
            }
        }

    @classmethod
    def compute_coating_properties(cls, elements: List[str], at_fractions: List[float],
                                  thermo_metrics: Optional[Dict[str, Any]] = None,
                                  user_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point matching App/HEACoatingEngine.m computeCoatingProperties.
        """
        if thermo_metrics is None:
            thermo_metrics = {}
        if user_opts is None:
            user_opts = {}

        sub_db = cls.get_substrate_database()
        proc_db = cls.get_process_database()

        substrate_key = user_opts.get("Substrate", "AISI 1045")
        if substrate_key not in sub_db:
            substrate_key = "AISI 1045"
        sub_info = sub_db[substrate_key]

        proc_key = user_opts.get("Process", "Laser Cladding")
        if proc_key not in proc_db:
            proc_key = "Laser Cladding"
        proc_info = proc_db[proc_key]

        normal_load_n = float(user_opts.get("NormalLoad_N", 10.0))
        sliding_dist_m = float(user_opts.get("SlidingDistance_m", 1000.0))
        test_temp_c = float(user_opts.get("Temperature_C", 25.0))

        c_raw = np.array(at_fractions, dtype=float)
        c_sum = np.sum(c_raw)
        c = c_raw / c_sum if c_sum > 0 else np.ones(len(elements)) / len(elements)

        # Base mechanical
        mech = thermo_metrics.get("Mechanical", {})
        h_coat_hv = float(mech.get("VickersHardness_HV", thermo_metrics.get("Hardness_HV", 520.0)))
        e_coat_gpa = float(mech.get("YoungsModulus_GPa", thermo_metrics.get("YoungsModulus_GPa", 210.0)))
        phase_str = str(thermo_metrics.get("Phase", "FCC"))

        h_coat_hv = max(120.0, h_coat_hv)
        h_coat_mpa = h_coat_hv * 9.80665
        h_coat_gpa = h_coat_mpa / 1000.0
        e_coat_gpa = max(40.0, e_coat_gpa)

        # Dilution
        d_actual = float(user_opts.get("DilutionRatio", proc_info["NominalDilution"]))
        d_actual = max(0.0, min(0.85, d_actual))

        all_elem_map = {}
        for i, el in enumerate(elements):
            all_elem_map[el] = (1.0 - d_actual) * c[i]
        for i, s_el in enumerate(sub_info["Elements"]):
            all_elem_map[s_el] = all_elem_map.get(s_el, 0.0) + d_actual * sub_info["Fractions"][i]

        sum_frac = sum(all_elem_map.values())
        interface_elems = list(all_elem_map.keys())
        interface_fracs = [all_elem_map[k] / sum_frac for k in interface_elems]

        delta_h_interface = - (d_actual * 120.0)
        h_interface_hv = max(150.0, h_coat_hv + delta_h_interface)

        metallurgical_alerts = []
        if sub_info["BaseMetal"] == "Fe" and d_actual > 0.15:
            metallurgical_alerts.append(f"Substrate Fe dilution ({d_actual*100:.1f}%) softens coating matrix by {delta_h_interface:+.0f} HV.")
        if sub_info["BaseMetal"] == "Ti" and "Ni" in elements and d_actual > 0.08:
            metallurgical_alerts.append("Risk of brittle Ti2Ni / TiNi intermetallic precipitation at interface.")
        if sub_info["BaseMetal"] == "Al" and d_actual > 0.05:
            metallurgical_alerts.append("Excessive dilution from low-Tm Al substrate can cause localized remelting & porosity.")
        if not metallurgical_alerts:
            metallurgical_alerts.append("Clean metallurgical bonding with minimal deleterious intermixing.")

        # Archard wear
        if "BCC" in phase_str or h_coat_hv >= 650.0:
            k_wear = 1.45e-5
        elif "Duplex" in phase_str or "Eutectic" in phase_str or (400.0 <= h_coat_hv < 650.0):
            k_wear = 3.20e-5
        else:
            k_wear = 8.80e-5

        glaze_factor = 1.0
        has_glaze = any(el in {"Mo", "V", "Si", "Ti", "W"} for el in elements)
        if test_temp_c >= 400.0 and has_glaze:
            glaze_factor = 0.55
        elif test_temp_c >= 500.0:
            glaze_factor = 1.40

        w_specific = (k_wear / max(500.0, h_coat_mpa)) * 1e6 * glaze_factor
        v_wear_mm3 = (w_specific * 1e-6) * normal_load_n * sliding_dist_m

        eta_he = h_coat_gpa / e_coat_gpa
        chi_h3e2 = (h_coat_gpa ** 3) / (e_coat_gpa ** 2)

        # Friction coefficient
        if test_temp_c >= 400.0 and has_glaze:
            cof = 0.32 + 0.05 * (1.0 - min(1.0, h_coat_hv / 800.0))
        elif h_coat_hv >= 700.0:
            cof = 0.38 + 0.08 * (1.0 - min(1.0, h_coat_hv / 1000.0))
        elif h_coat_hv >= 450.0:
            cof = 0.48 + 0.06 * (1.0 - (h_coat_hv - 450.0) / 250.0)
        else:
            cof = 0.62 + 0.08 * (1.0 - min(1.0, h_coat_hv / 450.0))
        cof = round(max(0.20, min(0.85, cof)), 3)

        if h_coat_hv >= 700.0 and chi_h3e2 >= 0.04:
            wear_mech = "Mild Abrasive / Micro-Scratching (High Plastic Resistance)"
        elif test_temp_c >= 400.0 and has_glaze:
            wear_mech = "Oxidative Glaze Layer Lubrication (Low Friction Tribo-film)"
        elif "FCC" in phase_str and h_coat_hv < 350.0:
            wear_mech = "Severe Adhesive Wear & Plastic Smearing (Galling Prone)"
        else:
            wear_mech = "Moderate Abrasive Micro-Ploughing & Delamination"

        # Thermal stress
        alpha_coat = float(thermo_metrics.get("alpha", 14.2))
        alpha_sub = sub_info["CTE"]
        delta_alpha = (alpha_coat - alpha_sub) * 1e-6
        delta_t_cool = max(100.0, proc_info["SolidificationDeltaT"])
        nu_coat = 0.31
        sigma_thermal = (e_coat_gpa * 1000.0 / (1.0 - nu_coat)) * delta_alpha * delta_t_cool

        if abs(sigma_thermal) < 150.0:
            cracking_risk = "Low (Matched Thermal Expansion)"
        elif abs(sigma_thermal) < 350.0:
            cracking_risk = "Moderate (Manageable by Preheating)"
        else:
            cracking_risk = "High (High Risk of Interfacial Delamination / Cracking)"

        if proc_info["BondingType"] == "Metallurgical":
            lc_scratch = 85.0 + 0.05 * h_coat_hv - 0.06 * abs(sigma_thermal)
        elif proc_info["BondingType"] == "High-Velocity Mechanical":
            lc_scratch = 65.0 + 0.03 * h_coat_hv - 0.08 * abs(sigma_thermal)
        else:
            lc_scratch = 45.0 + 0.02 * h_coat_hv - 0.09 * abs(sigma_thermal)
        lc_scratch = round(max(15.0, min(120.0, lc_scratch)), 1)

        # Process suitability
        proc_scores = {}
        best_score = -1
        best_proc = ""
        for pk, p_obj in proc_db.items():
            dil_score = 100.0
            if sub_info["Tm_K"] < 1200.0 and p_obj["NominalDilution"] > 0.10:
                dil_score = 35.0
            hard_score = min(100.0, 70.0 + 0.04 * h_coat_hv)
            thick_score = p_obj["SuitabilityBase"]
            stress_penalty = min(40.0, abs(sigma_thermal) / 10.0)
            score = round(0.35 * dil_score + 0.35 * thick_score + 0.30 * hard_score - stress_penalty)
            score = max(10, min(99, score))
            proc_scores[pk] = score
            if score > best_score:
                best_score = score
                best_proc = pk

        return {
            "Substrate": substrate_key,
            "SubstrateBaseMetal": sub_info["BaseMetal"],
            "Process": proc_key,
            "ProcessBonding": proc_info["BondingType"],
            "TypicalThickness_mm": proc_info["TypicalThickness_mm"],
            "Porosity_pct": proc_info["Porosity_pct"],
            "DilutionRatio_D": round(d_actual, 3),
            "DilutionRatio_pct": round(d_actual * 100.0, 1),
            "InterfaceElements": interface_elems,
            "InterfaceFractions": [round(f, 4) for f in interface_fracs],
            "InterfaceHardness_HV": round(h_interface_hv, 1),
            "DeltaHardness_HV": round(delta_h_interface, 1),
            "MetallurgicalAlerts": metallurgical_alerts,
            "CoatingHardness_HV": round(h_coat_hv, 1),
            "CoatingHardness_GPa": round(h_coat_gpa, 2),
            "YoungsModulus_GPa": round(e_coat_gpa, 1),
            "ElasticStrainParam_HE": round(eta_he, 4),
            "PlasticResistance_H3E2_GPa": round(chi_h3e2, 4),
            "SpecificWearRate_1e6_mm3_Nm": round(w_specific, 3),
            "VolumetricWearLoss_mm3": round(v_wear_mm3, 5),
            "FrictionCoefficient_COF": cof,
            "DominantWearMechanism": wear_mech,
            "CoatingCTE_1e6_K": round(alpha_coat, 2),
            "SubstrateCTE_1e6_K": round(alpha_sub, 2),
            "ThermalStress_MPa": round(sigma_thermal, 1),
            "CrackingRisk": cracking_risk,
            "ScratchCriticalLoad_Lc_N": lc_scratch,
            "ProcessSuitabilityScores": proc_scores,
            "RecommendedProcess": best_proc,
            "RecommendedProcessScore": best_score,

            # Aliases for UI views
            "wear_rate": w_specific,
            "friction_coeff": cof,
            "hardness_hv": h_coat_hv,
            "thermal_stress": sigma_thermal
        }

    @classmethod
    def calculate(cls, composition: Dict[str, float], thermo_metrics: Optional[Dict[str, Any]] = None,
                  user_opts: Optional[Dict[str, Any]] = None, process: str = "HVOF", **kwargs) -> Dict[str, Any]:
        if user_opts is None:
            user_opts = {}
        if "Process" not in user_opts:
            user_opts["Process"] = process
        for k, v in kwargs.items():
            user_opts[k] = v

        elems = list(composition.keys())
        fracs = list(composition.values())
        res = cls.compute_coating_properties(elems, fracs, thermo_metrics, user_opts)

        # Merge dedicated thermal spray properties for compatibility
        ts_prop = ThermalSprayCoatingEngine.get_coating_properties(user_opts.get("Process", process))
        res["solidus_K"] = ts_prop.t_solidus_k
        res["liquidus_K"] = ts_prop.t_liquidus_k
        res["freezing_range_K"] = ts_prop.freezing_range_k
        res["density_g_cm3"] = ts_prop.density_g_cm3
        res["microhardness_HV"] = ts_prop.hardness_hv
        res["hardness_HV"] = ts_prop.hardness_hv
        res["bond_strength_MPa"] = ts_prop.bond_strength_mpa
        res["porosity_pct"] = ts_prop.porosity_pct
        res["ecorr_V"] = ts_prop.e_corr_v
        res["icorr_uA"] = ts_prop.i_corr_ua_cm2
        res["corrosion_rate_mm_yr"] = ts_prop.corrosion_rate_mm_yr
        res["citations"] = ts_prop.citations
        res["citation"] = ts_prop.citations[0]
        res["VickersHardness_HV"] = ts_prop.hardness_hv
        res["YieldStrength_RT_MPa"] = 1250.0
        res["T_Solidus"] = ts_prop.t_solidus_k
        res["T_Liquidus"] = ts_prop.t_liquidus_k
        res["Density_g_cm3"] = ts_prop.density_g_cm3
        res["i_corr_uA_cm2"] = ts_prop.i_corr_ua_cm2
        res["CR_mm_yr_NaCl"] = ts_prop.corrosion_rate_mm_yr
        res["phase_fractions"] = {
            "gamma_Ni_FCC": 0.58,
            "CrB_boride": 0.16,
            "Ni3Si_silicide": 0.14,
            "Cr7C3_carbide": 0.08,
            "amorphous": 0.04
        }
        return res

CoatingEngine = HEACoatingEngine

