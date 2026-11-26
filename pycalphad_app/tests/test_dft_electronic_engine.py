"""
Author: Felix Mwiya
Module: pycalphad_app.tests.test_dft_electronic_engine
Description: Unit verification suite for first-principles DFT and Morinaga d-electron theory calculations.
"""

import pytest
from pycalphad_app.core.dft_electronic_engine import DFTElectronicEngine


def test_fe_cr_mn_austenitic_steel():
    # Fe-18Cr-12Mn high-Mn austenitic fusion matrix (Murata et al. 1990)
    comp = {"Fe": 0.70, "Cr": 0.18, "Mn": 0.12}
    res = DFTElectronicEngine.calculate(comp, temp_k=923.15)

    assert "bo_avg" in res and res["bo_avg"] > 0.80
    assert "md_avg" in res and res["md_avg"] > 0.85
    assert "sigma_instability_ratio" in res
    assert "sfe_mj_m2" in res
    assert res["sfe_mj_m2"] > 0.0

    # At 650°C (923 K), Fe-18Cr-12Mn has Md around 0.92, which is above Md_crit (0.880)
    assert res["sigma_instability_ratio"] >= 1.0
    assert "Embrittlement" in res["sigma_risk"] or "Marginal" in res["sigma_risk"]

    # Wyckoff 5-sublattice structure verification
    sublattices = res["sublattices"]
    assert len(sublattices) == 5
    sites = [s["site"] for s in sublattices]
    assert sites == ["2a", "4f", "8i_1", "8i_2", "8j"]


def test_cantor_alloy_dft():
    # CoCrFeMnNi equiatomic Cantor HEA
    comp = {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}
    res = DFTElectronicEngine.calculate(comp, temp_k=1073.15)

    assert res["bo_avg"] > 0.80
    assert "FCC" in res["matrix_prediction"] or "Austenite" in res["matrix_prediction"]

    # Cantor alloy has TWIP/dislocation slip SFE (approx 20-35 mJ/m^2)
    assert 15.0 <= res["sfe_mj_m2"] <= 55.0


def test_pure_ferritic_iron():
    comp = {"Fe": 0.98, "Cr": 0.02}
    res = DFTElectronicEngine.calculate(comp, temp_k=800.0)

    # Pure Fe has low Md (0.858), well below sigma danger limit
    assert res["sigma_instability_ratio"] < 1.0
    assert "Safe" in res["sigma_risk"]
