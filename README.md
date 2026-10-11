# CALPHADHEACalc: High-Entropy Alloy Multi-Physics Thermodynamic Properties Software

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Standalone Web & Desktop](https://img.shields.io/badge/Standalone-Web_&_Desktop_App-success.svg)](#running-without-matlab)
[![GitHub Pages](https://img.shields.io/badge/Live_Web_App-GitHub_Pages-2ea44f.svg)](#1-live-web-app-in-your-browser)
[![MATLAB](https://img.shields.io/badge/MATLAB-R2024b%20%7C%20R2026a-0076A8.svg)](https://www.mathworks.com/products/matlab.html)
[![OriginLab Style](https://img.shields.io/badge/Graphics-OriginLab_600_DPI-8B0000.svg)](#high-density-scientific-visualization)
[![Tests Passing](https://img.shields.io/badge/Test_Suite-20%2F20_PASS_(100%25)-brightgreen.svg)](#automated-test-suite)

> **CALPHADHEACalc** is an open-source, multi-physics thermodynamic simulation and alloy design software engineered for High-Entropy Alloys (HEAs) and Multi-Principal Element Alloys (MPEAs). It integrates phenomenological Gibbs free energy minimization, empirical Miedema models, Varvenne-Curtin solid solution strengthening, Hall-Petch grain size scaling, Wagner parabolic oxidation kinetics, ASTM G102 electrochemical corrosion prediction, and kinematic X-ray powder diffraction into a unified CAE suite mirroring Pandat PanGUI and Thermo-Calc.

---

## Running WITHOUT MATLAB

> [!TIP]
> **No MATLAB License or Installation Required!**  
> Anyone accessing this repository can run CALPHADHEACalc immediately using either the **interactive web suite** or the **native Windows desktop app mode** with **zero dependencies**.

### 1. Live Web App in Your Browser
Click the live GitHub Pages link to run the complete simulation suite directly in your browser:
* **Live Web App**: [https://felixmwiya200.github.io/CALPHADHEACalc/](https://felixmwiya200.github.io/CALPHADHEACalc/) *(or configure via repository Settings > Pages)*
* Compatible with all modern browsers: Chrome, Edge, Firefox, Safari on Windows, macOS, Linux, and mobile devices.

### 2. Software Installation (1-Click Install Scripts)
To install CALPHADHEACalc locally and set up desktop shortcuts and environment paths:

* **Windows 1-Click Installer**:
  Double-click `install.bat` (or `setup.bat`), or run in PowerShell:
  ```powershell
  .\install.ps1
  ```
  This automatically verifies repository modules, detects available runtimes (Node.js, MATLAB, Edge/Chrome), creates Desktop & Start Menu shortcuts with the official application icon, and registers MATLAB search paths.

* **Linux & macOS Installer**:
  ```bash
  chmod +x install.sh
  ./install.sh
  ```
  Configures executable permissions, tests runtimes, and creates desktop application entries.

* **MATLAB Native Installation**:
  In the MATLAB command prompt:
  ```matlab
  install
  ```
  Permanently registers `App/`, `materials_data/`, and `scripts/` in your MATLAB path, runs the multi-physics engine self-test, and prepares the software for launching.

### 3. Offline Web App from Cloned Repository
If you cloned or downloaded this repository, simply double-click:
```text
index.html
```
The entire application loads locally in your default web browser completely offline.

### 4. Native Windows Desktop App
For Windows users who want a dedicated standalone desktop window without browser toolbars:
```text
Double-click: CALPHADHEACalc_Desktop.bat
(or double-click CALPHADHEACalc_Desktop.vbs for silent launch)
```
This launches the interface in a borderless, dedicated CAE application window utilizing the native Microsoft Edge WebView2 / Chrome application framework.

### 5. Standalone Windows Executable (`.exe`) via MATLAB Runtime
For users running the compiled native executable (`CALPHADHEACalc.exe`):
* **Requires NO MATLAB license.**
* Requires only the **free, royalty-free MATLAB Runtime (MCR)** available from MathWorks:  
  [Download Free MATLAB Runtime](https://www.mathworks.com/products/compiler/matlab-runtime.html)

---

## Running with MATLAB (For Developers & Researchers)

To run the native MATLAB App Designer CAE application:

1. Clone the repository:
   ```bash
   git clone https://github.com/felixmwiya200/CALPHADHEACalc.git
   cd CALPHADHEACalc
   ```
2. Open MATLAB (R2023b, R2024b, or newer) and navigate to the repository directory.
3. Launch the application:
   ```matlab
   CALPHADHEACalc
   ```
   Or launch with a specific alloy preset:
   ```matlab
   CALPHADHEACalc('Cantor (CoCrFeMnNi)');
   CALPHADHEACalc('Al0.3CoCrFeNi');
   CALPHADHEACalc('NbMoTaW (Refractory 4-Elem)');
   ```

---

## Open-Source Governance & Contribution Policy

This repository is publicly shared and open-sourced under the **Apache 2.0 License**. However, to preserve strict scientific accuracy and first-principles validity:

> [!IMPORTANT]
> **All contributions require maintainer review and approval.**
> - Direct pushes to the `main` branch are blocked via GitHub Branch Protection Rules.
> - All proposed changes, bug fixes, and feature additions must be submitted via a **Fork and Pull Request (PR)**.
> - The lead maintainer (**Felix Mwiya**, under academic supervision of **Prof. (Dr.) Sheela Singh**, SRM University-AP) reviews every submission and reserves sole authority to approve, request revisions, or decline proposed changes.
> - Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) for detailed guidelines.

---

## Core Capabilities & Multiphysics Engines

```
+--------------------------------------------------------------------------------------------------------+
|                                  CALPHADHEACalc MULTI-PHYSICS SOFTWARE                                 |
+--------------------------------------------------------------------------------------------------------+
|  1. Phase Equilibria     | CALPHAD Gibbs free energy minimization, Redlich-Kister excess, Solvus T    |
|  2. Phase Diagrams       | 2D Isopleth (T-x) sections and isothermal Gibbs ternary composition space  |
|  3. Thermophysics        | Specific heat Cp(T), density rho(T), thermal conductivity k(T), viscosity  |
|  4. Mechanical Strength  | Varvenne-Curtin solid solution model, Hall-Petch grain size, Tabor hardness|
|  5. Environmental        | Wagner parabolic oxidation (kp), Ellingham oxides (54 candidate scales)   |
|  6. Aqueous Corrosion    | ASTM G102 equivalent weight, Faraday penetration rate, PREN_HEA, micro-cell|
|  7. Crystallography      | Bragg-Brentano Kinematic XRD diffractograms, Scherrer crystallite size     |
|  8. Industrial Sectors   | Multi-criteria radar scoring (0-100%) across 10 engineering applications   |
|  9. Command Terminal     | Interactive CALPHAD command REPL with script runner (Python, MATLAB, TCM)  |
| 10. OriginLab Graphics   | 4-sided boxed frames, inward ticks, 600 DPI publication exports             |
+--------------------------------------------------------------------------------------------------------+
```

### 1. Attached Thermodynamic Databases (8 Active)
1. **SGTE Unary Database (1991 Dinsdale Assessment)**: Pure element Gibbs free energies $G_i^\phi(T) - H_i^{\text{SER}}$ for 45 elements.
2. **PanHEA High-Entropy Solution Database**: Assessed binary and ternary Redlich-Kister excess interaction parameters $L_{ij}^{(k)}$ and $L_{ijk}^{(0)}$.
3. **Miedema Macroscopic Atom Model Database**: Semi-empirical enthalpy of mixing $\Delta H_{ij}$ across 2,701 interatomic pairs.
4. **HEAOxideDatabase (v2026.2 Comprehensive)**: 54 distinct candidate binary, refractory, volatile, and complex spinel oxides with Ellingham formation energies $\Delta G_f^\circ(T)$ and Pilling-Bedworth ratios (PBR).
5. **HEABenchmarkDatabase**: Validated experimental literature benchmarks for 22 HEA systems.
6. **IUPAC 118 Elements Registry**: Comprehensive atomic properties ($Z=1$ to $118$).
7. **ASTM G102 Electrochemical Standard**: Standardized equivalent weight and Faraday corrosion calculation.
8. **NIST-JANAF & Barin Thermochemical Tables**: Standard state thermodynamic reference values.

### 2. Governing Equations Documentation
Full mathematical derivations and code-path citations are documented in the [Attached Databases and Governing Equations Wiki](App/CALPHAD_DATABASES_AND_EQUATIONS_WIKI.md).

---

## Repository File Structure

```text
CALPHADHEACalc/
├── install.bat                          # 1-Click Windows batch installer (Desktop/Start Menu shortcuts)
├── setup.bat                            # Alias launcher for install.bat
├── install.ps1                          # Modern PowerShell installer script
├── install.m                            # Native MATLAB installer and automated engine self-test
├── setup.m                              # Alias launcher for install.m
├── install.sh                           # Cross-platform Linux and macOS installer script
├── uninstall.bat                        # Clean shortcut & path uninstaller (Batch)
├── uninstall.ps1                        # Clean shortcut & path uninstaller (PowerShell)
├── package.json                         # Node.js project metadata and npm task runner
├── index.html                           # Standalone web application (100% offline)
├── docs/                                # GitHub Pages deployment directory
│   └── index.html                       # Mirror for GitHub Pages
├── CALPHADHEACalc_Desktop.bat           # Native desktop window launcher
├── CALPHADHEACalc_Desktop.vbs           # Silent desktop launcher
├── compile_calphad_exe.m                # Standalone Windows .exe compiler script
├── CONTRIBUTING.md                      # Contribution guidelines & maintainer approval policy
├── BRANCH_PROTECTION.md                 # Step-by-step GitHub branch protection setup
├── LICENSE                              # Apache 2.0 Open Source License
├── CODE_OF_CONDUCT.md                  # Contributor Covenant v2.1
├── SECURITY.md                          # Vulnerability reporting protocol
├── README.md                            # Primary project documentation
├── .gitignore                           # Git ignore rules for MATLAB & OS files
├── .gitattributes                       # Line ending and binary asset definitions
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md         # Pull request template
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md                # Bug report template
│   │   └── feature_request.md           # Feature request template
│   └── workflows/
│       └── deploy-pages.yml             # Automated GitHub Pages CI/CD workflow
└── App/
    ├── CALPHADHEACalc.m                 # Master application (uifigure)
    ├── install.m                        # Local MATLAB installer in App
    ├── HEAThermoEngine.m                # CALPHAD Gibbs minimization & Miedema engine
    ├── HEAMechanicalEngine.m            # Varvenne-Curtin & Hall-Petch mechanical engine
    ├── HEAOxidationEngine.m             # Wagner parabolic oxidation & Ellingham engine
    ├── HEAOxideDatabase.m               # 54 candidate oxides database
    ├── HEAXRDEngine.m                   # Kinematic powder diffraction engine
    ├── HEAElementsData.m                # 118 IUPAC elements periodic database
    ├── HEABenchmarkDatabase.m           # Experimental literature benchmarks (22 alloys)
    ├── HEAApplicationDatabase.m         # 10 industrial sectors engineering thresholds
    ├── HEAApplicationScorer.m           # Multi-criteria radar suitability scoring
    ├── OriginPlotter.m                  # OriginLab publication graphics formatter
    ├── ThirdPartyLicenseRegistry.m      # 14 third-party offline software licenses
    ├── test_calphad_hea_calc.m          # 20-test end-to-end automated verification suite
    ├── CALPHAD_DATABASES_AND_EQUATIONS_WIKI.md # Formal technical wiki documentation
    ├── resources/                       # Branded icons (AppIcon.png, AppIcon.ico)
    ├── legal/                           # Bundled third-party license notices
    └── ui/
        └── index.html                   # High-density web application
```

---

## Authors & Academic Provenance

* **Lead Architect & Computational Developer**: **Felix Mwiya**
* **Research Guidance & Academic Supervision**: **Prof. (Dr.) Sheela Singh**
* **Institutional Affiliation**:  
  Department of Mechanical Engineering, School of Engineering and Sciences,  
  SRM University-AP, Andhra Pradesh 522240, India.

---

## How to Cite

If you use CALPHADHEACalc in academic research, alloy design, or industrial publications, please cite:

### APA Format
> Mwiya, F., & Singh, S. (2026). *CALPHADHEACalc: High-Entropy Alloy Multi-Physics Thermodynamic Properties Software* (v3.4.0). Department of Mechanical Engineering, School of Engineering and Sciences, SRM University-AP, Andhra Pradesh, India.

### BibTeX
```bibtex
@software{Mwiya_CALPHADHEACalc_2026,
  author       = {Mwiya, Felix and Singh, Sheela},
  title        = {{CALPHADHEACalc: High-Entropy Alloy Multi-Physics Thermodynamic Properties Software}},
  version      = {3.4.0},
  year         = {2026},
  institution  = {Department of Mechanical Engineering, School of Engineering and Sciences, SRM University-AP},
  address      = {Andhra Pradesh, India},
  url          = {https://github.com/felixmwiya200/CALPHADHEACalc}
}
```

---

## License

This project is licensed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for details.
