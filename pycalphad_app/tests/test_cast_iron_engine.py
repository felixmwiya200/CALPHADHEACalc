# -*- coding: utf-8 -*-
"""
test_cast_iron_engine.py - Unit and benchmark tests for CastIronEngine
Tests Carbon Equivalent (CE), stable vs metastable eutectic growth,
nodularity classification (nodular/ductile vs flake vs compacted), and mechanical properties.
"""

import pytest
from pycalphad_app.core.cast_iron_engine import CastIronEngine


def test_ductile_iron_nodularity_and_properties():
    # Ductile iron (ASTM 65-45-12 / EN-GJS-400-15): Fe-3.6C-2.5Si-0.2Mn-0.04Mg
    comp = {"Fe": 93.66, "C": 3.6, "Si": 2.5, "Mn": 0.2, "Mg": 0.04}
    engine = CastIronEngine("Cast Irons", comp, grain_size_um=30.0, process_type="Casting")

    # 1. Carbon Equivalent and phase transformations
    trans = engine.compute_phase_transformations()
    assert "CE" in trans
    # CE = %C + (%Si + %P)/3 = 3.6 + 2.5/3 = 4.433
    assert 4.35 <= trans["CE"] <= 4.50
    assert trans["IronType"] == "Ductile Iron"
    assert trans["Nodularity_pct"] >= 80.0
    assert trans["Eutectic_Stable_C"] > trans["Eutectic_Metastable_C"]

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    assert "Graphite" in thermo.get("Phases", {})
    assert "Ferrite" in thermo.get("Phases", {})
    assert 1400.0 <= thermo["T_Liquidus"] <= 1500.0

    # 3. Mechanical properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Ductile iron exhibits substantial tensile elongation and proof strength
    assert 220.0 <= mech["YieldStrength_MPa"] <= 350.0
    assert mech["Elongation_pct"] >= 10.0


def test_grey_iron_flake_graphite():
    # Class 30 Grey Iron: Fe-3.2C-2.0Si-0.6Mn-0.005Mg
    comp = {"Fe": 94.195, "C": 3.2, "Si": 2.0, "Mn": 0.6, "Mg": 0.005}
    engine = CastIronEngine("Cast Irons", comp, grain_size_um=40.0, process_type="Casting")

    trans = engine.compute_phase_transformations()
    assert trans["IronType"] == "Grey Iron"
    assert trans["Nodularity_pct"] <= 20.0

    thermo = engine.compute_thermodynamics()
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Grey iron has low ductility due to flake stress concentrations
    assert mech["Elongation_pct"] <= 1.5
    # High thermal conductivity from interconnected flake graphite
    transp = engine.compute_transport_properties(thermo)
    assert transp["ThermalConductivity_W_mK"] >= 40.0
