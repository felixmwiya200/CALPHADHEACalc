# -*- coding: utf-8 -*-
"""
test_benchmark_multi_point_series.py - Verifies multi-point experimental benchmark datasets
"""

from pycalphad_app.database.benchmark_database import BenchmarkDatabase


def test_cantor_plot_benchmarks():
    comp = {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "High Entropy Alloys")
    assert "tensile_temp" in pb
    assert len(pb["tensile_temp"]["T_K"]) >= 5
    assert len(pb["tensile_temp"]["Yield_MPa"]) >= 5
    assert "stress_strain" in pb
    assert len(pb["stress_strain"]["true_strain"]) >= 5
    assert "thermal_transport" in pb
    assert len(pb["thermal_transport"]["T_K"]) >= 4
    assert "oxidation_kinetics" in pb


def test_inconel_718_plot_benchmarks():
    comp = {"Ni": 53.0, "Cr": 19.0, "Fe": 18.5, "Nb": 5.1, "Mo": 3.0, "Ti": 0.9, "Al": 0.5}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "Nickel Based Superalloy")
    assert "tensile_temp" in pb
    assert len(pb["tensile_temp"]["T_K"]) >= 4
    assert "thermal_transport" in pb


def test_ti_6al_4v_plot_benchmarks():
    comp = {"Ti": 90.0, "Al": 6.0, "V": 4.0}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "Titanium Alloy")
    assert "tensile_temp" in pb
    assert len(pb["tensile_temp"]["T_K"]) >= 4


def test_aa_7075_plot_benchmarks():
    comp = {"Al": 88.87, "Zn": 5.60, "Mg": 2.50, "Cu": 1.60}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "Aluminium Alloy")
    assert "tensile_temp" in pb
    assert len(pb["tensile_temp"]["T_K"]) >= 4
