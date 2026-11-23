# Multi-Alloy Family Backend Engines Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and integrate dedicated, authentic calculation engines for each of the 14 alloy databases in PyCALPHAD Suite, replacing the generic HEA fallback with family-specific thermodynamic and metallurgical models via a polymorphic `BaseAlloyEngine` hierarchy.

**Architecture:** A clean Strategy and Abstract Factory pattern. `BaseAlloyEngine` defines the lifecycle hooks (`compute_thermodynamics`, `compute_phase_transformations`, `compute_mechanical_properties`, `compute_transport_properties`, `compute_environmental_properties`, `compute_single_temperature_step`). 10 dedicated family engines implement the physical formulations, and `MaterialDatabaseSelector` dynamically instantiates the correct engine for `SolverWorker` and `IterativeSolver`.

**Tech Stack:** Python 3.12, NumPy, SciPy, PyQt6, PyQtGraph, SGTE Dinsdale unary polynomials, Redlich-Kister excess parameters, PyInstaller.

---

### Phase 1: Abstract Base Foundation & Typing

#### Task 1: Implement `BaseAlloyEngine` Interface
**Files:**
- Create: `pycalphad_app/core/base_alloy_engine.py`
- Test: `pycalphad_app/tests/test_base_alloy_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_base_alloy_engine.py`:
- Test instantiation of concrete subclass.
- Test normalization of composition (wt% and at%).
- Test deterministic cooling rate lookup from `process_type`.
- Test dilute solute clamping ($x_i \ge 10^{-12}$).

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_base_alloy_engine.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'pycalphad_app.core.base_alloy_engine'`

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/base_alloy_engine.py`:
- Define `BaseAlloyEngine` ABC with lifecycle hooks.
- Implement `_normalize()`, `_convert_to_atomic()`, `_resolve_base_element()`.
- Define `COOLING_RATES` mapping dictionary.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_base_alloy_engine.py`
Expected: PASS

---

### Phase 2: Core Structural & High-Temperature Alloy Engines

#### Task 2: Implement `SteelEngine` (Steels & Stainless Steels)
**Files:**
- Create: `pycalphad_app/core/steel_engine.py`
- Test: `pycalphad_app/tests/test_steel_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_steel_engine.py`:
- Test AISI 4340 ($M_s \approx 290-320\,^\circ\text{C}$, $B_s \approx 480-520\,^\circ\text{C}$).
- Test AISI 304 Stainless ($\text{Cr-Ni}$ austenite stability, $M_s < -100\,^\circ\text{C}$).
- Test Hall-Petch grain size strengthening and carbon interstitial strengthening.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_steel_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/steel_engine.py`:
- Implement Andrews linear and product $M_s$ formulas, Koistinen-Marburger athermal martensite fractions.
- Implement Steven & Haynes $B_s$ formulation.
- Implement ferrite/pearlite/martensite mechanical constitutive models.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_steel_engine.py`
Expected: PASS

#### Task 3: Implement `CastIronEngine` (Grey, Ductile, CGI)
**Files:**
- Create: `pycalphad_app/core/cast_iron_engine.py`
- Test: `pycalphad_app/tests/test_cast_iron_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_cast_iron_engine.py`:
- Test Carbon Equivalent ($\text{CE}$) calculation.
- Test eutectic graphite vs ledeburite temperature thresholds.
- Test nodularity rating ($N_{\text{nod}}$) based on residual $\text{Mg}/\text{Ce}$.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_cast_iron_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/cast_iron_engine.py`:
- Implement CE formula, eutectic interval, graphite morphology classification, and hardness scaling.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_cast_iron_engine.py`
Expected: PASS

#### Task 4: Implement `NickelSuperalloyEngine` (Ni & Ni-Fe Superalloys, Single Crystal)
**Files:**
- Create: `pycalphad_app/core/nickel_superalloy_engine.py`
- Test: `pycalphad_app/tests/test_nickel_superalloy_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_nickel_superalloy_engine.py`:
- Test Inconel 718 ($\gamma'$ and $\gamma''$ solvus and fractions).
- Test CMSX-4 single-crystal rafting lattice misfit ($\delta < 0$).
- Test New PHACOMP $\bar{M}_d$ TCP embrittlement warning.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_nickel_superalloy_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/nickel_superalloy_engine.py`:
- Implement thermodynamic $\gamma'$ solvus, coherent volume fraction evolution, lattice misfit parameter $\delta$, New PHACOMP $d$-orbital levels, and Monkman-Grant creep life.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_nickel_superalloy_engine.py`
Expected: PASS

#### Task 5: Implement `CobaltAlloyEngine` (Stellites & Co-Base)
**Files:**
- Create: `pycalphad_app/core/cobalt_alloy_engine.py`
- Test: `pycalphad_app/tests/test_cobalt_alloy_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_cobalt_alloy_engine.py`:
- Test Stellite 6 allotropic $\gamma\text{-FCC} \to \epsilon\text{-HCP}$ transformation and carbide volume fractions ($M_{23}C_6$, $M_7C_3$).
- Test hardness and galling wear resistance scaling.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_cobalt_alloy_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/cobalt_alloy_engine.py`:
- Implement Co allotropic transformation temperature, carbide network volume fractions, and Archard wear coefficient.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_cobalt_alloy_engine.py`
Expected: PASS

#### Task 6: Implement `TitaniumEngine` (Ti Alloys)
**Files:**
- Create: `pycalphad_app/core/titanium_engine.py`
- Test: `pycalphad_app/tests/test_titanium_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_titanium_engine.py`:
- Test Ti-6Al-4V $\beta$-transus ($T_\beta \approx 995\,^\circ\text{C}$).
- Test $[\text{Al}]_{\text{eq}}$ and $[\text{Mo}]_{\text{eq}}$ classification into $\alpha+\beta$.
- Test shear martensite $\alpha'$ onset upon rapid cooling.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_titanium_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/titanium_engine.py`:
- Implement empirical $\beta$-transus formulation, $[\text{Al}]_{\text{eq}}$ and $[\text{Mo}]_{\text{eq}}$ formulas, dual-phase $\alpha+\beta$ lever rule, and martensite shear kinetics.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_titanium_engine.py`
Expected: PASS

---

### Phase 3: Lightweight, Nuclear & Functional Alloy Engines

#### Task 7: Implement `AluminiumEngine` (1xxx - 7xxx Wrought & 3xx Cast)
**Files:**
- Create: `pycalphad_app/core/aluminium_engine.py`
- Test: `pycalphad_app/tests/test_aluminium_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_aluminium_engine.py`:
- Test AA 7075-T6 ($\text{FCC matrix}$, $\eta'\text{-MgZn}_2$, solidus $750.15\text{ K}$, yield strength $\ge 450\text{ MPa}$).
- Test AA 2024-T3 ($\text{Al}_2\text{Cu}$, $S$-phase).
- Test A356 cast eutectic $\text{Al-Si}$ solidification.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_aluminium_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/aluminium_engine.py`:
- Implement multi-solute solvus, GP zone precipitation, Kampmann-Wagner numerical Orowan transition, and casting eutectic fraction.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_aluminium_engine.py`
Expected: PASS

#### Task 8: Implement `MagnesiumEngine` (AZ, AM, ZK + Twinning)
**Files:**
- Create: `pycalphad_app/core/magnesium_engine.py`
- Test: `pycalphad_app/tests/test_magnesium_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_magnesium_engine.py`:
- Test AZ91D ($\alpha\text{-Mg}$, $\beta\text{-Mg}_{17}\text{Al}_{12}$ eutectic at $437\,^\circ\text{C}$).
- Test tension vs compression yield asymmetry ($\sigma_y^T > \sigma_y^C$).

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_magnesium_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/magnesium_engine.py`:
- Implement HCP twinning asymmetry, $\beta\text{-Mg}_{17}\text{Al}_{12}$ cellular precipitation, and thermal softening.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_magnesium_engine.py`
Expected: PASS

#### Task 9: Implement `ZirconiumEngine` (Zircaloys & Refractories)
**Files:**
- Create: `pycalphad_app/core/zirconium_engine.py`
- Test: `pycalphad_app/tests/test_zirconium_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_zirconium_engine.py`:
- Test Zircaloy-4 ($\alpha\text{-Zr}$ HCP to $\beta\text{-Zr}$ BCC allotropy at $863\,^\circ\text{C}$).
- Test hydrogen solubility (TSSH) and low neutron cross-section cross-checks.

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_zirconium_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/zirconium_engine.py`:
- Implement Zr allotropic transus, hydride precipitation TSSH, and oxidation in pressurized water.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_zirconium_engine.py`
Expected: PASS

#### Task 10: Implement `SolderEngine` (Sn-Pb, SAC305)
**Files:**
- Create: `pycalphad_app/core/solder_engine.py`
- Test: `pycalphad_app/tests/test_solder_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_solder_engine.py`:
- Test SAC305 eutectic melting ($217\,^\circ\text{C}$) and $\text{Sn-37Pb}$ ($183\,^\circ\text{C}$).
- Test Anand viscoplastic flow parameters and intermetallic growth ($\text{Cu}_6\text{Sn}_5, \text{Ag}_3\text{Sn}$).

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_solder_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/solder_engine.py`:
- Implement solder eutectic thermodynamics, Anand viscoplastic creep resistance, and IMC growth diffusion.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_solder_engine.py`
Expected: PASS

#### Task 11: Implement `HEAEngine` (High-Entropy Alloys)
**Files:**
- Create: `pycalphad_app/core/hea_engine.py`
- Test: `pycalphad_app/tests/test_hea_engine.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_hea_engine.py`:
- Test Cantor alloy ($\text{CoCrFeMnNi}$) wrapping `AdaptiveContinuationSolver`.
- Verify Liquidus ($1425\,^\circ\text{C}$), Solidus ($1394\,^\circ\text{C}$), and $\sigma$-precipitation ($922\,^\circ\text{C}$).

**Step 2: Run test to verify it fails**
Run: `python -m pytest pycalphad_app/tests/test_hea_engine.py`
Expected: FAIL

**Step 3: Write minimal implementation**
Create `pycalphad_app/core/hea_engine.py`:
- Subclass `BaseAlloyEngine`, delegating thermodynamics and continuation to `AdaptiveContinuationSolver`.

**Step 4: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_hea_engine.py`
Expected: PASS

---

### Phase 4: Factory Dispatch, Stepper & Worker Integration

#### Task 12: Refactor `MaterialDatabaseSelector` into Dynamic Polymorphic Factory
**Files:**
- Modify: `pycalphad_app/database/material_selector.py`
- Test: `pycalphad_app/tests/test_material_selector.py`

**Step 1: Write tests for factory dispatch**
- Test that every one of the 14 database strings instantiates the correct `BaseAlloyEngine` subclass.
- Test fallback for uncatalogued HEAs.

**Step 2: Update `material_selector.py`**
- Register all 10 family engines + `CoatingEngine`.
- Implement `get_engine(database_name, composition, grain_size, process_type)`.

**Step 3: Run test to verify it passes**
Run: `python -m pytest pycalphad_app/tests/test_material_selector.py`
Expected: PASS

#### Task 13: Wire `SolverWorker` and `IterativeSolver` to Polymorphic Engines
**Files:**
- Modify: `pycalphad_app/gui/worker.py`
- Modify: `pycalphad_app/core/iterative_solver.py`
- Test: `pycalphad_app/tests/test_gui_integration.py`
- Test: `pycalphad_app/tests/test_iterative_solver.py`

**Step 1: Update `worker.py`**
- Replace the hardcoded `is_coating` conditional and generic fallback with polymorphic `MaterialDatabaseSelector.get_engine(...)`.
- Forward `thermo_res`, `transform_res`, `mech_res`, `transport_res`, `ox_res`, `corr_res` to `results`.

**Step 2: Update `iterative_solver.py`**
- Delegate single-temperature steps to `engine.compute_single_temperature_step(T)`.

**Step 3: Run tests to verify**
Run: `python -m pytest pycalphad_app/tests/test_gui_integration.py pycalphad_app/tests/test_iterative_solver.py`
Expected: PASS

#### Task 14: Dynamic Phase Legend Enhancements in GUI Plot Views
**Files:**
- Modify: `pycalphad_app/gui/plot_views/equilibrium_view.py`
- Modify: `pycalphad_app/gui/plot_views/phase_diagram_view.py`
- Test: `pycalphad_app/tests/test_phase_diagram_view.py`
- Test: `pycalphad_app/tests/test_ui_improvements_and_dialogs.py`

**Step 1: Update `equilibrium_view.py`**
- Dynamically iterate over whatever phases are present in `thermo["PhaseFractions"]` instead of hardcoding `FCC`, `BCC`, `B2`, `Sigma`, `Liquid`.
- Assign ColorBrewer qualitative palette colors dynamically.

**Step 2: Run tests to verify**
Run: `python -m pytest pycalphad_app/tests/test_phase_diagram_view.py pycalphad_app/tests/test_ui_improvements_and_dialogs.py`
Expected: PASS

---

### Phase 5: Verification, Packaging & Standalone Sync

#### Task 15: Comprehensive Test Suite & Parity Verification
**Files:**
- Create: `pycalphad_app/tests/test_all_alloy_engines.py`
- Test: All 14 databases simulated end-to-end.

**Step 1: Write integration tests covering all 14 databases**
Verify non-null outputs, physical liquidus > solidus, and positive yield strength for each family preset.

**Step 2: Run full test suite**
Run: `python -m pytest pycalphad_app/tests`
Expected: PASS (83+ tests passing, 0 failures)

#### Task 16: Standalone Executable Recompilation
**Files:**
- Modify: `PyCALPHAD_Suite.spec` (ensure all new engine modules are in hiddenimports/datas)
- Output: `dist/PyCALPHAD_Suite/PyCALPHAD_Suite.exe`

**Step 1: Recompile via PyInstaller**
Run: `pyinstaller PyCALPHAD_Suite.spec --noconfirm`
Expected: Success with `Building COLLECT completed successfully`

**Step 2: Verify Standalone Execution & Shortcut Target**
Launch `dist/PyCALPHAD_Suite/PyCALPHAD_Suite.exe` and verify process mounts with Florence flask loading jug and executes.
