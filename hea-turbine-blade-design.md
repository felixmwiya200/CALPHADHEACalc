# High Entropy Alloy Design for Turbine Blades with Film Cooling

## Goal
Design and evaluate candidate High Entropy Alloys (HEAs) synthesizable via mechanical alloying for film-cooled turbine blade applications, calculate CALPHAD thermodynamic/mechanical/oxidation parameters, and produce a ranked 10-candidate Excel workbook.

## Tasks
- [x] Task 1: Formulate 10 targeted HEA candidates tailored for mechanical alloying (MA/SPS) and film-cooled turbine blade operating conditions (high solidus, creep resistance, alumina/chromia scale, thermal fatigue tolerance, drillability) → Verify: Inspect composition matrix and literature citations.
- [x] Task 2: Execute CALPHADHEACalc calculation engine on all 10 candidates to extract thermodynamic (VEC, ΔH_mix, ΔS_mix, Ω, δ, Ts, Tl), mechanical (Yield Strength RT & 800°C, UTS, Elongation, Hardness, Toughness, Creep limit), thermophysical (density, thermal conductivity, CTE), and oxidation kinetics (kp, scale type) → Verify: Confirm complete output convergence and zero NaN values.
- [x] Task 3: Evaluate and score candidates against the `AERO_TURBINE_BLADE` multi-criteria decision matrix (solidus margin, high-T yield, oxidation rate kp, density penalty, fracture toughness, film cooling compatibility) → Verify: Verify ranking scores (0-100%) and identify top-performing alloy.
- [x] Task 4: Generate a professional, multi-tab Excel workbook (`HEA_Turbine_Blade_Candidates.xlsx`) containing ranked summary, detailed CALPHAD parameters, mechanical alloying synthesis parameters (milling energy, SPS temperature, grain size), and film cooling thermophysical indices → Verify: Verify Excel creation using python openpyxl and inspect cell values.
- [x] Task 5: Document the metallurgical design rationale, mechanical alloying protocol, film-cooling hole integrity considerations, and ranking trade-offs → Verify: Review final report and check all requirements are satisfied.

## Done When
- [x] 10 HEA candidates calculated using CALPHADHEACalc engine.
- [x] Complete parameters (thermodynamic, mechanical, thermophysical, oxidation) computed.
- [x] Candidate materials ranked from best (rank 1) to rank 10 with clear scoring logic.
- [x] High-quality Excel file `HEA_Turbine_Blade_Candidates.xlsx` generated in workspace.
- [x] Verification and technical documentation completed.
