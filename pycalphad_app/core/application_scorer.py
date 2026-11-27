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

from pycalphad_app.core.alloy_economics import (
    atomic_to_weight_fractions,
    compute_raw_alloy_cost,
    estimate_benchmark_cost,
    recommend_cost_optimization,
)

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
            },
            {
                "id": "AERO_HYPERSONIC_LEADING_EDGE",
                "name": "Hypersonic Leading Edges & Scramjet Combustors",
                "sector": "Aerospace & Hypersonics",
                "desc": "Aerodynamic frictional heating and extreme oxidation resistance above 2000 K.",
                "benchmark": "Hf-Ta-Zr-Nb-Ti Refractory HEA / C/SiC Composite",
                "git_ref": "Nature Materials 2024 / UHTC MPEA",
                "veto_elements": ["Al", "Mg", "Zn", "Sn", "Pb", "Bi", "Cd"],
                "min_solidus_k": 2100.0,
                "min_ductility_pct": 1.0,
                "weights": {"solidus": 0.45, "yield_strength": 0.35, "oxidation": 0.20}
            },
            {
                "id": "NUCLEAR_FUSION_DIVERTOR",
                "name": "Fusion Plasma-Facing Divertor Armor Tiles",
                "sector": "Nuclear & Fusion Energy",
                "desc": "Thermal erosion resistance under 10-20 MW/m² heat flux with low hydrogen isotope retention.",
                "benchmark": "Tungsten Heavy Alloys / W-Ta-Cr-V Refractory HEA",
                "git_ref": "ITER Divertor Materials Handb. / J. Nucl. Mater.",
                "veto_elements": ["Co", "Ni", "Cu", "Al", "Mg", "Zn", "Pb", "Bi"],
                "min_solidus_k": 2200.0,
                "min_ductility_pct": 0.5,
                "weights": {"solidus": 0.50, "neutrons": 0.30, "hardness": 0.20}
            },
            {
                "id": "PETRO_SOUR_GAS_WELLHEAD",
                "name": "Deepwater Sour Gas (H2S/CO2) Wellheads & Risers",
                "sector": "Petrochemical & Offshore",
                "desc": "Immunity to sulfide stress cracking (SSC) and chloride pitting under NACE MR0175.",
                "benchmark": "Inconel 625 / Incoloy 925 / Hastelloy C-276",
                "git_ref": "NACE MR0175 / ISO 15156 Petroleum Standard",
                "veto_elements": ["Mg", "Ca", "Zn", "Bi", "Pb"],
                "min_solidus_k": 1400.0,
                "min_ductility_pct": 18.0,
                "weights": {"corrosion": 0.45, "yield_strength": 0.30, "toughness": 0.25}
            },
            {
                "id": "TOOLING_COLD_PUNCH",
                "name": "High-Load Stamping & Blanking Punches",
                "sector": "Manufacturing & Tooling",
                "desc": "Extreme compressive yield strength and micro-chipping wear resistance for AHSS stamping.",
                "benchmark": "AISI D2 / Vanadis 4 Extra Powder Tool Steel",
                "git_ref": "Uddeholm Tooling / CIRP Annals 2025",
                "veto_elements": ["Pb", "Bi", "Sn", "Zn"],
                "min_solidus_k": 1350.0,
                "min_ductility_pct": 1.5,
                "weights": {"hardness": 0.45, "yield_strength": 0.40, "toughness": 0.15}
            },
            {
                "id": "CRYO_SUPERCONDUCTING_MAGNET",
                "name": "Superconducting Fusion & MRI Magnet Conduits",
                "sector": "Energy & Cryogenics",
                "desc": "Extreme 4.2 K liquid helium fracture toughness with low magnetic permeability (μ_r < 1.005).",
                "benchmark": "JJ1 Nitrogen-Strengthened Austenitic / CrCoNi",
                "git_ref": "Cryogenics Journal / CERN Superconducting Magnet Specs",
                "veto_elements": ["W", "Mo", "Ta", "Nb", "V"],
                "min_solidus_k": 1350.0,
                "min_ductility_pct": 28.0,
                "weights": {"toughness": 0.40, "ductility": 0.35, "yield_strength": 0.25}
            },
            {
                "id": "CLEAN_PEM_BIPOLAR_PLATE",
                "name": "PEM Electrolyzer & Fuel Cell Bipolar Plates",
                "sector": "Clean Energy & Hydrogen",
                "desc": "Low interfacial contact resistance and acidic corrosion resistance (pH 1-3) without noble metals.",
                "benchmark": "Grade 2 Ti (Pt/Ir-coated) / 316L / Pt-free HEA",
                "git_ref": "DOE Hydrogen Program / Int. J. Hydrogen Energy",
                "veto_elements": ["Pb", "Cd", "Mg", "Al", "Fe"],
                "min_solidus_k": 1300.0,
                "min_ductility_pct": 8.0,
                "weights": {"corrosion": 0.50, "yield_strength": 0.30, "density": 0.20}
            },
            {
                "id": "DEFENSE_BALLISTIC_ARMOR",
                "name": "High-Strain-Rate Ballistic Impact Strike Plates",
                "sector": "Defense & Security",
                "desc": "Dynamic Hugoniot elastic limit, adiabatic shear band resistance, and multi-hit spall suppression.",
                "benchmark": "Armox 500T / Ultra-High Hardness Armor (UHA)",
                "git_ref": "MIL-DTL-46100 / Int. J. Impact Engineering",
                "veto_elements": ["Bi", "Pb", "Cd", "Sn"],
                "min_solidus_k": 1400.0,
                "min_ductility_pct": 10.0,
                "weights": {"hardness": 0.35, "yield_strength": 0.35, "toughness": 0.30}
            },
            {
                "id": "ELEC_DIFFUSION_BARRIER",
                "name": "Semiconductor Thin-Film Diffusion Barriers",
                "sector": "Electronics & Semiconductors",
                "desc": "Boundary passivation preventing Cu/Si interdiffusion up to 800 °C in sub-3nm nodes.",
                "benchmark": "TaN / TiN / (AlCrTaTiZr)N High-Entropy Barrier",
                "git_ref": "IEEE Trans. Electron Devices / Applied Physics Letters",
                "veto_elements": ["Cu", "Au", "Ag", "Na", "K"],
                "min_solidus_k": 1500.0,
                "min_ductility_pct": 0.1,
                "weights": {"solidus": 0.50, "hardness": 0.30, "density": 0.20}
            },
            {
                "id": "SPACE_RADIATION_SHIELD",
                "name": "Deep-Space Cosmic Radiation Shielding & Lightweight Trusses",
                "sector": "Space Exploration & Defense",
                "desc": "High specific strength (E/rho), galactic cosmic ray/proton attenuation, and -150 C to +150 C thermal cycling stability.",
                "benchmark": "Al-Li 2195 / Al-Sc / W-Ta-Ti-V Graded RHEA",
                "git_ref": "NASA Technical Reports Server (NTRS) / Acta Astronautica",
                "veto_elements": ["Pb", "Hg", "Cd", "As"],
                "min_solidus_k": 900.0,
                "min_ductility_pct": 5.0,
                "weights": {"density": 0.40, "yield_strength": 0.35, "neutrons": 0.25}
            },
            {
                "id": "AUTO_EXHAUST_VALVE",
                "name": "Heavy-Duty Turbocharged Exhaust Valves & Manifolds",
                "sector": "Automotive & Heavy Transport",
                "desc": "Hot hardness (>250 HV at 800 C), cyclic thermal fatigue endurance, and resistance to fuel sulfur/lead combustion salt corrosion.",
                "benchmark": "Nimonic 80A / Inconel 751 / 21-4N Nitronic Steel",
                "git_ref": "SAE International Standards / ASTM F799",
                "veto_elements": ["Mg", "Zn", "Pb", "Bi"],
                "min_solidus_k": 1400.0,
                "min_ductility_pct": 8.0,
                "weights": {"solidus": 0.35, "yield_strength": 0.35, "oxidation": 0.30}
            },
            {
                "id": "QUANTUM_SUPERCONDUCTING_CAVITY",
                "name": "Superconducting RF Cavities & Qubit Interconnects",
                "sector": "Quantum Information & Accelerators",
                "desc": "Residual resistance ratio RRR > 300, Tc > 9.2 K, zero ferromagnetic hysteresis, and ultra-low microwave dielectric dissipation.",
                "benchmark": "Ultra-High Purity Niobium (RRR > 300) / Nb-47Ti / Nb3Sn",
                "git_ref": "CERN / Fermilab Superconducting RF Specifications",
                "veto_elements": ["Fe", "Co", "Ni", "Mn", "Cr", "Gd", "Dy"],
                "min_solidus_k": 1600.0,
                "min_ductility_pct": 15.0,
                "weights": {"solidus": 0.45, "ductility": 0.35, "toughness": 0.20}
            },
            {
                "id": "CHEM_ACID_AUTOCLAVE",
                "name": "High-Pressure Acid Digest Autoclaves & Exchangers",
                "sector": "Chemical Process Engineering",
                "desc": "Immunity to boiling concentrated mineral acids (HCl, H2SO4, HNO3) and transgranular chloride stress cracking under ASME Sec VIII.",
                "benchmark": "Zirconium 702 / Hastelloy B-3 / Tantalum Ta-2.5W",
                "git_ref": "ASME Boiler & Pressure Vessel Code Sec VIII / NACE",
                "veto_elements": ["Al", "Mg", "Zn", "Ca", "Pb"],
                "min_solidus_k": 1350.0,
                "min_ductility_pct": 12.0,
                "weights": {"corrosion": 0.55, "toughness": 0.25, "yield_strength": 0.20}
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
        wt_dict = atomic_to_weight_fractions(c_dict)
        raw_cost_kg, _ = compute_raw_alloy_cost(wt_dict, prefer_ferro=True)
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

                elif app_id == "AERO_HYPERSONIC_LEADING_EDGE":
                    s_ts = min(100.0, max(10.0, (ts - 1900.0) / 7.0))
                    s_ys = min(100.0, ys / 10.0)
                    s_ox = 90.0 if any(reg in ox.get("Regime", "") for reg in ["Alumina", "Chromia", "Hafnia", "Zirconia"]) else 40.0
                    score = 0.45 * s_ts + 0.35 * s_ys + 0.20 * s_ox
                    if ts < 2100.0:
                        bottleneck = f"Solidus temperature ({ts:.0f} K) insufficient for hypersonic stagnation point (>2100 K)."
                        advice = "Incorporate ultra-refractory metals (Hf, Ta, Zr) or boride/carbide ceramic formers."

                elif app_id == "NUCLEAR_FUSION_DIVERTOR":
                    s_ts = min(100.0, max(10.0, (ts - 2000.0) / 8.0))
                    s_neu = max(10.0, 100.0 - (sigma_barns / 5.0) * 80.0)
                    s_hv = min(100.0, hv / 5.0)
                    score = 0.50 * s_ts + 0.30 * s_neu + 0.20 * s_hv
                    if ts < 2200.0:
                        bottleneck = f"Melting point ({ts:.0f} K) below fusion divertor threshold (2200 K)."
                        advice = "Utilize W-Ta-Cr-V refractory multi-principal element architectures."

                elif app_id == "PETRO_SOUR_GAS_WELLHEAD":
                    s_pren = min(100.0, pren * 2.2)
                    s_ys = min(100.0, ys / 7.0)
                    s_tou = min(100.0, toughness * 0.5)
                    score = 0.45 * s_pren + 0.30 * s_ys + 0.25 * s_tou
                    if pren < 38.0:
                        bottleneck = f"PREN value ({pren:.1f}) below NACE MR0175 sour service standard (PREN >= 40)."
                        advice = "Increase Cr >= 21 at% and Mo >= 4 at% for pitting and stress cracking immunity."

                elif app_id == "TOOLING_COLD_PUNCH":
                    s_hv = min(100.0, hv / 7.0)
                    s_ys = min(100.0, ys / 9.0)
                    s_tou = min(100.0, toughness * 0.4)
                    score = 0.45 * s_hv + 0.40 * s_ys + 0.15 * s_tou
                    if hv < 600.0:
                        bottleneck = f"Hardness ({hv:.0f} HV) below cold-forming punch threshold (600+ HV)."
                        advice = "Introduce interstitial C/N/B or increase hard second-phase precipitation."

                elif app_id == "CRYO_SUPERCONDUCTING_MAGNET":
                    s_tou = min(100.0, toughness * 0.6)
                    s_duc = min(100.0, elong * 2.2)
                    s_ys = min(100.0, ys / 6.0)
                    score = 0.40 * s_tou + 0.35 * s_duc + 0.25 * s_ys
                    if "BCC" in phase and not "FCC" in phase:
                        score = min(score, 40.0)
                        bottleneck = "BCC lattice subject to 4.2 K brittle cleavage."
                        advice = "Ensure stable FCC matrix with high Ni/Cr/Co balance."

                elif app_id == "CLEAN_PEM_BIPOLAR_PLATE":
                    s_pren = min(100.0, pren * 2.4)
                    s_den = max(20.0, 100.0 - (density - 4.5) * 12.0)
                    score = 0.50 * s_pren + 0.30 * min(100.0, ys / 5.0) + 0.20 * s_den
                    if pren < 30.0:
                        bottleneck = f"Corrosion resistance in pH 1-3 sulfuric environment below threshold."
                        advice = "Enrich passive scale with Ti, Nb, Ta, or noble metal doping."

                elif app_id == "DEFENSE_BALLISTIC_ARMOR":
                    s_ys = min(100.0, ys / 12.0)
                    s_hv = min(100.0, hv / 6.0)
                    s_tou = min(100.0, toughness * 0.6)
                    score = 0.35 * s_ys + 0.35 * s_hv + 0.30 * s_tou
                    if ys < 900.0:
                        bottleneck = f"Dynamic yield strength below heavy ballistic projectile deformation limit."
                        advice = "Enhance grain boundary Hall-Petch strengthening and interstitial hardening."

                elif app_id == "ELEC_DIFFUSION_BARRIER":
                    s_ts = min(100.0, max(20.0, (ts - 1400.0) / 6.0))
                    s_hv = min(100.0, hv / 8.0)
                    score = 0.50 * s_ts + 0.30 * s_hv + 0.20 * max(20.0, 100.0 - (density - 8.0) * 8.0)
                    if ts < 1800.0:
                        bottleneck = f"Thermal stability insufficient for sub-3nm annealing cycle."
                        advice = "Incorporate refractory early transition metals (Ta, Nb, W, Ti)."

                elif app_id == "SPACE_RADIATION_SHIELD":
                    s_den = max(10.0, 100.0 - (density - 3.0) * 14.0)
                    s_ys = min(100.0, ys / 6.0)
                    s_neu = max(10.0, 100.0 - (sigma_barns / 10.0) * 80.0)
                    score = 0.40 * s_den + 0.35 * s_ys + 0.25 * s_neu
                    if density > 8.0:
                        bottleneck = f"Excessive density ({density:.2f} g/cm³) penalizes launch payload capacity."
                        advice = "Incorporate low-Z elements (Al, Ti, Sc, Li) to enhance specific strength."

                elif app_id == "AUTO_EXHAUST_VALVE":
                    s_ts = min(100.0, max(10.0, (ts - 1450.0) / 4.0))
                    s_ys = min(100.0, ys / 7.0)
                    s_ox = 95.0 if any(reg in ox.get("Regime", "") for reg in ["Alumina", "Chromia"]) else 45.0
                    score = 0.35 * s_ts + 0.35 * s_ys + 0.30 * s_ox
                    if s_ox < 60.0:
                        bottleneck = "Hot corrosion resistance requires protective Cr or Al passivating scale."
                        advice = "Ensure Cr >= 18 at% to resist combustion fuel contaminants."

                elif app_id == "QUANTUM_SUPERCONDUCTING_CAVITY":
                    ferro = sum(c_dict.get(el, 0.0) for el in ["Fe", "Co", "Ni", "Mn", "Cr"])
                    if ferro > 0.001:
                        score = 15.0
                        tier = "Unsuitable (Vetoed)"
                        bottleneck = f"Ferromagnetic atoms ({ferro*100:.1f} at%) destroy Cooper pair coherence."
                        advice = "Purify alloy to eliminate all 3d transition ferromagnetic elements."
                    else:
                        s_ts = min(100.0, max(20.0, (ts - 1600.0) / 8.0))
                        s_duc = min(100.0, elong * 2.5)
                        score = 0.50 * s_ts + 0.35 * s_duc + 0.15 * min(100.0, toughness * 0.5)

                elif app_id == "CHEM_ACID_AUTOCLAVE":
                    s_pren = min(100.0, pren * 2.5)
                    s_tou = min(100.0, toughness * 0.5)
                    s_ys = min(100.0, ys / 5.0)
                    score = 0.55 * s_pren + 0.25 * s_tou + 0.20 * s_ys
                    if pren < 35.0:
                        bottleneck = f"Pitting resistance equivalent (PREN = {pren:.1f}) insufficient for aggressive boiling acid service."
                        advice = "Increase Cr and Mo content or transition to Ta/Zr refractory chemistries."
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

            alloy_cost_kg, savings_pct, cost_rec = recommend_cost_optimization(
                elements=elements,
                at_comp=c_dict,
                wt_comp=wt_dict,
                thermo=thermo,
                mech=mech,
                app_id=app_id,
                raw_cost_kg=raw_cost_kg,
            )
            bench_cost_kg = estimate_benchmark_cost(bench, raw_cost_kg)

            scored_list.append({
                "id": app_id,
                "name": name,
                "sector": sector,
                "score": score,
                "tier": tier,
                "bottleneck": bottleneck,
                "advice": advice,
                "benchmark": bench,
                "git_reference": git_ref,
                "alloy_cost_usd_kg": alloy_cost_kg,
                "benchmark_cost_usd_kg": bench_cost_kg,
                "cost_savings_pct": savings_pct,
                "cost_recommendation": cost_rec,
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

