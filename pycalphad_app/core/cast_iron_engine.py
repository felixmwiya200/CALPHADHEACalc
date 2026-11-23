# -*- coding: utf-8 -*-
"""
cast_iron_engine.py - Specialized Metallurgical Engine for Cast Irons
Covers Grey Iron (flake graphite), Ductile/Nodular Iron (spheroidal graphite),
and Compacted Graphite Iron (CGI / vermicular graphite).
Implements Carbon Equivalent (CE), stable vs metastable eutectic solidification,
graphite nodularity rating, and matrix phase fractions (ferrite/pearlite).
"""

from typing import Dict, Any, List, Tuple
import math
import numpy as np

from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine


class CastIronEngine(BaseAlloyEngine):
    """
    Dedicated metallurgical calculation engine for Cast Iron databases.
    Accurately accounts for carbon equivalent, silicon graphitizing potential,
    magnesium nodularization, and eutectic chilling criteria.
    """

    def get_supported_phases(self) -> List[str]:
        return [
            "Liquid",
            "Austenite",
            "Ferrite",
            "Pearlite",
            "Graphite",
            "Ledeburite / Cementite"
        ]

    def _calc_ce(self) -> float:
        """Calculates Carbon Equivalent (CE) in wt. %: CE = %C + (%Si + %P) / 3."""
        c = self.comp_wt.get("C", 0.0) * 100.0
        si = self.comp_wt.get("Si", 0.0) * 100.0
        p = self.comp_wt.get("P", 0.0) * 100.0
        return c + (si + p) / 3.0

    def compute_phase_transformations(self) -> Dict[str, Any]:
        """
        Calculates solidification and solid-state transformation boundaries:
        - Carbon Equivalent (CE)
        - Stable graphite eutectic vs metastable ledeburite eutectic temperatures
        - Liquidus temperature based on hypoeutectic / hypereutectic regime
        - Nodularity classification based on residual Mg / Ce
        """
        ce = self._calc_ce()
        c = self.comp_wt.get("C", 0.0) * 100.0
        si = self.comp_wt.get("Si", 0.0) * 100.0
        mn = self.comp_wt.get("Mn", 0.0) * 100.0
        p = self.comp_wt.get("P", 0.0) * 100.0
        s = self.comp_wt.get("S", 0.0) * 100.0
        mg = self.comp_wt.get("Mg", 0.0) * 100.0
        ce_elem = self.comp_wt.get("Ce", 0.0) * 100.0

        # Stable (Austenite-Graphite) Eutectic Temperature (C)
        # Si raises stable eutectic, Mn lowers it
        t_eut_stable_c = 1153.0 + (5.0 * si) - (2.0 * mn) - (30.0 * p)

        # Metastable (Austenite-Fe3C Ledeburite) Eutectic Temperature (C)
        # Si depresses metastable eutectic, opening the eutectic window Delta T
        t_eut_meta_c = 1145.0 - (15.0 * si) + (3.0 * mn)

        # Liquidus Temperature (C)
        if ce <= 4.30:
            # Hypoeutectic iron (primary austenite dendrites)
            t_liq_c = 1633.0 - (113.0 * ce)
        else:
            # Hypereutectic iron (primary kish graphite)
            t_liq_c = 1153.0 + (85.0 * (ce - 4.30))

        # Solidus is bounded by eutectic completion
        t_sol_c = t_eut_stable_c if (t_eut_stable_c > t_eut_meta_c) else t_eut_meta_c

        # Nodularity classification from residual Mg and Ce
        effective_nodulizer = mg + 0.5 * ce_elem
        if effective_nodulizer >= 0.025:
            iron_type = "Ductile Iron"
            nodularity_pct = min(98.0, 75.0 + 500.0 * (effective_nodulizer - 0.025))
        elif effective_nodulizer >= 0.010:
            iron_type = "Compacted Graphite Iron (CGI)"
            nodularity_pct = 20.0 + 3600.0 * (effective_nodulizer - 0.010)
        else:
            iron_type = "Grey Iron"
            nodularity_pct = min(15.0, max(2.0, 200.0 * effective_nodulizer))

        # Pearlite / Ferrite eutectoid transformation interval
        t_eutectoid_c = 727.0 + (28.0 * si) - (25.0 * mn) - (15.0 * self.comp_wt.get("Ni", 0.0) * 100.0)

        return {
            "CE": float(ce),
            "IronType": iron_type,
            "Nodularity_pct": float(nodularity_pct),
            "Eutectic_Stable_C": float(t_eut_stable_c),
            "Eutectic_Metastable_C": float(t_eut_meta_c),
            "Eutectic_Window_C": float(t_eut_stable_c - t_eut_meta_c),
            "T_Liquidus_C": float(t_liq_c),
            "T_Solidus_C": float(t_sol_c),
            "Eutectoid_C": float(t_eutectoid_c),
            "T_Liquidus_K": float(t_liq_c + 273.15),
            "T_Solidus_K": float(t_sol_c + 273.15)
        }

    def compute_thermodynamics(self) -> Dict[str, Any]:
        """Computes phase equilibria and room-temperature constituent fractions."""
        trans = self.compute_phase_transformations()
        ce = trans["CE"]
        c = self.comp_wt.get("C", 0.0) * 100.0
        si = self.comp_wt.get("Si", 0.0) * 100.0
        mn = self.comp_wt.get("Mn", 0.0) * 100.0
        iron_type = trans["IronType"]

        # Graphite volume fraction: dependent on C content and Si graphitizing
        # Typical cast iron graphite fraction is ~8-12 vol.%
        c_in_graphite = max(1.5, c - 0.8)  # ~0.8 wt% C stays dissolved in pearlite matrix
        graphite_vol_frac = (c_in_graphite * 7.85) / (100.0 * 2.25)  # density ratio
        graphite_vol_frac = max(0.04, min(0.14, graphite_vol_frac))

        # Matrix phase distribution: Ferrite vs Pearlite
        # Higher cooling rate and higher Mn promote pearlite; higher Si promotes ferrite
        cooling = self.cooling_rate_k_s
        pearlite_promoter = (mn * 1.5) + math.log10(max(0.1, cooling)) * 0.25 - (si * 0.15)
        pearlite_frac = 1.0 / (1.0 + math.exp(-2.5 * (pearlite_promoter - 0.2)))
        ferrite_frac = max(0.0, 1.0 - pearlite_frac)

        # Total room-temperature constituent phases
        phases = {
            "Graphite": float(graphite_vol_frac),
            "Ferrite": float(ferrite_frac * (1.0 - graphite_vol_frac)),
            "Pearlite": float(pearlite_frac * (1.0 - graphite_vol_frac))
        }

        t_liq_k = trans["T_Liquidus_K"]
        t_sol_k = trans["T_Solidus_K"]

        # Enthalpy of fusion: ~260 J/g for eutectic cast iron
        delta_h_fus = 260.0 * 1000.0  # J/kg

        return {
            "T_Liquidus": float(t_liq_k),
            "T_Solidus": float(t_sol_k),
            "Solidus_K": float(t_sol_k),
            "Liquidus_K": float(t_liq_k),
            "Enthalpy_Fusion_J_kg": float(delta_h_fus),
            "Phases": phases,
            "DominantPhase": "Ferrite" if ferrite_frac > pearlite_frac else "Pearlite",
            "MatrixState": f"{iron_type} ({phases['Pearlite']*100:.0f}% Pearlite / {phases['Ferrite']*100:.0f}% Ferrite)"
        }

    def compute_mechanical_properties(self, thermo: Dict[str, Any],
                                      transform: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes tensile yield strength, ultimate tensile strength, elongation,
        and hardness according to ASTM/ISO cast iron standards.
        """
        iron_type = transform["IronType"]
        nodularity = transform["Nodularity_pct"]
        phases = thermo.get("Phases", {})
        f_pearlite = phases.get("Pearlite", 0.5)
        si = self.comp_wt.get("Si", 0.0) * 100.0

        if iron_type == "Ductile Iron":
            # ASTM A536 standards:
            # Fully ferritic (60-40-18): Yield ~280 MPa, UTS ~420 MPa, Elong ~18%
            # Pearlitic (100-70-03): Yield ~480 MPa, UTS ~700 MPa, Elong ~3%
            sy = 240.0 + (220.0 * f_pearlite) + (35.0 * (si - 2.0))
            uts = 400.0 + (320.0 * f_pearlite) + (25.0 * (si - 2.0))
            elong = max(2.5, 18.0 - (15.0 * f_pearlite))
            hv = 140.0 + (120.0 * f_pearlite)
            k1c = 35.0 - (15.0 * f_pearlite)
            youngs_e = 170.0  # GPa for ductile iron
        elif iron_type == "Compacted Graphite Iron (CGI)":
            # ISO 16112 / CGI 400: intermediate between grey and ductile
            sy = 220.0 + (160.0 * f_pearlite)
            uts = 300.0 + (220.0 * f_pearlite)
            elong = max(1.0, 3.5 - (2.5 * f_pearlite))
            hv = 160.0 + (90.0 * f_pearlite)
            k1c = 22.0 - (8.0 * f_pearlite)
            youngs_e = 145.0  # GPa
        else:
            # Grey Iron: ASTM A48 (Class 20 to Class 50)
            # Notch effect of flake graphite tips limits elongation to < 1.0%
            uts = 180.0 + (160.0 * f_pearlite)
            sy = 0.65 * uts  # nominal 0.2% offset (elastic-plastic curve)
            elong = 0.5 + 0.3 * (1.0 - f_pearlite)
            hv = 170.0 + (80.0 * f_pearlite)
            k1c = 14.0
            youngs_e = 110.0  # GPa for flake graphite

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
            "PoissonRatio": 0.275,
            "PughRatio": float(youngs_e / (2.0 * (1.0 + 0.275) * max(10.0, sy * 0.001))),
            "DominantStructure": f"{iron_type} ({transform['Nodularity_pct']:.0f}% Nodularity)"
        }

    def compute_transport_properties(self, thermo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates thermophysical properties. Note that flake grey iron possesses
        exceptional thermal conductivity (~45-52 W/mK) due to interconnected graphite.
        """
        trans = self.compute_phase_transformations()
        iron_type = trans["IronType"]
        nodularity = trans["Nodularity_pct"]

        # Interconnected flake graphite channels heat far more effectively than isolated spheres
        if iron_type == "Grey Iron":
            k_th = 48.0 - (0.015 * (nodularity))
            damping_capacity = 0.85  # relative specific damping capacity
        elif iron_type == "Compacted Graphite Iron (CGI)":
            k_th = 38.0
            damping_capacity = 0.55
        else:
            k_th = 34.0
            damping_capacity = 0.25

        # Density: ~7.10 g/cm3 for grey iron, ~7.25 g/cm3 for ductile iron
        rho_rt = 7.10 + 0.0015 * nodularity
        cte_rt = 12.0e-6 + (1.5e-6 * (100.0 - nodularity) / 100.0)

        return {
            "TheoreticalDensity_g_cm3": float(rho_rt),
            "Density_RT_g_cm3": float(rho_rt),
            "ThermalConductivity_W_mK": float(k_th),
            "SpecificHeat_J_kgK": 490.0,
            "ThermalDiffusivity_m2_s": float(k_th / (rho_rt * 1000.0 * 490.0)),
            "CTE_1e6_K": float(cte_rt * 1e6),
            "ElectricalConductivity_MS_m": 1.45,
            "SpecificDampingCapacity": float(damping_capacity)
        }

    def compute_environmental_properties(self, thermo: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Computes oxidation and aqueous corrosion response."""
        trans = self.compute_phase_transformations()
        iron_type = trans["IronType"]
        nodularity = trans["Nodularity_pct"]

        # In grey iron, flake graphite provides galvanic micro-cells accelerating rust
        if iron_type == "Grey Iron":
            corr_rate_mpy = 14.5
            e_corr_v = -0.58
            pitting_resistance = 8.0
        else:
            corr_rate_mpy = 9.8
            e_corr_v = -0.54
            pitting_resistance = 12.0

        corr = {
            "CorrosionRate_mpy": float(corr_rate_mpy),
            "Ecorr_V_vs_SCE": float(e_corr_v),
            "Icorr_uA_cm2": 22.0,
            "PREN": float(pitting_resistance),
            "CorrosionMechanism": "Galvanic Ferrite-Graphite Micro-Cell Dissolution"
        }

        ox = {
            "OxidationKinetics": "Parabolic Rate Law",
            "Kp_g2_m4_s": 3.8e-5,
            "MaxServiceTemperature_C": 650.0 if iron_type == "Ductile Iron" else 550.0,
            "ProtectiveOxide": "Fe3O4 / Fe2O3 Duplex Scale"
        }

        return corr, ox

    def compute_single_temperature_step(self, t_k: float) -> Dict[str, Any]:
        """Provides instantaneous thermodynamic and phase fraction state at temperature T_K."""
        trans = self.compute_phase_transformations()
        t_c = t_k - 273.15
        t_liq_c = trans["T_Liquidus_C"]
        t_sol_c = trans["T_Solidus_C"]
        t_eutectoid_c = trans["Eutectoid_C"]

        if t_c >= t_liq_c:
            phases = {"Liquid": 1.0}
            dominant = "Liquid"
        elif t_c >= t_sol_c:
            f_liq = (t_c - t_sol_c) / max(1.0, (t_liq_c - t_sol_c))
            phases = {"Liquid": float(f_liq), "Austenite": float(1.0 - f_liq)}
            dominant = "Liquid + Austenite"
        elif t_c >= t_eutectoid_c:
            phases = {"Austenite": 0.90, "Graphite": 0.10}
            dominant = "Austenite + Graphite"
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
