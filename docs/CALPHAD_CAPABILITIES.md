# CALPHAD XOC: Advanced Capabilities & Computational Metallurgy Architecture

**Application**: CALPHAD XOC (2026 Edition)  
**Binary Executable**: `PyCalphadSuite.Desktop.exe`  
**Desktop Shortcut**: [CALPHAD XOC.lnk](file:///C:/Users/Dell/Desktop/CALPHAD XOC.lnk)  
**Last Capabilities Audit**: 2026-11-22 14:16:14 (IST)  
**Trigger Classification**: `ManualForce`  
**Supervisory Principal**: Felix Mwiya (Department of Mechanical Engineering, SRM University-AP)  

---

## 1. Executive Summary & Application Identity

CALPHAD XOC is a high-performance materials design desktop application engineered for multicomponent alloy discovery, high-entropy alloy (HEA/MPEA) design, and computational thermodynamic simulation. Built with a C# .NET 8 WPF user interface, ScottPlot 5 scientific charting, and a headless high-throughput thermodynamic engine backend, CALPHAD XOC unifies first-principles equilibrium calculations, multi-sublattice Compound Energy Formalism (CEF), kinetic solidification, and multi-physics computer-aided engineering export pipelines.

```
+----------------------------------------------------------------------------------------------------------+
|                                    CALPHAD XOC CORE ARCHITECTURE                                         |
+----------------------------------------------------------------------------------------------------------+
|  Desktop Layer     | C# .NET 8 WPF, ScottPlot 5, Otani-Liu High-Contrast Scientific Palette, 3D Lattice |
|  IPC Protocol      | Non-blocking JSON-RPC over Standard Input/Output Pipes (<10ms IPC Latency)          |
|  Solver Backend    | PyCALPHAD 0.12+ / OpenCalphad 6 GTS Engine with Analytical SymEngine Hessians       |
|  Thermodynamics    | SGTE 45-Element Unaries, PanHEA Redlich-Kister Multicomponent Polynomials, CEF      |
|  Kinetic Engines   | Scheil-Gulliver Solidification with Back-Diffusion, Kampmann-Wagner Precipitation   |
|  CAE Exporters     | Native Decks: COMSOL Multiphysics, Abaqus, ANSYS, TRANSVALOR FORGE, DEFORM-3D      |
+----------------------------------------------------------------------------------------------------------+
```

---

## 2. State-of-the-Art Capability Benchmark

| Capability Area | Industry Baseline (Thermo-Calc / Pandat / FactSage) | Open-Source Engines (PyCALPHAD 0.12 / OpenCalphad 6) | CALPHAD XOC Native Desktop Application Implementation | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Global Equilibrium Minimization** | GES / POLY-3 (Thermo-Calc), PanEngine (Pandat), ChemApp (FactSage) | Global convex-hull projection with xarray hyperplanes; Newton-Raphson Active Set | Dual-engine: Adaptive continuation solver with bounded Newton-Raphson and PyCALPHAD `equilibrium()` | **Active** |
| **Sublattice Formalism (CEF)** | Full $(A,B)_p(C,D)_q(VA)_r$ multi-sublattice with vacancy site balancing | Compound Energy Formalism with SymPy analytical gradients | Strict Cacciamani (2016) CEF with vacancy balance and Inden-Hillert-Jarl magnetic terms | **Active** |
| **Order-Disorder Transformations** | Partitioned Bragg-Williams / BWG models preventing artificial gaps | Continuous Gibbs energy model without phase discontinuities | Unified order-disorder transformations ($B2/A2$, $L1_2/A1$) across FCC/BCC matrices | **Active** |
| **Multicomponent Extrapolations** | Muggianu, Kohler, Colinet, and Toop geometric schemes | Symmetric Muggianu and Kohler polynomials | Selectable Muggianu (symmetric) and Toop (asymmetric) extrapolation engines | **Active** |
| **Assessed Alloy Systems** | Proprietary multi-megabyte commercial databases (TCNI, TTNi, PanTi) | SGTE unary v5.2, COST507 light alloys, NIST solders | 50+ validated alloy compositions, SGTE 45 unaries, and PanHEA Redlich-Kister excess | **Active** |
| **Solidification Simulation** | Scheil-Gulliver with Brody-Flemings back-diffusion | Basic equilibrium step cooling | Non-equilibrium Scheil-Gulliver with solute back-diffusion and liquidus tracking | **Active** |
| **Precipitation Kinetics** | TC-PRISMA (Langer-Schwartz / Kampmann-Wagner Numerical) | Standalone external scripts | Integrated Lifshitz-Slyozov-Wagner (LSW) coarsening and KWN nucleation rates | **In Progress** |
| **Diffusion & Mobilities** | DICTRA numerical mobility databases ($Q_i$, $B_i$) | Primitive Fickian diffusion | 1D/2D transient diffusion profiles with temperature-dependent atomic mobilities | **In Progress** |
| **Solid Solution Hardening** | Labusch / Fleischer empirical parameter fitting | Rule of Mixtures (ROM) | Varvenne-Curtin elastic misfit and Hall-Petch grain boundary strengthening | **Active** |
| **CAE Multiphysics Export** | Limited text tables or proprietary binary links | Generic CSV/JSON | Direct generation of ready-to-run decks for COMSOL, Abaqus, ANSYS, and DEFORM-3D | **Active** |

---

## 3. Core Thermodynamic Equilibrium & Minimization Algorithms

### 3.1 Mathematical Formulation & KKT Conditions
Thermodynamic equilibrium at fixed temperature $T$, pressure $P$, and system composition vector $\mathbf{N} = [N_1, \dots, N_C]^T$ corresponds to the constrained minimization of total Gibbs energy:

$$\min_{\mathbf{n}^\alpha, \mathbf{y}^\alpha} G_{\text{total}} = \sum_{\alpha=1}^{\Phi} N^\alpha G_m^\alpha(T, P, \mathbf{y}^\alpha)$$

subject to mass conservation ($\sum_{\alpha=1}^{\Phi} N^\alpha x_i^\alpha(\mathbf{y}^\alpha) - N_i = 0$), sublattice site fraction normalization ($\sum_{j} y_{sj}^\alpha - 1 = 0$), and non-negativity bounds ($y_{sj}^\alpha \ge 0, N^\alpha \ge 0$).

Formulating the Lagrangian:

$$\mathcal{L} = \sum_{\alpha} N^\alpha G_m^\alpha - \sum_{i=1}^C \mu_i \left( \sum_\alpha N^\alpha x_i^\alpha - N_i \right) - \sum_\alpha \sum_s \lambda_s^\alpha \left( \sum_j y_{sj}^\alpha - 1 \right)$$

The Karush-Kuhn-Tucker (KKT) first-order optimality conditions enforce:
1. Uniform chemical potentials across all active phases: $\mu_i^\alpha = \mu_i^\beta = \mu_i$.
2. For inactive candidate phases, the driving force must satisfy non-positivity:
   $$D^\phi = \sum_{i=1}^C \mu_i x_i^\phi - G_m^\phi(\mathbf{y}^{\phi*}) \le 0$$
   If $D^\phi > 0$, candidate phase $\phi$ is unstable and precipitates into the active set.

### 3.2 Convex Hull & Adaptive Continuation
- **Global Convex Hull (PyCALPHAD Engine)**: Evaluates discrete compositions across all candidate phases and constructs the lower convex hull via Delaunay triangulation and Qhull hyperplanes. This bypasses local false minima and provides robust initial chemical potentials.
- **Adaptive Continuation (CALPHAD XOC Engine)**: Uses predictor-corrector Euler-Newton stepping along phase boundary manifolds ($N^{\text{new}} = 0$) in $(T, P, x_i)$ space, detecting eutectic, peritectic, and miscibility gap bifurcations where $\det(\nabla^2 G_m) = 0$.

---

## 4. Advanced Modeling Formalisms

### 4.1 Multi-Sublattice Compound Energy Formalism (CEF)
For phases with multiple sublattices $(A, B, \dots)_{p} (C, D, \dots)_{q} \dots$, molar Gibbs energy is evaluated according to Cacciamani (2016):

$$G_m = \sum_{I_0} \left( \prod_{s} y_{i_s}^{(s)} \right) {}^\circ G_{I_0}(T) + R T \sum_s a_s \sum_i y_i^{(s)} \ln y_i^{(s)} + {}^E G_m + G_{mag}$$

where excess energy ${}^E G_m$ applies Redlich-Kister polynomials with Muggianu or Toop geometric extrapolations, and $G_{mag}$ evaluates the Inden-Hillert-Jarl / Xiong magnetic contribution:

$$G_{mag} = R T \ln(\beta + 1) g(\tau), \quad \tau = \frac{T}{T^*}$$

### 4.2 Order-Disorder Partitioning
Transitions such as FCC $A1 \leftrightarrow L1_2$ and BCC $A2 \leftrightarrow B2$ utilize a partitioned energy formulation:

$$G_m^{\text{total}}(\mathbf{x}, \mathbf{y}) = G_m^{\text{disordered}}(\mathbf{x}) + \Delta G_m^{\text{order}}(\mathbf{y}) - \Delta G_m^{\text{order}}(\mathbf{y}=\mathbf{x})$$

guaranteeing zero artificial miscibility gaps when sublattice fractions collapse to overall elemental mole fractions ($y_i^{(s)} = x_i$).

---

## 5. Microstructural Solidification & Kinetic Extensions

### 5.1 Non-Equilibrium Scheil-Gulliver Solidification with Back-Diffusion
Classical Scheil assumes zero solid diffusion and infinite liquid diffusion:

$$C_L = C_0 (1 - f_s)^{k_p - 1}$$

CALPHAD XOC computes instantaneous partition coefficients $k_p(T)$ from equilibrium tie-lines at incremental temperature steps ($\Delta T = 0.5\,\text{K}$) and integrates Brody-Flemings / Clyne-Kurz back-diffusion:

$$\alpha' = \alpha \left[ 1 - \exp\left(-\frac{1}{\alpha}\right) \right] - \frac{1}{2} \exp\left(-\frac{1}{2\alpha}\right), \quad \alpha = \frac{D_S t_f}{( \lambda_2 / 2 )^2}$$

### 5.2 Precipitation Kinetics (LSW & KWN Models)
- **Lifshitz-Slyozov-Wagner (LSW) Coarsening**: $\bar{r}(t)^3 - \bar{r}_0^3 = K t$, with $K = \frac{8 \gamma D C_\infty V_m^2}{9 R T}$.
- **Kampmann-Wagner Numerical (KWN) Framework**: Solves simultaneous nucleation (Classical Nucleation Theory with Zeldovich factor), diffusion-controlled growth ($v = \frac{dr}{dt}$), and particle size distribution continuity over discrete size classes.

---

## 6. High-Throughput CAE Integration & Export Decks

```
+---------------------------------------------------------------------------------+
|                       CALPHAD XOC Desktop Application                          |
+---------------------------------------------------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
+------------------+                                     +-------------------+
| Python Backend   |                                     | Native C++ Core   |
| (PyCALPHAD Core) |                                     | (OpenCalphad OC)  |
+------------------+                                     +-------------------+
         |                                                         |
         v                                                         v
+---------------------------------------------------------------------------------+
|                         Unified Thermodynamic Facade                            |
|       (Equilibrium, Phase Fractions, Driving Forces, Scheil Curves)             |
+---------------------------------------------------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+----------------------------------+     +----------------------------------+
| Dynamic CAE Decks                |     | Fast In-Situ Tabulation (ISAT)   |
|  - Abaqus (.inp, UMAT)           |     |  - High-dimensional Splines      |
|  - ANSYS (.mat, APDL)            |     |  - Sub-microsecond Interpolation |
|  - COMSOL Multiphysics (.xml)    |     |  - Real-Time Simulation Loops    |
+----------------------------------+     +----------------------------------+
```

CALPHAD XOC generates native, ready-to-run material cards and decks for:
- **COMSOL Multiphysics**: Interpolated phase fractions $f_\alpha(T)$, enthalpy $H(T)$, and thermal properties for 2D/3D transient Marangoni convection models.
- **Abaqus & ANSYS**: Temperature-dependent mechanical strength cards incorporating Varvenne-Curtin solid-solution hardening and Hall-Petch grain size relationships.
- **TRANSVALOR FORGE & DEFORM-3D**: Thermo-mechanical constitutive tables for forging, rolling, and planetary ball milling deformation.

---

## 7. Automated Synchronization & Missed-Run Catch-Up Protocol

This document and the associated capability matrix are governed by an automated, unattended synchronization service:
- **Scheduled Interval**: Every Thursday at 14:00:00 IST (2:00 PM).
- **Antigravity Standing Daemon**: Registered background schedule task (`task-58`) with cron expression `0 14 * * 4`.
- **System-Level Catch-Up (Windows Task Scheduler)**: Task `CALPHAD_XOC_Weekly_Capabilities_Sync` triggers at user logon and on Thursdays at 14:00 IST with `StartWhenAvailable = true`.
- **Missed-Run Detection**: If the computer was powered off during the scheduled Thursday 14:00 IST window, `automate_calphad_capabilities.ps1` detects that the last completed run precedes the most recent Thursday 14:00 IST, activates immediate research execution, and logs the catch-up in `calphad_schedule_state.json`.

---
*Maintained autonomously by Jane for Felix Mwiya | Materials CAE & Computational Metallurgy Workstation.*
