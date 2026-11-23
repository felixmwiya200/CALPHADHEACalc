# JMatPro Stepping Engine & Experimental Verification Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement JMatPro's temperature-stepping console workflow with global `'s'` keyboard interruption alongside multi-point experimental benchmark verification with $\pm 5\%\text{ to }\pm 7.5\%$ shaded uncertainty envelopes across all PyCALPHAD views.

**Architecture:** 
1. Build reusable `plot_experimental_series` in `plot_theme.py` generating discrete markers, connecting lines, and shaded `pg.FillBetweenItem` uncertainty envelopes.
2. Structure multi-point benchmark trajectories in `BenchmarkDatabase.get_plot_benchmarks()`.
3. Equip `SolverWorker` with a warm-start downward temperature-stepping loop emitting JMatPro console syntax (`T(K) = ...`) and listening for atomic interruptions.
4. Install an application-level `'s'` keypress event filter in `MainWindow`.
5. Update `MechanicalView`, `TransportView`, `EnvironmentalView`, `PhaseDiagramView`, and `EquilibriumView` to render Option 2 experimental overlays.

**Tech Stack:** Python 3.10+, PyQt6, pyqtgraph, NumPy, PyInstaller.

---

### Task 1: Reusable Experimental Series with Uncertainty Envelopes (`plot_theme.py`)

**Files:**
- Modify: `pycalphad_app/gui/plot_theme.py`
- Test: `pycalphad_app/tests/test_plot_theme_experimental_series.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_plot_theme_experimental_series.py`:
```python
import numpy as np
import pytest
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg
from pycalphad_app.gui.plot_theme import plot_experimental_series

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_plot_experimental_series(qapp):
    plot_widget = pg.PlotWidget()
    x = [100.0, 300.0, 500.0, 700.0]
    y = [10.0, 20.0, 30.0, 40.0]
    
    item = plot_experimental_series(
        plot_widget, x, y, name="Exp. Benchmark Test",
        color="#D97706", symbol="o", uncertainty_pct=0.075, show_envelope=True
    )
    assert item is not None
    # Check that fill item exists in plot
    fill_items = [it for it in plot_widget.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(fill_items) >= 1
```

**Step 2: Run test to verify it fails**
Run: `pytest pycalphad_app/tests/test_plot_theme_experimental_series.py -v`
Expected: FAIL (`ImportError: cannot import name 'plot_experimental_series'`)

**Step 3: Implement `plot_experimental_series` in `plot_theme.py`**
Add the function to `pycalphad_app/gui/plot_theme.py`:
```python
def plot_experimental_series(
    plot_widget: pg.PlotWidget,
    x: Sequence[float],
    y: Sequence[float],
    name: str,
    color: str = "#D97706",
    symbol: str = "o",
    symbol_size: int = 8,
    uncertainty_pct: float = 0.075,
    show_envelope: bool = True,
    line_style: Qt.PenStyle = Qt.PenStyle.SolidLine
) -> pg.PlotDataItem:
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    q_color = QColor(color)

    if show_envelope and len(x_arr) >= 2 and uncertainty_pct > 0:
        y_upper = y_arr * (1.0 + uncertainty_pct)
        y_lower = y_arr * (1.0 - uncertainty_pct)
        c_up = pg.PlotCurveItem(x_arr, y_upper, pen=None)
        c_low = pg.PlotCurveItem(x_arr, y_lower, pen=None)
        plot_widget.addItem(c_up)
        plot_widget.addItem(c_low)
        fill_brush = QColor(q_color.red(), q_color.green(), q_color.blue(), 35)
        fill_item = pg.FillBetweenItem(c_low, c_up, brush=pg.mkBrush(fill_brush))
        plot_widget.addItem(fill_item)

    pen = pg.mkPen(color=q_color, width=1.6, style=line_style)
    brush = pg.mkBrush(q_color)
    sym_pen = pg.mkPen(color="#0F172A", width=0.8)
    return plot_widget.plot(
        x_arr, y_arr,
        pen=pen,
        symbol=symbol,
        symbolSize=symbol_size,
        symbolBrush=brush,
        symbolPen=sym_pen,
        name=name
    )
```

**Step 4: Run test to verify it passes**
Run: `pytest pycalphad_app/tests/test_plot_theme_experimental_series.py -v`
Expected: PASS

---

### Task 2: Multi-Point Literature Datasets in `BenchmarkDatabase`

**Files:**
- Modify: `pycalphad_app/database/benchmark_database.py`
- Test: `pycalphad_app/tests/test_benchmark_multi_point_series.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_benchmark_multi_point_series.py`:
```python
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

def test_inconel_718_plot_benchmarks():
    comp = {"Ni": 0.53, "Cr": 0.19, "Fe": 0.18, "Nb": 0.05, "Mo": 0.03, "Ti": 0.01, "Al": 0.005}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "Nickel & Ni-Fe Superalloys")
    assert "tensile_temp" in pb
    assert len(pb["tensile_temp"]["T_K"]) >= 4
```

**Step 2: Run test to verify it fails**
Run: `pytest pycalphad_app/tests/test_benchmark_multi_point_series.py -v`
Expected: FAIL (`AttributeError: type object 'BenchmarkDatabase' has no attribute 'get_plot_benchmarks'`)

**Step 3: Implement `get_plot_benchmarks` in `BenchmarkDatabase`**
Enrich `BenchmarkDatabase.BENCHMARK_PROFILES` with `stress_strain`, `thermal_transport`, `oxidation_kinetics`, and add `@classmethod def get_plot_benchmarks(...)`.

**Step 4: Run test to verify it passes**
Run: `pytest pycalphad_app/tests/test_benchmark_multi_point_series.py -v`
Expected: PASS

---

### Task 3: JMatPro Stepping Engine in `SolverWorker` (`worker.py`)

**Files:**
- Modify: `pycalphad_app/gui/worker.py`
- Test: `pycalphad_app/tests/test_worker_jmatpro_stepping.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_worker_jmatpro_stepping.py`:
```python
from pycalphad_app.gui.worker import SolverWorker

def test_worker_interrupt_flag():
    w = SolverWorker("High Entropy Alloys", {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20})
    assert not w._is_interrupted
    w.request_interrupt()
    assert w._is_interrupted
```

**Step 2: Run test to verify it fails/passes initial state**
Run: `pytest pycalphad_app/tests/test_worker_jmatpro_stepping.py -v`

**Step 3: Implement JMatPro Stepping in `SolverWorker`**
1. Add `step_updated = pyqtSignal(dict)` and `step_logged = pyqtSignal(str)`.
2. Add `request_interrupt()` and `self._is_interrupted = False`.
3. In `run()`:
   - Output `Calculating...to interrupt press the 's' key`.
   - Perform downward temperature sweep ($T_{\text{start}}$ to $T_{\text{stop}}$), logging `T(K) = XXXX.XX`.
   - Check `self._is_interrupted`.
   - Package `results["benchmarks"] = BenchmarkDatabase.get_plot_benchmarks(...)`.

**Step 4: Run test to verify it passes**
Run: `pytest pycalphad_app/tests/test_worker_jmatpro_stepping.py -v`
Expected: PASS

---

### Task 4: Global 's' Interrupter Event Filter in `MainWindow` (`main_window.py`)

**Files:**
- Modify: `pycalphad_app/gui/main_window.py`
- Test: `pycalphad_app/tests/test_main_window_interrupt_key.py`

**Step 1: Write test for 's' key interception**
Verify `MainWindow.keyPressEvent` catches `Qt.Key.Key_S` when `worker.isRunning()` and invokes `worker.request_interrupt()`.

**Step 2: Implement in `main_window.py`**

**Step 3: Run test to verify it passes**

---

### Task 5: Mechanical View Overhaul (`mechanical_view.py`)

**Files:**
- Modify: `pycalphad_app/gui/plot_views/mechanical_view.py`
- Test: `pycalphad_app/tests/test_mechanical_view_overlays.py`

**Step 1: Write the failing test**
Create `pycalphad_app/tests/test_mechanical_view_overlays.py`:
```python
def test_mechanical_view_renders_experimental_series(qapp):
    from pycalphad_app.gui.plot_views.mechanical_view import MechanicalView
    from pycalphad_app.database.benchmark_database import BenchmarkDatabase

    view = MechanicalView()
    comp = {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "High Entropy Alloys")
    results = {
        "composition": comp,
        "mechanical": {
            "YieldStrength_RT_MPa": 205.0,
            "UTS_RT_MPa": 460.0,
            "DominantStructure": "FCC (Cantor)",
        },
        "benchmarks": pb,
        "is_coating": False
    }
    view.update_data(results)
    # Both plot_sy and plot_ss must contain experimental items
    assert len(view.plot_sy.plotItem.items) > 2
    assert len(view.plot_ss.plotItem.items) > 1
```

**Step 2: Implement updates in `mechanical_view.py`**
- Fix temperature dependence to respect room temperature strength without cryogenic offset artifact.
- Use `plot_experimental_series` for full Otto 2013 7-point series in `plot_sy`.
- Use `plot_experimental_series` for Gludovatz 2014 true stress–strain flow points in `plot_ss`.

**Step 3: Run test to verify it passes**
Run: `pytest pycalphad_app/tests/test_mechanical_view_overlays.py -v`
Expected: PASS

---

### Task 6: Transport & Environmental View Updates

**Files:**
- Modify: `pycalphad_app/gui/plot_views/transport_view.py`
- Modify: `pycalphad_app/gui/plot_views/environmental_view.py`
- Test: `pycalphad_app/tests/test_transport_environmental_overlays.py`

**Step 1: Implement `plot_experimental_series` in `transport_view.py` and `environmental_view.py`**
- $k(T)$ and $C_p(T)$ with Ke Jin (2016) / Touloukian TPRC points and $\pm 5\%$ uncertainty envelope.
- Wagner oxidation mass-gain curve with TGA points (Butler 2018) and $\pm 7.5\%$ envelope.

**Step 2: Run test to verify it passes**
Run: `pytest pycalphad_app/tests/test_transport_environmental_overlays.py -v`
Expected: PASS

---

### Task 7: Full Test Suite Regression & Standalone Packaging

**Files:**
- Test: Entire test suite (`pytest pycalphad_app/tests`)
- Build: `pyinstaller PyCALPHAD_Suite.spec --noconfirm`

**Step 1: Execute test suite**
Run: `pytest pycalphad_app/tests -v`
Expected: 125+ passed, 0 failures.

**Step 2: Recompile executable**
Run: `pyinstaller PyCALPHAD_Suite.spec --noconfirm`
Confirm `dist/PyCALPHAD_Suite/PyCALPHAD_Suite.exe` builds cleanly.
Confirm desktop shortcut launches the application.
