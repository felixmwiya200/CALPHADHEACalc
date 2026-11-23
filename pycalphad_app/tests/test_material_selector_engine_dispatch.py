# -*- coding: utf-8 -*-
"""
test_material_selector_engine_dispatch.py - Unit test for polymorphic engine dispatch
Verifies that MaterialDatabaseSelector.get_engine(...) returns the proper dedicated engine
for all 14 alloy databases.
"""

import pytest
from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.core.steel_engine import SteelEngine
from pycalphad_app.core.cast_iron_engine import CastIronEngine
from pycalphad_app.core.nickel_superalloy_engine import NickelSuperalloyEngine
from pycalphad_app.core.cobalt_alloy_engine import CobaltAlloyEngine
from pycalphad_app.core.titanium_engine import TitaniumEngine
from pycalphad_app.core.aluminium_engine import AluminiumEngine
from pycalphad_app.core.magnesium_engine import MagnesiumEngine
from pycalphad_app.core.zirconium_engine import ZirconiumEngine
from pycalphad_app.core.solder_engine import SolderEngine
from pycalphad_app.core.hea_engine import HEAEngine
from pycalphad_app.core.coating_alloy_engine import CoatingAlloyEngine


def test_engine_dispatch_for_all_databases():
    expected_mappings = {
        "High Entropy Alloys": HEAEngine,
        "Thermal Spray Coatings": CoatingAlloyEngine,
        "Aluminium Alloy": AluminiumEngine,
        "Magnesium Alloy": MagnesiumEngine,
        "Cast Iron": CastIronEngine,
        "General Steel": SteelEngine,
        "Stainless Steel": SteelEngine,
        "Cobalt Alloy": CobaltAlloyEngine,
        "Nickel Based Superalloy": NickelSuperalloyEngine,
        "NiFe Based Superalloy": NickelSuperalloyEngine,
        "Single Crystal": NickelSuperalloyEngine,
        "Titanium Alloy": TitaniumEngine,
        "Zirconium Alloy": ZirconiumEngine,
        "Solder Alloy": SolderEngine,
    }

    dummy_comp = {"Fe": 50.0, "Ni": 50.0}

    for db_name, expected_engine_cls in expected_mappings.items():
        engine = MaterialDatabaseSelector.get_engine(db_name, dummy_comp)
        assert isinstance(engine, expected_engine_cls), f"Database '{db_name}' should map to {expected_engine_cls.__name__}, got {type(engine).__name__}"
        phases = engine.get_supported_phases()
        assert len(phases) > 0
