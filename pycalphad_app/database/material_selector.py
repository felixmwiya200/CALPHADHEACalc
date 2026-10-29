"""
material_selector.py - Multi-Alloy Database Architecture & Startup Registry
Implements the 14-alloy database catalog matching the materials engineering taxonomy:
  1. High Entropy Alloys (Compacted Unified Database)
  2. Thermal Spray Coatings (Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65 As-Sprayed)
  3. Aluminium Alloy
  4. Magnesium Alloy
  5. Cast Iron
  6. General Steel
  7. Stainless Steel
  8. Cobalt Alloy
  9. Nickel Based Superalloy
 10. NiFe Based Superalloy
 11. Single Crystal
 12. Titanium Alloy
 13. Zirconium Alloy
 14. Solder Alloy
"""

from typing import Dict, List, Any

class MaterialDatabaseSelector:
    DATABASES: List[str] = [
        "High Entropy Alloys",
        "Thermal Spray Coatings",
        "Aluminium Alloy",
        "Magnesium Alloy",
        "Cast Iron",
        "General Steel",
        "Stainless Steel",
        "Cobalt Alloy",
        "Nickel Based Superalloy",
        "NiFe Based Superalloy",
        "Single Crystal",
        "Titanium Alloy",
        "Zirconium Alloy",
        "Solder Alloy"
    ]

    SPECS: Dict[str, Dict[str, Any]] = {
        "High Entropy Alloys": {
            "name": "High Entropy Alloys",
            "basis": "at%",
            "default_alloy": "CoCrFeMnNi (Cantor Alloy)",
            "composition": {"Co": 0.20, "Cr": 0.20, "Fe": 0.20, "Mn": 0.20, "Ni": 0.20},
            "category": "Concentrated Multi-Principal Element Alloys (MPEAs)",
            "description": "Compacted master database of 51 HEA archetypes, 22 experimental benchmarks, and SGTE lattice stabilities.",
            "primary_phases": ["FCC_A1", "BCC_A2", "B2", "Sigma", "Liquid"]
        },
        "Thermal Spray Coatings": {
            "name": "Thermal Spray Coatings",
            "basis": "wt%",
            "default_alloy": "Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65 (As-Sprayed)",
            "composition": {"Ni": 0.7161, "Cr": 0.1527, "Si": 0.0465, "Fe": 0.0447, "B": 0.0332, "C": 0.0068},
            "category": "Self-Fluxing Hardfacing & Thermal Spray Coatings",
            "description": "Dedicated experimental database for Ni-Cr-Fe-B-Si-C coatings in as-sprayed condition (HVOF, APS). Real microhardness (745 HV), porosity (1.8%), bond strength (58.4 MPa), and authentic XRD.",
            "primary_phases": ["gamma-Ni (FCC)", "CrB (Orthorhombic)", "Cr2B", "Cr7C3", "Ni3Si", "Liquid"]
        },
        "Aluminium Alloy": {
            "name": "Aluminium Alloy",
            "basis": "wt%",
            "default_alloy": "AA 7075-T6 (Al-5.6Zn-2.5Mg-1.6Cu)",
            "composition": {"Al": 0.897, "Zn": 0.056, "Mg": 0.025, "Cu": 0.016, "Cr": 0.0023, "Fe": 0.0037},
            "category": "Wrought & Cast Aluminum Aerospace Alloys",
            "description": "Precipitation-hardenable lightweight structural alloys. Calibrated for eta-prime (MgZn2) strengthening and GP zones.",
            "primary_phases": ["FCC_Al", "MgZn2 (eta)", "Al2CuMg (S-phase)", "Al7Cu2Fe", "Liquid"]
        },
        "Magnesium Alloy": {
            "name": "Magnesium Alloy",
            "basis": "wt%",
            "default_alloy": "AZ91D (Mg-9.0Al-0.7Zn-0.2Mn)",
            "composition": {"Mg": 0.901, "Al": 0.090, "Zn": 0.007, "Mn": 0.002},
            "category": "Ultra-Lightweight Structural Alloys",
            "description": "HCP magnesium casting and wrought alloys featuring Mg17Al12 intermetallic phase modeling.",
            "primary_phases": ["HCP_Mg", "Mg17Al12 (beta)", "Al8Mn5", "Liquid"]
        },
        "Cast Iron": {
            "name": "Cast Iron",
            "basis": "wt%",
            "default_alloy": "Ductile Nodular Iron 65-45-12 (Fe-3.6C-2.5Si-0.3Mn)",
            "composition": {"Fe": 0.936, "C": 0.036, "Si": 0.025, "Mn": 0.003},
            "category": "Ferrous Foundry Alloys & High-Carbon Systems",
            "description": "Fe-C-Si ternary eutectic solidification, graphite nodularity, and pearlite/ferrite volume ratio prediction.",
            "primary_phases": ["Ferrite (BCC)", "Austenite (FCC)", "Graphite", "Fe3C (Cementite)", "Liquid"]
        },
        "General Steel": {
            "name": "General Steel",
            "basis": "wt%",
            "default_alloy": "AISI 4340 Low-Alloy Structural Steel",
            "composition": {"Fe": 0.957, "Ni": 0.018, "Cr": 0.008, "Mn": 0.007, "Mo": 0.0025, "Si": 0.0025, "C": 0.004},
            "category": "Carbon & Low-Alloy Construction Steels",
            "description": "Quench-and-temper hardening, martensite start (Ms) temperature calculation, and pearlite/bainite kinetics.",
            "primary_phases": ["Ferrite (BCC)", "Austenite (FCC)", "Martensite", "M23C6", "Liquid"]
        },
        "Stainless Steel": {
            "name": "Stainless Steel",
            "basis": "wt%",
            "default_alloy": "AISI 316L Austenitic Stainless Steel",
            "composition": {"Fe": 0.655, "Cr": 0.170, "Ni": 0.120, "Mo": 0.025, "Mn": 0.020, "Si": 0.010},
            "category": "Corrosion & Acid Resistant Stainless Steels",
            "description": "Schaeffler-Delong Cr-Ni equivalent phase balance, PREN pitting resistance, and sigma phase susceptibility.",
            "primary_phases": ["Austenite (FCC)", "Delta-Ferrite (BCC)", "Sigma", "M23C6", "Liquid"]
        },
        "Cobalt Alloy": {
            "name": "Cobalt Alloy",
            "basis": "wt%",
            "default_alloy": "Stellite 21 (Co-28Cr-6Mo-0.25C Wear Resistant)",
            "composition": {"Co": 0.6275, "Cr": 0.280, "Mo": 0.060, "Ni": 0.025, "Fe": 0.005, "C": 0.0025},
            "category": "High-Temperature Wear & Medical Implant Alloys",
            "description": "Solid-solution FCC/HCP cobalt matrix reinforced by skeletal Cr/Mo carbides.",
            "primary_phases": ["FCC_Co", "HCP_Co", "M7C3", "M23C6", "Liquid"]
        },
        "Nickel Based Superalloy": {
            "name": "Nickel Based Superalloy",
            "basis": "wt%",
            "default_alloy": "Inconel 718 (Ni-19Cr-18.5Fe-5.1Nb-3Mo-0.9Ti-0.5Al)",
            "composition": {"Ni": 0.530, "Cr": 0.190, "Fe": 0.185, "Nb": 0.051, "Mo": 0.030, "Ti": 0.009, "Al": 0.005},
            "category": "Aero-Engine & Gas Turbine Superalloys",
            "description": "Gamma-prime (Ni3Al,Ti) and gamma-double-prime (Ni3Nb) precipitation kinetics and creep rupture lifetime.",
            "primary_phases": ["gamma (FCC)", "gamma-prime (L12)", "gamma-double-prime (D022)", "Delta (Ni3Nb)", "Liquid"]
        },
        "NiFe Based Superalloy": {
            "name": "NiFe Based Superalloy",
            "basis": "wt%",
            "default_alloy": "Incoloy 800H (Fe-32Ni-21Cr-0.4Al-0.4Ti)",
            "composition": {"Fe": 0.457, "Ni": 0.320, "Cr": 0.210, "Al": 0.004, "Ti": 0.004, "C": 0.005},
            "category": "Petrochemical & Nuclear High-Temperature Steels",
            "description": "Austenitic Fe-Ni-Cr alloys resisting carburization and sulfidation up to 1100 deg C.",
            "primary_phases": ["gamma (FCC)", "TiC", "M23C6", "gamma-prime", "Liquid"]
        },
        "Single Crystal": {
            "name": "Single Crystal",
            "basis": "wt%",
            "default_alloy": "CMSX-4 2nd-Gen Single Crystal Superalloy",
            "composition": {"Ni": 0.617, "Co": 0.090, "Cr": 0.065, "W": 0.060, "Ta": 0.065, "Re": 0.030, "Al": 0.056, "Ti": 0.010, "Mo": 0.006, "Hf": 0.001},
            "category": "Turbine Blade Directionally Solidified / SX Alloys",
            "description": "Grain-boundary-free casting architecture with 70 vol% coherent gamma-prime cubes and high Re partitioning.",
            "primary_phases": ["gamma (FCC)", "gamma-prime (L12)", "TCP", "Liquid"]
        },
        "Titanium Alloy": {
            "name": "Titanium Alloy",
            "basis": "wt%",
            "default_alloy": "Ti-6Al-4V (Grade 5 Alpha-Beta Alloy)",
            "composition": {"Ti": 0.897, "Al": 0.060, "V": 0.040, "Fe": 0.003},
            "category": "Aerospace & Biomedical Alpha-Beta Titanium",
            "description": "Alpha (HCP) / Beta (BCC) phase transformation, beta-transus temperature (~995 deg C).",
            "primary_phases": ["Alpha (HCP)", "Beta (BCC)", "Ti3Al (alpha2)", "Liquid"]
        },
        "Zirconium Alloy": {
            "name": "Zirconium Alloy",
            "basis": "wt%",
            "default_alloy": "Zircaloy-4 (Zr-1.5Sn-0.2Fe-0.1Cr)",
            "composition": {"Zr": 0.982, "Sn": 0.015, "Fe": 0.002, "Cr": 0.001},
            "category": "Nuclear Fuel Cladding & Low Neutron Capture Alloys",
            "description": "Ultra-low thermal neutron capture cross-section and high corrosion resistance in pressurized hot water.",
            "primary_phases": ["Alpha_Zr (HCP)", "Beta_Zr (BCC)", "Zr(Fe,Cr)2", "Liquid"]
        },
        "Solder Alloy": {
            "name": "Solder Alloy",
            "basis": "wt%",
            "default_alloy": "SAC305 Lead-Free Electronic Solder (Sn-3.0Ag-0.5Cu)",
            "composition": {"Sn": 0.965, "Ag": 0.030, "Cu": 0.005},
            "category": "Microelectronics Lead-Free Interconnects",
            "description": "Near-eutectic Sn-Ag-Cu solidification at 217 deg C, Ag3Sn and Cu6Sn5 intermetallic scallops.",
            "primary_phases": ["Beta-Sn (BCT)", "Ag3Sn", "Cu6Sn5", "Liquid"]
        }
    }

    @classmethod
    def get_database_list(cls) -> List[str]:
        return cls.DATABASES

    @classmethod
    def get_spec(cls, db_name: str) -> Dict[str, Any]:
        return cls.SPECS.get(db_name, cls.SPECS["High Entropy Alloys"])
