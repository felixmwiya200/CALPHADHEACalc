# -*- coding: utf-8 -*-
"""
coating_alloy_engine.py - Adapter Engine for Thermal Spray Coatings
Conforms ThermalSprayCoatingEngine to the standard BaseAlloyEngine lifecycle contract.
"""

from typing import Dict, Any, List, Tuple
from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine
from pycalphad_app.core.coating_engine import CoatingEngine, ThermalSprayCoatingEngine


class CoatingAlloyEngine(BaseAlloyEngine):
    """
    Dedicated calculation engine for Thermal Spray Coating databases.
    Conforms to the polymorphic BaseAlloyEngine interface.
    """

    def get_supported_phases(self) -> List[str]:
        return [
            "Liquid",
            "FCC_Matrix",
            "CrB_Boride",
            "Cr2B_Boride",
            "Ni3Si_Silicide",
            "Cr7C3_Carbide"
        ]

    def compute_phase_transformations(self) -> Dict[str, Any]:
        coating_res = CoatingEngine.calculate(self.comp_wt, process=self.process_type)
        t_sol_k = coating_res["solidus_K"]
        t_liq_k = coating_res["liquidus_K"]
        return {
            "T_Liquidus_K": float(t_liq_k),
            "T_Solidus_K": float(t_sol_k),
            "T_Liquidus_C": float(t_liq_k - 273.15),
            "T_Solidus_C": float(t_sol_k - 273.15),
            "FreezingRange_K": float(t_liq_k - t_sol_k)
        }

    def compute_thermodynamics(self) -> Dict[str, Any]:
        coating_res = CoatingEngine.calculate(self.comp_wt, process=self.process_type)
        phases = {
            "FCC_Matrix": 0.65,
            "CrB_Boride": 0.12,
            "Cr2B_Boride": 0.08,
            "Ni3Si_Silicide": 0.10,
            "Cr7C3_Carbide": 0.05
        }
        return {
            "T_Liquidus": float(coating_res["liquidus_K"]),
            "T_Solidus": float(coating_res["solidus_K"]),
            "Solidus_K": float(coating_res["solidus_K"]),
            "Liquidus_K": float(coating_res["liquidus_K"]),
            "Density_g_cm3": float(coating_res["density_g_cm3"]),
            "Phases": phases,
            "DominantPhase": "FCC Matrix + Borides/Silicides"
        }

    def compute_mechanical_properties(self, thermo: Dict[str, Any],
                                      transform: Dict[str, Any]) -> Dict[str, Any]:
        coating_res = CoatingEngine.calculate(self.comp_wt, process=self.process_type)
        hv = coating_res["hardness_HV"]
        sy = hv * 2.8  # approximate conversion for hardfacing deposit
        uts = sy * 1.2
        return {
            "YieldStrength_MPa": float(sy),
            "YieldStrength_RT_MPa": float(sy),
            "UTS_MPa": float(uts),
            "UTS_RT_MPa": float(uts),
            "Elongation_pct": 1.5,
            "Elongation_RT_pct": 1.5,
            "VickersHardness_HV": float(hv),
            "Hardness_HV": float(hv),
            "YoungsModulus_GPa": 210.0,
            "FractureToughness_MPa_m05": 18.0,
            "PoissonRatio": 0.30,
            "PughRatio": 2.1,
            "BondStrength_MPa": float(coating_res.get("bond_strength_MPa", 45.0)),
            "WearRate_mm3_Nm": float(coating_res.get("wear_rate", coating_res.get("SpecificWearRate_1e6_mm3_Nm", 3.5e-5))),
            "FrictionCoefficient": float(coating_res.get("friction_coeff", coating_res.get("FrictionCoefficient_COF", 0.55))),
            "DominantStructure": f"Thermal Spray Coating ({self.process_type})"
        }

    def compute_transport_properties(self, thermo: Dict[str, Any]) -> Dict[str, Any]:
        coating_res = CoatingEngine.calculate(self.comp_wt, process=self.process_type)
        density = float(coating_res.get("density_g_cm3", 8.12))
        k_th = 16.4  # Planche 2005 laser flash benchmark at 298 K
        cp = 440.0   # J/kg*K
        cte = float(coating_res.get("CoatingCTE_1e6_K", 14.2))
        return {
            "TheoreticalDensity_g_cm3": density,
            "Density_RT_g_cm3": density,
            "ThermalConductivity_W_mK": k_th,
            "SpecificHeat_J_kgK": cp,
            "ThermalDiffusivity_m2_s": float(k_th / (density * 1000.0 * cp)),
            "CTE_1e6_K": cte,
            "ElectricalConductivity_MS_m": 1.10
        }

    def compute_environmental_properties(self, thermo: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        coating_res = CoatingEngine.calculate(self.comp_wt, process=self.process_type)
        corr = {
            "CorrosionRate_mpy": float(coating_res["corrosion_rate_mm_yr"] * 39.37),
            "Ecorr_V_vs_SCE": float(coating_res["ecorr_V"]),
            "Icorr_uA_cm2": float(coating_res["icorr_uA"]),
            "PREN": 22.4,
            "CorrosionMechanism": "Cr2O3 Passivation + Intermetallic Micro-Galvanic Resistance"
        }
        ox = {
            "ProtectiveOxide": "Cr2O3 / SiO2 Duplex Protective Scale",
            "Kp_g2_m4_s": 2.2e-6,
            "MaxServiceTemperature_C": 850.0,
            "OxidationKinetics": "Parabolic Rate Law"
        }
        return corr, ox

    def compute_single_temperature_step(self, t_k: float) -> Dict[str, Any]:
        trans = self.compute_phase_transformations()
        t_c = t_k - 273.15
        t_liq_c = trans["T_Liquidus_C"]
        t_sol_c = trans["T_Solidus_C"]

        if t_c >= t_liq_c:
            phases = {"Liquid": 1.0}
            dominant = "Liquid"
        elif t_c >= t_sol_c:
            f_liq = (t_c - t_sol_c) / max(1.0, (t_liq_c - t_sol_c))
            phases = {"Liquid": float(f_liq), "FCC_Matrix": float(1.0 - f_liq)}
            dominant = "Liquid + FCC_Matrix"
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
