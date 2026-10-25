classdef HEALatticeDistortionEngine
    % HEALatticeDistortionEngine - High-Entropy Alloy Lattice Distortion & Soft Sphere Model Engine
    % 100% Native MATLAB implementation based on:
    %   1. Quanfeng He and Yong Yang, "On Lattice Distortion in High Entropy Alloys",
    %      Frontiers in Materials 5:42 (2018), doi: 10.3389/fmats.2018.00042.
    %   2. Y. F. Ye, Q. Wang, J. Lu, C. T. Liu, Y. Yang, "The 'soft-sphere' model for
    %      local lattice distortion in high entropy alloys", Mater. Today 19, 349-355 (2016).
    %   3. Y. F. Ye, Q. F. He, M. F. Lu, et al., "Atomic-scale local strain fluctuations in
    %      chemical complex alloys", Acta Mater. 150, 182-194 (2018).
    %   4. R. Labusch, "A statistical theory of solid solution hardening",
    %      Phys. Stat. Sol. 41, 659-669 (1970).
    %
    % Lead Computational Materials Engineering Suite: CALPHADHEACalc
    % Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)

    methods (Static)

        function metrics = computeDistortionMetrics(elements, at_fractions, thermoMetrics, userOpts)
            % Computes comprehensive lattice distortion, soft-sphere residual strains,
            % critical effective shear strain, and dislocation glide mode.
            % Syntax:
            %   metrics = HEALatticeDistortionEngine.computeDistortionMetrics(elements, at_fractions)
            %   metrics = HEALatticeDistortionEngine.computeDistortionMetrics(elements, at_fractions, thermoMetrics, userOpts)

            if nargin < 3 || isempty(thermoMetrics)
                thermoMetrics = struct();
            end
            if nargin < 4 || isempty(userOpts)
                userOpts = struct();
            end

            % Clean and normalize compositions
            if iscell(elements)
                elemList = elements(:);
            else
                elemList = cellstr(elements(:));
            end
            c = double(at_fractions(:));
            cSum = sum(c);
            if cSum > 0
                c = c / cSum;
            else
                c = ones(numel(elemList), 1) / max(1, numel(elemList));
            end
            n = numel(elemList);

            elemDb = HEAThermoEngine.getElementDatabase();

            % Extract or estimate crystal structure and Poisson's ratio
            crystalStructure = 'FCC';
            nu_alloy = 0.31;
            G_alloy_GPa = 80.0;
            b_nm = 0.255; % Burgers vector magnitude in nm

            if isfield(thermoMetrics, 'Phase') && ~isempty(thermoMetrics.Phase)
                phStr = thermoMetrics.Phase;
                if contains(phStr, 'BCC')
                    crystalStructure = 'BCC';
                    b_nm = 0.286 * sqrt(3) / 2.0; % a * sqrt(3)/2 ~ 0.248 nm
                elseif contains(phStr, 'HCP')
                    crystalStructure = 'HCP';
                    b_nm = 0.265;
                else
                    crystalStructure = 'FCC';
                    b_nm = 0.360 / sqrt(2.0); % a / sqrt(2) ~ 0.255 nm
                end
            end

            if isfield(thermoMetrics, 'Mechanical') && isstruct(thermoMetrics.Mechanical)
                mm = thermoMetrics.Mechanical;
                if isfield(mm, 'PoissonRatio') && ~isnan(mm.PoissonRatio) && mm.PoissonRatio > 0
                    nu_alloy = double(mm.PoissonRatio);
                end
                if isfield(mm, 'ShearModulus_GPa') && ~isnan(mm.ShearModulus_GPa) && mm.ShearModulus_GPa > 0
                    G_alloy_GPa = double(mm.ShearModulus_GPa);
                end
                if isfield(mm, 'BurgersVector_nm') && ~isnan(mm.BurgersVector_nm) && mm.BurgersVector_nm > 0
                    b_nm = double(mm.BurgersVector_nm);
                end
            end

            % -------------------------------------------------------------
            % 1. Hard-Sphere Atomic Size Mismatch (Zhang et al. 2008)
            % -------------------------------------------------------------
            r = zeros(n, 1);
            for i = 1:n
                el = strtrim(elemList{i});
                if isKey(elemDb, el)
                    r(i) = elemDb(el).r; % in pm
                else
                    r(i) = 130.0;
                end
            end
            r_bar = sum(c .* r);
            delta_hard_sphere_pct = sqrt(sum(c .* ((1.0 - (r / r_bar)).^2))) * 100.0;

            % -------------------------------------------------------------
            % 2. Soft-Sphere Model: Radial Volumetric Strain & eps_RMS (Ye et al. 2015, 2018)
            % -------------------------------------------------------------
            % Coordination number Ni: FCC=12, BCC=8, HCP=12
            if strcmp(crystalStructure, 'BCC')
                N_coord = 8;
                eta_pack = 0.680;
            else
                N_coord = 12;
                eta_pack = 0.7405;
            end

            % Compute local radial strain eps_i for each element
            % eps_i = (sum_j Omega_ij * c_j) / (sum_k A_ik * c_k) - (4*pi*eta) / (Ni * sum_k A_ik * c_k)
            % where A_ij = 2*pi*x_ij / ((x_ij+1)^2 * sqrt(x_ij*(x_ij+2))) and x_ij = r_i / r_j
            eps_i = zeros(n, 1);
            A_matrix = zeros(n, n);
            Omega_matrix = zeros(n, n);

            for i = 1:n
                for j = 1:n
                    x_ij = r(i) / max(1.0, r(j));
                    denom_A = ((x_ij + 1.0)^2) * sqrt(x_ij * (x_ij + 2.0));
                    A_ij = (2.0 * pi * x_ij) / max(1e-6, denom_A);
                    A_matrix(i, j) = A_ij;
                    % Solid angle subtended by sphere j around sphere i
                    Omega_matrix(i, j) = 2.0 * pi * (1.0 - sqrt(x_ij * (x_ij + 2.0)) / (x_ij + 1.0));
                end
            end

            for i = 1:n
                sum_Omega = sum(Omega_matrix(i, :)' .* c);
                sum_A = sum(A_matrix(i, :)' .* c);
                if sum_A > 0
                    eps_i(i) = (sum_Omega / sum_A) - (4.0 * pi * eta_pack) / (N_coord * sum_A);
                else
                    eps_i(i) = (r(i) - r_bar) / r_bar;
                end
            end

            % Average volumetric strain must satisfy sum(c_i * eps_i) ~ 0
            mean_eps = sum(c .* eps_i);
            eps_i_zero_mean = eps_i - mean_eps;

            % Root-mean-square residual strain eps_RMS (Ye et al. 2018 Eq. 2)
            eps_RMS = sqrt(sum(c .* (eps_i_zero_mean.^2)));
            eps_RMS_pct = eps_RMS * 100.0;

            % -------------------------------------------------------------
            % 3. Critical Effective Shear Strain gamma_th (He & Yang 2018 Eq. 6)
            % -------------------------------------------------------------
            % gamma_th = 0.485 * sqrt( 2*(1+nu) / (1-2*nu) ) * (delta/100)
            nu_clamped = max(0.15, min(0.46, nu_alloy));
            poisson_factor = sqrt((2.0 * (1.0 + nu_clamped)) / max(0.01, (1.0 - 2.0 * nu_clamped)));
            gamma_th = 0.485 * poisson_factor * (delta_hard_sphere_pct / 100.0);

            % Elastic constants estimate for cubic symmetry
            C11_GPa = G_alloy_GPa * 2.0 * (1.0 - nu_clamped) / max(0.01, 1.0 - 2.0 * nu_clamped);
            C12_GPa = C11_GPa * nu_clamped / (1.0 - nu_clamped);
            C44_GPa = G_alloy_GPa;

            % Stored elastic strain energy density change Delta_E_elastic (J/m^3)
            % Delta_Ep = 3/4 * (C11 - C12) * gamma_th^2
            delta_Ep_MPa = 0.75 * (C11_GPa - C12_GPa) * (gamma_th^2);

            % -------------------------------------------------------------
            % 4. Phase Stability & Structural Regime (Ye et al. 2016, 2018)
            % -------------------------------------------------------------
            % Thresholds:
            %   eps_RMS < 5.0%   -> Single-Phase Solid Solution (FCC / BCC)
            %   5.0% <= eps_RMS <= 10.0% -> Multi-Phase / Ordered Intermetallic
            %   eps_RMS > 10.0%  -> Metallic Glass / Amorphization (E_elastic > 1/12)
            if eps_RMS_pct < 5.0
                structuralRegime = 'Single-Phase Solid Solution (Low Strain Fluctuation)';
                stabilityClass = 'Stable Solid Solution';
                amorphizationRisk = 'Negligible (Crystalline Lattice Preserved)';
            elseif eps_RMS_pct <= 10.0
                structuralRegime = 'Multi-Phase / Ordered Intermetallic Precursor';
                stabilityClass = 'Intermediate Lattice Strain';
                amorphizationRisk = 'Moderate (Local Phase Separation Likely)';
            else
                structuralRegime = 'Amorphous Destabilization / Metallic Glass Regime';
                stabilityClass = 'Severe Lattice Distortion';
                amorphizationRisk = 'High (Topological Amorphization Triggered)';
            end

            % -------------------------------------------------------------
            % 5. Dislocation Glide Mechanism: Peierls Kink-Pair vs Labusch Forest Pinning
            % -------------------------------------------------------------
            % In He & Yang (2018 Figure 8):
            %   Low distortion (gamma_th < 0.02): Dislocation moves by Peierls kink-pair nucleation.
            %   High distortion (gamma_th >= 0.02): Dislocation is tortuous/wavy, pinned by collective
            %   weak obstacles governed by the Labusch model (Labusch 1970).
            if gamma_th < 0.020
                glideMechanism = 'Peierls Kink-Pair Glide (Planar Straight Slip)';
                pinningRegime = 'Weak Peierls Lattice Friction (Hirth & Lothe 1982)';
                activationVolume_b3 = round(8.0 + 150.0 * gamma_th, 1); % ~ 8 - 11 b^3
                wavyTortuosity = 1.0 + 1.2 * gamma_th;
            else
                glideMechanism = 'Labusch Collective Weak Pinning (Wavy Tortuous Slip)';
                pinningRegime = 'Labusch Statistical Forest Pinning (Labusch 1970, 1972)';
                % Activation volume expands dramatically from collective pinning
                activationVolume_b3 = round(30.0 + 1200.0 * (gamma_th - 0.02), 1); % ~ 40 - 120 b^3
                wavyTortuosity = 1.0 + 3.5 * gamma_th;
            end
            activationVolume_m3 = activationVolume_b3 * ((b_nm * 1e-9)^3);

            % Labusch strengthening increment (MPa)
            % Delta_sigma_Labusch ~ 0.5 * G * gamma_th^(4/3) * (1+nu)
            delta_sigma_labusch_MPa = 0.5 * (G_alloy_GPa * 1e3) * (gamma_th^(4.0 / 3.0)) * (1.0 + nu_clamped);

            % -------------------------------------------------------------
            % 6. XRD High-Angle Peak Splitting Parameters (He & Yang 2018 Figure 7)
            % -------------------------------------------------------------
            % High-angle peaks (2theta > 60 deg) split due to local tetragonality/rhombicity
            xrdSplitting_deg = zeros(4, 1);
            targetAngles = [43.5, 50.8, 74.7, 90.7]; % Typical FCC reflections: (111), (200), (220), (311)
            for k = 1:numel(targetAngles)
                th_rad = (targetAngles(k) / 2.0) * (pi / 180.0);
                % Angular splitting Delta_2theta = gamma_th * tan(theta) * (180/pi)
                xrdSplitting_deg(k) = round(gamma_th * tan(th_rad) * (180.0 / pi), 3);
            end

            % Check literature benchmark matching (He & Yang 2018 Table/Figures)
            bench = HEALatticeDistortionEngine.matchLiteratureBenchmark(elemList, c);

            % -------------------------------------------------------------
            % Construct Output Metrics Struct
            % -------------------------------------------------------------
            metrics = struct();
            metrics.Delta_HardSphere_pct = round(delta_hard_sphere_pct, 3);
            metrics.Eps_RMS_SoftSphere_pct = round(eps_RMS_pct, 3);
            metrics.MeanAtomicRadius_pm = round(r_bar, 2);
            metrics.ElementalResidualStrains = eps_i_zero_mean;
            metrics.PackingEfficiency_eta = eta_pack;
            metrics.CoordinationNumber = N_coord;

            metrics.PoissonRatio = round(nu_clamped, 3);
            metrics.PoissonFactor = round(poisson_factor, 3);
            metrics.CriticalEffectiveShearStrain_gamma_th = round(gamma_th, 4);
            metrics.ElasticShearEnergy_DeltaEp_MPa = round(delta_Ep_MPa, 2);
            metrics.C11_GPa = round(C11_GPa, 1);
            metrics.C12_GPa = round(C12_GPa, 1);
            metrics.C44_GPa = round(C44_GPa, 1);

            metrics.StructuralRegime = structuralRegime;
            metrics.StabilityClass = stabilityClass;
            metrics.AmorphizationRisk = amorphizationRisk;

            metrics.DislocationGlideMechanism = glideMechanism;
            metrics.PinningRegime = pinningRegime;
            metrics.ActivationVolume_b3 = activationVolume_b3;
            metrics.ActivationVolume_m3 = activationVolume_m3;
            metrics.WavyDislocationTortuosity = round(wavyTortuosity, 3);
            metrics.LabuschStrengthening_MPa = round(delta_sigma_labusch_MPa, 1);

            metrics.XRDAngles_2Theta_deg = targetAngles;
            metrics.XRDAngularSplitting_deg = xrdSplitting_deg;
            metrics.HasHighAnglePeakSplitting = (gamma_th >= 0.020);

            metrics.Benchmark = bench;
            metrics.LiteratureCitation = 'Q. He & Y. Yang, Front. Mater. 5:42 (2018) / Y. Ye et al., Acta Mater. 150 (2018)';
        end

        function bench = matchLiteratureBenchmark(elemList, c)
            % Matches alloy against authoritative benchmark data from He & Yang (2018)
            bench = struct('Matched', false, 'System', '', 'ExpDelta_pct', NaN, ...
                           'ExpEpsRMS_pct', NaN, 'ExpGammaTh', NaN, 'ObservedPhase', '', 'Citation', '');

            compMap = containers.Map();
            for i = 1:numel(elemList)
                compMap(strtrim(elemList{i})) = c(i);
            end

            % 1. Cantor Alloy CoCrFeMnNi (Figure 2, 4)
            if isKey(compMap, 'Co') && isKey(compMap, 'Cr') && isKey(compMap, 'Fe') && ...
               isKey(compMap, 'Mn') && isKey(compMap, 'Ni') && numel(elemList) == 5
                if abs(compMap('Co') - 0.20) <= 0.03
                    bench.Matched = true;
                    bench.System = 'Cantor (CoCrFeMnNi)';
                    bench.ExpDelta_pct = 1.18;
                    bench.ExpEpsRMS_pct = 1.12;
                    bench.ExpGammaTh = 0.015;
                    bench.ObservedPhase = 'Single-Phase FCC (Low Distortion, Kink-Pair Glide)';
                    bench.Citation = 'He & Yang, Front. Mater. 2018, Fig. 2; Owen et al., 2017';
                    return;
                end
            end

            % 2. CoCrNi (Medium Entropy Alloy, Figure 2)
            if isKey(compMap, 'Co') && isKey(compMap, 'Cr') && isKey(compMap, 'Ni') && numel(elemList) == 3
                if abs(compMap('Co') - 0.33) <= 0.04
                    bench.Matched = true;
                    bench.System = 'CoCrNi (Toughness Benchmark)';
                    bench.ExpDelta_pct = 1.15;
                    bench.ExpEpsRMS_pct = 1.08;
                    bench.ExpGammaTh = 0.014;
                    bench.ObservedPhase = 'Single-Phase FCC (Exceptional Damage Tolerance)';
                    bench.Citation = 'Gludovatz et al., Nat. Commun. 2016; He & Yang 2018';
                    return;
                end
            end

            % 3. CoCrFeNiPd (Severe Distortion FCC, Page 2)
            if isKey(compMap, 'Co') && isKey(compMap, 'Cr') && isKey(compMap, 'Fe') && ...
               isKey(compMap, 'Ni') && isKey(compMap, 'Pd') && numel(elemList) == 5
                bench.Matched = true;
                bench.System = 'CoCrFeNiPd (Pd-Expanded FCC)';
                bench.ExpDelta_pct = 4.25;
                bench.ExpEpsRMS_pct = 3.85;
                bench.ExpGammaTh = 0.052;
                bench.ObservedPhase = 'Severely Distorted FCC (Tong et al. 2017, Labusch Pinning)';
                bench.Citation = 'Tong et al., 2017; He & Yang, Front. Mater. 2018';
                return;
            end

            % 4. TiZrHfNbTa (Refractory Senkov BCC, Figure 2)
            if isKey(compMap, 'Ti') && isKey(compMap, 'Zr') && isKey(compMap, 'Hf') && ...
               isKey(compMap, 'Nb') && isKey(compMap, 'Ta') && numel(elemList) == 5
                bench.Matched = true;
                bench.System = 'TiZrHfNbTa (Refractory BCC)';
                bench.ExpDelta_pct = 5.62;
                bench.ExpEpsRMS_pct = 4.75;
                bench.ExpGammaTh = 0.068;
                bench.ObservedPhase = 'Ductile Refractory BCC (Guo et al. 2013; He & Yang 2018)';
                bench.Citation = 'Senkov et al. 2011; He & Yang, Front. Mater. 2018 Fig. 2';
                return;
            end

            % 5. NbMoTaW (Refractory Ultra-High Temperature BCC, Figure 2)
            if isKey(compMap, 'Nb') && isKey(compMap, 'Mo') && isKey(compMap, 'Ta') && ...
               isKey(compMap, 'W') && numel(elemList) == 4
                bench.Matched = true;
                bench.System = 'NbMoTaW (Refractory BCC)';
                bench.ExpDelta_pct = 4.31;
                bench.ExpEpsRMS_pct = 3.65;
                bench.ExpGammaTh = 0.048;
                bench.ObservedPhase = 'Single-Phase BCC (Senkov et al. 2011, Labusch Slip)';
                bench.Citation = 'Senkov et al., 2011; He & Yang, Front. Mater. 2018';
                return;
            end
        end

    end
end
