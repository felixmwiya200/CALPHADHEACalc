from pycalphad_app.core.xrd_engine import XRDEngine

def test_cantor_xrd():
    res = XRDEngine.calculate({'Co': 0.2, 'Cr': 0.2, 'Fe': 0.2, 'Mn': 0.2, 'Ni': 0.2})
    assert "FCC (A1)" in res["Phases"]
    assert res["LatticeParams"]["a_FCC"] == 3.596
    pks = {p["HKL"]: p for p in res["Peaks"]}
    assert "(111)" in pks
    assert abs(pks["(111)"]["TwoTheta"] - 43.56) < 0.15
    assert abs(pks["(200)"]["TwoTheta"] - 50.73) < 0.15
    assert abs(pks["(220)"]["TwoTheta"] - 74.58) < 0.15
    assert abs(pks["(311)"]["TwoTheta"] - 90.54) < 0.15
    assert abs(pks["(222)"]["TwoTheta"] - 95.81) < 0.15
    # Verify intensity ordering: (111) = 100%, (200) ~ 40-45%, (220) > (311)
    assert pks["(111)"]["Intensity"] == 1.0
    assert 0.35 <= pks["(200)"]["Intensity"] <= 0.50
    assert pks["(220)"]["Intensity"] > 0.15
    assert pks["(311)"]["Intensity"] > 0.10

def test_stainless_316l_xrd():
    res = XRDEngine.calculate({'Fe': 0.655, 'Cr': 0.17, 'Ni': 0.12, 'Mo': 0.025, 'Mn': 0.02, 'Si': 0.01})
    assert "FCC (A1)" in res["Phases"]
    assert 3.590 <= res["LatticeParams"]["a_FCC"] <= 3.610
    pks = {p["HKL"]: p for p in res["Peaks"]}
    assert "(111)" in pks
    assert 43.4 <= pks["(111)"]["TwoTheta"] <= 43.7
    assert 50.5 <= pks["(200)"]["TwoTheta"] <= 50.9

def test_senkov_rhea_xrd():
    res = XRDEngine.calculate({'Nb': 0.25, 'Mo': 0.25, 'Ta': 0.25, 'W': 0.25})
    assert "BCC (A2)" in res["Phases"]
    assert res["LatticeParams"]["a_BCC"] == 3.235
    pks = {p["HKL"]: p for p in res["Peaks"]}
    assert "(110)" in pks
    assert abs(pks["(110)"]["TwoTheta"] - 39.36) < 0.20
    assert abs(pks["(200)"]["TwoTheta"] - 56.88) < 0.20
    assert abs(pks["(211)"]["TwoTheta"] - 71.36) < 0.20

if __name__ == "__main__":
    test_cantor_xrd()
    test_stainless_316l_xrd()
    test_senkov_rhea_xrd()
    print("All XRD tests passed successfully!")
