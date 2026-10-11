# Contributing to CALPHADHEACalc

Thank you for your interest in contributing to **CALPHADHEACalc** (High-Entropy Alloy Multi-Physics Software & Standalone Web Suite).

This project is governed under a **Maintainer-Review / BDFL (Benevolent Dictator for Life)** model. While the codebase is open-source and publicly accessible to researchers, engineers, and developers worldwide, **all proposed contributions, bug fixes, and feature additions must seek formal approval from the primary maintainer before being incorporated**.

---

## 1. Governance & Contribution Policy

> [!IMPORTANT]
> **Maintainer Approval Requirement**  
> Direct pushes to the `main` branch are disabled and protected by branch protection rules. All modifications must be submitted via a **Fork and Pull Request (PR)**. The primary maintainer (**Felix Mwiya**, under academic supervision of **Prof. (Dr.) Sheela Singh**, SRM University-AP) exercises sole authority to:
> - Review all incoming Pull Requests
> - Request scientific, architectural, or code quality revisions
> - Decide whether or not to merge any proposed change into the authoritative release

---

## 2. Contribution Workflow

To propose a modification:

1. **Open an Issue First**  
   Before writing significant amounts of code, open an issue using the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) or [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template describing:
   - The thermodynamic, kinetic, or UI problem being addressed
   - Literature citations or experimental validation datasets
   - The proposed implementation strategy

2. **Fork the Repository**  
   Click the **Fork** button at the top right of the GitHub repository page to create your personal copy:
   ```bash
   git clone https://github.com/<your-username>/CALPHADHEACalc.git
   cd CALPHADHEACalc
   ```

3. **Create a Dedicated Branch**  
   Create a descriptive branch for your work:
   ```bash
   git checkout -b feature/refractory-modulus-model
   # or
   git checkout -b fix/solvus-iteration-boundary
   ```

4. **Adhere to Code Quality Standards**
   - **Zero Emojis**: In accordance with CAE desktop software conventions (OriginLab, Thermo-Calc, Pandat), emojis are strictly prohibited across all code, UI labels, tooltips, dialogs, and commit messages.
   - **First-Principles Citations**: Any new physical equation or parameter must include formal literature citations (Author, Year, Journal, Volume, Pages, DOI).
   - **Dual Compatibility**: Modifications to calculation engines must maintain synchronization between the native MATLAB app (`App/CALPHADHEACalc.m`, `App/HEAThermoEngine.m`) and the standalone web suite (`index.html`, `App/ui/index.html`).

5. **Run the Automated Test Suite**  
   Ensure all 20 end-to-end verification tests pass with zero warnings or errors:
   ```bash
   matlab -batch "cd('App'); test_calphad_hea_calc();"
   ```

6. **Submit a Pull Request**  
   Push your branch to your fork and submit a Pull Request against `main` on the upstream repository. Complete the provided [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).

---

## 3. Review & Decision Process

- **Triage & Review**: The maintainer will review the code diff, mathematical soundness, documentation, and automated test logs.
- **Discussion**: Review comments may suggest refactoring, request additional benchmark comparisons, or seek clarification.
- **Maintainer Decision**: The maintainer will make the final decision to:
  - **Approve and Merge**
  - **Request Changes**
  - **Close / Decline** (with an explanation of why the change is outside project scope or conflicts with core physics)

---

## 4. Developer Certificate of Origin (DCO)

By submitting a Pull Request, you certify that:
- The contribution was created by you, in whole or in part, or you have the necessary intellectual property rights to submit it.
- The contribution is provided under the terms of the project's open-source license.
- You grant the project maintainers full authorization to redistribute and maintain the code.
