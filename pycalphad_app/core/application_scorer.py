"""
application_scorer.py - Multi-Criteria Industrial Suitability Scorer
Ranks alloy suitability (0-100%) across 10 strategic industrial sectors.
"""

from typing import Dict, List, Any

class ApplicationScorer:
    @staticmethod
    def score_alloy(elements: List[str], at_fractions: List[float], thermo: Dict[str, Any], mech: Dict[str, Any], ox: Dict[str, Any]) -> List[Dict[str, Any]]:
        is_coating = any(el in ["B", "Si"] for el in elements) and "Ni" in elements
        phase = thermo.get("Phase", "FCC")
        ys = mech.get("YieldStrength_RT_MPa", 300.0)
        hv = mech.get("VickersHardness_HV", 200)
        ts = thermo.get("T_Solidus", 1553.0)
        toughness = mech.get("FractureToughness_MPa_m05", 100.0)
        pren = (at_fractions[elements.index("Cr")] * 100.0) if "Cr" in elements else 0.0

        scores = []

        # 1. Hardfacing & Thermal Spray Coatings
        if is_coating:
            score = 96.5
            tier = "Prime Candidate (Industry Standard)"
            bottle = "None (Tailored Hardfacing Metco 16C)"
        elif hv >= 500:
            score = 78.0
            tier = "Strong Candidate"
            bottle = "Higher Ductility Than Standard Coatings"
        else:
            score = 42.0
            tier = "Unsuitable"
            bottle = "Low Vickers Hardness (<500 HV)"
        scores.append({"id": "COATINGS_WEAR", "name": "Thermal Spray & Hardfacing Wear Coatings", "score": score, "tier": tier, "bottleneck": bottle})

        # 2. Cryogenic Storage & LNG Tanks
        if "FCC" in phase and toughness >= 180 and not is_coating:
            score = 92.4
            tier = "Prime Candidate (Zero DBTT)"
            bottle = "Room Temp Yield Strength (<350 MPa)"
        elif is_coating:
            score = 22.0
            tier = "Unsuitable"
            bottle = "Brittle Hardfacing High Risk of Spallation"
        else:
            score = 55.0
            tier = "Conditional Candidate"
            bottle = "Cryogenic Impact Toughness"
        scores.append({"id": "CRYO_STORAGE", "name": "Cryogenic Storage & Liquid H2 / LNG Tanks", "score": score, "tier": tier, "bottleneck": bottle})

        # 3. High-Temperature Gas Turbine Blades
        if ts >= 1700.0 and ys >= 600.0 and not is_coating:
            score = 88.5
            tier = "Prime Candidate"
            bottle = "High-Temperature Creep Life"
        elif is_coating:
            score = 84.0
            tier = "Protective Overlay Only"
            bottle = "Substrate Required (Cannot be bulk structural)"
        elif ts >= 1500.0:
            score = 74.0
            tier = "Good Candidate"
            bottle = "Refractory Melting Point"
        else:
            score = 38.0
            tier = "Unsuitable"
            bottle = "Low Melting Point"
        scores.append({"id": "TURBINE_BLADES", "name": "Gas Turbine Blades & Combustor Liners", "score": score, "tier": tier, "bottleneck": bottle})

        # 4. Marine Propulsion & Desalination Valves
        if pren >= 20.0 and not is_coating:
            score = 86.0
            tier = "Prime Candidate"
            bottle = "Cost of Cobalt / Nickel"
        elif is_coating:
            score = 89.0
            tier = "Excellent Protective Cladding"
            bottle = "Substrate Galvanic Coupling"
        else:
            score = 48.0
            tier = "Conditional Candidate"
            bottle = "Chloride Pitting Susceptibility"
        scores.append({"id": "MARINE_PUMPS", "name": "Marine Propulsion & Desalination Valves", "score": score, "tier": tier, "bottleneck": bottle})

        # 5. Hot Work Tooling & Extrusion Dies
        if hv >= 650 or is_coating:
            score = 91.0
            tier = "Prime Candidate"
            bottle = "Thermal Shock Fatigue"
        elif hv >= 400:
            score = 65.0
            tier = "Conditional Candidate"
            bottle = "Elevated Temperature Hot Hardness"
        else:
            score = 35.0
            tier = "Unsuitable"
            bottle = "Low Hardness"
        scores.append({"id": "TOOLING_HOT_DIE", "name": "Hot Work Tooling & Metal Extrusion Dies", "score": score, "tier": tier, "bottleneck": bottle})

        # 6. Nuclear Cladding & Accident Tolerant Fuels
        if "Zr" in elements or ("Fe" in elements and "Cr" in elements and not is_coating):
            score = 82.5
            tier = "Strong Candidate"
            bottle = "Neutron Swelling & Transmutation"
        else:
            score = 45.0
            tier = "Conditional Candidate"
            bottle = "Thermal Neutron Capture Cross-Section"
        scores.append({"id": "NUCLEAR_CLADDING", "name": "Nuclear Core Cladding & Reactor Liners", "score": score, "tier": tier, "bottleneck": bottle})

        # 7. Biomedical & Orthopedic Implants
        if "Ti" in elements or "Ta" in elements or "Nb" in elements:
            score = 88.0
            tier = "Prime Candidate (Biocompatible)"
            bottle = "Cytotoxicity Testing"
        elif is_coating:
            score = 30.0
            tier = "Unsuitable"
            bottle = "Nickel Leaching in Vivo"
        else:
            score = 52.0
            tier = "Conditional Candidate"
            bottle = "Potential Allergic Sensitization"
        scores.append({"id": "BIOMEDICAL_IMPLANTS", "name": "Biomedical Orthopedic & Dental Implants", "score": score, "tier": tier, "bottleneck": bottle})

        # 8. Aerospace Airframe & Hypersonic Fasteners
        if ys >= 1000.0 and not is_coating:
            score = 89.0
            tier = "Prime Candidate"
            bottle = "Specific Density"
        elif ys >= 600.0:
            score = 75.0
            tier = "Good Candidate"
            bottle = "Density / Specific Strength"
        else:
            score = 44.0
            tier = "Unsuitable"
            bottle = "Insufficient Room Temperature Strength"
        scores.append({"id": "AEROSPACE_STRUCTURAL", "name": "Aerospace Hypersonic & Structural Fasteners", "score": score, "tier": tier, "bottleneck": bottle})

        # 9. Petrochemical Sour Gas & Hydrogen Pipeline
        if pren >= 25.0:
            score = 87.0
            tier = "Prime Candidate"
            bottle = "Hydrogen Embrittlement Threshold"
        elif is_coating:
            score = 81.0
            tier = "Good Protective Overlay"
            bottle = "Coating Micro-Crack Ingress"
        else:
            score = 50.0
            tier = "Conditional Candidate"
            bottle = "Sulfide Stress Cracking Susceptibility"
        scores.append({"id": "PETROCHEM_HYDROGEN", "name": "Petrochemical Sour Gas & H2 Valves", "score": score, "tier": tier, "bottleneck": bottle})

        # 10. Radiation & Plasma Facing Divertor Shielding
        if "W" in elements or "Ta" in elements or "Mo" in elements:
            score = 94.0
            tier = "Prime Candidate (High-Z)"
            bottle = "Ductile-to-Brittle Transition Temperature"
        else:
            score = 40.0
            tier = "Low Suitability"
            bottle = "Sputtering Yield & Sputter Erosion"
        scores.append({"id": "RADIATION_SHIELDING", "name": "Fusion Divertor & Radiation Shielding", "score": score, "tier": tier, "bottleneck": bottle})

        # Sort by score descending
        scores.sort(key=lambda s: s["score"], reverse=True)
        return scores


    @classmethod
    def score_all(cls, thermo: Dict[str, Any], mech: Dict[str, Any], ox: Dict[str, Any],
                  corr: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        elems = ["Ni", "Cr", "Fe"]
        fracs = [0.6, 0.2, 0.2]
        raw_scores = cls.score_alloy(elems, fracs, thermo, mech, ox)
        # Adapt keys for GUI view
        out = []
        for s in raw_scores:
            out.append({
                "sector": s.get("name", ""),
                "score": s.get("score", 0.0),
                "status": s.get("tier", "Suitable"),
                "bottleneck": s.get("bottleneck", "")
            })
        return out

