"""
application_scorer.py - Multi-Criteria Industrial Suitability Scoring Engine
Comprehensive translation of App/HEAApplicationDatabase.m and App/HEAApplicationScorer.m.

Features:
  1. 12 Curated industrial engineering sectors (Aerospace, Cryogenics, Nuclear Gen-IV,
     Biomedical, Marine, Hot Tooling, Refractory, Hydrogen, Catalysis, Disc Rotor,
     Laser Cladding, Cavitation Overlay)
  2. Thermal neutron capture cross section checks (barns) for nuclear core transparency
  3. Biocompatibility cytotoxicity checks for permanent orthopedic implants
  4. Continuous utility scoring (0-100%) with hard vetoes
  5. Suitability Match Tiers (Prime, Viable, Conditional, Unsuitable)
  6. Bottleneck identification and actionable metallurgical tuning advice
"""

import math
from typing import Dict, List, Any, Optional

class ApplicationDatabase:
    NEUTRON_CROSS_SECTIONS = {
        "Zr": 0.185, "Al": 0.231, "Si": 0.171, "Mg": 0.063, "C": 0.0035,
        "Nb": 1.15, "Mo": 2.48, "Fe": 2.56, "Cr": 3.05, "Ni": 4.49,
        "V": 5.08, "Ti": 6.09, "W": 18.3, "Ta": 20.6, "Co": 37.2,
        "Hf": 104.0, "B": 767.0, "Gd": 49700.0
    }

    BIOCOMPATIBILITY_MAP = {
        "Ti": {"Safe": True,  "Class": "Biocompatible", "Reason": "Excellent osseointegration and passive TiO2"},
        "Zr": {"Safe": True,  "Class": "Biocompatible", "Reason": "Non-toxic, bio-inert ZrO2 passive scale"},
        "Nb": {"Safe": True,  "Class": "Biocompatible", "Reason": "Non-toxic, highly tissue-tolerant"},
        "Ta": {"Safe": True,  "Class": "Biocompatible", "Reason": "Superb biocompatibility and bone ingrowth"},
        "Mo": {"Safe": True,  "Class": "Tolerable",     "Reason": "Trace essential micronutrient (<10 at%)"},
        "Hf": {"Safe": True,  "Class": "Biocompatible", "Reason": "Bio-inert similar to Zr"},
        "Si": {"Safe": True,  "Class": "Biocompatible", "Reason": "Trace biocompatible"},
        "Ni": {"Safe": False, "Class": "Toxic/Allergenic", "Reason": "Severe Type IV contact allergy, DNA damage"},
        "Co": {"Safe": False, "Class": "Cytotoxic",        "Reason": "Metallosis, local cardiomyopathy, toxicity"},
        "Cr": {"Safe": False, "Class": "Cytotoxic (Cr VI)","Reason": "Release of carcinogenic hexavalent Cr ions"},
        "Al": {"Safe": False, "Class": "Neurotoxic",       "Reason": "Linked to osteomalacia and Alzheimer pathology"},
        "V":  {"Safe": False, "Class": "Cytotoxic",        "Reason": "Strong cytotoxicity and cellular inhibition"},
        "Cu": {"Safe": False, "Class": "Cytotoxic (burst)","Reason": "High ion cytotoxicity in soft tissues"}
    }

    @staticmethod
    def get_all_applications() -> List[Dict[str, Any]]:
        return [
            {
                "id": "AERO_TURBINE_BLADE",
                "name": "Gas Turbine Blades & Combustor Liners",
                "sector": "Aerospace & Propulsion",
                "desc": "High-temperature creep, thermal fatigue, and oxidation resistance for stage-1 turbine blades.",
                "benchmark": "Inconel 718 / CMSX-4 Superalloys",
                "git_ref": "CitrineInformatics/MPEA_dataset",
                "veto_elements": ["Pb", "Bi", "Cd", "Sn", "Zn", "Hg"],
                "min_solidus_k": 1550.0,
                "min_ductility_pct": 5.0,
                "weights": {"solidus": 0.30, "yield_strength": 0.25, "oxidation": 0.25, "density": 0.20}
            },
            {
                "id": "CRYO_LNG_VESSEL",
                "name": "Cryogenic Storage & Liquid H2 / LNG Vessels",
                "sector": "Energy & Cryogenics",
                "desc": "Zero ductile-to-brittle transition temperature (DBTT) and extreme toughness at 77 K and 20 K.",
                "benchmark": "Cantor CoCrFeMnNi / 316L Stainless",
                "git_ref": "ChenCheng-976/COD_HEM",
                "veto_elements": ["W", "Mo", "Ta", "Nb", "V"],
                "min_solidus_k": 1200.0,
                "min_ductility_pct": 25.0,
                "weights": {"ductility": 0.35, "toughness": 0.35, "yield_strength": 0.20, "solidus": 0.10}
            },
            {
                "id": "NUCLEAR_GEN4_CLAD",
                "name": "Generation-IV Nuclear Reactor Fuel Cladding",
                "sector": "Nuclear Engineering",
                "desc": "Low thermal neutron absorption cross section and high radiation swelling resistance.",
                "benchmark": "Zircaloy-4 / ODS FeCrAl",
                "git_ref": "IdahoLabResearch/HEA_Code",
                "veto_elements": ["Co", "Hf", "B", "Cd", "Gd", "Eu", "Sm"],
                "max_neutron_barns": 4.5,
                "min_solidus_k": 1600.0,
                "min_ductility_pct": 8.0,
                "weights": {"neutrons": 0.40, "oxidation": 0.30, "solidus": 0.20, "ductility": 0.10}
            },
            {
                "id": "BIOMED_ORTHO_IMPLANT",
                "name": "Biomedical Orthopedic Implants & Stents",
                "sector": "Biomedical Engineering",
                "desc": "Non-toxic, allergy-free elements with bone-matching low Young's modulus (<80 GPa).",
                "benchmark": "Ti-6Al-4V ELI / Ti-29Nb-13Ta-4.6Zr",
                "git_ref": "HEAPS / Bio-HEA Database",
                "veto_elements": ["Ni", "Co", "Cr", "V", "Al", "Cu", "Be", "Pb"],
                "max_modulus_gpa": 85.0,
                "min_ductility_pct": 12.0,
                "weights": {"modulus": 0.40, "ductility": 0.30, "yield_strength": 0.20, "corrosion": 0.10}
            },
            {
                "id": "MARINE_SUBSEA_VALVE",
                "name": "Marine Propulsion & Subsea Valves",
                "sector": "Marine & Offshore",
                "desc": "High resistance to chloride pitting, crevice corrosion, and cavitational erosion.",
                "benchmark": "Super Duplex 2507 / Monel K-500",
                "git_ref": "ChenCheng-976/COD_HEM",
                "veto_elements": ["Mg", "Li", "Ca", "Sr", "Ba"],
                "min_ductility_pct": 15.0,
                "weights": {"corrosion": 0.40, "yield_strength": 0.30, "ductility": 0.20, "density": 0.10}
            },
            {
                "id": "TOOLING_HOT_DIE",
                "name": "Hot Work Tooling & Metal Extrusion Dies",
                "sector": "Manufacturing & Tooling",
                "desc": "Extreme hot hardness, thermal shock resistance, and anti-galling wear performance.",
                "benchmark": "AISI H13 / Inconel 718",
                "git_ref": "cast_mpea_ouyang",
                "veto_elements": ["Pb", "Bi", "Sn", "In", "Ga"],
                "min_solidus_k": 1400.0,
                "min_ductility_pct": 2.0,
                "weights": {"hardness": 0.40, "yield_strength": 0.30, "solidus": 0.20, "toughness": 0.10}
            },
            {
                "id": "REFRACTORY_FURNACE",
                "name": "Ultra-High Temperature Refractory Furnace Elements",
                "sector": "High-Temperature Processing",
                "desc": "Melting points exceeding 2200 K for inert furnace shields and aerospace re-entry skins.",
                "benchmark": "Mo-TZM / W-25Re Refractory Alloys",
                "git_ref": "PhasesResearchLab/PyQAlloy",
                "veto_elements": ["Al", "Mg", "Zn", "Cu", "Sn", "Pb", "Bi"],
                "min_solidus_k": 2100.0,
                "min_ductility_pct": 1.0,
                "weights": {"solidus": 0.50, "yield_strength": 0.30, "oxidation": 0.20}
            },
            {
                "id": "HYDROGEN_STORAGE",
                "name": "Solid-State Metal Hydride Hydrogen Storage",
                "sector": "Clean Energy",
                "desc": "Reversible hydrogen absorption/desorption thermodynamics at ambient pressure.",
                "benchmark": "TiVNbZrFe Hydride / LaNi5",
                "git_ref": "Nature Scientific Data 2026",
                "veto_elements": ["Pb", "Bi", "Hg", "Cd"],
                "min_ductility_pct": 2.0,
                "weights": {"hydride_affinity": 0.45, "density": 0.30, "solidus": 0.25}
            },
            {
                "id": "ENERGY_CATALYSIS",
                "name": "Electrochemical Water Splitting (HER/OER)",
                "sector": "Renewable Energy",
                "desc": "High electrocatalytic activity, low overpotential, and alkaline corrosion resistance.",
                "benchmark": "Pt/C / IrO2 / FeCoNiCrMo Multi-Principal",
                "git_ref": "Nature Scientific Data 2026",
                "veto_elements": ["Pb", "Hg", "Cd", "As"],
                "weights": {"catalytic_surface": 0.50, "corrosion": 0.30, "cost": 0.20}
            },
            {
                "id": "AERO_DISC_ROTOR",
                "name": "High-Pressure Turbine & Compressor Disc Rotors",
                "sector": "Aerospace Propulsion",
                "desc": "High burst margin, high low-cycle fatigue (LCF) resistance, and uniform grain microstructure.",
                "benchmark": "Udimet 720Li / Rene 88DT",
                "git_ref": "CitrineInformatics/MPEA_dataset",
                "veto_elements": ["Pb", "Bi", "Sn", "Zn", "Cd"],
                "min_solidus_k": 1500.0,
                "min_ductility_pct": 12.0,
                "weights": {"yield_strength": 0.35, "toughness": 0.30, "solidus": 0.20, "density": 0.15}
            },
            {
                "id": "LASER_CLADDING_OVERLAY",
                "name": "Thermal Spray & Laser Cladding Wear Coatings",
                "sector": "Surface Engineering",
                "desc": "High metallurgical bond integrity, low dilution susceptibility, and Archard wear resistance.",
                "benchmark": "Metco 16C (NiCrBSi) / Stellite 6",
                "git_ref": "Adv. Eng. Mater. 2019, 21, 1900343",
                "veto_elements": ["Pb", "Cd", "Hg"],
                "min_ductility_pct": 0.5,
                "weights": {"hardness": 0.40, "wear": 0.35, "bond_adhesion": 0.25}
            },
            {
                "id": "CAVITATION_CORROSION_OVERLAY",
                "name": "Hydro-Turbine Cavitation & Slurry Erosion Overlays",
                "sector": "Hydropower & Mining",
                "desc": "Resistance to localized micro-jet impact shock waves and abrasive slurry scour.",
                "benchmark": "High-Cobalt Tribaloy T-800 / Cavitec",
                "git_ref": "Adv. Eng. Mater. 2019, 21, 1900343",
                "veto_elements": ["Pb", "Bi", "Mg"],
                "min_ductility_pct": 6.0,
                "weights": {"toughness": 0.35, "hardness": 0.35, "corrosion": 0.30}
            }
        ]

class ApplicationScorer:
    @classmethod
    def score_alloy(cls, elements: List[str], at_fractions: List[float],
                    thermo: Dict[str, Any], mech: Dict[str, Any], ox: Dict[str, Any]) -> List[Dict[str, Any]]:
        apps = ApplicationDatabase.get_all_applications()
        is_coating = any(el in ["B", "Si"] for el in elements) and ("Ni" in elements)
        phase = str(thermo.get("Phase", "FCC"))
        ys = float(mech.get("YieldStrength_RT_MPa", mech.get("YieldStrength_MPa", 300.0)))
        uts = float(mech.get("UTS_RT_MPa", mech.get("UTS_MPa", 500.0)))
        hv = float(mech.get("VickersHardness_HV", mech.get("Hardness_HV", 200.0)))
        ts = float(thermo.get("T_Solidus", thermo.get("Solidus_K", 1553.0)))
        toughness = float(mech.get("FractureToughness_MPa_m05", mech.get("FractureToughness_K1c", 100.0)))
        elong = float(mech.get("Elongation_pct", mech.get("Elongation_RT_pct", 20.0)))
        density = float(thermo.get("density", 7.8))
        e_gpa = float(mech.get("YoungsModulus_GPa", 200.0))

        c_dict = {el: at_fractions[i] for i, el in enumerate(elements)}
        cr_at = c_dict.get("Cr", 0.0) * 100.0
        mo_at = c_dict.get("Mo", 0.0) * 100.0
        pren = cr_at + 3.3 * mo_at

        # Calculate thermal neutron cross section
        sigma_barns = sum(c_dict.get(el, 0.0) * ApplicationDatabase.NEUTRON_CROSS_SECTIONS.get(el, 5.0) for el in elements)

        scored_list = []

        for app in apps:
            app_id = app["id"]
            name = app["name"]
            sector = app["sector"]
            desc = app["desc"]
            bench = app["benchmark"]
            git_ref = app["git_ref"]

            # 1. Check Hard Vetoes
            veto = False
            veto_reason = ""
            for v_el in app.get("veto_elements", []):
                if v_el in c_dict and c_dict[v_el] > 0.005:
                    veto = True
                    veto_reason = f"Prohibited element present: {v_el} ({c_dict[v_el]*100:.1f} at%)"
                    break

            if not veto and "max_neutron_barns" in app:
                if sigma_barns > app["max_neutron_barns"]:
                    veto = True
                    veto_reason = f"Thermal neutron cross-section ({sigma_barns:.2f} b) exceeds {app['max_neutron_barns']} b limit."

            if not veto and "max_modulus_gpa" in app:
                if e_gpa > app["max_modulus_gpa"] and ("Biomed" in name or "Orthopedic" in name):
                    # Soft penalty rather than veto, but high stress shielding
                    pass

            if not veto and "min_solidus_k" in app:
                if ts < app["min_solidus_k"] - 200.0:
                    veto = True
                    veto_reason = f"Solidus temperature ({ts:.0f} K) is below minimum threshold ({app['min_solidus_k']} K)."

            # 2. Continuous utility scoring
            if veto:
                score = 15.0
                tier = "Unsuitable (Vetoed)"
                bottleneck = veto_reason
                advice = "Reformulate alloy to remove prohibited elements or increase refractory balance."
            else:
                score = 50.0
                bottleneck = "Balanced"
                advice = "Optimal property baseline achieved."

                if app_id == "AERO_TURBINE_BLADE":
                    s_ts = min(100.0, max(20.0, (ts - 1400.0) / 4.0))
                    s_ys = min(100.0, max(20.0, ys / 8.0))
                    s_ox = 95.0 if "Alumina" in ox.get("Regime", "") else (80.0 if "Chromia" in ox.get("Regime", "") else 40.0)
                    s_den = max(20.0, 100.0 - (density - 7.0) * 15.0)
                    score = 0.30 * s_ts + 0.25 * s_ys + 0.25 * s_ox + 0.20 * s_den
                    if s_ox < 60:
                        bottleneck = "Oxidation resistance requires protective Al or Cr scale."
                        advice = "Add Al >= 12 at% or Cr >= 16 at% for hermetic oxide layer."
                    elif s_ys < 60:
                        bottleneck = "Yield strength at elevated temperatures."
                        advice = "Add refractory elements (Ta, Mo, Nb) or coherent precipitate formers (Al, Ti)."

                elif app_id == "CRYO_LNG_VESSEL":
                    if is_coating:
                        score = 25.0
                        bottleneck = "Thermal spray coating is prone to spallation under cryogenic contraction."
                    else:
                        s_duc = min(100.0, elong * 2.0)
                        s_tou = min(100.0, toughness * 0.5)
                        s_ys = min(100.0, ys / 4.0)
                        score = 0.35 * s_duc + 0.35 * s_tou + 0.30 * s_ys
                        if "BCC" in phase and not "FCC" in phase:
                            score = min(score, 45.0)
                            bottleneck = "BCC lattice prone to ductile-to-brittle transition (DBTT) at 77 K."
                            advice = "Stabilize single-phase FCC lattice (VEC >= 8.0) via Ni/Co additions."

                elif app_id == "NUCLEAR_GEN4_CLAD":
                    s_neu = max(10.0, 100.0 - (sigma_barns / 4.0) * 80.0)
                    s_ox = 90.0 if "Alumina" in ox.get("Regime", "") or "Chromia" in ox.get("Regime", "") else 45.0
                    score = 0.50 * s_neu + 0.30 * s_ox + 0.20 * min(100.0, ts / 18.0)
                    if sigma_barns > 2.5:
                        bottleneck = f"Neutron capture cross section ({sigma_barns:.2f} barns)."
                        advice = "Increase Zr, Al, Si, or C; remove high-capture transition metals."

                elif app_id == "BIOMED_ORTHO_IMPLANT":
                    s_mod = max(10.0, 100.0 - max(0.0, (e_gpa - 60.0) * 1.5))
                    s_duc = min(100.0, elong * 3.5)
                    score = 0.50 * s_mod + 0.30 * s_duc + 0.20 * min(100.0, ys / 7.0)
                    if e_gpa > 90.0:
                        bottleneck = f"Young's modulus ({e_gpa:.0f} GPa) causes bone stress shielding."
                        advice = "Incorporate beta-stabilizing Ti-Nb-Zr-Ta to lower modulus toward 60-75 GPa."

                elif app_id == "MARINE_SUBSEA_VALVE":
                    s_pren = min(100.0, pren * 2.5)
                    s_ys = min(100.0, ys / 6.0)
                    score = 0.45 * s_pren + 0.35 * s_ys + 0.20 * min(100.0, elong * 2.5)
                    if pren < 32.0:
                        bottleneck = f"PREN value ({pren:.1f}) below super-duplex 40 standard."
                        advice = "Add Cr >= 20 at% and Mo >= 3 at% to enhance chloride pitting resistance."

                elif app_id == "TOOLING_HOT_DIE":
                    s_hv = min(100.0, hv / 7.5)
                    s_ys = min(100.0, ys / 8.0)
                    score = 0.45 * s_hv + 0.35 * s_ys + 0.20 * min(100.0, ts / 16.0)
                    if hv < 500.0:
                        bottleneck = "Vickers hardness below die wear resistance requirements."
                        advice = "Add B, C, or refractory carbide/boride formers."

                elif app_id == "REFRACTORY_FURNACE":
                    s_ts = min(100.0, max(10.0, (ts - 1800.0) / 8.0))
                    score = 0.60 * s_ts + 0.40 * min(100.0, ys / 10.0)
                    if ts < 2200.0:
                        bottleneck = f"Melting point ({ts:.0f} K) insufficient for extreme furnace environments."
                        advice = "Formulate in W-Ta-Mo-Nb high refractory space."

                elif app_id in ["LASER_CLADDING_OVERLAY", "CAVITATION_CORROSION_OVERLAY"]:
                    if is_coating or hv >= 600.0:
                        score = 92.0
                        bottleneck = "None (Ideal Hardfacing Composition)"
                        advice = "Excellent wear and cavitation overlay performance."
                    else:
                        s_hv = min(100.0, hv / 6.5)
                        score = 0.50 * s_hv + 0.30 * min(100.0, ys / 6.0) + 0.20 * min(100.0, toughness * 0.4)
                        bottleneck = "Hardness below optimal hardfacing overlay threshold."
                        advice = "Employ NiCrBSi chemistry or increase interstitial boride/carbide content."
                else:
                    score = min(95.0, max(30.0, 0.4 * (ys / 6.0) + 0.3 * (hv / 6.0) + 0.3 * (ts / 18.0)))

                score = round(max(10.0, min(99.0, score)), 1)
                if score >= 85.0:
                    tier = "Prime Candidate (Optimal Match)"
                elif score >= 70.0:
                    tier = "Viable Candidate"
                elif score >= 50.0:
                    tier = "Conditional Candidate"
                else:
                    tier = "Unsuitable"

            scored_list.append({
                "id": app_id,
                "name": name,
                "sector": sector,
                "score": score,
                "tier": tier,
                "bottleneck": bottleneck,
                "advice": advice,
                "benchmark": bench,
                "git_reference": git_ref
            })

        scored_list.sort(key=lambda x: x["score"], reverse=True)
        for r, item in enumerate(scored_list, 1):
            item["rank"] = r

        return scored_list

    @classmethod
    def calculate(cls, composition: Dict[str, float], thermo: Dict[str, Any],
                  mech: Dict[str, Any], ox: Dict[str, Any]) -> List[Dict[str, Any]]:
        elems = list(composition.keys())
        fracs = list(composition.values())
        return cls.score_alloy(elems, fracs, thermo, mech, ox)

    @classmethod
    def score_all(cls, thermo: Dict[str, Any], mech: Dict[str, Any],
                  ox: Dict[str, Any], corr: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Convenience method matching worker usage."""
        comp = thermo.get("composition", {})
        if not comp and "Elements" in thermo and "AtFractions" in thermo:
            comp = dict(zip(thermo["Elements"], thermo["AtFractions"]))
        if not comp:
            comp = {"Fe": 0.2, "Ni": 0.2, "Co": 0.2, "Cr": 0.2, "Al": 0.2}
        elems = list(comp.keys())
        fracs = list(comp.values())
        return cls.score_alloy(elems, fracs, thermo, mech, ox)

