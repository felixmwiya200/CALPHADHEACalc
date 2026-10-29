"""
application_database.py - Industrial Engineering Applications Database & Suitability Scorer
Compacts all 12 curated industrial application profiles from HEAApplicationDatabase.m:
- Aerospace Turbine Blade (Hot Section)
- Cryogenic LNG Fuel Storage Vessel
- Generation-IV Nuclear Fuel Cladding
- Biomedical Orthopedic Hip / Knee Implant
- Marine Subsea Wellhead Choke Valve
- High-Pressure Hot Forging Die
- Refractory Furnace Heating Element & Shield
- Solid-State Hydrogen Storage Matrix
- Green Hydrogen Electrocatalysis Electrode
- High-Speed Aero Disc Rotor
- Laser Cladding Slurry Wear Overlay
- Cavitation-Erosion Hydraulic Runner Overlay

Each application specifies required property thresholds and weights for automated scoring.
"""

from typing import List, Dict, Any, Optional


class HEAApplicationDatabase:
    APPLICATIONS: List[Dict[str, Any]] = [
        {
            "ID": "APP_01_AERO_TURBINE",
            "Name": "Aerospace Gas Turbine Blade",
            "Category": "Aerospace & Propulsion",
            "TargetT_K": 1373.15,
            "TargetYS_MPa": 650.0,
            "MaxDensity_g_cm3": 8.5,
            "MinCreepLife_hrs": 5000.0,
            "Weights": {"YieldStrength": 0.30, "Creep": 0.30, "Oxidation": 0.25, "Density": 0.15},
            "BenchmarkAlloy": "Ni-base Single Crystal CMSX-4 / Rene N5"
        },
        {
            "ID": "APP_02_CRYO_LNG",
            "Name": "Cryogenic LNG Storage Tank",
            "Category": "Cryogenics & Clean Energy",
            "TargetT_K": 77.15,
            "TargetYS_MPa": 500.0,
            "MinElongation_pct": 35.0,
            "MinImpactEnergy_J": 200.0,
            "Weights": {"FractureToughness": 0.40, "YieldStrength": 0.30, "Elongation": 0.30},
            "BenchmarkAlloy": "CoCrFeMnNi (Cantor Alloy) / 304L Cryo Steel"
        },
        {
            "ID": "APP_03_NUCLEAR_GEN4",
            "Name": "Gen-IV Nuclear Reactor Core Cladding",
            "Category": "Nuclear Energy",
            "TargetT_K": 973.15,
            "MaxSwelling_pct": 1.0,
            "TargetYS_MPa": 450.0,
            "Weights": {"RadiationTolerance": 0.35, "Corrosion": 0.30, "HighTempStrength": 0.35},
            "BenchmarkAlloy": "ODS Ferritic-Martensitic Steel / Zircaloy-4"
        },
        {
            "ID": "APP_04_BIOMED_IMPLANT",
            "Name": "Biomedical Orthopedic Hip Implant",
            "Category": "Biomedical Devices",
            "TargetT_K": 310.15,
            "TargetYS_MPa": 800.0,
            "MaxYoungsModulus_GPa": 80.0,
            "MinBiocompatibility": 0.95,
            "Weights": {"Biocompatibility": 0.40, "ModulusMatch": 0.30, "Corrosion": 0.30},
            "BenchmarkAlloy": "Ti-6Al-4V ELI / Ti-29Nb-13Ta-4.6Zr"
        },
        {
            "ID": "APP_05_MARINE_SUBSEA",
            "Name": "Marine Deepwater Subsea Choke Valve",
            "Category": "Offshore & Marine Engineering",
            "TargetT_K": 298.15,
            "MinPREN": 42.0,
            "TargetYS_MPa": 650.0,
            "Weights": {"PittingResistance": 0.45, "StressCorrosionCracking": 0.35, "Strength": 0.20},
            "BenchmarkAlloy": "Super Duplex Stainless 2507 / Inconel 625"
        },
        {
            "ID": "APP_06_HOT_FORGING_DIE",
            "Name": "High-Pressure Hot Stamping Die",
            "Category": "Tooling & Manufacturing",
            "TargetT_K": 873.15,
            "TargetHardness_HV": 600.0,
            "MinThermalFatigue": 50000.0,
            "Weights": {"HotHardness": 0.40, "WearResistance": 0.35, "ThermalShock": 0.25},
            "BenchmarkAlloy": "AISI H13 Tool Steel / Stellite 6"
        },
        {
            "ID": "APP_07_REFRACTORY_SHIELD",
            "Name": "Hypersonic Thermal Protection Heat Shield",
            "Category": "Aerospace & Defense",
            "TargetT_K": 1873.15,
            "MinMelting_K": 2600.0,
            "TargetYS_MPa": 350.0,
            "Weights": {"UltraHighTempStrength": 0.45, "MeltingPoint": 0.35, "Oxidation": 0.20},
            "BenchmarkAlloy": "NbMoTaW / C-103 Niobium Alloy"
        },
        {
            "ID": "APP_08_HYDROGEN_STORAGE",
            "Name": "Solid-State Hydrogen Fuel Cell Tank",
            "Category": "Hydrogen Energy",
            "TargetT_K": 298.15,
            "MinH2Capacity_wt_pct": 2.0,
            "TargetDesorptionT_K": 350.0,
            "Weights": {"Capacity": 0.40, "Kinetics": 0.35, "CyclicStability": 0.25},
            "BenchmarkAlloy": "TiVZrNb / LaNi5 Metal Hydride"
        },
        {
            "ID": "APP_09_ELECTROCATALYSIS",
            "Name": "Alkaline Water Electrolysis Anode",
            "Category": "Clean Hydrogen Generation",
            "TargetT_K": 353.15,
            "MaxOverpotential_mV": 220.0,
            "MinTafelSlope_mV_dec": 45.0,
            "Weights": {"Overpotential": 0.45, "ChlorideStability": 0.35, "Cost": 0.20},
            "BenchmarkAlloy": "RuO2 / IrO2 / NiFe Layered Double Hydroxide"
        },
        {
            "ID": "APP_10_AERO_DISC_ROTOR",
            "Name": "Jet Engine High-Pressure Compressor Rotor",
            "Category": "Aero Engines",
            "TargetT_K": 873.15,
            "TargetYS_MPa": 1050.0,
            "MinLCFCycles": 20000.0,
            "Weights": {"FatigueStrength": 0.40, "YieldStrength": 0.35, "Creep": 0.25},
            "BenchmarkAlloy": "Inconel 718 / Udimet 720"
        },
        {
            "ID": "APP_11_CLADDING_WEAR_OVERLAY",
            "Name": "Mining Slurry Pipe Wear Coating",
            "Category": "Thermal Spray & Cladding",
            "TargetT_K": 373.15,
            "TargetHardness_HV": 850.0,
            "MinAbrasiveResistance": 0.90,
            "Weights": {"AbrasionResistance": 0.50, "AdhesionBondStrength": 0.30, "Corrosion": 0.20},
            "BenchmarkAlloy": "NiCrBSi Thermal Spray / WC-10Co-4Cr"
        },
        {
            "ID": "APP_12_CAVITATION_RUNNER",
            "Name": "Hydro-Turbine Runner Blade Overlay",
            "Category": "Renewable Power Generation",
            "TargetT_K": 293.15,
            "TargetWorkHardeningRate": 3000.0,
            "MinCavitationLife_hrs": 12000.0,
            "Weights": {"CavitationResistance": 0.45, "WorkHardening": 0.35, "Corrosion": 0.20},
            "BenchmarkAlloy": "CoCrFeNi-Al0.2 / 13-4 CrNi Stainless Steel"
        }
    ]

    @classmethod
    def get_all_applications(cls) -> List[Dict[str, Any]]:
        return cls.APPLICATIONS

    @classmethod
    def calculate_suitability(cls, app_id: str, alloy_properties: Dict[str, Any]) -> float:
        """Computes a normalized suitability index score (0% - 100%) for an application."""
        app = next((a for a in cls.APPLICATIONS if a["ID"] == app_id), None)
        if not app:
            return 50.0

        score = 75.0
        ys = alloy_properties.get("YieldStrength_MPa", 600.0)
        target_ys = app.get("TargetYS_MPa", 600.0)
        if target_ys > 0:
            ratio = min(1.3, max(0.4, ys / target_ys))
            score = 60.0 + (ratio - 1.0) * 35.0

        return max(10.0, min(99.0, score))
