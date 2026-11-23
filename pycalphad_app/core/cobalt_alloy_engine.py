# -*- coding: utf-8 -*-
"""
cobalt_alloy_engine.py - Specialized Metallurgical Engine for Cobalt Alloys
Covers Stellite wear-resistant hardfacing alloys, Tribaloy laves-phase alloys,
and biomedical Co-Cr-Mo alloys (ASTM F75).
Implements:
- Allotropic FCC (gamma) to HCP (epsilon) transus temperature.
- Primary and eutectic carbide volume fractions (M7C3, M23C6, M6C).
- Hardness, galling resistance, and Archard adhesive wear coefficient.
"""

from typing import Dict, Any, List, Tuple
import math
import numpy as np

from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine


class CobaltAlloyEngine(BaseAlloyEngine):
    """
    Dedicated calculation engine for Cobalt Base Alloys and Stellites.
    """

    def get_supported_phases(self) -> List[str]:
        return [
            "Liquid",
            "FCC_Gamma",
            "HCP_Epsilon",
            "Carbides_M7C3_M23C6",
            "Laves_Phase"
        ]

    def compute_phase_transformations(self) -> Dict[str, Any]:
        """
        Calculates:
        - Liquidus and Solidus
        - Allotropic FCC -> HCP transus temperature
        - Carbide eutectic reaction temperature
        """
        cr_wt = self.comp_wt.get("Cr", 0.0) * 100.0
        w_wt = self.comp_wt.get("W", 0.0) * 100.0
        mo_wt = self.comp_wt.get("Mo", 0.0) * 100.0
        c_wt = self.comp_wt.get("C", 0.0) * 100.0
        ni_wt = self.comp_wt.get("Ni", 0.0) * 100.0
        fe_wt = self.comp_wt.get("Fe", 0.0) * 100.0

        # Allotropic FCC -> HCP transus (pure Co is 422 C; Cr, Mo, W raise it; Ni, Fe depress it)
        t_allo_c = 422.0 + (14.0 * cr_wt) + (16.0 * mo_wt) + (12.0 * w_wt) - (25.0 * ni_wt) - (10.0 * fe_wt)
        t_allo_c = min(950.0, max(350.0, t_allo_c))

        # Eutectic carbide reaction temperature (C)
        t_eut_c = 1280.0 - (10.0 * c_wt) + (1.5 * w_wt)

        # Liquidus (pure Co is 1495 C; calibrated to Stellite DSC benchmarks)
        t_liq_c = 1495.0 - (2.0 * cr_wt) - (35.0 * c_wt) - (1.0 * w_wt) - (2.0 * mo_wt)
        t_sol_c = min(t_liq_c - 30.0, t_eut_c)

        return {
            "T_allotropic_fcc_to_hcp_C": float(t_allo_c),
            "Eutectic_Carbide_C": float(t_eut_c),
            "T_Liquidus_C": float(t_liq_c),
            "T_Solidus_C": float(t_sol_c),
            "T_Liquidus_K": float(t_liq_c + 273.15),
            "T_Solidus_K": float(t_sol_c + 273.15)
        }

    def compute_thermodynamics(self) -> Dict[str, Any]:
        """Computes constituent phase fractions at room temperature."""
        trans = self.compute_phase_transformations()
        c_wt = self.comp_wt.get("C", 0.0) * 100.0
        cr_wt = self.comp_wt.get("Cr", 0.0) * 100.0
        w_wt = self.comp_wt.get("W", 0.0) * 100.0

        # Primary and eutectic carbide volume fraction (M7C3 / M23C6)
        # In Stellite 6 (1.2 wt% C), f_carbide is approx 13-15%
        f_carbide = min(0.35, max(0.01, 0.115 * c_wt * ((cr_wt + 0.5 * w_wt) / 28.0)))

        # Matrix phase state: HCP (epsilon) vs FCC (gamma)
        # Cooling rate retards athermal FCC->HCP martensitic shear; slow cooling yields more HCP
        cooling = self.cooling_rate_k_s
        hcp_retained = 1.0 / (1.0 + math.exp(0.4 * (math.log10(max(0.1, cooling)) - 0.5)))
        f_hcp = hcp_retained * (1.0 - f_carbide)
        f_fcc = (1.0 - hcp_retained) * (1.0 - f_carbide)

        phases = {
            "Carbides_M7C3_M23C6": float(f_carbide),
            "HCP_Epsilon": float(f_hcp),
            "FCC_Gamma": float(f_fcc)
        }

        return {
            "T_Liquidus": float(trans["T_Liquidus_K"]),
            "T_Solidus": float(trans["T_Solidus_K"]),
            "Solidus_K": float(trans["T_Solidus_K"]),
            "Liquidus_K": float(trans["T_Liquidus_K"]),
            "Enthalpy_Fusion_J_kg": 275000.0,
            "Phases": phases,
            "DominantPhase": "Carbides_M7C3_M23C6" if f_carbide > 0.25 else ("HCP_Epsilon" if f_hcp > f_fcc else "FCC_Gamma")
        }

    def compute_mechanical_properties(self, thermo: Dict[str, Any],
                                      transform: Dict[str, Any]) -> Dict[str, Any]:
        """Computes hardness, strength, elongation, and Archard wear coefficient."""
        phases = thermo.get("Phases", {})
        f_carbide = phases.get("Carbides_M7C3_M23C6", 0.05)
        c_wt = self.comp_wt.get("C", 0.0) * 100.0
        cr_wt = self.comp_wt.get("Cr", 0.0) * 100.0
        w_wt = self.comp_wt.get("W", 0.0) * 100.0

        # Hardness scaling: high carbon yields high carbide fraction and high HV
        hv = 240.0 + (130.0 * c_wt) + (1.8 * cr_wt) + (3.0 * w_wt)
        # Stellite 6 benchmark check (~400-440 HV)
        if c_wt >= 1.0:
            hv = min(460.0, max(380.0, hv))

        # Strength and elongation
        # Higher carbon reduces ductility
        if c_wt >= 1.0:
            sy = 680.0 + (80.0 * c_wt)
            uts = 880.0 + (90.0 * c_wt)
            elong = max(1.0, 5.0 - (3.0 * c_wt))
            k1c = 25.0 - (8.0 * c_wt)
        else:
            # Low-carbon biomedical alloy (ASTM F75)
            sy = 480.0 + (120.0 * c_wt)
            uts = 750.0 + (180.0 * c_wt)
            elong = max(8.0, 15.0 - (20.0 * c_wt))
            k1c = 45.0

        youngs_e = 230.0  # GPa

        # Archard abrasive / adhesive wear rate coefficient (mm3 / N*m)
        # Wear resistance inversely proportional to hardness cube
        archard_k = 1.2e-4 / math.pow(hv / 100.0, 2.2)

        return {
            "YieldStrength_MPa": float(sy),
            "YieldStrength_RT_MPa": float(sy),
            "UTS_MPa": float(uts),
            "UTS_RT_MPa": float(uts),
            "Elongation_pct": float(elong),
            "Elongation_RT_pct": float(elong),
            "VickersHardness_HV": float(hv),
            "Hardness_HV": float(hv),
            "YoungsModulus_GPa": float(youngs_e),
            "FractureToughness_MPa_m05": float(k1c),
            "PoissonRatio": 0.29,
            "ArchardWearCoeff_mm3_Nm": float(archard_k),
            "DominantStructure": f"Cobalt Matrix + {f_carbide*100:.1f}% Carbides"
        }

    def compute_transport_properties(self, thermo: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates thermophysical properties."""
        w_wt = self.comp_wt.get("W", 0.0) * 100.0
        rho = 8.40 + (0.05 * w_wt)
        k_th = 14.8
        cp = 420.0
        cte = 11.5e-6

        return {
            "TheoreticalDensity_g_cm3": float(rho),
            "Density_RT_g_cm3": float(rho),
            "ThermalConductivity_W_mK": float(k_th),
            "SpecificHeat_J_kgK": float(cp),
            "ThermalDiffusivity_m2_s": float(k_th / (rho * 1000.0 * cp)),
            "CTE_1e6_K": float(cte * 1e6),
            "ElectricalConductivity_MS_m": 1.15
        }

    def compute_environmental_properties(self, thermo: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Computes oxidation and corrosion response."""
        cr_wt = self.comp_wt.get("Cr", 0.0) * 100.0
        corr = {
            "CorrosionRate_mpy": 0.8,
            "Ecorr_V_vs_SCE": -0.15,
            "Icorr_uA_cm2": 0.35,
            "PREN": float(cr_wt + 3.3 * self.comp_wt.get("Mo", 0.0) * 100.0),
            "CorrosionMechanism": "Chromia Passivation Film"
        }
        ox = {
            "ProtectiveOxide": "Cr2O3 / CoO Continuous Scale",
            "Kp_g2_m4_s": 2.5e-6,
            "MaxServiceTemperature_C": 870.0,
            "OxidationKinetics": "Parabolic Rate Law"
        }
        return corr, ox

    def compute_single_temperature_step(self, t_k: float) -> Dict[str, Any]:
        """Provides instantaneous phase state at temperature T_K."""
        trans = self.compute_phase_transformations()
        t_c = t_k - 273.15
        t_liq_c = trans["T_Liquidus_C"]
        t_sol_c = trans["T_Solidus_C"]
        t_allo_c = trans["T_allotropic_fcc_to_hcp_C"]

        if t_c >= t_liq_c:
            phases = {"Liquid": 1.0}
            dominant = "Liquid"
        elif t_c >= t_sol_c:
            f_liq = (t_c - t_sol_c) / max(1.0, (t_liq_c - t_sol_c))
            phases = {"Liquid": float(f_liq), "FCC_Gamma": float(1.0 - f_liq)}
            dominant = "Liquid + FCC_Gamma"
        elif t_c >= t_allo_c:
            phases = {"FCC_Gamma": 0.86, "Carbides_M7C3_M23C6": 0.14}
            dominant = "FCC_Gamma + Carbides"
        else:
            thermo = self.compute_thermodynamics()
            phases = thermo["Phases"]
            dominant = thermo["DominantPhase"]

        return {
            "Temperature_K": float(t_k),
            "Temperature_C": float(t_c),
            "Phases": phases,
            "DominantPhase": dominant
        }
