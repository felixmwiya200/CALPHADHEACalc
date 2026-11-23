# Scientific Desktop CALPHAD CAE Architecture Implementation Plan

> **For Claude / Antigravity:** REQUIRED SUB-SKILL: Use executing-plans or systematic implementation to execute this plan task-by-task.

**Goal:** Transform the CALPHAD Materials Engineering Suite into a 100% native scientific desktop CAE application featuring mouse-drag resizable splitters, full MATLAB engine and database parity, interactive stepped calculation gating, a silent background splash screen, and clean, simple engineering terminology with zero web-style clutter.

**Architecture:** A native PyQt6 desktop framework utilizing a central `QSplitter` between a simple, non-clipping Left Input Pane and a Central Scientific Viewport Canvas, driven by a stateful `IterativeSolver` thread supporting both `Run to Completion` and `Step Forward` execution. All 30 MATLAB classes from `./App/` are ported to pure, vectorized Python modules.

**Tech Stack:** Python 3.12, PyQt6, pyqtgraph, NumPy, SciPy, PyCALPHAD.

---

### Task 1: Silent Startup Splash Screen (`pycalphad_app/gui/splash_screen.py` & `pycalphad_app/main.py`)

**Files:**
- Create: `pycalphad_app/gui/splash_screen.py`
- Modify: `pycalphad_app/main.py`
- Test: `pycalphad_app/tests/test_splash_screen.py`

**Step 1: Write unit test for splash screen lifecycle**
Verify that `QuickSplashScreen` instantiates borderless, reports progress, and closes cleanly when `MainWindow` signals readiness.

**Step 2: Implement `QuickSplashScreen`**
Create clean, native `QSplashScreen` with application title, version, and a standard `QProgressBar` reporting dependency loading in a lightweight background thread (`LoaderWorker`).

**Step 3: Update `main.py` entry point**
Integrate `QuickSplashScreen` into `main.py` so the splash screen displays instantly, loads packages silently in the background, and seamlessly transitions to `MainWindow`.

**Step 4: Run test to verify passes**
Execute test to confirm zero-stutter startup and graceful exit.

---

### Task 2: Elimination of Panel Clipping & Mouse-Drag Resizable Splitter (`pycalphad_app/gui/database_dock.py` & `main_window.py`)

**Files:**
- Modify: `pycalphad_app/gui/database_dock.py`
- Modify: `pycalphad_app/gui/main_window.py`
- Test: `pycalphad_app/tests/test_panel_resizing.py`

**Step 1: Write test for panel resizing and non-clipping scroll area**
Verify that the left panel has a minimum width of 320 px, enables horizontal scrollbar as needed, and that the splitter responds to resize events.

**Step 2: Overhaul `database_dock.py` to Simple Engineering Controls**
- Strip all verbose text, AI-style descriptions, and card containers.
- Enforce simple labels: `Alloy System`, `Composition (wt% / at%)`, `Temperature (K)`, `Step ΔT (K)`.
- Replace radio buttons with simple toggles.
- Set `QScrollArea` policies: `ScrollBarAsNeeded` in both directions.
- Add simple buttons: `Calculate` (Run to Completion), `Step Forward`, and `Reset`.

**Step 3: Configure primary `QSplitter` in `main_window.py`**
- Replace fixed dock attachment with a primary `QSplitter(Qt.Orientation.Horizontal)`.
- Set splitter handle width to 6 px with hover affordance and `split-h` cursor.
- Set `setChildrenCollapsible(False)` to guarantee no accidental collapse.
- Add Window Navigation Tools menu (`View -> Reset Default Layout`, `View -> Maximize Canvas`).

**Step 4: Run test to verify zero clipping and splitter functionality**

---

### Task 3: Interactive Stepped Solver Engine (`pycalphad_app/core/iterative_solver.py` & `gui/worker.py`)

**Files:**
- Create: `pycalphad_app/core/iterative_solver.py`
- Modify: `pycalphad_app/gui/worker.py`
- Modify: `pycalphad_app/gui/main_window.py`
- Test: `pycalphad_app/tests/test_iterative_solver.py`

**Step 1: Write unit test for stepped execution**
Test `IterativeSolver`:
- Initial state: idle, 0 calculations run.
- `step_forward()`: executes exactly $T_1 = T_{\text{start}}$, returns step state, increments $k$.
- Subsequent `step_forward()`: executes $T_2 = T_1 + \Delta T$.
- `run_to_completion()`: loops through remaining steps up to $T_{\text{stop}}$.
- `reset()`: clears step history.

**Step 2: Implement `IterativeSolver` in pure Python**
Implement stateful solver handling discrete temperature and equilibrium evaluation.

**Step 3: Wire into `MainWindow` and UI buttons**
- Connect `btn_calc` to `run_to_completion()`.
- Connect `btn_step` to `step_forward()`.
- Connect `btn_reset` to `reset()`.
- Ensure canvases and data sheets remain pristine until the user clicks either button.

**Step 4: Run unit tests to verify solver state machine passes**

---

### Task 4: Port Remaining MATLAB Engines and Connect All 14 Databases (`pycalphad_app/core/engines/`)

**Files:**
- Create/Audit: `pycalphad_app/core/engines/`
- Modify: `pycalphad_app/core/thermo_engine.py`
- Modify: `pycalphad_app/core/mechanical_engine.py`
- Modify: `pycalphad_app/core/oxidation_engine.py`
- Modify: `pycalphad_app/core/xrd_engine.py`
- Modify: `pycalphad_app/core/coating_engine.py`
- Modify: `pycalphad_app/core/application_scorer.py`
- Test: `pycalphad_app/tests/test_matlab_engine_parity.py`

**Step 1: Write comprehensive test verifying calculations against MATLAB `./App/` baselines**
Compare yield strength, hardness, oxidation rate $k_p$, XRD $2\theta$ peaks, and phase fractions against verified test cases in `./App/test_*.m`.

**Step 2: Implement full math routines in pure Python**
- Port remaining logic from `CALPHADHEACalc.m`, `HEACalculator.m`, `HEALatticeDistortionEngine.m`, and `HEAOxideDatabase.m`.
- Ensure 100% vectorized NumPy computation for real-time responsiveness.
- Hook all 14 databases into the unified registry.

**Step 3: Run test suite to verify mathematical fidelity**

---

### Task 5: Eliminate Web-style Modal Dialog (`pycalphad_app/gui/database_modal.py`)

**Files:**
- Refactor: `pycalphad_app/gui/database_modal.py`
- Modify: `pycalphad_app/gui/main_window.py`
- Test: `pycalphad_app/tests/test_no_web_modals.py`

**Step 1: Replace web card popup with standard JMatPro native alloy catalog selector**
Convert any secondary alloy selector into a simple, high-density native tree or table dialog without rounded SaaS cards, pill badges, or long text paragraphs.

**Step 2: Verify all menu items and shortcuts trigger native actions**

---

### Task 6: End-to-End System Integration & Verification

**Files:**
- Test: `pycalphad_app/tests/test_full_suite_e2e.py`

**Step 1: Run comprehensive end-to-end integration test**
- Launch application sequence (splash screen $\to$ main window).
- Verify mouse-drag splitter handles.
- Execute `Step Forward` across 5 increments, verify incremental plotting.
- Execute `Calculate` to completion, verify full plot convergence.
- Verify status telemetry and memory cleanliness.
