# -*- coding: utf-8 -*-
"""
solder_engine.py - Specialized Metallurgical Engine for Electronic Solder Alloys
Covers Lead-Free SAC (SAC305, SAC387, SAC105), Legacy Eutectic Sn-Pb,
and Low-Melting Systems (Sn-Bi, In-Sn).
Implements:
- Invariant eutectic melting points (SAC305 at 217 C, Sn-37Pb at 183 C, Sn-58Bi at 138 C).
- Intermetallic compound (IMC) formation: Ag3Sn platelets and Cu6Sn5 scallops.
- Anand viscoplastic constitutive parameters (s0, Q/R, A, xi, m, h0, a, s_hat, n).
- Homologous temperature (T / Tm > 0.5 at room temperature) and high-rate creep deformation.
"""

from typing import Dict, Any, List, Tuple
import math
import numpy as np

from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine


class SolderEngine(BaseAlloyEngine):
    """
    Dedicated calculation engine for Electronic Solder databases.
    """

    def get_supported_phases(self) -> List[str]:
        return [
            "Liquid",
            "BCT_Beta_Sn",
            "FCC_Pb",
            "Ag3Sn_IMC",
            "Cu6Sn5_IMC",
            "Cu3Sn_IMC",
            "Bi_Rhombohedral"
        ]

    def compute_phase_transformations(self) -> Dict[str, Any]:
        """
        Calculates:
        - Invariant eutectic melting temperature
        - Liquidus and Solidus
        - Freezing range (Delta T)
        - Lead-free classification
        """
        sn = self.comp_wt.get("Sn", 0.0) * 100.0
        ag = self.comp_wt.get("Ag", 0.0) * 100.0
        cu = self.comp_wt.get("Cu", 0.0) * 100.0
        pb = self.comp_wt.get("Pb", 0.0) * 100.0
        bi = self.comp_wt.get("Bi", 0.0) * 100.0

        is_lead_free = pb < 0.10

        if not is_lead_free and pb >= 20.0:
            # Sn-Pb eutectic system
            # Invariant eutectic at 38.1 wt% Pb / 61.9 wt% Sn is 183.0 C
            t_eut_c = 183.0
            # Liquidus deviation off eutectic
            delta_off = abs(pb - 37.0)
            t_liq_c = 183.0 + (delta_off * 1.5)
            t_sol_c = 183.0
            alloy_type = "Eutectic / Near-Eutectic Sn-Pb"
        elif bi >= 40.0:
            # Sn-Bi low-temp eutectic (58 wt% Bi / 42 wt% Sn is 138 C)
            t_eut_c = 138.0
            delta_off = abs(bi - 58.0)
            t_liq_c = 138.0 + (delta_off * 2.0)
            t_sol_c = 138.0
            alloy_type = "Low-Temperature Sn-Bi Eutectic"
        else:
            # Lead-Free SAC (Sn-Ag-Cu) alloy
            # SAC305 invariant ternary eutectic is 217.0 C
            t_eut_c = 217.0
            # Liquidus off-eutectic slope
            delta_ag = abs(ag - 3.0)
            delta_cu = abs(cu - 0.5)
            t_liq_c = 217.0 + (delta_ag * 1.8) + (delta_cu * 3.5)
            t_sol_c = 217.0
            alloy_type = f"Lead-Free SAC (Sn-{ag:.1f}Ag-{cu:.1f}Cu)"

        return {
            "Eutectic_Melting_C": float(t_eut_c),
            "T_Liquidus_C": float(t_liq_c),
            "T_Solidus_C": float(t_sol_c),
            "T_Liquidus_K": float(t_liq_c + 273.15),
            "T_Solidus_K": float(t_sol_c + 273.15),
            "FreezingRange_K": float(t_liq_c - t_sol_c),
            "IsLeadFree": bool(is_lead_free),
            "AlloyType": alloy_type
        }

    def compute_thermodynamics(self) -> Dict[str, Any]:
        """Calculates equilibrium phase fractions at room temperature."""
        trans = self.compute_phase_transformations()
        ag = self.comp_wt.get("Ag", 0.0) * 100.0
        cu = self.comp_wt.get("Cu", 0.0) * 100.0
        pb = self.comp_wt.get("Pb", 0.0) * 100.0
        bi = self.comp_wt.get("Bi", 0.0) * 100.0

        phases = {}
        if trans["IsLeadFree"]:
            if bi >= 40.0:
                f_bi = bi / 100.0
                phases["BCT_Beta_Sn"] = float(1.0 - f_bi)
                phases["Bi_Rhombohedral"] = float(f_bi)
            else:
                # In SAC305: Ag forms Ag3Sn (~4.2 vol.%), Cu forms Cu6Sn5 (~1.2 vol.%) + interfacial Cu3Sn (epsilon)
                f_ag3sn = min(0.08, max(0.005, 0.014 * ag))
                f_cu6sn5 = min(0.04, max(0.002, 0.024 * cu))
                f_cu3sn = min(0.02, 0.30 * f_cu6sn5)
                f_sn = 1.0 - (f_ag3sn + f_cu6sn5 + f_cu3sn)
                phases["BCT_Beta_Sn"] = float(f_sn)
                phases["Ag3Sn_IMC"] = float(f_ag3sn)
                phases["Cu6Sn5_IMC"] = float(f_cu6sn5)
                phases["Cu3Sn_IMC"] = float(f_cu3sn)
        else:
            f_pb = min(0.45, max(0.05, pb / 100.0))
            phases["BCT_Beta_Sn"] = float(1.0 - f_pb)
            phases["FCC_Pb"] = float(f_pb)

        return {
            "T_Liquidus": float(trans["T_Liquidus_K"]),
            "T_Solidus": float(trans["T_Solidus_K"]),
            "Solidus_K": float(trans["T_Solidus_K"]),
            "Liquidus_K": float(trans["T_Liquidus_K"]),
            "Enthalpy_Fusion_J_kg": 60000.0,
            "Phases": phases,
            "DominantPhase": "BCT_Beta_Sn (Eutectic Matrix)"
        }

    def compute_mechanical_properties(self, thermo: Dict[str, Any],
                                      transform: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes mechanical and viscoplastic creep parameters.
        Because room temperature (298 K) is > 0.6 of melting point (490 K),
        creep deformation is active even under ambient conditions.
        Provides Anand viscoplastic model parameters.
        """
        t_sol_k = transform["T_Solidus_K"]
        homologous_rt = 298.15 / max(1.0, t_sol_k)

        ag = self.comp_wt.get("Ag", 0.0) * 100.0
        cu = self.comp_wt.get("Cu", 0.0) * 100.0

        if transform["IsLeadFree"]:
            # SAC305 benchmark: Proof yield ~ 34-40 MPa, UTS ~ 45-52 MPa
            sy = 30.0 + (3.0 * ag) + (4.0 * cu)
            sy = min(50.0, max(28.0, sy))
            uts = sy * 1.35
            elong = 28.0
            youngs_e = 50.0  # GPa
            hv = 15.0

            # Anand Viscoplastic Model Parameters for SAC305 (Darveaux / Wang 2004 benchmark):
            anand_s0 = 12.41       # Initial value of deformation resistance (MPa)
            anand_q_r = 9320.0     # Q/R activation energy parameter (K)
            anand_a = 3501.0       # Pre-exponential factor (1/s)
            anand_xi = 4.0         # Stress multiplier
            anand_m = 0.25         # Strain rate sensitivity
            anand_h0 = 180000.0    # Hardening constant (MPa)
            anand_a_param = 1.78   # Strain rate sensitivity of hardening
            anand_s_hat = 40.25    # Saturation value of deformation resistance (MPa)
            anand_n = 0.07         # Sensitivity of saturation
        else:
            # Sn-37Pb benchmark: Proof yield ~ 28-34 MPa
            sy = 32.0
            uts = 42.0
            elong = 35.0
            youngs_e = 32.0
            hv = 13.0

            # Anand parameters for eutectic Sn-Pb
            anand_s0 = 12.41
            anand_q_r = 9400.0
            anand_a = 4000.0
            anand_xi = 1.5
            anand_m = 0.303
            anand_h0 = 137890.0
            anand_a_param = 1.96
            anand_s_hat = 43.2
            anand_n = 0.06

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
            "FractureToughness_MPa_m05": 12.0,
            "PoissonRatio": 0.40,
            "HomologousTemperature_RT": float(homologous_rt),
            "Anand_s0_MPa": float(anand_s0),
            "Anand_Q_R": float(anand_q_r),
            "Anand_A": float(anand_a),
            "Anand_xi": float(anand_xi),
            "Anand_m": float(anand_m),
            "Anand_h0_MPa": float(anand_h0),
            "Anand_a": float(anand_a_param),
            "Anand_s_hat_MPa": float(anand_s_hat),
            "Anand_n": float(anand_n),
            "DominantStructure": f"{transform['AlloyType']} (Creep Active: T/Tm={homologous_rt:.2f})"
        }

    def compute_transport_properties(self, thermo: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates thermophysical properties."""
        trans = self.compute_phase_transformations()
        pb = self.comp_wt.get("Pb", 0.0) * 100.0

        if trans["IsLeadFree"]:
            rho = 7.38  # SAC305
            k_th = 58.0
            cp = 230.0
            cte = 21.0e-6
            elec_cond = 7.5
        else:
            rho = 8.42  # Sn-37Pb
            k_th = 50.0
            cp = 176.0
            cte = 24.5e-6
            elec_cond = 6.8

        return {
            "TheoreticalDensity_g_cm3": float(rho),
            "Density_RT_g_cm3": float(rho),
            "ThermalConductivity_W_mK": float(k_th),
            "SpecificHeat_J_kgK": float(cp),
            "ThermalDiffusivity_m2_s": float(k_th / (rho * 1000.0 * cp)),
            "CTE_1e6_K": float(cte * 1e6),
            "ElectricalConductivity_MS_m": float(elec_cond)
        }

    def compute_environmental_properties(self, thermo: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Computes corrosion response and Sn whisker / oxidation risk."""
        corr = {
            "CorrosionRate_mpy": 0.6,
            "Ecorr_V_vs_SCE": -0.45,
            "Icorr_uA_cm2": 0.8,
            "PREN": 5.0,
            "CorrosionMechanism": "SnO2 Native Passivation / IMC Scallop Galvanic Couple"
        }
        ox = {
            "ProtectiveOxide": "SnO / SnO2 Thin Oxide Film",
            "Kp_g2_m4_s": 1.2e-8,
            "MaxServiceTemperature_C": 125.0,  # Package operating limit
            "OxidationKinetics": "Logarithmic Ambient Oxidation"
        }
        return corr, ox

    def compute_single_temperature_step(self, t_k: float) -> Dict[str, Any]:
        """Provides state at temperature T_K."""
        trans = self.compute_phase_transformations()
        t_c = t_k - 273.15
        t_liq_c = trans["T_Liquidus_C"]
        t_sol_c = trans["T_Solidus_C"]

        if t_c >= t_liq_c:
            phases = {"Liquid": 1.0}
            dominant = "Liquid"
        elif t_c >= t_sol_c:
            f_liq = (t_c - t_sol_c) / max(0.1, (t_liq_c - t_sol_c))
            phases = {"Liquid": float(f_liq), "BCT_Beta_Sn": float(1.0 - f_liq)}
            dominant = "Liquid + BCT_Beta_Sn"
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
