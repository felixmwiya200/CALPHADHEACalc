# Native C/C++ CAE Platform with Embedded ImGui & ImPlot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Port all C# WPF platform features into the native C/C++ frontend, embedding a DirectX 11 Dear ImGui & ImPlot graphics engine for interactive scientific plotting, modal simulation solvers, database browsing, composition profiling, and CAE exports.

**Architecture:** Native Win32 application host retaining the left parameter dock and complete `HMENU` top bar, with a central DirectX 11 swapchain hosting an immediate-mode ImGui/ImPlot viewport. Secondary dialogs (`ScientificSimulationDialog`, `DatabaseSelector`, `CompositionLibrary`) operate as native Win32 modal dialogs backed by secondary swapchains sharing the central `ID3D11Device`.

**Tech Stack:** C++20, MSVC x64, Win32 API, DirectX 11 (`d3d11.lib`, `dxgi.lib`, `d3dcompiler.lib`), Dear ImGui, ImPlot, `nlohmann::json`, Python CAE daemon IPC.

---

### Task 1: Vendor Dear ImGui & ImPlot Libraries into C++ Project

**Files:**
- Create: `cpp/third_party/imgui/imgui.h`
- Create: `cpp/third_party/imgui/imgui.cpp`
- Create: `cpp/third_party/imgui/imgui_draw.cpp`
- Create: `cpp/third_party/imgui/imgui_tables.cpp`
- Create: `cpp/third_party/imgui/imgui_widgets.cpp`
- Create: `cpp/third_party/imgui/backends/imgui_impl_win32.h`
- Create: `cpp/third_party/imgui/backends/imgui_impl_win32.cpp`
- Create: `cpp/third_party/imgui/backends/imgui_impl_dx11.h`
- Create: `cpp/third_party/imgui/backends/imgui_impl_dx11.cpp`
- Create: `cpp/third_party/implot/implot.h`
- Create: `cpp/third_party/implot/implot_internal.h`
- Create: `cpp/third_party/implot/implot.cpp`
- Create: `cpp/third_party/implot/implot_items.cpp`
- Modify: `cpp/build.bat`

**Step 1: Write header check script to verify absence of vendor files**
Run: `powershell -Command "Test-Path 'cpp/third_party/imgui/imgui.h'"`
Expected: `False`

**Step 2: Verify failure before vendoring**
Ensure `cpp/third_party/imgui` and `cpp/third_party/implot` do not exist.

**Step 3: Download/Stage official single-header ImGui & ImPlot distribution**
Stage the verified Dear ImGui (v1.91.x) and ImPlot (v0.16) headers and implementations under `cpp/third_party/imgui` and `cpp/third_party/implot`.

**Step 4: Update `cpp/build.bat` to include include paths and DirectX 11 libraries**
Add `/I"%~dp0third_party\imgui" /I"%~dp0third_party\imgui\backends" /I"%~dp0third_party\implot"` and link `d3d11.lib dxgi.lib d3dcompiler.lib`.
Run: `cmd /c cpp\build.bat`
Expected: PASS (MSVC compiles all ImGui and ImPlot translation units with 0 errors).

**Step 5: Commit**
```bash
git add cpp/third_party/ cpp/build.bat
git commit -m "feat(graphics): vendor Dear ImGui and ImPlot C++ libraries with DirectX 11 support"
```

---

### Task 2: Implement DirectX 11 Device & Multi-SwapChain Renderer

**Files:**
- Create: `cpp/include/DirectX11Renderer.hpp`
- Create: `cpp/src/DirectX11Renderer.cpp`
- Modify: `cpp/include/MainWindow.hpp`
- Modify: `cpp/src/MainWindow.cpp`

**Step 1: Write the interface definition for `DirectX11Renderer`**
Define `DirectX11Renderer` with methods:
- `bool initialize(HWND hPrimaryCanvas);`
- `void shutdown();`
- `void resize_primary(int width, int height);`
- `IDXGISwapChain* create_secondary_swapchain(HWND hWnd, int width, int height);`
- `void begin_frame(HWND hWnd);`
- `void end_frame(HWND hWnd);`
- `bool handle_win32_message(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);`

**Step 2: Verify build failure prior to implementation**
Run: `cmd /c cpp\build.bat`
Expected: FAIL (`DirectX11Renderer.hpp` not found).

**Step 3: Implement `DirectX11Renderer.cpp`**
- Initialize `D3D11CreateDeviceAndSwapChain` with hardware feature level 11_0, falling back to WARP if hardware is unavailable.
- Initialize `ImGui::CreateContext()` and `ImPlot::CreateContext()`.
- Configure Dark Scientific Theme (Slate-900 background, cyan/blue accent colours).
- Configure font atlas with ClearType filtering.
- Implement `ImGui_ImplWin32_Init` and `ImGui_ImplDX11_Init`.

**Step 4: Verify clean compile and DirectX 11 initialization**
Run: `cmd /c cpp\build.bat`
Expected: PASS (`PyCALPHAD_Suite.exe` links cleanly with `d3d11.lib` and `dxgi.lib`).

**Step 5: Commit**
```bash
git add cpp/include/DirectX11Renderer.hpp cpp/src/DirectX11Renderer.cpp cpp/include/MainWindow.hpp cpp/src/MainWindow.cpp
git commit -m "feat(renderer): implement DirectX 11 device and multi-swapchain manager for Dear ImGui"
```

---

### Task 3: Build the ImPlot Scientific Viewport for the 9 Analysis Tabs

**Files:**
- Create: `cpp/include/ImPlotViewport.hpp`
- Create: `cpp/src/ImPlotViewport.cpp`
- Modify: `cpp/src/MainWindow.cpp`

**Step 1: Define `ImPlotViewport` rendering interface**
Methods:
- `void set_result(const EquilibriumResult& res);`
- `void render_viewport(int width, int height, Crystal3DViewer& viewer);`
- Sub-methods for all 9 tabs:
  - `render_phase_equilibrium_tab();`
  - `render_phase_diagram_scheil_tab();`
  - `render_mechanical_properties_tab();`
  - `render_transport_rheology_tab();`
  - `render_environmental_oxidation_tab();`
  - `render_xrd_diffractogram_tab();`
  - `render_crystal_viewer_tab(Crystal3DViewer& viewer);`
  - `render_suitability_radar_tab();`
  - `render_calculation_matrix_tab();`

**Step 2: Verify failure before implementation**
Run: `cmd /c cpp\build.bat`
Expected: FAIL (`ImPlotViewport` missing).

**Step 3: Implement `ImPlotViewport.cpp` using ImPlot widgets**
- Tab 0 (Phase Equilibrium): `ImPlot::BeginPlot("Phase Fraction vs Temperature")` with temperature X-axis and fraction Y-axis [0, 1]. Render phase fraction curves with `ImPlot::PlotLine`. Add vertical solidus/liquidus boundary lines. Display cursor crosshairs and coordinate readouts.
- Tab 1 (Scheil): Plot Lever-rule vs Scheil solidification curves ($f_s$ vs $T$).
- Tab 2 (Mechanical): Dual-axis plot for Yield Strength / UTS (MPa) vs Temperature, and constitutive Hollomon/Voce flow stress.
- Tab 3 (Transport): Viscosity, thermal conductivity, and density curves.
- Tab 4 (Environmental): Mass gain parabolic curves ($k_p$) and Ellingham $\Delta G^\circ$ lines.
- Tab 5 (XRD): Continuous diffractogram trace ($2\theta$ vs Intensity %) with $hkl$ stick markers and benchmark overlays.
- Tab 7 (Suitability Radar): 6-axis spider plot using polar coordinate transformations.
- Tab 8 (Calculation Matrix): `ImGui::BeginTable` with sortable columns and search filter.

**Step 4: Verify build and test with simulated dataset**
Run: `cmd /c cpp\build.bat`
Expected: PASS (`PyCALPHAD_Suite.exe` compiles with complete ImPlot viewport).

**Step 5: Commit**
```bash
git add cpp/include/ImPlotViewport.hpp cpp/src/ImPlotViewport.cpp
git commit -m "feat(viewport): implement high-resolution interactive ImPlot scientific tabs"
```

---

### Task 4: Port 3D Crystal Viewer to GPU-Accelerated `ImDrawList` Projection

**Files:**
- Modify: `cpp/include/Crystal3DViewer.hpp`
- Modify: `cpp/src/Crystal3DViewer.cpp`
- Modify: `cpp/src/ImPlotViewport.cpp`

**Step 1: Write test for `Crystal3DViewer::render_imgui` interface**
Add method signature:
`void render_imgui(ImDrawList* drawList, ImVec2 canvasPos, ImVec2 canvasSize);`

**Step 2: Verify compile error before adding implementation**
Run: `cmd /c cpp\build.bat`
Expected: FAIL (`render_imgui` member not found).

**Step 3: Implement `render_imgui` in `Crystal3DViewer.cpp`**
- Compute 3D rotation matrix from mouse orbit angles ($R_x, R_y, R_z$).
- Project 3D coordinates $(x, y, z)$ to 2D screen space using orthographic/perspective camera scaling.
- Depth-sort all atom spheres and bond cylinders back-to-front ($z$-order).
- Render bond lines using `drawList->AddLine()` with depth-attenuated antialiased widths.
- Render atom spheres using `drawList->AddCircleFilled()` with radial lighting gradient.
- Render element symbol labels when `m_show_labels` is true via `drawList->AddText()`.
- Add ImGui controls directly above the canvas: Checkbox for Element Labels, Combobox for Phase Selection (including Frank-Kasper Tetragonal $\sigma$-Phase), Buttons for Rotate 180°, Auto-spin, Reset View, and Export PNG.

**Step 4: Build and verify 3D rendering**
Run: `cmd /c cpp\build.bat`
Expected: PASS (0 errors, 3D lattice renders at 60 fps inside ImGui canvas).

**Step 5: Commit**
```bash
git add cpp/include/Crystal3DViewer.hpp cpp/src/Crystal3DViewer.cpp
git commit -m "feat(3d): port crystal structure viewer to GPU-accelerated ImDrawList vector rasterizer"
```

---

### Task 5: Implement Win32 Top Menu Hierarchy (`HMENU`) with Full C# Feature Parity

**Files:**
- Modify: `cpp/resources/app.rc`
- Modify: `cpp/include/MainWindow.hpp`
- Modify: `cpp/src/MainWindow.cpp`

**Step 1: Define Menu ID constants in `MainWindow.hpp`**
Add:
- `IDM_FILE_HOME`, `IDM_FILE_SELECT_DB`, `IDM_FILE_SAVE_COMP`, `IDM_FILE_OPEN_COMP`, `IDM_FILE_MANAGE_LIB`
- `IDM_FILE_EXPORT_ALL`, `IDM_FILE_EXPORT_DAT`, `IDM_FILE_EXPORT_CSV`, `IDM_FILE_EXPORT_PNG`, `IDM_FILE_EXPORT_SVG`
- `IDM_FILE_QUICK_DEFORM`, `IDM_FILE_QUICK_SIMUFACT`, `IDM_FILE_COMSOL_PIECEWISE`, `IDM_FILE_EXIT`
- `IDM_VIEW_RESET_LAYOUT`, `IDM_VIEW_TOGGLE_DOCK`, `IDM_VIEW_TOGGLE_CONSOLE`, `IDM_VIEW_MAXIMIZE`
- `IDM_TYPES_DB_START` through `IDM_TYPES_DB_END` (14 alloy system quick selectors)
- `IDM_SIM_SINGLE_STEP`, `IDM_SIM_CONCENTRATION_STEP`, `IDM_SIM_CREEP`, `IDM_SIM_FATIGUE`, `IDM_SIM_TTT_CCT`
- `IDM_SIM_LATTICE_MISMATCH`, `IDM_SIM_SFE`, `IDM_SIM_COARSENING`, `IDM_SIM_JOMINY`
- `IDM_UTIL_AUSTENITE_GRAIN`, `IDM_UTIL_PERIODIC_TABLE`, `IDM_UTIL_CRYSTAL_3D`, `IDM_UTIL_CONVERSIONS`, `IDM_UTIL_MARTENSITE`
- `IDM_HELP_ABOUT`, `IDM_HELP_QUICKSTART`, `IDM_HELP_AUTHORSHIP`, `IDM_HELP_REFERENCES`

**Step 2: Verify compile without menu binding**
Run: `cmd /c cpp\build.bat`
Expected: PASS.

**Step 3: Construct the native Win32 Menu Bar (`CreateMenu`, `AppendMenuW`)**
In `MainWindow::init_controls()`, construct the complete hierarchical menu tree matching `csharp/PyCalphadSuite.Desktop/MainWindow.xaml` and attach it via `SetMenu(m_hwnd, hMenuBar)`.
In `MainWindow::WndProc(WM_COMMAND)`, route each menu ID to its handler.

**Step 4: Verify menu layout and command dispatch**
Run: `cmd /c cpp\build.bat`
Expected: PASS (Application launches with complete top menu bar).

**Step 5: Commit**
```bash
git add cpp/include/MainWindow.hpp cpp/src/MainWindow.cpp
git commit -m "feat(ui): implement complete Win32 top menu hierarchy matching C# desktop platform"
```

---

### Task 6: Implement Secondary Scientific Simulation Dialog Hosting the 12 Solvers

**Files:**
- Create: `cpp/include/SimulationDialog.hpp`
- Create: `cpp/src/SimulationDialog.cpp`
- Modify: `cpp/src/MainWindow.cpp`

**Step 1: Write interface for `SimulationDialog`**
Define `SimulationDialog::show(HWND hParent, CaeClient& client, const std::string& module, const std::string& title, const std::string& dbName, const std::map<std::string, double>& comp);`

**Step 2: Verify build failure before implementation**
Run: `cmd /c cpp\build.bat`
Expected: FAIL (`SimulationDialog.hpp` not found).

**Step 3: Implement `SimulationDialog.cpp`**
- Create top-level Win32 modal dialog window (`WS_POPUPWINDOW | WS_CAPTION | WS_SYSMENU | WS_THICKFRAME`).
- Embed child canvas HWND with secondary DirectX 11 swapchain.
- Handle modules:
  - `concentration_step`: Sweep element concentration (0–30%) and plot solidus/liquidus boundary shift.
  - `creep`: Larson-Miller parameter & Norton power-law creep rate vs stress ($T = 800\text{--}1200\text{ K}$).
  - `fatigue`: Basquin-Manson-Coffin S-N stress-life fatigue curve.
  - `ttt_cct`: Time-Temperature-Transformation and Continuous-Cooling-Transformation C-curves.
  - `lattice_mismatch`: Gamma/Gamma-prime ($\gamma/\gamma'$) lattice misfit vs temperature.
  - `sfe`: Stacking Fault Energy ($mJ/m^2$) vs temperature.
  - `coarsening`: Lifshitz-Slyozov-Wagner (LSW) precipitate coarsening kinetics ($r^3 - r_0^3 = K \cdot t$).
  - `jominy`: General Steel Jominy end-quench hardenability curve (Hardness HRC vs distance mm).
  - `conversions`: Interactive metallurgical unit converter (°C $\leftrightarrow$ K, MPa $\leftrightarrow$ ksi, J $\leftrightarrow$ cal).
  - `martensite`: Martensite start ($M_s$), finish ($M_f$), and hardness estimation.
- Render interactive ImPlot curves inside the dialog with real-time parameter editing and execution.

**Step 4: Verify compilation and dialog interaction**
Run: `cmd /c cpp\build.bat`
Expected: PASS (Dialog opens, queries CAE daemon, and plots curves with ImPlot).

**Step 5: Commit**
```bash
git add cpp/include/SimulationDialog.hpp cpp/src/SimulationDialog.cpp cpp/src/MainWindow.cpp
git commit -m "feat(sim): implement modal scientific simulation dialog hosting 12 specialized solvers"
```

---

### Task 7: Implement Material Database Selector & Composition Library Dialogs

**Files:**
- Create: `cpp/include/DatabaseSelectorDlg.hpp`
- Create: `cpp/src/DatabaseSelectorDlg.cpp`
- Create: `cpp/include/CompositionLibraryDlg.hpp`
- Create: `cpp/src/CompositionLibraryDlg.cpp`
- Modify: `cpp/src/MainWindow.cpp`

**Step 1: Write header interfaces for both dialogs**
- `DatabaseSelectorDlg::show(HWND hParent, const std::map<std::string, DatabaseSpec>& dbs, std::function<void(const std::string&)> onSelect);`
- `CompositionLibraryDlg::show(HWND hParent, std::function<void(const SavedCompositionProfile&)> onLoad);`

**Step 2: Verify failure before implementation**
Run: `cmd /c cpp\build.bat`
Expected: FAIL (Headers missing).

**Step 3: Implement dialogs**
- `DatabaseSelectorDlg.cpp`: Native Win32 dialog displaying the 14 material databases with badges, base element, allowable elements, descriptions, and presets.
- `CompositionLibraryDlg.cpp`: Persistent manager reading/writing `saved_compositions.json` with alloy name, author notes, tags, and atomic/weight percentages.

**Step 4: Build and test database selection and composition saving**
Run: `cmd /c cpp\build.bat`
Expected: PASS (Can browse databases and save/load custom compositions).

**Step 5: Commit**
```bash
git add cpp/include/DatabaseSelectorDlg.hpp cpp/src/DatabaseSelectorDlg.cpp cpp/include/CompositionLibraryDlg.hpp cpp/src/CompositionLibraryDlg.cpp
git commit -m "feat(library): implement visual database selector and persistent alloy composition manager"
```

---

### Task 8: Implement Multi-Format CAE & FEA Export Formatters

**Files:**
- Create: `cpp/include/CaeExportEngine.hpp`
- Create: `cpp/src/CaeExportEngine.cpp`
- Modify: `cpp/src/MainWindow.cpp`

**Step 1: Write interface for `CaeExportEngine`**
Static methods:
- `static std::string export_abaqus(const EquilibriumResult& res);`
- `static std::string export_ansys(const EquilibriumResult& res);`
- `static std::string export_comsol_piecewise(const EquilibriumResult& res);`
- `static std::string export_deform(const EquilibriumResult& res);`
- `static bool export_full_bundle(const std::wstring& outDir, const EquilibriumResult& res);`

**Step 2: Verify failure before implementation**
Run: `cmd /c cpp\build.bat`
Expected: FAIL (`CaeExportEngine.hpp` not found).

**Step 3: Implement export formatters**
- ABAQUS: Generate `*MATERIAL, NAME=...`, `*ELASTIC`, `*EXPANSION`, `*CONDUCTIVITY`, `*DENSITY`, `*PLASTIC`.
- ANSYS: Generate `MPDATA, EX, 1, 1, ...`, `MPDATA, ALPX, 1, 1, ...`, `MPDATA, KXX, 1, 1, ...`.
- COMSOL: Generate piecewise continuous functions for all 21 thermophysical properties.
- DEFORM-HT: Generate flow stress tables ($T, \dot{\epsilon}, \epsilon$).
- Full Bundle: Save `.zip` / folder containing CSV tables, CALPHAD `.dat`, and JSON dossier.

**Step 4: Verify export formatting via unit verification**
Run: `cmd /c cpp\build.bat`
Expected: PASS (Verified card generation matching C# exporter output).

**Step 5: Commit**
```bash
git add cpp/include/CaeExportEngine.hpp cpp/src/CaeExportEngine.cpp
git commit -m "feat(export): implement ABAQUS, ANSYS, COMSOL, and DEFORM multi-format CAE card generators"
```

---

### Task 9: Comprehensive End-to-End Build, Verification, and Desktop Launcher Update

**Files:**
- Modify: `cpp/build.bat`
- Modify: `Launch_Native_Cpp_Suite.bat`
- Modify: `C:\Users\Dell\Desktop\PyCALPHAD_Suite.bat`
- Modify: `scripts/create_shortcuts.ps1`

**Step 1: Execute full clean build of native C/C++ suite**
Run: `cmd /c cpp\build.bat`
Expected: PASS (0 errors, 0 warnings, binary generated at `cpp/bin/PyCALPHAD_Suite.exe`).

**Step 2: Execute full regression test suite**
Run: `python -m pytest pycalphad_app/tests/test_cae_daemon.py pycalphad_app/tests/test_all_alloy_engines.py pycalphad_app/tests/test_matlab_engine_parity.py`
Expected: PASS (37/37 tests pass).

**Step 3: Verify C# unit tests continue to pass with 100% green**
Run: `& "C:\Users\Dell\.dotnet\dotnet.exe" test csharp/PyCalphadSuite.Tests/PyCalphadSuite.Tests.csproj`
Expected: PASS (13/13 tests pass).

**Step 4: Update Desktop shortcuts and launch scripts**
Run: `powershell -ExecutionPolicy Bypass -File scripts/create_shortcuts.ps1`
Expected: PASS.

**Step 5: Commit and tag release**
```bash
git add .
git commit -m "chore(release): verify full feature parity between C# and native C++ suites (v2026.3.0)"
```
