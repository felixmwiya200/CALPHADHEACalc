"""
usgs_conductivity.py - McCleskey (2012) Electrolyte Electrical Conductivity & EPA Regulatory Limits.
Implements the USGS geochemical model for solution conductivity (conductivity-USGS.dat)
and EPA drinking water maximum contaminant limits (WaterQualityRegs.dat) for corrosion leaching.
"""

import os
import re
import math
from typing import Dict, List, Any, Optional, Tuple


class USGSConductivityEngine:
    """
    Computes electrical conductivity of aqueous solutions using the McCleskey et al. (2012)
    formulation from conductivity-USGS.dat and checks EPA limits from WaterQualityRegs.dat.
    """

    _INSTANCE: Optional["USGSConductivityEngine"] = None

    def __init__(self, dat_dir: Optional[str] = None):
        if dat_dir is None:
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Databases"),
                r"C:\Users\Dell\Documents\Material design\Databases",
            ]
            for c in candidates:
                if os.path.exists(c):
                    dat_dir = c
                    break
            if dat_dir is None:
                dat_dir = os.path.dirname(os.path.abspath(__file__))
        self.dat_dir = dat_dir
        self.species_coeffs: Dict[str, Dict[str, float]] = {}
        self.epa_limits: Dict[str, Dict[str, Any]] = {}
        self._load_conductivity_dat()
        self._load_water_quality_dat()

    @classmethod
    def get_instance(cls) -> "USGSConductivityEngine":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def _load_conductivity_dat(self) -> None:
        p = os.path.join(self.dat_dir, "conductivity-USGS.dat")
        if not os.path.exists(p):
            return

        with open(p, "r", encoding="latin1") as f:
            lines = f.readlines()

        for l in lines:
            l = l.strip()
            if not l or l.startswith("*") or l.startswith("#"):
                continue
            if l.startswith("EC_"):
                continue
            tokens = l.split()
            if len(tokens) >= 8:
                sp_name = tokens[0]
                try:
                    # Columns 2-4: ionic conductance quadratic coeffs (a1, a2, a3)
                    # Columns 5-7: parameter A quadratic coeffs (c1, c2, c3)
                    # Column 8: parameter B
                    a1, a2, a3 = float(tokens[1]), float(tokens[2]), float(tokens[3])
                    c1, c2, c3 = float(tokens[4]), float(tokens[5]), float(tokens[6])
                    b = float(tokens[7])
                    self.species_coeffs[sp_name] = {
                        "a1": a1, "a2": a2, "a3": a3,
                        "c1": c1, "c2": c2, "c3": c3,
                        "b": b
                    }
                except ValueError:
                    pass

    def _load_water_quality_dat(self) -> None:
        p = os.path.join(self.dat_dir, "WaterQualityRegs.dat")
        if not os.path.exists(p):
            return

        with open(p, "r", encoding="latin1") as f:
            lines = f.readlines()

        for l in lines:
            l = l.strip()
            if not l or l.startswith("#"):
                continue
            # Format: Al+++ -- 0.05 "mg/kg as Al" NSDWR
            tokens = re.split(r'\s+', l)
            if len(tokens) >= 4:
                sp = tokens[0]
                try:
                    limit_val = float(tokens[2])
                    std_type = tokens[-1]
                    unit = tokens[3].replace('"', '') if len(tokens) > 3 else "mg/kg"
                    self.epa_limits[sp] = {
                        "species": sp,
                        "limit_mg_kg": limit_val,
                        "standard": std_type,
                        "unit": unit
                    }
                except ValueError:
                    pass

    def calculate_conductivity(
        self,
        temperature_c: float = 25.0,
        molarities: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates electrical conductivity kappa (uS/cm and mS/cm) using McCleskey et al. (2012).
        molarities: Dict of species name -> concentration in mol/L (e.g. {'Na+': 0.1, 'Cl-': 0.1, 'H+': 0.001})
        """
        if molarities is None:
            # Default seawater / saline electrolyte: 0.5 M NaCl + 0.05 M MgSO4
            molarities = {"Na+": 0.5, "Cl-": 0.5, "Mg++": 0.05, "SO4--": 0.05}

        # Temperature bounds
        temp_c = max(0.0, min(95.0, temperature_c))

        # Compute ionic strength I = 0.5 * sum(z_i^2 * m_i)
        charges = {
            "H+": 1, "Na+": 1, "K+": 1, "Li+": 1, "Cs+": 1, "NH4+": 1,
            "Ca++": 2, "Ca+2": 2, "Mg++": 2, "Mg+2": 2, "Ba++": 2, "Ba+2": 2, "Sr++": 2, "Sr+2": 2,
            "Fe++": 2, "Fe+2": 2, "Fe+++": 3, "Fe+3": 3, "Al+++": 3, "Al+3": 3,
            "Cl-": 1, "F-": 1, "Br-": 1, "OH-": 1, "HCO3-": 1,
            "SO4--": 2, "SO4-2": 2, "CO3--": 2, "CO3-2": 2
        }

        ionic_strength = 0.0
        for sp, conc in molarities.items():
            z = charges.get(sp, 1)
            ionic_strength += 0.5 * (z ** 2) * conc

        sqrt_i = math.sqrt(max(1e-9, ionic_strength))

        total_kappa_uS_cm = 0.0
        contributions = {}

        for sp, conc in molarities.items():
            if conc <= 0.0:
                continue
            coeffs = self.species_coeffs.get(sp)
            if not coeffs:
                # Fallback approximation: lambda0 ~ 50 S*cm^2/mol
                z = charges.get(sp, 1)
                lambda_i = 50.0 * z
                equiv_cond = lambda_i * (1.0 - 0.2 * sqrt_i)
            else:
                a1, a2, a3 = coeffs["a1"], coeffs["a2"], coeffs["a3"]
                c1, c2, c3 = coeffs["c1"], coeffs["c2"], coeffs["c3"]
                b = coeffs["b"]
                lambda_0 = (a1 * (temp_c ** 2)) + (a2 * temp_c) + a3
                param_a = (c1 * (temp_c ** 2)) + (c2 * temp_c) + c3
                equiv_cond = lambda_0 - (param_a * sqrt_i / (1.0 + b * sqrt_i))

            # Contribution: kappa_i = m_i * Lambda_i (in uS/cm when m_i in mol/L)
            contrib = max(0.0, conc * equiv_cond * 1000.0)
            total_kappa_uS_cm += contrib
            contributions[sp] = round(contrib, 2)

        # Electrolyte resistivity: rho = 1 / (kappa in S/cm)
        kappa_S_cm = (total_kappa_uS_cm * 1e-6)
        resistivity_ohm_cm = 1.0 / kappa_S_cm if kappa_S_cm > 0 else 1e9

        return {
            "temperature_c": temp_c,
            "ionic_strength_mol_L": round(ionic_strength, 4),
            "conductivity_uS_cm": round(total_kappa_uS_cm, 1),
            "conductivity_mS_cm": round(total_kappa_uS_cm / 1000.0, 3),
            "resistivity_ohm_cm": round(resistivity_ohm_cm, 2),
            "species_contributions_uS_cm": contributions,
        }

    def check_epa_compliance(self, aqueous_concentrations_mg_kg: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Checks metal leaching concentrations against USEPA drinking water maximum contaminant limits (MCL).
        """
        results = []
        for sp, conc in aqueous_concentrations_mg_kg.items():
            lim = self.epa_limits.get(sp)
            if lim:
                limit_val = lim["limit_mg_kg"]
                ratio = conc / limit_val if limit_val > 0 else 0.0
                status = "EXCEEDS_LIMIT" if ratio > 1.0 else ("NEAR_LIMIT" if ratio > 0.8 else "COMPLIANT")
                results.append({
                    "species": sp,
                    "measured_mg_kg": conc,
                    "epa_limit_mg_kg": limit_val,
                    "standard": lim["standard"],
                    "ratio": round(ratio, 2),
                    "status": status,
                })
        return results
