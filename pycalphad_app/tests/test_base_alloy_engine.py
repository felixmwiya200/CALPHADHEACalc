# -*- coding: utf-8 -*-
"""
test_base_alloy_engine.py - Unit test suite for BaseAlloyEngine abstraction.
Verifies normalization, atomic fraction conversion, process cooling rates,
and lifecycle method contract enforcement.
"""

import pytest
from typing import Dict, List, Any, Tuple
from pycalphad_app.core.base_alloy_engine import BaseAlloyEngine


class DummyAlloyEngine(BaseAlloyEngine):
    """Concrete dummy implementation for contract testing."""
    def get_supported_phases(self) -> List[str]:
        return ["LIQUID", "FCC_A1"]

    def compute_thermodynamics(self) -> Dict[str, Any]:
        return {
            "Solidus_K": 1000.0,
            "Liquidus_K": 1100.0,
            "PhaseFractions": {"T_K": [1000.0, 1100.0], "FCC_A1": [1.0, 0.0], "LIQUID": [0.0, 1.0]}
        }

    def compute_phase_transformations(self) -> Dict[str, Any]:
        return {"Solvus_K": 850.0}

    def compute_mechanical_properties(self, thermo_state: Dict[str, Any], transform_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"YieldStrength_MPa": 350.0, "UTS_MPa": 520.0}

    def compute_transport_properties(self, thermo_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"ThermalConductivity_W_mK": 45.0, "Density_g_cm3": 7.8}

    def compute_environmental_properties(self, thermo_state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return ({"kp_values": [1e-12]}, {"Corrosion_Ecorr_V": -0.4})

    def compute_single_temperature_step(self, temperature_k: float) -> Dict[str, Any]:
        return {"T_K": temperature_k, "Phase": "FCC_A1"}


def test_base_alloy_engine_normalization():
    raw_comp = {"Al": 80.0, "Cu": 20.0}
    engine = DummyAlloyEngine("Test Al-Cu", raw_comp, grain_size_um=30.0, process_type="Casting")
    
    assert pytest.approx(sum(engine.comp_wt.values()), 1e-6) == 1.0
    assert pytest.approx(engine.comp_wt["Al"], 1e-4) == 0.8
    assert pytest.approx(engine.comp_wt["Cu"], 1e-4) == 0.2
    assert engine.base_element == "Al"


def test_base_alloy_engine_atomic_conversion():
    # Fe-50 wt% Ni
    raw_comp = {"Fe": 50.0, "Ni": 50.0}
    engine = DummyAlloyEngine("Test Fe-Ni", raw_comp)
    
    # Molar mass: Fe=55.845, Ni=58.693 -> at% Fe should be slightly higher than Ni
    assert engine.comp_at["Fe"] > engine.comp_at["Ni"]
    assert pytest.approx(sum(engine.comp_at.values()), 1e-6) == 1.0


def test_base_alloy_engine_cooling_rate():
    eng_cast = DummyAlloyEngine("Alloy", {"Al": 100.0}, process_type="Casting")
    assert eng_cast.cooling_rate_k_s == 1.5
    
    eng_quench = DummyAlloyEngine("Alloy", {"Al": 100.0}, process_type="Water Quench")
    assert eng_quench.cooling_rate_k_s == 150.0


def test_base_alloy_engine_lifecycle():
    engine = DummyAlloyEngine("Alloy", {"Fe": 100.0})
    thermo = engine.compute_thermodynamics()
    transform = engine.compute_phase_transformations()
    mech = engine.compute_mechanical_properties(thermo, transform)
    transport = engine.compute_transport_properties(thermo)
    ox, corr = engine.compute_environmental_properties(thermo)
    step = engine.compute_single_temperature_step(800.0)

    assert thermo["Solidus_K"] == 1000.0
    assert mech["YieldStrength_MPa"] == 350.0
    assert transport["ThermalConductivity_W_mK"] == 45.0
    assert ox["kp_values"] == [1e-12]
    assert corr["Corrosion_Ecorr_V"] == -0.4
    assert step["T_K"] == 800.0
