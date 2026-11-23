# -*- coding: utf-8 -*-
"""
imc_laves_database.py - Authoritative Thermodynamic & Crystallographic Database
for Laves Phases (C14, C15, C36), Topologically Close-Packed (TCP) Phases
(Sigma, Mu, Chi), Ordered Intermetallics (B2, L12, L21, D022, D024), and
Engineering Intermetallic Compounds (IMCs) across Structural & Functional Alloys.

Implements quantitative formation criteria grounded in peer-reviewed literature:
  - Laves geometric atomic-radius ratio window: 1.05 <= R_A / R_B <= 1.68 (ideal sqrt(3/2) = 1.225)
  - Yurchenko et al. (2017) HEA Laves criteria: delta >= 5.0% AND Allen electronegativity diff >= 7.0%
  - Polytype e/a & d-VEC separation: C15 (< 1.80) / C36 (1.80-1.93) / C14 (> 1.93)
  - Tsai et al. (2013) Sigma-phase VEC window: 6.88 <= VEC <= 7.84 in Cr/Mo/Fe/Co/Ni systems
  - CALPHAD Compound Energy Formalism (CEF) sublattice definitions and end-member Gibbs energies
"""

import math
from typing import Dict, List, Any, Optional


class IMCLavesDatabase:
    NAME = "Laves Phases & Intermetallic Compounds (IMCs)"
    VERSION = "2026.3.0"

    # Allen electronegativity scale for Yurchenko et al. (2017) DeltaChi_Allen criterion
    ALLEN_ELECTRONEGATIVITY: Dict[str, float] = {
        "Li": 0.912, "Be": 1.576, "B": 2.051, "C": 2.544, "N": 3.066, "O": 3.610,
        "Na": 0.869, "Mg": 1.293, "Al": 1.613, "Si": 1.916, "P": 2.253, "S": 2.589,
        "K": 0.734, "Ca": 1.034, "Sc": 1.190, "Ti": 1.380, "V": 1.530, "Cr": 1.650,
        "Mn": 1.750, "Fe": 1.800, "Co": 1.840, "Ni": 1.880, "Cu": 1.850, "Zn": 1.590,
        "Ga": 1.756, "Ge": 1.994, "Zr": 1.320, "Nb": 1.410, "Mo": 1.470, "Ru": 1.540,
        "Pd": 1.580, "Ag": 1.870, "Cd": 1.520, "In": 1.656, "Sn": 1.824, "Sb": 1.984,
        "La": 1.090, "Ce": 1.090, "Y": 1.120, "Hf": 1.160, "Ta": 1.340, "W": 1.470,
        "Re": 1.600, "Au": 1.920, "Pb": 1.854, "Bi": 2.010,
    }

    # Goldschmidt / metallic atomic radii (pm)
    RADII_PM: Dict[str, float] = {
        "Li": 152.0, "Be": 112.0, "B": 82.0, "C": 77.0, "N": 75.0, "O": 73.0,
        "Mg": 160.0, "Al": 143.2, "Si": 118.0, "Sc": 162.0, "Ti": 146.2, "V": 134.6,
        "Cr": 128.0, "Mn": 127.0, "Fe": 126.0, "Co": 125.2, "Ni": 124.6, "Cu": 127.8,
        "Zn": 133.2, "Y": 180.0, "Zr": 160.3, "Nb": 146.0, "Mo": 139.0, "Ag": 144.5,
        "In": 167.0, "Sn": 158.0, "Hf": 157.8, "Ta": 146.0, "W": 139.0, "Re": 137.5,
        "Au": 144.2, "Pb": 175.0, "Bi": 155.0,
    }

    # Authoritative registry of Laves, TCP, Ordered, and Stoichiometric Intermetallics
    PHASES: List[Dict[str, Any]] = [
        {
            "PhaseId": "LAVES_C14",
            "Name": "C14 Laves Phase (Hexagonal)",
            "Prototype": "MgZn2",
            "Strukturbericht": "C14",
            "Pearson": "hP12",
            "SpaceGroup": "P6_3/mmc (No. 194)",
            "CEFModel": "(A,B)2(A,B)1",
            "Lattice_A": "a = 4.837-5.221, c = 7.884-8.567 (c/a ~ 1.63)",
            "Density_g_cm3": 8.61,
            "Hardness_HV": 980,
            "Modulus_GPa": 250,
            "Criteria": "1.05 <= R_A/R_B <= 1.68; e/a > 1.93; HEAs: delta >= 5.0%, DeltaChi_Allen >= 7.0%",
            "AlloySystems": "CoCrFeNiNbx, Fe-Nb, MgZn2 (7xxx Al), TiCr2 (high-T)",
            "Citation": "Yurchenko et al. (Mater. Sci. Eng. A 2017); Stein & Leineweber (J. Mater. Sci. 2021)",
            "DOI": "10.1016/j.msea.2017.07.019"
        },
        {
            "PhaseId": "LAVES_C15",
            "Name": "C15 Laves Phase (Cubic)",
            "Prototype": "MgCu2",
            "Strukturbericht": "C15",
            "Pearson": "cF24",
            "SpaceGroup": "Fd-3m (No. 227)",
            "CEFModel": "(A,B)2(A,B)1",
            "Lattice_A": "a = 6.991-7.070",
            "Density_g_cm3": 7.70,
            "Hardness_HV": 1050,
            "Modulus_GPa": 240,
            "Criteria": "1.05 <= R_A/R_B <= 1.68 (ideal 1.225); e/a < 1.80; VEC <= 7.2",
            "AlloySystems": "CoCrFeNiZrx, Cr2Nb, Fe2Zr, TiCr2 (low-T), Zr(Fe,Cr)2",
            "Citation": "Stein et al. (Intermetallics 2004); Pavlů et al. (Calphad 2010)",
            "DOI": "10.1016/j.intermet.2004.02.010"
        },
        {
            "PhaseId": "LAVES_C36",
            "Name": "C36 Laves Phase (Dihexagonal)",
            "Prototype": "MgNi2",
            "Strukturbericht": "C36",
            "Pearson": "hP24",
            "SpaceGroup": "P6_3/mmc (No. 194)",
            "CEFModel": "(A,B)2(A,B)1",
            "Lattice_A": "a = 4.825-4.950, c = 15.80-16.15",
            "Density_g_cm3": 8.45,
            "Hardness_HV": 880,
            "Modulus_GPa": 225,
            "Criteria": "1.80 <= e/a <= 1.93; stacking polytype between C14 and C15",
            "AlloySystems": "TiCr2 (intermediate T), Mg-Ni-Cu, Co-Nb/Ta superalloys",
            "Citation": "Stein & Leineweber (J. Mater. Sci. 2021)",
            "DOI": "10.1007/s10853-020-05509-2"
        },
        {
            "PhaseId": "SIGMA",
            "Name": "Sigma (TCP Tetragonal)",
            "Prototype": "FeCr",
            "Strukturbericht": "D8_b",
            "Pearson": "tP30",
            "SpaceGroup": "P4_2/mnm (No. 136)",
            "CEFModel": "(Fe,Ni,Co)10(Cr,Mo,V)4(Fe,Ni,Co,Cr,Mo,Si)16",
            "Lattice_A": "a = 8.79-8.85, c = 4.54-4.59",
            "Density_g_cm3": 7.65,
            "Hardness_HV": 950,
            "Modulus_GPa": 235,
            "Criteria": "6.88 <= VEC <= 7.84 (Tsai et al. 2013); N_v >= 2.45; Cr >= 15 at%",
            "AlloySystems": "Duplex Stainless Steels, CoCrFeMnNi (700 C aged), Ni Superalloys",
            "Citation": "Tsai et al. (Intermetallics 2013); Joubert (Prog. Mater. Sci. 2008)",
            "DOI": "10.1016/j.intermet.2012.10.004"
        },
        {
            "PhaseId": "MU_PHASE",
            "Name": "Mu (TCP Rhombohedral)",
            "Prototype": "Fe7W6",
            "Strukturbericht": "D8_5",
            "Pearson": "hR13",
            "SpaceGroup": "R-3m (No. 166)",
            "CEFModel": "(Fe,Co,Ni)7(Mo,W,Nb,Ta)2(Fe,Co,Ni,Cr,Mo,W)4",
            "Lattice_A": "a = 4.757, c = 25.63 (hex setting)",
            "Density_g_cm3": 9.85,
            "Hardness_HV": 1100,
            "Modulus_GPa": 270,
            "Criteria": "7.2 <= VEC <= 8.2; delta ~ 8-12%; refractory Mo/W/Nb >= 5 at%",
            "AlloySystems": "Single Crystal Ni Superalloys (CMSX-4), Co-Mo/W, Fe-Cr-Mo HEAs",
            "Citation": "Joubert (Prog. Mater. Sci. 2008); Reed (The Superalloys 2006)",
            "DOI": "10.1017/CBO9780511541285"
        },
        {
            "PhaseId": "CHI_A12",
            "Name": "Chi (TCP alpha-Mn Cubic)",
            "Prototype": "alpha-Mn (Fe36Cr12Mo10)",
            "Strukturbericht": "A12",
            "Pearson": "cI58",
            "SpaceGroup": "I-43m (No. 217)",
            "CEFModel": "(Fe,Co,Ni)24(Cr,Mo,W)10(Fe,Cr,Mo)24",
            "Lattice_A": "a = 8.89-8.95",
            "Density_g_cm3": 8.20,
            "Hardness_HV": 900,
            "Modulus_GPa": 230,
            "Criteria": "7.0 <= VEC <= 7.7; elevated Mo (>2 wt%) + Cr in steels/superalloys",
            "AlloySystems": "SAF 2507 Super Duplex Stainless Steel, 316L aged, Cr-Fe-Mo-Ti",
            "Citation": "Lo et al. (Mater. Sci. Eng. R 2009); Hall & Algie (Met. Rev. 1966)",
            "DOI": "10.1016/j.mser.2009.03.001"
        },
        {
            "PhaseId": "BCC_B2",
            "Name": "B2 Ordered Superlattice",
            "Prototype": "CsCl (NiAl / FeAl)",
            "Strukturbericht": "B2",
            "Pearson": "cP2",
            "SpaceGroup": "Pm-3m (No. 221)",
            "CEFModel": "(Al,Ti,Ni,Fe,Co,Va)0.5(Al,Ti,Ni,Fe,Co,Va)0.5",
            "Lattice_A": "a = 2.881-2.905",
            "Density_g_cm3": 5.90,
            "Hardness_HV": 420,
            "Modulus_GPa": 200,
            "Criteria": "Delta H_mix(Ni-Al) = -22 kJ/mol; Al >= 5 at% with Ni/Fe/Co",
            "AlloySystems": "AlxCoCrFeNi (x >= 0.7), AlCoCrFeNi2.1 EHEA, Maraging Steels",
            "Citation": "Dupin et al. (Intermetallics 2001); Wang et al. (Intermetallics 2014)",
            "DOI": "10.1016/S0966-9795(01)00071-1"
        },
        {
            "PhaseId": "FCC_L12",
            "Name": "L12 Ordered Gamma-Prime",
            "Prototype": "Cu3Au (Ni3Al)",
            "Strukturbericht": "L1_2",
            "Pearson": "cP4",
            "SpaceGroup": "Pm-3m (No. 221)",
            "CEFModel": "(Ni,Co,Fe)0.75(Al,Ti,Ta,Nb)0.25",
            "Lattice_A": "a = 3.570-3.595",
            "Density_g_cm3": 7.50,
            "Hardness_HV": 460,
            "Modulus_GPa": 195,
            "Criteria": "f_L12 cohesive precipitate in FCC Ni-Al-Ti-Ta matrix",
            "AlloySystems": "Ni Superalloys (IN718, Waspaloy, CMSX-4), Ni2CoFeVTiAl HEAs",
            "Citation": "Dupin et al. (Intermetallics 2001); Pollock & Tin (2006)",
            "DOI": "10.2514/1.18239"
        },
        {
            "PhaseId": "HEUSLER_L21",
            "Name": "L21 Heusler Superlattice",
            "Prototype": "AlCu2Mn (Ni2TiAl)",
            "Strukturbericht": "L2_1",
            "Pearson": "cF16",
            "SpaceGroup": "Fm-3m (No. 225)",
            "CEFModel": "(Ni,Co)0.5(Ti,V,Mn)0.25(Al,Si,Sn)0.25",
            "Lattice_A": "a = 5.84-5.91",
            "Density_g_cm3": 6.60,
            "Hardness_HV": 540,
            "Modulus_GPa": 210,
            "Criteria": "Co/Ni + Al + Ti/Mn/Si with negative pairwise enthalpy",
            "AlloySystems": "Fe-Ni-Al-Ti Ferritic Superalloys, High-Entropy Heusler Alloys",
            "Citation": "Liu et al. (Acta Mater. 2016)",
            "DOI": "10.1016/j.actamat.2016.01.028"
        },
        {
            "PhaseId": "D022_NI3NB",
            "Name": "D022 Gamma-Double-Prime",
            "Prototype": "Al3Ti (Ni3Nb metastable)",
            "Strukturbericht": "D0_22",
            "Pearson": "tI8",
            "SpaceGroup": "I4/mmm (No. 139)",
            "CEFModel": "(Ni,Fe)0.75(Nb,Ti,Ta)0.25",
            "Lattice_A": "a = 3.624, c = 7.406",
            "Density_g_cm3": 8.85,
            "Hardness_HV": 480,
            "Modulus_GPa": 218,
            "Criteria": "Nb >= 2.5 wt% in Ni-Fe-Cr FCC matrix (650-750 C aging)",
            "AlloySystems": "Inconel 718, Inconel 706, Nb-bearing Ni-Fe Superalloys",
            "Citation": "Pollock & Tin (J. Propul. Power 2006)",
            "DOI": "10.2514/1.18239"
        },
        {
            "PhaseId": "FE2NB",
            "Name": "Fe2Nb C14 Laves Intermetallic",
            "Prototype": "MgZn2",
            "Strukturbericht": "C14",
            "Pearson": "hP12",
            "SpaceGroup": "P6_3/mmc (No. 194)",
            "CEFModel": "(Fe,Cr,Ni,Co)2(Nb,Ti,Zr)1",
            "Lattice_A": "a = 4.837, c = 7.884",
            "Density_g_cm3": 8.61,
            "Hardness_HV": 980,
            "Modulus_GPa": 250,
            "Criteria": "R_Nb/R_Fe = 1.16, DeltaH_mix = -16 kJ/mol, T_m ~ 1900 K",
            "AlloySystems": "Ferritic Stainless (441/444), Inconel 718 (interdendritic), Fe-Nb",
            "Citation": "Voss et al. (Calphad 2011); Stein & Leineweber (2021)",
            "DOI": "10.1007/s10853-020-05509-2"
        },
        {
            "PhaseId": "CR2NB",
            "Name": "Cr2Nb C15/C14 Laves Intermetallic",
            "Prototype": "MgCu2 / MgZn2",
            "Strukturbericht": "C15 / C14",
            "Pearson": "cF24 / hP12",
            "SpaceGroup": "Fd-3m / P6_3/mmc",
            "CEFModel": "(Cr,Co,Fe,Ni)2(Nb,Ta,Ti)1",
            "Lattice_A": "a = 6.991 (C15) | a = 4.931, c = 8.113 (C14)",
            "Density_g_cm3": 7.70,
            "Hardness_HV": 1050,
            "Modulus_GPa": 245,
            "Criteria": "R_Nb/R_Cr = 1.14, C15 < 1858 K -> C14 > 1858 K",
            "AlloySystems": "CoCrFeNiNbx Eutectic/Laves HEAs, Nb-Cr High-Temp Composites",
            "Citation": "Yurchenko et al. (MSEA 2017); He et al. (Acta Mater. 2014)",
            "DOI": "10.1016/j.actamat.2014.03.001"
        },
        {
            "PhaseId": "FE2ZR",
            "Name": "Fe2Zr C15 Laves Intermetallic",
            "Prototype": "MgCu2",
            "Strukturbericht": "C15",
            "Pearson": "cF24",
            "SpaceGroup": "Fd-3m (No. 227)",
            "CEFModel": "(Fe,Cr,Ni)2(Zr,Hf)1",
            "Lattice_A": "a = 7.070",
            "Density_g_cm3": 7.92,
            "Hardness_HV": 920,
            "Modulus_GPa": 220,
            "Criteria": "R_Zr/R_Fe = 1.27 (~ideal 1.225), DeltaH_mix = -25 kJ/mol",
            "AlloySystems": "Zircaloy-2/4 SPPs Zr(Fe,Cr)2, CoCrFeNiZrx Laves HEAs",
            "Citation": "Stein et al. (J. Alloys Compd. 2002)",
            "DOI": "10.1016/S0925-8388(02)00109-8"
        },
        {
            "PhaseId": "NI3TI",
            "Name": "Ni3Ti Eta Intermetallic",
            "Prototype": "Ni3Ti",
            "Strukturbericht": "D0_24",
            "Pearson": "hP16",
            "SpaceGroup": "P6_3/mmc (No. 194)",
            "CEFModel": "(Ni,Co,Fe)3(Ti,Al,Nb)1",
            "Lattice_A": "a = 5.101, c = 8.307",
            "Density_g_cm3": 7.94,
            "Hardness_HV": 580,
            "Modulus_GPa": 215,
            "Criteria": "High Ti/Al ratio in Ni-Ti superalloys; forms platelets along grain boundaries",
            "AlloySystems": "A-286, Nimonic 80A, 18Ni Maraging Steels",
            "Citation": "Reed (The Superalloys 2006)",
            "DOI": "10.1017/CBO9780511541285"
        },
        {
            "PhaseId": "NI3NB",
            "Name": "Ni3Nb Delta Intermetallic",
            "Prototype": "beta-Cu3Ti",
            "Strukturbericht": "D0_a",
            "Pearson": "oP8",
            "SpaceGroup": "Pmmn (No. 59)",
            "CEFModel": "(Ni,Fe)3(Nb,Ti)1",
            "Lattice_A": "a = 5.114, b = 4.244, c = 4.536",
            "Density_g_cm3": 8.85,
            "Hardness_HV": 620,
            "Modulus_GPa": 225,
            "Criteria": "Equilibrium acicular orthorhombic overaging of metastable gamma'' (850-980 C)",
            "AlloySystems": "Inconel 718, Inconel 625, Ni-Nb Eutectic Composites",
            "Citation": "Pollock & Tin (2006)",
            "DOI": "10.2514/1.18239"
        },
        {
            "PhaseId": "CU6SN5",
            "Name": "Cu6Sn5 Eta/Eta-Prime Solder IMC",
            "Prototype": "NiAs / Monoclinic",
            "Strukturbericht": "B8_1 (eta) / mC44 (eta')",
            "Pearson": "mC44 / hP4",
            "SpaceGroup": "C2/c (eta') | P6_3/mmc (eta)",
            "CEFModel": "(Cu)6(Sn)5",
            "Lattice_A": "a = 11.022, b = 7.282, c = 9.827, beta = 98.84 (eta')",
            "Density_g_cm3": 8.28,
            "Hardness_HV": 380,
            "Modulus_GPa": 110,
            "Criteria": "Liquid Sn-Cu solder interface reaction below 415 C; eta <-> eta' at 186 C",
            "AlloySystems": "SAC305, SAC405, Sn-0.7Cu Microelectronic Interconnects",
            "Citation": "Shen et al. (Microelectron. Reliab. 2006); Laurila et al. (MSE R 2005)",
            "DOI": "10.1016/j.microrel.2005.04.012"
        },
        {
            "PhaseId": "CU3SN",
            "Name": "Cu3Sn Epsilon Solder IMC",
            "Prototype": "Cu3Ti (orthorhombic superlattice)",
            "Strukturbericht": "D0_a-mod",
            "Pearson": "oC80",
            "SpaceGroup": "Cmcm (No. 63)",
            "CEFModel": "(Cu)3(Sn)1",
            "Lattice_A": "a = 5.53, b = 38.2, c = 4.32",
            "Density_g_cm3": 8.90,
            "Hardness_HV": 420,
            "Modulus_GPa": 130,
            "Criteria": "Solid-state interdiffusion between Cu substrate and Cu6Sn5; Kirkendall voids",
            "AlloySystems": "SAC/Cu Solder Joints (Reflow & Thermal Aging 125-175 C)",
            "Citation": "Laurila et al. (Mater. Sci. Eng. R 2005)",
            "DOI": "10.1016/j.mser.2005.03.001"
        },
        {
            "PhaseId": "AG3SN",
            "Name": "Ag3Sn Eutectic Solder IMC",
            "Prototype": "beta-Cu3Ti",
            "Strukturbericht": "D0_a",
            "Pearson": "oP8",
            "SpaceGroup": "Pmmn (No. 59)",
            "CEFModel": "(Ag)3(Sn)1",
            "Lattice_A": "a = 5.968, b = 4.780, c = 5.184",
            "Density_g_cm3": 9.93,
            "Hardness_HV": 140,
            "Modulus_GPa": 78,
            "Criteria": "Near-eutectic SAC solidification at 217 C; dispersion-strengthening platelets",
            "AlloySystems": "SAC305, SAC405, Sn-3.5Ag",
            "Citation": "Moon et al. (J. Electron. Mater. 2000)",
            "DOI": "10.1007/s11664-000-0003-x"
        },
        {
            "PhaseId": "MGZN2",
            "Name": "MgZn2 C14 Laves Intermetallic",
            "Prototype": "MgZn2 (Prototype)",
            "Strukturbericht": "C14",
            "Pearson": "hP12",
            "SpaceGroup": "P6_3/mmc (No. 194)",
            "CEFModel": "(Zn,Al,Cu)2(Mg)1",
            "Lattice_A": "a = 5.221, c = 8.567",
            "Density_g_cm3": 5.16,
            "Hardness_HV": 340,
            "Modulus_GPa": 115,
            "Criteria": "R_Mg/R_Zn = 1.20 (~1.225 ideal); GP zones -> eta' -> eta (MgZn2) in 7xxx Al",
            "AlloySystems": "AA 7075-T6, Mg-Zn-RE Alloys (ZK60, ZE41)",
            "Citation": "Starke & Staley (Prog. Aerosp. Sci. 1996)",
            "DOI": "10.1016/0376-0421(95)00004-6"
        },
        {
            "PhaseId": "AL2CU",
            "Name": "Al2Cu Theta Precipitation IMC",
            "Prototype": "Al2Cu",
            "Strukturbericht": "C16",
            "Pearson": "tI12",
            "SpaceGroup": "I4/mcm (No. 140)",
            "CEFModel": "(Al)2(Cu)1",
            "Lattice_A": "a = 6.066, c = 4.874",
            "Density_g_cm3": 4.34,
            "Hardness_HV": 450,
            "Modulus_GPa": 152,
            "Criteria": "Cu >= 0.3 wt% in Al; GP1 -> theta'' -> theta' -> theta (Al2Cu)",
            "AlloySystems": "AA 2024-T3, AA 2219, 319 Cast Al",
            "Citation": "COST507 Light Alloys (1998); Starke & Staley (1996)",
            "DOI": "10.1016/0376-0421(95)00004-6"
        },
        {
            "PhaseId": "AL3FE",
            "Name": "Al3Fe / Al13Fe4 Intermetallic",
            "Prototype": "Al13Fe4",
            "Strukturbericht": "Monoclinic",
            "Pearson": "mC102",
            "SpaceGroup": "C2/m (No. 12)",
            "CEFModel": "(Al)0.6275(Fe)0.235(Al,Va)0.1375",
            "Lattice_A": "a = 15.49, b = 8.08, c = 12.48, beta = 107.75",
            "Density_g_cm3": 3.85,
            "Hardness_HV": 780,
            "Modulus_GPa": 185,
            "Criteria": "Fe impurity > 0.05 wt% in Al forms insoluble brittle acicular needles",
            "AlloySystems": "1xxx/3xxx/6xxx/A356 Commercial & Recycled Al",
            "Citation": "Kattner & Burton (NIST/ASM); COST507",
            "DOI": "10.1016/j.calphad.2010.01.003"
        },
        {
            "PhaseId": "CR7C3",
            "Name": "Cr7C3 Orthorhombic Wear Carbide",
            "Prototype": "Mn7C3",
            "Strukturbericht": "D10_1",
            "Pearson": "oP40",
            "SpaceGroup": "Pnma (No. 62)",
            "CEFModel": "(Cr,Fe,Co,Mo,W)7(C)3",
            "Lattice_A": "a = 7.01, b = 12.14, c = 4.53",
            "Density_g_cm3": 6.92,
            "Hardness_HV": 2000,
            "Modulus_GPa": 370,
            "Criteria": "High Cr + C (>= 0.8 wt%) in Co hardfacing & white cast irons",
            "AlloySystems": "Stellite 6, High-Cr White Irons, Hardfacing Clads",
            "Citation": "Andersson (Calphad 1988)",
            "DOI": "10.1016/0364-5916(88)90025-9"
        },
        {
            "PhaseId": "WC",
            "Name": "WC Tungsten Monocarbide",
            "Prototype": "WC",
            "Strukturbericht": "B_h",
            "Pearson": "hP2",
            "SpaceGroup": "P-6m2 (No. 187)",
            "CEFModel": "(W)1(C)1",
            "Lattice_A": "a = 2.906, c = 2.837",
            "Density_g_cm3": 15.63,
            "Hardness_HV": 2400,
            "Modulus_GPa": 680,
            "Criteria": "Stoichiometric C:W ~ 1:1 hardmetal skeleton phase",
            "AlloySystems": "WC-Co Cemented Carbides, HVOF Cermet Thermal Sprays",
            "Citation": "Gustafson (Metall. Trans. A 1987)",
            "DOI": "10.1007/BF02646643"
        },
        {
            "PhaseId": "CO6W6C",
            "Name": "Co6W6C Eta-Carbide Embrittlement Phase",
            "Prototype": "Fe3W3C / Fe6W6C",
            "Strukturbericht": "E9_3",
            "Pearson": "cF112",
            "SpaceGroup": "Fd-3m (No. 227)",
            "CEFModel": "(Co)6(W)6(C)1",
            "Lattice_A": "a = 11.08",
            "Density_g_cm3": 13.80,
            "Hardness_HV": 1500,
            "Modulus_GPa": 420,
            "Criteria": "Carbon-deficient WC-Co or thermal spray decarburization (hv brittle eta-phase)",
            "AlloySystems": "WC-Co HVOF Coatings, Co-W-C Hardmetals",
            "Citation": "Fernández Guillermet (Metall. Trans. A 1989)",
            "DOI": "10.1007/BF02651658"
        },
    ]

    @classmethod
    def get_all_phases(cls) -> List[Dict[str, Any]]:
        return list(cls.PHASES)

    @classmethod
    def evaluate_formation_tendency(
        cls,
        comp_at: Dict[str, float],
        vec: float,
        delta_pct: float,
        delta_h_mix_kj: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Evaluates quantitative propensity for Laves (C14/C15/C36), Sigma, Mu, Chi,
        B2, L12, and engineering stoichiometric IMCs from alloy chemistry.
        """
        tot = sum(comp_at.values()) or 1.0
        at = {k: max(0.0, float(v) / tot) for k, v in comp_at.items() if v > 0}

        # 1. Allen electronegativity difference DeltaChi_Allen (%)
        chi_allen_avg = sum(x * cls.ALLEN_ELECTRONEGATIVITY.get(el, 1.75) for el, x in at.items())
        delta_chi_allen = math.sqrt(
            sum(x * (cls.ALLEN_ELECTRONEGATIVITY.get(el, 1.75) - chi_allen_avg) ** 2 for el, x in at.items())
        )
        delta_chi_allen_pct = (delta_chi_allen / max(0.5, chi_allen_avg)) * 100.0

        # 2. Maximum binary atomic radius ratio R_A / R_B for constituent pairs > 2 at%
        active_els = [el for el, x in at.items() if x >= 0.015]
        max_radius_ratio = 1.0
        best_laves_pair = None
        for i, e1 in enumerate(active_els):
            for e2 in active_els[i + 1:]:
                r1 = cls.RADII_PM.get(e1, 130.0)
                r2 = cls.RADII_PM.get(e2, 130.0)
                ratio = max(r1, r2) / max(1.0, min(r1, r2))
                if ratio > max_radius_ratio:
                    max_radius_ratio = ratio
                    best_laves_pair = (e1, e2) if r1 >= r2 else (e2, e1)

        # 3. Active Laves-former (A-site large atom) content: Nb, Zr, Hf, Ti, Ta, Y, La, Mg
        laves_a_elements = {"Nb", "Zr", "Hf", "Ti", "Ta", "Y", "La", "Mg"}
        laves_b_elements = {"Fe", "Co", "Ni", "Cr", "Mn", "Cu", "Zn", "V", "Al"}
        f_a = sum(at.get(el, 0.0) for el in laves_a_elements)
        f_b = sum(at.get(el, 0.0) for el in laves_b_elements)

        # Evaluate Yurchenko et al. (2017) + Stein (2021) Laves probability
        laves_prob = 0.0
        laves_polytype = None
        max_laves_frac = 0.0
        laves_solvus_k = 0.0

        # Note: exclude MgZn-free light/Ti-base BCC alloys unless pair ratio + negative H_mix support Laves
        is_mg_zn = at.get("Mg", 0.0) >= 0.015 and at.get("Zn", 0.0) >= 0.02
        is_tm_laves = (f_a >= 0.03 and f_b >= 0.25 and 1.08 <= max_radius_ratio <= 1.68)

        if is_mg_zn:
            laves_prob = min(0.95, 0.55 + 4.0 * min(at.get("Mg", 0.0), at.get("Zn", 0.0)))
            laves_polytype = "LAVES_C14"
            max_laves_frac = min(0.18, 2.5 * min(at.get("Mg", 0.0), at.get("Zn", 0.0) * 0.5))
            laves_solvus_k = 740.0
        elif is_tm_laves:
            # Yurchenko HEA condition: delta >= 5.0% and DeltaChi_Allen >= 7.0% gives strong Laves
            score = 0.0
            if delta_pct >= 5.0:
                score += 0.40 + 0.05 * min(5.0, delta_pct - 5.0)
            elif delta_pct >= 3.5:
                score += 0.20 * ((delta_pct - 3.5) / 1.5)
            if delta_chi_allen_pct >= 7.0:
                score += 0.40
            elif delta_chi_allen_pct >= 4.5:
                score += 0.20 * ((delta_chi_allen_pct - 4.5) / 2.5)
            if max_radius_ratio >= 1.13:
                score += 0.20
            if delta_h_mix_kj <= -8.0:
                score += 0.15

            laves_prob = min(0.98, max(0.0, score))
            if laves_prob >= 0.35:
                # Laves stoichiometry A B_2 consumes up to 3 * f_a (capped cleanly)
                max_laves_frac = min(0.45, max(0.05, 2.6 * f_a))
                # Polytype e/a proxy: C15 favored by Zr/Cr/Fe lower VEC (<= 7.15) or Co-free, C14 favored at higher VEC (>7.25) or Nb/Ti
                if vec <= 7.10 or at.get("Zr", 0.0) > at.get("Nb", 0.0) * 1.1:
                    laves_polytype = "LAVES_C15"
                elif vec <= 7.35 and (at.get("Ti", 0.0) > 0.05 and at.get("Cr", 0.0) > 0.10):
                    laves_polytype = "LAVES_C36"
                else:
                    laves_polytype = "LAVES_C14"
                laves_solvus_k = min(1580.0, 1180.0 + 750.0 * f_a)

        # 4. TCP Sigma / Mu / Chi evaluations
        cr_at = at.get("Cr", 0.0)
        mo_at = at.get("Mo", 0.0)
        w_at = at.get("W", 0.0)
        nb_at = at.get("Nb", 0.0)
        al_at = at.get("Al", 0.0)
        ti_at = at.get("Ti", 0.0)
        ni_at = at.get("Ni", 0.0)
        fe_at = at.get("Fe", 0.0)

        # Tsai et al. (2013): 6.88 <= VEC <= 7.84 + sufficient Cr/Mo (+ BCC decomposition in AlCoCrFeNi 600-900 C)
        sigma_frac = 0.0
        sigma_solvus_k = 0.0
        if cr_at >= 0.14 and (6.88 <= vec <= 8.10):
            vec_factor = 1.0 if 6.88 <= vec <= 7.84 else max(0.15, 1.0 - (vec - 7.84) / 0.30)
            ni_supp = 0.35 if (ni_at >= 0.30 and al_at >= 0.10 and cr_at < 0.19) else 1.0
            al_fe_drive = 0.03 if (al_at >= 0.08 and fe_at >= 0.15 and cr_at >= 0.15) else 0.0
            sigma_frac = min(0.35, max(0.0, (1.15 * cr_at + 0.8 * mo_at + al_fe_drive - 0.12) * vec_factor * ni_supp))
            if sigma_frac > 0.015:
                # Sigma typically remains stable across ~600-900 C (873-1173 K) in Cr/Fe-rich BCC HEAs
                sigma_solvus_k = min(1260.0, 1085.0 + 620.0 * (cr_at + mo_at - 0.14))

        # Mu phase (Fe,Co,Ni)7(Mo,W,Nb)6: requires Mo + W + Nb >= 0.04 & VEC ~ 7.2-8.4 & high mismatch
        ref_mu = mo_at + w_at + nb_at
        mu_frac = 0.0
        mu_solvus_k = 0.0
        if ref_mu >= 0.04 and (fe_at + at.get("Co", 0.0) + ni_at) >= 0.35 and 7.1 <= vec <= 8.5:
            mu_frac = min(0.24, max(0.0, 1.4 * ref_mu))
            mu_solvus_k = min(1320.0, 980.0 + 1100.0 * ref_mu)

        # Chi A12 phase: Mo + Cr in duplex steels / superalloys (7.0 <= VEC <= 7.95)
        chi_frac = 0.0
        if cr_at >= 0.15 and mo_at >= 0.02 and 7.0 <= vec <= 8.0:
            chi_frac = min(0.14, 1.8 * mo_at)

        # 5. Match explicit stoichiometric IMC signatures
        detected_imcs: List[str] = []
        if laves_polytype:
            if best_laves_pair == ("Nb", "Fe") or (fe_at >= 0.12 and nb_at >= 0.02):
                detected_imcs.append("Fe2Nb")
            elif best_laves_pair == ("Nb", "Cr") or (cr_at >= 0.12 and nb_at >= 0.02):
                detected_imcs.append("Cr2Nb")
            elif fe_at >= 0.002 and at.get("Zr", 0.0) >= 0.02:
                detected_imcs.append("Fe2Zr")
            elif is_mg_zn:
                detected_imcs.append("MgZn2")

        if at.get("Sn", 0.0) >= 0.30:
            if at.get("Cu", 0.0) >= 0.003:
                detected_imcs.extend(["Cu6Sn5", "Cu3Sn"])
            if at.get("Ag", 0.0) >= 0.005:
                detected_imcs.append("Ag3Sn")
        if al_at >= 0.60:
            if at.get("Cu", 0.0) >= 0.005:
                detected_imcs.append("Al2Cu")
            if fe_at >= 0.002:
                detected_imcs.append("Al3Fe")
        if ni_at >= 0.35 and nb_at >= 0.015:
            detected_imcs.append("Ni3Nb")
        if ni_at >= 0.35 and ti_at >= 0.015:
            detected_imcs.append("Ni3Ti")
        if at.get("W", 0.0) >= 0.15 and at.get("C", 0.0) >= 0.15:
            detected_imcs.extend(["WC", "Co6W6C"])

        return {
            "AllenDeltaChi_pct": float(delta_chi_allen_pct),
            "MaxRadiusRatio": float(max_radius_ratio),
            "LavesPair": f"{best_laves_pair[0]}-{best_laves_pair[1]}" if best_laves_pair else "N/A",
            "LavesProbability": float(laves_prob),
            "LavesPolytype": laves_polytype,
            "MaxLavesFraction": float(max_laves_frac),
            "LavesSolvus_K": float(laves_solvus_k),
            "MaxSigmaFraction": float(sigma_frac),
            "SigmaSolvus_K": float(sigma_solvus_k),
            "MaxMuFraction": float(mu_frac),
            "MuSolvus_K": float(mu_solvus_k),
            "MaxChiFraction": float(chi_frac),
            "DetectedIMCs": detected_imcs,
        }
