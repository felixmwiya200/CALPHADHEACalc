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

---

## 4. Contributor License Agreement (CLA)

To ensure the long-term stewardship, distribution, and binary packaging of the Project, **all contributors must sign the [CALPHADHEACalc Contributor License Agreement (CLA)](CLA.md)** before any Pull Request can be merged.

### What the CLA Does
- **You Retain Your Copyright**: You keep full copyright ownership in your original contributions.
- **Open-Source Protection**: Your contribution is distributed under the project's open-source license.
- **Distribution & Sublicensing Grant**: You grant the project maintainers the standard non-exclusive permissions to compile, package, sublicense, and distribute derivative works of the Project.

### How to Sign the CLA
1. **Automated Pull Request Check (Recommended)**: When you open a Pull Request, the automated CLA bot will verify your signature. If this is your first contribution, reply to the bot's comment with:
   ```
   I have read the CALPHADHEACalc Contributor License Agreement and I hereby agree to its terms.
   ```
2. **Git Commit Sign-Off**: Add a `Signed-off-by` trailer to every git commit using `git commit -s`:
   ```bash
   git commit -s -m "feat(thermo): add high-temperature refractory solvus model"
   ```
3. **Corporate Contributions**: If contributing on behalf of an employer or institution, review the Corporate CLA provisions in [`CLA.md`](CLA.md).
