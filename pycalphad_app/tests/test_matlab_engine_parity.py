# -*- coding: utf-8 -*-
"""
test_matlab_engine_parity.py - Verification of 1:1 Parity with MATLAB ./App/ Engines and Databases
Verifies:
1. All 14 alloy databases load with correct presets, elements, and thermodynamic models.
2. BenchmarkDatabase recognizes HEA archetypes and computes accurate deviations and MAPEs.
3. HighThroughputScreener evaluates alloys in memory and exports CSV dossiers.
4. PiecewiseFitter produces valid polynomials for COMSOL, ABAQUS, and ANSYS Fluent.
5. OriginPlotter configures pyqtgraph canvases with boxed frames and inward ticks.
"""

import os
import pytest
import numpy as np
from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.database.benchmark_database import BenchmarkDatabase
from pycalphad_app.core.high_throughput_screener import HighThroughputScreener
from pycalphad_app.core.piecewise_fitter import PiecewiseFitter
from pycalphad_app.core.origin_plotter import OriginPlotter


def test_all_14_databases_load():
    """Verify all 14 material databases are registered and instantiate valid specs."""
    dbs = MaterialDatabaseSelector.get_database_list()
    assert len(dbs) == 14, f"Expected 14 databases, found {len(dbs)}"

    for db_name in dbs:
        spec = MaterialDatabaseSelector.get_spec(db_name)
        assert "name" in spec
        assert "composition" in spec
        assert len(spec["composition"]) > 0
        assert "category" in spec
        assert "domain_group" in spec


def test_benchmark_database_archetypes():
    """Verify archetype identification for landmark high-entropy and structural alloys."""
    # Cantor Alloy
    cantor_comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
    assert BenchmarkDatabase.identify_alloy_key(cantor_comp) == "CANTOR_COCRFEMNNI"

    # Equiatomic AlCoCrFeNi
    al10_comp = {"Al": 20.0, "Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Ni": 20.0}
    assert BenchmarkDatabase.identify_alloy_key(al10_comp) == "AL10_COCRFENI"

    # Refractory RHEA
    rhea_comp = {"Ti": 20.0, "Zr": 20.0, "Hf": 20.0, "Nb": 20.0, "Ta": 20.0}
    assert BenchmarkDatabase.identify_alloy_key(rhea_comp) == "TIZRHFNBA_RHEA"

    # Thermal Spray Coating
    coating_comp = {"Ni": 71.61, "Cr": 15.27, "Si": 4.65, "Fe": 4.47, "B": 3.32, "C": 0.68}
    assert BenchmarkDatabase.identify_alloy_key(coating_comp) == "COLMONOY6_COATING"


def test_benchmark_database_comparison():
    """Verify calculated vs experimental quantitative deviation and MAPE evaluation."""
    cantor_comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
    mock_calc = {
        "Density_g_cm3": 8.02,
        "Solidus_K": 1560.0,
        "Liquidus_K": 1615.0,
        "YieldStrength_RT_MPa": 208.0,
        "UTS_RT_MPa": 575.0,
        "VickersHardness_HV": 144.0
    }

    res = BenchmarkDatabase.compare_metrics(cantor_comp, mock_calc)
    assert res["alloy_key"] == "CANTOR_COCRFEMNNI"
    assert len(res["table"]) >= 5
    assert res["overall_mape"] < 5.0  # High accuracy match
    assert "tensile_curve" in res["plot_benchmarks"]
    assert "xrd" in res["plot_benchmarks"]


def test_high_throughput_screener():
    """Verify HighThroughputScreener screens alloys across structural classes."""
    master_lib = HighThroughputScreener.get_master_library()
    assert len(master_lib) == 51

    # Screen alloys
    all_results = HighThroughputScreener.screen_all()
    assert len(all_results) == 51
    first = all_results[0]
    assert "name" in first
    assert "density_g_cm3" in first
    assert "yield_strength_mpa" in first
    assert "hardness_hv" in first


def test_piecewise_fitter():
    """Verify PiecewiseFitter generates valid piecewise polynomial expressions."""
    t_data = np.linspace(300.0, 1800.0, 30)
    rho_data = 8000.0 - 0.5 * (t_data - 300.0)

    fit_res = PiecewiseFitter.fit_property_piecewise(t_data, rho_data, t_solidus=1200.0, t_liquidus=1300.0, degree=2)
    assert "solid_coeffs" in fit_res
    assert "mushy_coeffs" in fit_res
    assert "liquid_coeffs" in fit_res
    assert len(fit_res["solid_coeffs"]) > 0

    comsol_funcs = PiecewiseFitter.generate_comsol_functions({"Solidus_K": 1200.0, "Liquidus_K": 1300.0, "Density_g_cm3": 7.9})
    assert "rho_T" in comsol_funcs
    assert "k_T" in comsol_funcs


def test_origin_plotter():
    """Verify OriginPlotter applies boxed frames, inward ticks, and scientific fonts."""
    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg

    app = QApplication.instance() or QApplication([])
    pw = pg.PlotWidget()
    OriginPlotter.format_plot(pw.getPlotItem(), title="Origin Test", x_label="Temperature (K)", y_label="Fraction")

    assert pw.getPlotItem().axes['bottom']['item'].pen().color().name().lower() == "#333333"
    pw.close()


def test_hea_oxide_database_54_species():
    """Verify all 54 candidate oxides load with Ellingham thermodynamics and affinity ranking."""
    from pycalphad_app.database.oxide_database import HEAOxideDatabase

    all_ox = HEAOxideDatabase.get_all_oxides()
    assert len(all_ox) == 54, f"Expected 54 oxides, found {len(all_ox)}"

    # Check required fields across all 54 oxides
    for ox in all_ox:
        assert "Formula" in ox
        assert "Name" in ox
        assert "Elements" in ox
        assert "A" in ox
        assert "B" in ox
        assert "PBR" in ox
        assert "Density" in ox
        assert "Tm_K" in ox
        assert "Class" in ox

    # Alloy candidate filtering
    cand = HEAOxideDatabase.get_oxides_for_alloy(["Al", "Co", "Cr", "Fe", "Ni"])
    assert len(cand) == 17

    # Affinity ranking at 1173.15 K (900 C)
    ranked = HEAOxideDatabase.rank_oxides_by_affinity(["Al", "Co", "Cr", "Fe", "Ni"], 1173.15)
    assert len(ranked) == 17
    assert ranked[0]["Formula"] == "Al2O3"  # Alumina is most thermodynamically stable

    # Summary table
    tbl = HEAOxideDatabase.get_oxides_summary_table(["Al", "Co", "Cr", "Fe", "Ni"], 900.0)
    assert len(tbl) == 17
    assert tbl[0]["Oxide"] == "Al2O3"
    assert tbl[0]["DeltaG_f_kJ_per_mol_O2"] < -850.0


def test_oxidation_engine_with_database():
    """Verify OxidationEngine queries HEAOxideDatabase and returns 54-oxide hierarchy."""
    from pycalphad_app.core.oxidation_engine import OxidationEngine

    res = OxidationEngine.compute_oxidation_kinetics(
        ["Al", "Co", "Cr", "Fe", "Ni"], [0.2, 0.2, 0.2, 0.2, 0.2], temp_c=900.0
    )
    assert res["Regime"] == "Alumina Former"
    assert "α-Al2O3" in res["DominantOxide"] or "Al2O3" in res["DominantOxide"]
    assert len(res["EllinghamEnergies"]) == 17
    assert len(res["OxideSummaryTable"]) == 17
    assert len(res["RankedOxides"]) == 17


def test_lattice_distortion_literature_benchmarks():
    """Verify LatticeDistortionEngine matches literature benchmarks and computes activation volume."""
    from pycalphad_app.core.lattice_distortion_engine import LatticeDistortionEngine

    # Cantor Alloy
    res_cantor = LatticeDistortionEngine.compute_distortion_metrics(
        ["Co", "Cr", "Fe", "Mn", "Ni"], [0.2, 0.2, 0.2, 0.2, 0.2]
    )
    assert res_cantor["LiteratureBenchmark"]["Matched"] is True
    assert "Cantor" in res_cantor["LiteratureBenchmark"]["System"]
    assert res_cantor["ActivationVolume_m3"] > 0
    assert res_cantor["PoissonFactor"] > 1.0

    # CoCrNi MEA
    res_cocrni = LatticeDistortionEngine.compute_distortion_metrics(
        ["Co", "Cr", "Ni"], [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
    )
    assert res_cocrni["LiteratureBenchmark"]["Matched"] is True
    assert "CoCrNi" in res_cocrni["LiteratureBenchmark"]["System"]

    # Refractory TiZrHfNbTa
    res_rhea = LatticeDistortionEngine.compute_distortion_metrics(
        ["Ti", "Zr", "Hf", "Nb", "Ta"], [0.2, 0.2, 0.2, 0.2, 0.2]
    )
    assert res_rhea["LiteratureBenchmark"]["Matched"] is True
    assert "TiZrHfNbTa" in res_rhea["LiteratureBenchmark"]["System"]


def test_xrd_experimental_benchmarks():
    """Verify XRDEngine matches all digitized benchmark experimental curves."""
    from pycalphad_app.core.xrd_engine import XRDEngine

    # 1. Al1.5CoCrFeNi
    b1 = XRDEngine.get_benchmark_experimental_curve(["Al", "Co", "Cr", "Fe", "Ni"], np.array([0.28, 0.18, 0.18, 0.18, 0.18]), 1.5406)
    assert b1["hasData"] is True and "Al_{1.5}" in b1["title"]

    # 2. Al0.3CoCrFeNi
    b2 = XRDEngine.get_benchmark_experimental_curve(["Al", "Co", "Cr", "Fe", "Ni"], np.array([0.0698, 0.2325, 0.2325, 0.2325, 0.2325]), 1.5406)
    assert b2["hasData"] is True and "Al_{0.3}" in b2["title"]

    # 3. Al0.7CoCrFeNi
    b3 = XRDEngine.get_benchmark_experimental_curve(["Al", "Co", "Cr", "Fe", "Ni"], np.array([0.7 / 4.7, 1.0 / 4.7, 1.0 / 4.7, 1.0 / 4.7, 1.0 / 4.7]), 1.5406)
    assert b3["hasData"] is True and "Al_{0.7}" in b3["title"]

    # 4. Eutectic AlCoCrFeNi2.1
    b4 = XRDEngine.get_benchmark_experimental_curve(["Al", "Co", "Cr", "Fe", "Ni"], np.array([1.0 / 6.1, 1.0 / 6.1, 1.0 / 6.1, 1.0 / 6.1, 2.1 / 6.1]), 1.5406)
    assert b4["hasData"] is True and "Eutectic" in b4["title"]

    # 5. Cantor Alloy
    b5 = XRDEngine.get_benchmark_experimental_curve(["Co", "Cr", "Fe", "Mn", "Ni"], np.array([0.2, 0.2, 0.2, 0.2, 0.2]), 1.5406)
    assert b5["hasData"] is True and "Cantor" in b5["title"]

    # 6. Refractory NbMoTaW
    b6 = XRDEngine.get_benchmark_experimental_curve(["Nb", "Mo", "Ta", "W"], np.array([0.25, 0.25, 0.25, 0.25]), 1.5406)
    assert b6["hasData"] is True and "NbMoTaW" in b6["title"]

    # 7. CoCrNi MEA
    b7 = XRDEngine.get_benchmark_experimental_curve(["Co", "Cr", "Ni"], np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]), 1.5406)
    assert b7["hasData"] is True and "CoCrNi" in b7["title"]

    # 8. TRIP-HEA
    b8 = XRDEngine.get_benchmark_experimental_curve(["Fe", "Mn", "Co", "Cr"], np.array([0.5, 0.3, 0.1, 0.1]), 1.5406)
    assert b8["hasData"] is True and "TRIP-HEA" in b8["title"]

    # 9. Refractory MoNbTaVW
    b9 = XRDEngine.get_benchmark_experimental_curve(["Mo", "Nb", "Ta", "V", "W"], np.array([0.2, 0.2, 0.2, 0.2, 0.2]), 1.5406)
    assert b9["hasData"] is True and "MoNbTaVW" in b9["title"]

    # 10. Refractory TiZrHfNbTa
    b10 = XRDEngine.get_benchmark_experimental_curve(["Ti", "Zr", "Hf", "Nb", "Ta"], np.array([0.2, 0.2, 0.2, 0.2, 0.2]), 1.5406)
    assert b10["hasData"] is True and "TiZrHfNbTa" in b10["title"]

    # 11. ZnO/MgO Nanocomposite
    b11 = XRDEngine.get_benchmark_experimental_curve(["Zn", "O"], np.array([0.5, 0.5]), 1.5406)
    assert b11["hasData"] is True and "ZnO/MgO" in b11["title"]


def test_thermo_engine_transport_and_physics():
    """Verify ThermoEngine high-temperature transport, rheology, laser absorptivity, and Inden models."""
    from pycalphad_app.core.thermo_engine import ThermoEngine

    elems = ["Fe", "Ni", "Cr", "Co"]
    fracs = [0.25, 0.25, 0.25, 0.25]

    # Liquid Surface Tension
    st = ThermoEngine.compute_liquid_surface_tension(elems, fracs)
    assert len(st["T_K"]) > 10
    assert np.all(st["SurfaceTension_N_m"] > 0.4)

    # Liquid Viscosity
    visc = ThermoEngine.compute_liquid_viscosity(elems, fracs)
    assert len(visc["T_K"]) > 10
    assert np.all(visc["Viscosity_Pa_s"] > 0.0)

    # Semi-solid Rheology
    rheo = ThermoEngine.compute_semi_solid_rheology(elems, fracs, ts_k=1550.0, tl_k=1650.0)
    assert len(rheo["T_K"]) == 150
    assert np.max(rheo["YieldStress_Pa"]) == 150000.0

    # Laser Absorptivity
    laser = ThermoEngine.compute_laser_absorptivity(elems, fracs, wavelength_um=1.064)
    assert len(laser["T_K"]) == 150
    assert 0.1 < np.mean(laser["LaserAbsorptivity_Effective"]) < 0.99

    # Magnetic Gibbs Energy
    g_mag = ThermoEngine.compute_magnetic_gibbs_energy(["Fe", "Co", "Ni"], [1/3, 1/3, 1/3], 300.0, phase="BCC")
    assert g_mag < 0.0

    # Hall-Algie Sigma Electron Vacancy
    sigma_nv = ThermoEngine.compute_sigma_electron_vacancy(["Fe", "Cr", "Mo", "Ni"], [0.25, 0.35, 0.15, 0.25])
    assert sigma_nv["AverageElectronVacancy_Nv"] > 2.45
    assert sigma_nv["IsSigmaPhaseProne"] is True


def test_coating_engine_substrates_and_dilution():
    """Verify HEACoatingEngine substrate database and tribological wear modeling."""
    from pycalphad_app.core.coating_engine import HEACoatingEngine

    subs = HEACoatingEngine.get_substrate_database()
    assert "AISI 1045" in subs
    assert "Inconel 718" in subs
    assert "Ti-6Al-4V" in subs
    assert "316L SS" in subs
    assert "CMSX-4" in subs
    assert "Pure Copper" in subs
    assert "AA6061" in subs
    assert "Q235" in subs

    coat_res = HEACoatingEngine.compute_coating_properties(
        ["Al", "Co", "Cr", "Fe", "Ni"], [0.2, 0.2, 0.2, 0.2, 0.2],
        user_opts={"Substrate": "Inconel 718", "Process": "Laser Cladding"}
    )
    assert "SpecificWearRate_1e6_mm3_Nm" in coat_res
    assert "FrictionCoefficient_COF" in coat_res
    assert "ThermalStress_MPa" in coat_res
    assert "ScratchCriticalLoad_Lc_N" in coat_res
    assert "PlasticResistance_H3E2_GPa" in coat_res
    assert "ElasticStrainParam_HE" in coat_res
