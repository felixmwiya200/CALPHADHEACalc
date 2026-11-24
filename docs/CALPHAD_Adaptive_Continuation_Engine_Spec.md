# Architectural Specification: In-Process Adaptive CALPHAD Continuation Engine

**Document Status**: Validated & Approved  
**Version**: 1.0.0  
**Lead System Architect**: Felix Mwiya (Computational Metallurgy & Materials CAE)  
**Date**: November 2026  

---

## 1. Executive Summary & Purpose
This specification governs the transition of the PyCALPHAD Materials Engineering Suite from empirical algebraic approximations to an authentic, high-performance in-process CALPHAD thermodynamic equilibrium engine.

By pairing `pycalphad` symbolic `.TDB` parsing with an **Euler Predictor / Constrained Newton-Raphson Corrector Continuation Solver**, the engine eliminates the combinatorial grid discretization bottleneck, enabling millisecond multi-component phase equilibrium, tie-line tracking, and phase boundary detection within an asynchronous desktop Qt environment.

---

## 2. Understanding Summary & System Scope
* **Core Function**: True multi-component Gibbs free energy minimization, phase fraction tracking $f_\phi(T)$, invariant point detection ($T_{\text{solidus}}$, $T_{\text{liquidus}}$, solvus boundaries), and thermophysical property generation.
* **Target Audience**: Materials scientists, alloy design engineers, and computational CAE researchers requiring authentic, publication-grade CALPHAD predictions.
* **Key Constraints**:
  1. Complete responsiveness of the PyQt6 desktop user interface (60 FPS fluid rendering).
  2. Native execution on 64-bit Windows environments without requiring external compiler installations for end users.
  3. Strict numerical stability across steep invariant phase reactions (eutectics, peritectics, and spinodal gaps).
* **Explicit Non-Goals**:
  1. The rapid empirical screening mode (<10 ms) will not be discarded; it remains available for instant composition scouting.
  2. End users will not be burdened with manual Fortran or C compiler setup.

---

## 3. Assumptions & Non-Functional Requirements
* **Performance**: Target stepping speed of $\le 5\text{ ms}$ per temperature interval for systems of up to 6 components once models are cached in memory.
* **Concurrency**: All mathematical minimization must run on background worker threads (`CALPHADContinuationWorker` via `QThread`) with atomic cancellation flags responding in $\le 2\text{ ms}$.
* **Database Compatibility**: Direct ingestion of standard SGTE, NIST, and open literature `.TDB` files containing Redlich-Kister excess polynomials and Inden-Hillert-Jarl magnetic models.
* **Resilience**: Graceful in-app diagnostic reporting and empirical fallback if unconstrained interaction parameters or missing unaries are encountered.

---

## 4. Running Decision Log

| Decision ID | Topic | Selection | Rationale |
| :--- | :--- | :--- | :--- |
| **DEC-001** | Branding Standardization | Remove all institutional text (`SRM University-AP`). | Professional, unadorned materials engineering desktop suite. |
| **DEC-002** | Startup Splash Screen | Restore native Florence flask loading jug (`MaterialSplash.exe`). | High-fidelity, immediate visual feedback (<25 ms) while background modules initialise. |
| **DEC-003** | Thermodynamic Backend Tier | Transition to compiled authentic CALPHAD Gibbs energy minimization. | Replace empirical curve-fitting with genuine multi-phase chemical equilibria and `.TDB` support. |
| **DEC-004** | Engine Architecture | **Approach 3: In-Process Adaptive Cython / C Continuation Engine**. | High in-process performance, direct memory coupling, and elimination of brute-force composition grid bottlenecks. |
| **DEC-005** | Model Compilation Strategy | In-memory compilation of SymEngine energy models and Hessians. | Eliminates repeated string parsing of `.TDB` files and provides microsecond function evaluation. |
| **DEC-006** | Concurrency & Telemetry | Asynchronous streaming via dedicated background `QThread`. | Maintains 60 FPS viewport responsiveness and plots phase boundaries progressively as the temperature marches. |
| **DEC-007** | Numerical Edge-Case Guard | Strict $\epsilon$-clamping and multi-start Hessian checking. | Prevents logarithmic singularities in entropy terms and detects isostructural phase demixing. |

---

## 5. Architectural Components & Mathematical Formulation

### 5.1 Predictor-Corrector Numerical Scheme
Unlike brute-force composition sampling, the engine tracks equilibrium along a continuous temperature trajectory:
1. **Model Cache (`TDBModelCache`)**:
   - Compiles symbolic Gibbs energy $G_m^\phi$, analytical gradient $\nabla G$, and Hessian $\mathbf{H} = \frac{\partial^2 G}{\partial y_i \partial y_j}$ into vectorised in-memory callables for each phase $\phi$.
2. **Predictor Step (Euler Tangent)**:
   - Differentiating the equilibrium condition $\nabla_{\mathbf{y}} G(\mathbf{y}, T) = 0$ with respect to temperature gives:
     $$\frac{d\mathbf{y}}{dT} = -\mathbf{H}^{-1} \frac{\partial^2 G}{\partial T \, \partial\mathbf{y}}$$
   - Advances temperature $T_{k+1} = T_k - \Delta T$ to provide a high-accuracy starting estimate.
3. **Corrector Step (Constrained Newton-Raphson)**:
   - Balances phase chemical potentials to tight convergence:
     $$|\mu_i^\alpha - \mu_i^\beta| < 10^{-6} \text{ J/mol}$$
4. **Active Set & Driving Force Tracking (`ActiveSetManager`)**:
   - For all dormant phases $\theta$ in the system:
     $$\Delta G_{\text{drive}}^\theta = G_m^\theta(\mathbf{y}^*) - \sum_i x_i \mu_i$$
   - A dormant phase is activated when $\Delta G_{\text{drive}}^\theta < 0$. If an active phase fraction drops below $f_\phi < 10^{-7}$, it is retired to the dormant set.

### 5.2 Adaptive Step-Size Management
* If Newton convergence completes in $\le 2$ iterations, the step size expands: $\Delta T \leftarrow \min(25\text{ K}, 1.25 \cdot \Delta T)$.
* If convergence requires $> 5$ iterations or encounters an invariant reaction, the step contracts: $\Delta T \leftarrow \max(0.1\text{ K}, 0.5 \cdot \Delta T)$.

---

## 6. Threading, Telemetry, and Edge-Case Protections
* **Progressive Live Plotting**: The worker emits `step_completed(T_c, phase_fractions_dict)` after every converged temperature point, rendering real-time curves without waiting for completion.
* **Logarithmic Singularity Guard**: Enforces $x_i \ge 10^{-12}$ to avoid singularities in ideal entropy terms $R T \ln(x_i)$.
* **Miscibility Gap Detection**: Monitors condition number $\kappa(\mathbf{H})$; forks multi-start search if $\kappa(\mathbf{H}) > 10^7$ to capture spinodal demixing ($\text{FCC}_1 + \text{FCC}_2$).

---

## 7. Verification & Automated Parity Strategy
1. **Binary Benchmark Testing**: Verifies Fe-Ni, Cr-Ni, and Cu-Ni liquidus/solidus lines against SGTE reference data within $\pm 0.8\text{ K}$.
2. **Quinary Cantor Alloy Parity**: Confirms single-phase FCC matrix stability for equiatomic $\text{CoCrFeMnNi}$ above $900 \text{ ^\circ C}$.
3. **Ni-Cr-Si-Fe-B-C Hardfacing Coating Parity**: Validates $\gamma\text{-Ni}$ solidus ($\sim 970 \text{ ^\circ C}$) and liquidus ($\sim 1045 \text{ ^\circ C}$) with boride/carbide precipitation.
4. **Non-Regression Assurance**: All 74 existing automated test suites must remain strictly green.
