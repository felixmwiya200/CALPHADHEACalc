# -*- coding: utf-8 -*-
"""
oxide_database.py - Thermodynamic & Kinetic Database of Oxides in High-Entropy Alloys
Complete 1:1 translation of App/HEAOxideDatabase.m to native Python.

Contains assessed standard Gibbs free energies of formation (Ellingham lines):
    Delta G_f(T) = A + B * T  [J / mol O2]
Pilling-Bedworth Ratios (PBR), theoretical densities, melting points, volatility thresholds,
and protectiveness classifications for 54 binary, multi-component, and spinel oxides.

References:
    - Kubaschewski & Alcock, "Metallurgical Thermochemistry", 5th Ed., Pergamon Press.
    - NIST-JANAF Thermochemical Tables, 4th Ed., J. Phys. Chem. Ref. Data.
    - Reed (1971), "Free Energy of Formation of Binary Compounds", MIT Press.
    - Rost et al. (2015), Nature Communications 6:8485 (Entropy-stabilized oxides).
    - Butler et al. (2018), Oxid. Met. 90:199-223 (AlxCoCrFeNi oxidation).
    - Senkov et al. (2018), J. Mater. Res. 33:3092 (RHEA oxidation & pesting).
"""

from typing import List, Dict, Any, Optional


class HEAOxideDatabase:
    """
    Comprehensive Thermodynamic & Kinetic Database of Oxides in High-Entropy Alloys.
    Holds assessed properties for all 54 candidate oxide species.
    """
    OXIDES: List[Dict[str, Any]] = [
        {
            "Formula": "Al2O3", "Name": "\\alpha-Alumina", "Elements": ["Al"],
            "A": -1120000.0, "B": 214.0, "PBR": 1.28, "Density": 3.98, "Tm_K": 2345.0,
            "Class": "Protective Alumina", "Color": "#1A9E47",
            "Citation": ""
        },
        {
            "Formula": "Cr2O3", "Name": "Eskolaite", "Elements": ["Cr"],
            "A": -755000.0, "B": 180.0, "PBR": 2.07, "Density": 5.22, "Tm_K": 2708.0,
            "Class": "Protective Chromia", "Color": "#1F66D9",
            "Citation": ""
        },
        {
            "Formula": "SiO2", "Name": "Silica", "Elements": ["Si"],
            "A": -910000.0, "B": 175.0, "PBR": 2.15, "Density": 2.65, "Tm_K": 1986.0,
            "Class": "Protective Silica", "Color": "#0DA6BF",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "TiO2", "Name": "Rutile", "Elements": ["Ti"],
            "A": -944000.0, "B": 185.0, "PBR": 1.77, "Density": 4.23, "Tm_K": 2116.0,
            "Class": "Refractory Scale", "Color": "#3380B2",
            "Citation": "Kubaschewski & Alcock (1979)"
        },
        {
            "Formula": "ZrO2", "Name": "Baddeleyite", "Elements": ["Zr"],
            "A": -1100000.0, "B": 190.0, "PBR": 1.56, "Density": 5.68, "Tm_K": 2988.0,
            "Class": "Refractory Scale", "Color": "#268CA6",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "HfO2", "Name": "Hafnia", "Elements": ["Hf"],
            "A": -1140000.0, "B": 192.0, "PBR": 1.62, "Density": 9.68, "Tm_K": 3031.0,
            "Class": "Refractory Scale", "Color": "#1A8099",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "Nb2O5", "Name": "Niobium Pentoxide", "Elements": ["Nb"],
            "A": -760000.0, "B": 168.0, "PBR": 2.68, "Density": 4.6, "Tm_K": 1785.0,
            "Class": "Refractory Scale", "Color": "#7359A6",
            "Citation": "Senkov et al. (2018)"
        },
        {
            "Formula": "NbO2", "Name": "Niobium Dioxide", "Elements": ["Nb"],
            "A": -792000.0, "B": 172.0, "PBR": 1.95, "Density": 5.9, "Tm_K": 2175.0,
            "Class": "Refractory Suboxide", "Color": "#8066B2",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "Ta2O5", "Name": "Tantalum Pentoxide", "Elements": ["Ta"],
            "A": -815000.0, "B": 165.0, "PBR": 2.47, "Density": 8.2, "Tm_K": 2145.0,
            "Class": "Refractory Scale", "Color": "#5973B2",
            "Citation": "Senkov et al. (2018)"
        },
        {
            "Formula": "Y2O3", "Name": "Yttria", "Elements": ["Y"],
            "A": -1270000.0, "B": 205.0, "PBR": 1.14, "Density": 5.01, "Tm_K": 2698.0,
            "Class": "Rare-Earth Protective", "Color": "#14AD59",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "Sc2O3", "Name": "Scandia", "Elements": ["Sc"],
            "A": -1260000.0, "B": 200.0, "PBR": 1.25, "Density": 3.86, "Tm_K": 2758.0,
            "Class": "Refractory Oxide", "Color": "#1FA666",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "MoO3", "Name": "Molybdenum Trioxide (Volatile >700C)", "Elements": ["Mo"],
            "A": -495000.0, "B": 162.0, "PBR": 3.4, "Density": 4.69, "Tm_K": 1068.0,
            "Class": "Catastrophic Volatile", "Color": "#E62626",
            "Citation": ""
        },
        {
            "Formula": "MoO2", "Name": "Molybdenum Dioxide", "Elements": ["Mo"],
            "A": -588000.0, "B": 170.0, "PBR": 2.11, "Density": 6.47, "Tm_K": 2873.0,
            "Class": "Volatile Precursor", "Color": "#D94C33",
            "Citation": "Reed (1971)"
        },
        {
            "Formula": "WO3", "Name": "Tungsten Trioxide (Volatile >800C)", "Elements": ["W"],
            "A": -560000.0, "B": 175.0, "PBR": 3.35, "Density": 7.16, "Tm_K": 1746.0,
            "Class": "Catastrophic Volatile", "Color": "#D9331A",
            "Citation": "Gorr et al. (2017)"
        },
        {
            "Formula": "WO2", "Name": "Tungsten Dioxide", "Elements": ["W"],
            "A": -589000.0, "B": 165.0, "PBR": 2.08, "Density": 10.8, "Tm_K": 2023.0,
            "Class": "Volatile Precursor", "Color": "#CC5926",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "V2O5", "Name": "Vanadium Pentoxide (Molten >690C)", "Elements": ["V"],
            "A": -620000.0, "B": 178.0, "PBR": 3.19, "Density": 3.36, "Tm_K": 963.0,
            "Class": "Low-Melting Catastrophic", "Color": "#F2400D",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "VO2", "Name": "Vanadium Dioxide", "Elements": ["V"],
            "A": -714000.0, "B": 180.0, "PBR": 2.16, "Density": 4.34, "Tm_K": 2240.0,
            "Class": "Intermediate Oxide", "Color": "#BF661A",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "MnO", "Name": "Manganosite", "Elements": ["Mn"],
            "A": -770000.0, "B": 145.0, "PBR": 1.77, "Density": 5.37, "Tm_K": 2115.0,
            "Class": "Transition Metal Oxide", "Color": "#997340",
            "Citation": "Holcomb et al. (2015)"
        },
        {
            "Formula": "Mn3O4", "Name": "Hausmannite", "Elements": ["Mn"],
            "A": -690000.0, "B": 160.0, "PBR": 2.05, "Density": 4.86, "Tm_K": 1837.0,
            "Class": "Transition Metal Oxide", "Color": "#A66633",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "Fe3O4", "Name": "Magnetite", "Elements": ["Fe"],
            "A": -555000.0, "B": 155.0, "PBR": 2.1, "Density": 5.17, "Tm_K": 1870.0,
            "Class": "Intermediate Oxide", "Color": "#8C6659",
            "Citation": "Reed (1971)"
        },
        {
            "Formula": "Fe2O3", "Name": "Hematite", "Elements": ["Fe"],
            "A": -545000.0, "B": 165.0, "PBR": 2.14, "Density": 5.24, "Tm_K": 1838.0,
            "Class": "Intermediate Oxide", "Color": "#99594C",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "FeO", "Name": "Wustite", "Elements": ["Fe"],
            "A": -530000.0, "B": 130.0, "PBR": 1.78, "Density": 5.74, "Tm_K": 1650.0,
            "Class": "Fast-Growing Non-Protective", "Color": "#80594C",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "CoO", "Name": "Cobalt Monoxide", "Elements": ["Co"],
            "A": -475000.0, "B": 145.0, "PBR": 1.86, "Density": 6.45, "Tm_K": 2083.0,
            "Class": "Transition Metal Oxide", "Color": "#5959A6",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "Co3O4", "Name": "Cobalt Spinel", "Elements": ["Co"],
            "A": -445000.0, "B": 168.0, "PBR": 1.99, "Density": 6.11, "Tm_K": 1173.0,
            "Class": "Spinel Scale", "Color": "#664C99",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "NiO", "Name": "Bunsenite", "Elements": ["Ni"],
            "A": -470000.0, "B": 172.0, "PBR": 1.65, "Density": 6.67, "Tm_K": 2228.0,
            "Class": "Transition Metal Oxide", "Color": "#4C8073",
            "Citation": "Reed (1971)"
        },
        {
            "Formula": "Cu2O", "Name": "Cuprite", "Elements": ["Cu"],
            "A": -340000.0, "B": 145.0, "PBR": 1.68, "Density": 6.0, "Tm_K": 1505.0,
            "Class": "Non-Protective Scale", "Color": "#BF734C",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "CuO", "Name": "Tenorite", "Elements": ["Cu"],
            "A": -310000.0, "B": 185.0, "PBR": 1.75, "Density": 6.31, "Tm_K": 1599.0,
            "Class": "Non-Protective Scale", "Color": "#B26640",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "ZnO", "Name": "Zincite", "Elements": ["Zn"],
            "A": -700000.0, "B": 205.0, "PBR": 1.55, "Density": 5.61, "Tm_K": 2247.0,
            "Class": "Moderate Scale", "Color": "#8C8C8C",
            "Citation": "Reed (1971)"
        },
        {
            "Formula": "MnCr2O4", "Name": "Manganese Chromite Spinel", "Elements": ["Mn", "Cr"],
            "A": -785000.0, "B": 170.0, "PBR": 2.1, "Density": 4.9, "Tm_K": 2450.0,
            "Class": "Spinel Scale (Cantor Dominant)", "Color": "#A626B2",
            "Citation": ""
        },
        {
            "Formula": "CoCr2O4", "Name": "Cobalt Chromite Spinel", "Elements": ["Co", "Cr"],
            "A": -735000.0, "B": 168.0, "PBR": 2.05, "Density": 5.25, "Tm_K": 2370.0,
            "Class": "Spinel Scale", "Color": "#8C33BF",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "NiCr2O4", "Name": "Nickel Chromite Spinel", "Elements": ["Ni", "Cr"],
            "A": -725000.0, "B": 170.0, "PBR": 2.02, "Density": 5.24, "Tm_K": 2350.0,
            "Class": "Spinel Scale", "Color": "#8040B2",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "FeCr2O4", "Name": "Iron Chromite Spinel", "Elements": ["Fe", "Cr"],
            "A": -745000.0, "B": 165.0, "PBR": 2.08, "Density": 5.1, "Tm_K": 2430.0,
            "Class": "Spinel Scale", "Color": "#9940A6",
            "Citation": "Reed (1971)"
        },
        {
            "Formula": "NiAl2O4", "Name": "Nickel Aluminate Spinel", "Elements": ["Ni", "Al"],
            "A": -1050000.0, "B": 205.0, "PBR": 1.45, "Density": 4.45, "Tm_K": 2380.0,
            "Class": "Aluminate Spinel", "Color": "#26A673",
            "Citation": "Butler et al. (2018)"
        },
        {
            "Formula": "CoAl2O4", "Name": "Cobalt Aluminate Spinel", "Elements": ["Co", "Al"],
            "A": -1060000.0, "B": 204.0, "PBR": 1.48, "Density": 4.48, "Tm_K": 2230.0,
            "Class": "Aluminate Spinel", "Color": "#339980",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "FeAl2O4", "Name": "Hercynite Spinel", "Elements": ["Fe", "Al"],
            "A": -1045000.0, "B": 202.0, "PBR": 1.5, "Density": 4.39, "Tm_K": 2050.0,
            "Class": "Aluminate Spinel", "Color": "#408C73",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "CrTaO4", "Name": "Chromium Tantalate", "Elements": ["Cr", "Ta"],
            "A": -835000.0, "B": 172.0, "PBR": 2.25, "Density": 8.55, "Tm_K": 2200.0,
            "Class": "Complex Refractory Oxide", "Color": "#667399",
            "Citation": "Senkov et al. (2018)"
        },
        {
            "Formula": "CrNbO4", "Name": "Chromium Niobate", "Elements": ["Cr", "Nb"],
            "A": -805000.0, "B": 170.0, "PBR": 2.3, "Density": 5.2, "Tm_K": 1950.0,
            "Class": "Complex Refractory Oxide", "Color": "#736699",
            "Citation": "Senkov et al. (2018)"
        },
        {
            "Formula": "La2O3", "Name": "Lanthanum Oxide", "Elements": ["La"],
            "A": -1220000.0, "B": 195.0, "PBR": 1.12, "Density": 6.51, "Tm_K": 2588.0,
            "Class": "Rare-Earth Oxide", "Color": "#2E9461",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "CeO2", "Name": "Ceria", "Elements": ["Ce"],
            "A": -1089000.0, "B": 200.0, "PBR": 1.15, "Density": 7.65, "Tm_K": 2673.0,
            "Class": "Rare-Earth Oxide", "Color": "#389E6B",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "Nd2O3", "Name": "Neodymium Oxide", "Elements": ["Nd"],
            "A": -1230000.0, "B": 196.0, "PBR": 1.14, "Density": 7.24, "Tm_K": 2545.0,
            "Class": "Rare-Earth Oxide", "Color": "#40A666",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "Gd2O3", "Name": "Gadolinium Oxide", "Elements": ["Gd"],
            "A": -1240000.0, "B": 198.0, "PBR": 1.18, "Density": 7.41, "Tm_K": 2693.0,
            "Class": "Rare-Earth Oxide", "Color": "#339959",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "Sm2O3", "Name": "Samarium Oxide", "Elements": ["Sm"],
            "A": -1235000.0, "B": 195.0, "PBR": 1.16, "Density": 8.35, "Tm_K": 2608.0,
            "Class": "Rare-Earth Oxide", "Color": "#38945C",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "MnFe2O4", "Name": "Jacobsite Spinel", "Elements": ["Mn", "Fe"],
            "A": -690000.0, "B": 162.0, "PBR": 2.08, "Density": 5.05, "Tm_K": 1850.0,
            "Class": "Ferrite Spinel", "Color": "#995973",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "CoFe2O4", "Name": "Cobalt Ferrite", "Elements": ["Co", "Fe"],
            "A": -660000.0, "B": 165.0, "PBR": 2.05, "Density": 5.3, "Tm_K": 1860.0,
            "Class": "Ferrite Spinel", "Color": "#804C8C",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "NiFe2O4", "Name": "Trevorite Spinel", "Elements": ["Ni", "Fe"],
            "A": -650000.0, "B": 168.0, "PBR": 2.02, "Density": 5.38, "Tm_K": 1930.0,
            "Class": "Ferrite Spinel", "Color": "#735980",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "Ti2O3", "Name": "Titanium Sesquioxide", "Elements": ["Ti"],
            "A": -985000.0, "B": 188.0, "PBR": 1.68, "Density": 4.49, "Tm_K": 2415.0,
            "Class": "Refractory Suboxide", "Color": "#408CA6",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "TiO", "Name": "Titanium Monoxide", "Elements": ["Ti"],
            "A": -1020000.0, "B": 192.0, "PBR": 1.52, "Density": 4.95, "Tm_K": 2023.0,
            "Class": "Refractory Suboxide", "Color": "#4C8099",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "NbO", "Name": "Niobium Monoxide", "Elements": ["Nb"],
            "A": -810000.0, "B": 175.0, "PBR": 1.7, "Density": 7.3, "Tm_K": 2210.0,
            "Class": "Refractory Suboxide", "Color": "#8C59A6",
            "Citation": "Senkov et al. (2018)"
        },
        {
            "Formula": "V2O3", "Name": "Karelianite", "Elements": ["V"],
            "A": -780000.0, "B": 182.0, "PBR": 1.85, "Density": 4.87, "Tm_K": 2240.0,
            "Class": "Intermediate Oxide", "Color": "#B27326",
            "Citation": "Kubaschewski (1979)"
        },
        {
            "Formula": "VO", "Name": "Vanadium Monoxide", "Elements": ["V"],
            "A": -825000.0, "B": 186.0, "PBR": 1.6, "Density": 5.76, "Tm_K": 2063.0,
            "Class": "Intermediate Oxide", "Color": "#A68033",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "CrO2", "Name": "Chromium Dioxide", "Elements": ["Cr"],
            "A": -590000.0, "B": 175.0, "PBR": 1.98, "Density": 4.89, "Tm_K": 670.0,
            "Class": "Metastable Oxide", "Color": "#3359BF",
            "Citation": "Reed (1971)"
        },
        {
            "Formula": "SnO2", "Name": "Cassiterite", "Elements": ["Sn"],
            "A": -580000.0, "B": 210.0, "PBR": 1.32, "Density": 6.95, "Tm_K": 1903.0,
            "Class": "Post-Transition Oxide", "Color": "#80998C",
            "Citation": "Barin (1995)"
        },
        {
            "Formula": "Dy2O3", "Name": "Dysprosium Oxide", "Elements": ["Dy"],
            "A": -1245000.0, "B": 197.0, "PBR": 1.15, "Density": 7.8, "Tm_K": 2680.0,
            "Class": "Rare-Earth Oxide", "Color": "#3D9E61",
            "Citation": "NIST-JANAF (1998)"
        },
        {
            "Formula": "Er2O3", "Name": "Erbium Oxide", "Elements": ["Er"],
            "A": -1250000.0, "B": 198.0, "PBR": 1.17, "Density": 8.64, "Tm_K": 2691.0,
            "Class": "Rare-Earth Oxide", "Color": "#429966",
            "Citation": "Barin (1995)"
        },
    ]

    @classmethod
    def get_all_oxides(cls) -> List[Dict[str, Any]]:
        """Returns complete inventory of all 54 candidate oxides in HEAs and RHEAs."""
        return [dict(ox) for ox in cls.OXIDES]

    @classmethod
    def get_oxides_for_elements(cls, elements: List[str]) -> List[Dict[str, Any]]:
        """Alias for get_oxides_for_alloy to match MATLAB API."""
        return cls.get_oxides_for_alloy(elements)

    @classmethod
    def get_oxides_for_alloy(cls, elements: List[str]) -> List[Dict[str, Any]]:
        """
        Returns all candidate oxides whose metal constituents exist in the current alloy.
        Falls back to protective baseline (Al2O3, Cr2O3, SiO2) if no direct match is found.
        """
        clean_elems = {str(el).strip() for el in elements}
        matches = []
        for ox in cls.OXIDES:
            req = set(ox["Elements"])
            if req.issubset(clean_elems):
                matches.append(dict(ox))

        if not matches:
            matches = [dict(ox) for ox in cls.OXIDES[:3]]
        return matches

    @classmethod
    def get_oxides_for_composition(cls, comp_elements: List[str]) -> List[Dict[str, Any]]:
        """Legacy compatibility wrapper."""
        return cls.get_oxides_for_alloy(comp_elements)

    @staticmethod
    def compute_delta_g(oxide_dict: Dict[str, Any], temp_k: float) -> float:
        """
        Computes standard Gibbs free energy of formation Delta G_f(T) in kJ / mol O2.
        Delta G_f(T) = (A + B * T) * 1e-3
        """
        dg_j = float(oxide_dict.get("A", 0.0)) + float(oxide_dict.get("B", 0.0)) * temp_k
        return dg_j * 1e-3

    @classmethod
    def calculate_gibbs_free_energy(cls, formula: str, temp_k: float) -> Optional[float]:
        """
        Calculates standard Gibbs free energy of formation Delta G_f(T) in kJ / mol O2
        for a given oxide formula.
        """
        for ox in cls.OXIDES:
            if ox["Formula"].lower() == formula.strip().lower():
                return cls.compute_delta_g(ox, temp_k)
        return None

    @classmethod
    def rank_oxides_by_affinity(cls, elements: List[str], temp_k: float) -> List[Dict[str, Any]]:
        """
        Returns candidate oxides for the alloy sorted by oxygen affinity
        (most negative Delta G_f first).
        """
        cand = cls.get_oxides_for_alloy(elements)
        for ox in cand:
            ox["DeltaG_f_kJ_per_mol_O2"] = cls.compute_delta_g(ox, temp_k)
        cand.sort(key=lambda x: x["DeltaG_f_kJ_per_mol_O2"])
        return cand

    @classmethod
    def get_oxides_summary_table(cls, elements: List[str], temp_c: float = 900.0) -> List[Dict[str, Any]]:
        """
        Generates a summary list of records for candidate oxides at temp_c.
        """
        temp_k = temp_c + 273.15
        ranked = cls.rank_oxides_by_affinity(elements, temp_k)
        summary = []
        for ox in ranked:
            summary.append({
                "Oxide": ox["Formula"],
                "Name": ox["Name"],
                "DeltaG_f_kJ_per_mol_O2": round(ox["DeltaG_f_kJ_per_mol_O2"], 1),
                "PBR": ox["PBR"],
                "Density_g_cm3": ox["Density"],
                "Scale_Classification": ox["Class"],
                "MeltingPoint_K": ox["Tm_K"],
                "Citation": ox.get("Citation", "")
            })
        return summary
