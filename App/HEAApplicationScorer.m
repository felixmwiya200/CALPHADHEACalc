classdef HEAApplicationScorer
    % HEAApplicationScorer - Multi-Criteria Suitability Scoring Engine for HEAs
    % Evaluates high-entropy alloy compositions against 10 industrial application domains
    % and computes:
    %   1. Normalized continuous utility scoring (0-100%)
    %   2. Strict elemental and physical property hard vetoes
    %   3. Suitability Match Tiers (Prime, Viable, Conditional, Unsuitable)
    %   4. Limiting Bottleneck Identification
    %   5. Actionable Metallurgical Composition Tuning Advice

    methods (Static)

        function results = scoreAlloy(elements, at_fractions, thermoMetrics, mechMetrics, oxMetrics)
            % Main entry point evaluating an alloy against all 10 applications
            % Syntax:
            %   results = HEAApplicationScorer.scoreAlloy(elements, at_fractions)
            %   results = HEAApplicationScorer.scoreAlloy(elements, at_fractions, thermoMetrics, mechMetrics, oxMetrics)

            % Normalize inputs
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
                error('Sum of atomic fractions must be greater than zero.');
            end

            % Ensure upstream multiphysics metrics are available
            if nargin < 3 || isempty(thermoMetrics)
                thermoMetrics = HEAThermoEngine.computeThermodynamics(elemList, c);
            end
            if nargin < 4 || isempty(mechMetrics)
                mechMetrics = HEAMechanicalEngine.computeMechanicalProperties(elemList, c, thermoMetrics);
            end
            if nargin < 5 || isempty(oxMetrics)
                oxMetrics = HEAOxidationEngine.computeOxidationKinetics(elemList, c, thermoMetrics);
            end

            % Retrieve all application definitions
            apps = HEAApplicationDatabase.getAllApplications();
            numApps = numel(apps);

            scoredList = cell(numApps, 1);

            for a = 1:numApps
                if iscell(apps)
                    app = apps{a};
                else
                    app = apps(a);
                end
                evalRes = HEAApplicationScorer.evaluateSingleApplication(app, elemList, c, thermoMetrics, mechMetrics, oxMetrics);
                scoredList{a} = evalRes;
            end

            % Convert to array of structs and sort descending by Score_pct
            allResults = [scoredList{:}];
            [~, sortIdx] = sort([allResults.Score_pct], 'descend');
            sortedResults = allResults(sortIdx);

            % Assign ranks 1..N
            for r = 1:numel(sortedResults)
                sortedResults(r).Rank = r;
            end

            results = sortedResults;
        end

        function evalRes = evaluateSingleApplication(app, elemList, c, thermoMetrics, mechMetrics, oxMetrics)
            % Evaluates an alloy against a single application definition
            evalRes = struct();
            evalRes.ID          = app.ID;
            evalRes.Name        = app.Name;
            evalRes.Sector      = app.Sector;
            evalRes.Description = app.Description;
            evalRes.Benchmark   = app.BenchmarkAlloy;
            evalRes.GitSource   = app.GitReference;

            % 1. Check Hard Vetoes
            vetoTriggered = false;
            vetoReason = '';

            % Elemental Veto Check
            if isfield(app, 'VetoElements') && ~isempty(app.VetoElements)
                vetoedElems = {};
                for i = 1:numel(elemList)
                    el = elemList{i};
                    if ismember(el, app.VetoElements) && c(i) > 0.005 % > 0.5 at%
                        vetoedElems{end+1} = sprintf('%s (%.1f at%%)', el, c(i)*100); %#ok<AGROW>
                    end
                end
                if ~isempty(vetoedElems)
                    vetoTriggered = true;
                    vetoReason = sprintf('Vetoed: Prohibited elements present: %s.', strjoin(vetoedElems, ', '));
                end
            end

            % Physical Property Hard Vetoes
            if ~vetoTriggered
                if isfield(app, 'MinSolidus_K') && isfield(thermoMetrics, 'Solidus_K')
                    if thermoMetrics.Solidus_K < app.MinSolidus_K
                        vetoTriggered = true;
                        vetoReason = sprintf('Vetoed: Solidus temperature (%.0f K) below minimum threshold (%.0f K).', ...
                            thermoMetrics.Solidus_K, app.MinSolidus_K);
                    end
                end
                if isfield(app, 'MinDuctility_pct') && isfield(mechMetrics, 'Elongation_RT_pct')
                    if mechMetrics.Elongation_RT_pct < app.MinDuctility_pct
                        vetoTriggered = true;
                        vetoReason = sprintf('Vetoed: Room-temperature ductility (%.1f%%) insufficient for cryogenic service (min %.1f%%).', ...
                            mechMetrics.Elongation_RT_pct, app.MinDuctility_pct);
                    end
                end
                if isfield(app, 'MaxModulus_GPa') && isfield(thermoMetrics, 'YoungsModulus_GPa')
                    if thermoMetrics.YoungsModulus_GPa > app.MaxModulus_GPa
                        vetoTriggered = true;
                        vetoReason = sprintf('Vetoed: Elastic modulus (%.0f GPa) causes severe bone stress-shielding (max %.0f GPa).', ...
                            thermoMetrics.YoungsModulus_GPa, app.MaxModulus_GPa);
                    end
                end
            end

            % 2. Extract Properties & Compute Continuous Utilities
            criteria = app.Criteria;
            nCrit = size(criteria, 1);
            critBreakdown = cell(nCrit, 1);
            weightedUtilitySum = 0.0;
            totalWeight = 0.0;

            lowestUtility = 1.0;
            bottleneckProp = 'None';
            bottleneckActual = 0.0;
            bottleneckTarget = 0.0;
            bottleneckUnit = '';

            for k = 1:nCrit
                propName  = criteria{k, 1};
                weight    = criteria{k, 2};
                direction = criteria{k, 3};
                threshold = criteria{k, 4};
                targetVal = criteria{k, 5};
                unitStr   = criteria{k, 6};

                actualVal = HEAApplicationScorer.extractPropertyValue(propName, elemList, c, thermoMetrics, mechMetrics, oxMetrics);

                % Continuous utility function u in [0, 1]
                u = HEAApplicationScorer.computeUtility(actualVal, direction, threshold, targetVal);

                critStruct = struct(...
                    'Property',    propName, ...
                    'Weight',      weight, ...
                    'Direction',   direction, ...
                    'Threshold',   threshold, ...
                    'Target',      targetVal, ...
                    'Actual',      actualVal, ...
                    'Utility',     round(u, 3), ...
                    'Unit',        unitStr);
                critBreakdown{k} = critStruct;

                weightedUtilitySum = weightedUtilitySum + weight * u;
                totalWeight = totalWeight + weight;

                if u < lowestUtility
                    lowestUtility = u;
                    bottleneckProp = propName;
                    bottleneckActual = actualVal;
                    bottleneckTarget = targetVal;
                    bottleneckUnit = unitStr;
                end
            end

            % 3. Calculate Final Composite Score
            if totalWeight > 0
                normalizedScore = (weightedUtilitySum / totalWeight) * 100.0;
            else
                normalizedScore = 0.0;
            end

            if vetoTriggered
                finalScore = 0.0;
            else
                finalScore = round(min(100.0, max(0.0, normalizedScore)), 1);
            end

            % 4. Match Tier Determination
            if vetoTriggered
                tier = 'Unsuitable';
                badge = 'DISQUALIFIED (VETO)';
                tierColor = [0.75, 0.20, 0.20]; % Red
            elseif finalScore >= 85.0
                tier = 'Prime Candidate';
                badge = 'PRIME CANDIDATE (SOTA)';
                tierColor = [0.12, 0.60, 0.32]; % Green
            elseif finalScore >= 70.0
                tier = 'Viable Candidate';
                badge = 'VIABLE CANDIDATE';
                tierColor = [0.15, 0.45, 0.85]; % Blue
            elseif finalScore >= 50.0
                tier = 'Conditional Candidate';
                badge = 'CONDITIONAL CANDIDATE';
                tierColor = [0.85, 0.55, 0.10]; % Amber
            else
                tier = 'Unsuitable';
                badge = 'POOR MATCH';
                tierColor = [0.55, 0.55, 0.55]; % Gray
            end

            % 5. Formulate Composition Tuning Advice
            tuningAdvice = HEAApplicationScorer.generateTuningAdvice(app.ID, bottleneckProp, bottleneckActual, bottleneckTarget, ...
                bottleneckUnit, vetoTriggered, vetoReason, elemList, c);

            % Populate return struct
            evalRes.Score_pct           = finalScore;
            evalRes.Tier                = tier;
            evalRes.Badge               = badge;
            evalRes.TierColor           = tierColor;
            evalRes.VetoTriggered       = vetoTriggered;
            evalRes.VetoReason          = vetoReason;
            evalRes.BottleneckProperty  = bottleneckProp;
            evalRes.BottleneckValue     = bottleneckActual;
            evalRes.BottleneckTarget    = bottleneckTarget;
            evalRes.BottleneckUnit      = bottleneckUnit;
            evalRes.BottleneckUtility   = round(lowestUtility, 3);
            evalRes.TuningAdvice        = tuningAdvice;
            evalRes.CriteriaBreakdown   = [critBreakdown{:}];
        end

        function u = computeUtility(x, direction, threshold, target)
            % Evaluates continuous satisfaction utility u in [0, 1]
            if isnan(x) || isinf(x)
                u = 0.0;
                return;
            end

            switch lower(direction)
                case 'max'
                    if x <= 0.5 * threshold
                        u = 0.05;
                    elseif x <= threshold
                        u = 0.10 + 0.30 * max(0.0, (x - 0.5 * threshold) / (0.5 * threshold));
                    elseif x >= target
                        u = 1.0;
                    else
                        % Linear / smooth ramp between threshold and target
                        u = 0.40 + 0.60 * ((x - threshold) / max(1e-9, target - threshold));
                    end

                case 'min'
                    if x >= 2.0 * threshold
                        u = 0.05;
                    elseif x >= threshold
                        u = 0.10 + 0.30 * max(0.0, (2.0 * threshold - x) / threshold);
                    elseif x <= target
                        u = 1.0;
                    else
                        % Ramp down from target (1.0) to threshold (0.4)
                        u = 0.40 + 0.60 * ((threshold - x) / max(1e-9, threshold - target));
                    end

                case 'target'
                    % Gaussian bell around target
                    sigma = max(0.1, abs(threshold - target));
                    u = exp(-0.5 * ((x - target) / sigma)^2);

                otherwise
                    u = 0.5;
            end

            u = min(1.0, max(0.0, u));
        end

        function val = extractPropertyValue(propName, elemList, c, thermoMetrics, mechMetrics, oxMetrics)
            % Maps abstract criterion property key to physical metric from engines
            switch propName
                case 'Solidus_K'
                    if isfield(thermoMetrics, 'T_Solidus') && ~isempty(thermoMetrics.T_Solidus)
                        val = double(thermoMetrics.T_Solidus);
                    elseif isfield(thermoMetrics, 'Solidus_K') && ~isempty(thermoMetrics.Solidus_K)
                        val = double(thermoMetrics.Solidus_K);
                    elseif isfield(thermoMetrics, 'Tm_avg') && ~isempty(thermoMetrics.Tm_avg)
                        val = double(thermoMetrics.Tm_avg);
                    elseif isfield(thermoMetrics, 'Tm') && ~isempty(thermoMetrics.Tm)
                        val = double(thermoMetrics.Tm);
                    else
                        val = 1600.0;
                    end

                case {'YieldStrength_800C', 'YieldStrength_HighT'}
                    val = 250.0;
                    if isfield(mechMetrics, 'TempCurve') && isfield(mechMetrics.TempCurve, 'T_C')
                        tArr = mechMetrics.TempCurve.T_C;
                        syArr = mechMetrics.TempCurve.YieldStrength_MPa;
                        val = interp1(tArr, syArr, 800.0, 'linear', 'extrap');
                    elseif isfield(mechMetrics, 'YieldStrength_RT_MPa')
                        val = mechMetrics.YieldStrength_RT_MPa * 0.45; % Estimation
                    end
                    val = max(10.0, round(val, 1));

                case {'YieldStrength_1200C', 'YieldStrength_1000C'}
                    val = 150.0;
                    if isfield(mechMetrics, 'TempCurve') && isfield(mechMetrics.TempCurve, 'T_C')
                        tArr = mechMetrics.TempCurve.T_C;
                        syArr = mechMetrics.TempCurve.YieldStrength_MPa;
                        val = interp1(tArr, syArr, 1200.0, 'linear', 'extrap');
                    elseif isfield(mechMetrics, 'YieldStrength_RT_MPa')
                        val = mechMetrics.YieldStrength_RT_MPa * 0.28;
                    end
                    val = max(10.0, round(val, 1));

                case 'YieldStrength_RT'
                    if isfield(mechMetrics, 'YieldStrength_RT_MPa')
                        val = double(mechMetrics.YieldStrength_RT_MPa);
                    else
                        val = 450.0;
                    end

                case 'UTS_RT_MPa'
                    if isfield(mechMetrics, 'UTS_RT_MPa')
                        val = double(mechMetrics.UTS_RT_MPa);
                    else
                        val = 700.0;
                    end

                case 'Elongation_pct'
                    if isfield(mechMetrics, 'Elongation_RT_pct')
                        val = double(mechMetrics.Elongation_RT_pct);
                    else
                        val = 25.0;
                    end

                case 'VickersHardness_HV'
                    if isfield(mechMetrics, 'VickersHardness_HV')
                        val = double(mechMetrics.VickersHardness_HV);
                    else
                        val = 220.0;
                    end

                case 'FractureToughness'
                    if isfield(mechMetrics, 'FractureToughness_MPa_m05')
                        val = double(mechMetrics.FractureToughness_MPa_m05);
                    else
                        val = 65.0;
                    end

                case 'Density_g_cm3'
                    if isfield(thermoMetrics, 'Density_g_cm3')
                        val = double(thermoMetrics.Density_g_cm3);
                    else
                        val = 8.0;
                    end

                case 'Oxidation_kp'
                    if isfield(oxMetrics, 'kp_g2_cm4_s')
                        val = double(oxMetrics.kp_g2_cm4_s);
                    else
                        val = 1e-11;
                    end

                case 'HighTempCreepLimit'
                    val = 220.0;
                    if isfield(mechMetrics, 'TempCurve') && isfield(mechMetrics.TempCurve, 'T_C')
                        tArr = mechMetrics.TempCurve.T_C;
                        syArr = mechMetrics.TempCurve.YieldStrength_MPa;
                        val = interp1(tArr, syArr, 850.0, 'linear', 'extrap');
                    end

                case 'PhaseStabilityFCC'
                    % Approximate FCC fraction from VEC: VEC >= 8.0 => 1.0 FCC
                    if isfield(thermoMetrics, 'VEC')
                        vec = thermoMetrics.VEC;
                        if vec >= 8.0
                            val = 1.0;
                        elseif vec <= 6.87
                            val = 0.05;
                        else
                            val = (vec - 6.87) / (8.0 - 6.87);
                        end
                    else
                        val = 0.5;
                    end

                case 'CorrosionRate_NaCl'
                    if isfield(thermoMetrics, 'Corrosion') && isfield(thermoMetrics.Corrosion, 'CR_mm_yr_NaCl')
                        val = double(thermoMetrics.Corrosion.CR_mm_yr_NaCl);
                    else
                        val = 0.01;
                    end

                case 'NeutronCrossSection'
                    % Weighted sum of thermal neutron capture cross sections (barns)
                    sigMap = HEAApplicationDatabase.getThermalNeutronCrossSections();
                    crossSecSum = 0.0;
                    for i = 1:numel(elemList)
                        el = elemList{i};
                        if isKey(sigMap, el)
                            crossSecSum = crossSecSum + c(i) * sigMap(el);
                        else
                            crossSecSum = crossSecSum + c(i) * 3.5; % Default moderate capture
                        end
                    end
                    val = round(crossSecSum, 3);

                case 'SwellingResistance'
                    % HEAs with higher lattice distortion (delta) and refractory elements resist radiation swelling
                    deltaVal = 0.03;
                    if isfield(thermoMetrics, 'delta'), deltaVal = thermoMetrics.delta; end
                    val = min(1.0, 0.4 + 10.0 * deltaVal);

                case 'BiocompatibilityScore'
                    toxMap = HEAApplicationDatabase.getBiocompatibilityMap();
                    safeFraction = 0.0;
                    for i = 1:numel(elemList)
                        el = elemList{i};
                        if isKey(toxMap, el)
                            rec = toxMap(el);
                            if rec.Safe
                                safeFraction = safeFraction + c(i);
                            end
                        end
                    end
                    val = round(safeFraction, 3);

                case 'YoungsModulus_GPa'
                    if isfield(thermoMetrics, 'YoungsModulus_GPa')
                        val = double(thermoMetrics.YoungsModulus_GPa);
                    else
                        val = 180.0;
                    end

                case 'PREN'
                    if isfield(thermoMetrics, 'Corrosion') && isfield(thermoMetrics.Corrosion, 'PREN_HEA')
                        val = double(thermoMetrics.Corrosion.PREN_HEA);
                    elseif isfield(thermoMetrics, 'Corrosion') && isfield(thermoMetrics.Corrosion, 'PREN_ASTM')
                        val = double(thermoMetrics.Corrosion.PREN_ASTM);
                    else
                        val = 20.0;
                    end

                case 'GalvanicImmunity'
                    if isfield(thermoMetrics, 'Corrosion') && isfield(thermoMetrics.Corrosion, 'PhaseImmunity')
                        val = double(thermoMetrics.Corrosion.PhaseImmunity);
                    else
                        val = 0.65;
                    end

                case 'ShearModulus_GPa'
                    if isfield(thermoMetrics, 'ShearModulus_GPa')
                        val = double(thermoMetrics.ShearModulus_GPa);
                    else
                        val = 75.0;
                    end

                case 'ThermalStability_K'
                    % Temperature where ordered phases remain stable
                    val = 1100.0;
                    if isfield(thermoMetrics, 'Solidus_K')
                        val = min(1300.0, thermoMetrics.Solidus_K * 0.65);
                    end

                case 'ThermalConductivity'
                    if isfield(thermoMetrics, 'ThermalConductivity_W_mK') && ~isempty(thermoMetrics.ThermalConductivity_W_mK)
                        val = double(thermoMetrics.ThermalConductivity_W_mK);
                    else
                        val = 25.0;
                        try
                            elemDb = HEAThermoEngine.getElementDatabase();
                            kSum = 0.0;
                            for ie = 1:numel(elemList)
                                if isKey(elemDb, elemList{ie})
                                    p = elemDb(elemList{ie});
                                    kSum = kSum + c(ie) * p.k0;
                                end
                            end
                            if kSum > 0, val = kSum; end
                        catch
                        end
                    end

                case {'ElasticModulus_GPa', 'YoungsModulus_GPa'}
                    if isfield(thermoMetrics, 'YoungsModulus_GPa') && ~isempty(thermoMetrics.YoungsModulus_GPa)
                        val = double(thermoMetrics.YoungsModulus_GPa);
                    else
                        val = 180.0;
                        try
                            mechDb = HEAMechanicalEngine.getElementMechanicalDatabase();
                            eSum = 0.0;
                            for ie = 1:numel(elemList)
                                if isKey(mechDb, elemList{ie})
                                    p = mechDb(elemList{ie});
                                    eSum = eSum + c(ie) * p.E_GPa;
                                end
                            end
                            if eSum > 0, val = eSum; end
                        catch
                        end
                    end

                case 'HydrogenAffinity'
                    % Fraction of strong hydride formers (Ti, Zr, V, Nb, Hf, Ta)
                    hydrideFormers = {'Ti', 'Zr', 'V', 'Nb', 'Hf', 'Ta', 'Mg', 'La', 'Y'};
                    hFrac = 0.0;
                    for i = 1:numel(elemList)
                        if ismember(elemList{i}, hydrideFormers)
                            hFrac = hFrac + c(i);
                        end
                    end
                    val = round(hFrac, 3);

                case 'BCC_PhaseFraction'
                    if isfield(thermoMetrics, 'VEC')
                        if thermoMetrics.VEC < 6.87
                            val = 1.0;
                        elseif thermoMetrics.VEC >= 8.0
                            val = 0.0;
                        else
                            val = (8.0 - thermoMetrics.VEC) / (8.0 - 6.87);
                        end
                    else
                        val = 0.5;
                    end

                case 'LatticeExpansion'
                    deltaVal = 0.04;
                    if isfield(thermoMetrics, 'delta'), deltaVal = thermoMetrics.delta; end
                    val = deltaVal;

                case 'ElectrocatalyticActivity'
                    % Transition metals count and VEC optimality
                    actElems = {'Fe', 'Co', 'Ni', 'Mo', 'Cr', 'W', 'V', 'Mn'};
                    actCount = sum(ismember(elemList, actElems));
                    val = min(1.0, 0.4 + 0.12 * actCount);

                case 'TransitionMetalCount'
                    tMetals = {'Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Y','Zr','Nb','Mo','Hf','Ta','W','Re'};
                    val = sum(ismember(elemList, tMetals));

                case 'PBR_Stability'
                    if isfield(thermoMetrics, 'Corrosion') && isfield(thermoMetrics.Corrosion, 'PBR_eff')
                        pbr = thermoMetrics.Corrosion.PBR_eff;
                        % Ideal PBR between 1.2 and 1.8
                        if pbr >= 1.2 && pbr <= 1.8
                            val = 1.0;
                        else
                            val = max(0.2, 1.0 - 0.8 * abs(pbr - 1.5));
                        end
                    else
                        val = 0.8;
                    end

                case 'VEC'
                    if isfield(thermoMetrics, 'VEC')
                        val = double(thermoMetrics.VEC);
                    else
                        val = 7.5;
                    end

                otherwise
                    val = 0.5;
            end
        end

        function advice = generateTuningAdvice(appId, bottleneckProp, actualVal, targetVal, unitStr, isVeto, vetoReason, elemList, c)
            % Formulates specific metallurgical recommendations based on bottleneck property
            if isVeto
                advice = sprintf('Disqualification remediation: %s Restructure elemental formulation to eliminate prohibited elements.', vetoReason);
                return;
            end

            switch bottleneckProp
                case 'Solidus_K'
                    advice = sprintf('Solidus temperature is low (%.0f K vs target %.0f %s). Substitute lower-melting components with refractory elements (Nb, Mo, Ta, W, or Cr).', ...
                        actualVal, targetVal, unitStr);

                case 'YieldStrength_800C'
                    advice = sprintf('High-temperature strength is marginal (%.0f MPa vs target %.0f %s). Add 8-12 at%% Al or Ti to trigger B2 or gamma-prime precipitation hardening, or add Mo/W to retard dislocation climb.', ...
                        actualVal, targetVal, unitStr);

                case 'YieldStrength_1200C'
                    advice = sprintf('Ultra-high temperature strength at 1200 °C is insufficient (%.0f MPa vs target %.0f %s). Restructure system using refractory group V/VI metals (Mo, W, Ta, Nb) with high shear moduli.', ...
                        actualVal, targetVal, unitStr);

                case 'Density_g_cm3'
                    advice = sprintf('Density is too high for weight-critical application (%.2f g/cm^3 vs target %.2f %s). Decrease high-density elements (W, Ta, Mo, Hf) and alloy with Al, Ti, Cr, or V.', ...
                        actualVal, targetVal, unitStr);

                case 'Oxidation_kp'
                    advice = sprintf('Parabolic oxidation rate is high (%.2e vs target %.2e %s). Increase Al content >= 12 at%% to transition to protective alpha-Al2O3 scale, or increase Cr >= 18 at%% for chromia.', ...
                        actualVal, targetVal, unitStr);

                case 'FractureToughness'
                    advice = sprintf('Fracture toughness is low (%.1f MPa*m^0.5 vs target %.1f %s). Increase FCC-stabilizing elements (Ni, Co, Fe) to elevate the Pugh ratio B/G and eliminate brittle BCC/intermetallic cleavage.', ...
                        actualVal, targetVal, unitStr);

                case 'Elongation_pct'
                    advice = sprintf('Tensile elongation is limited (%.1f%% vs target %.1f %s). Suppress brittle B2 or sigma phases by reducing Al or Cr content below their precipitation solvus.', ...
                        actualVal, targetVal, unitStr);

                case 'VickersHardness_HV'
                    advice = sprintf('Hardness is below tooling requirement (%.0f HV vs target %.0f %s). Elevate Al/Ti to promote ordered B2/L12 intermetallic phases and maximize atomic size mismatch delta.', ...
                        actualVal, targetVal, unitStr);

                case 'PREN'
                    advice = sprintf('Pitting Resistance Equivalent is low (%.1f vs target %.1f %s). Enrich system with Cr (>= 20 at%%), Mo (>= 3 at%%), or W to strengthen the passive oxyhydroxide film.', ...
                        actualVal, targetVal, unitStr);

                case 'YoungsModulus_GPa'
                    advice = sprintf('Elastic modulus is too stiff for bone matching (%.0f GPa vs target %.0f %s). Favor beta-Ti stabilizers (Nb, Ta, Zr, Mo) with open BCC lattices to suppress modulus below 75 GPa.', ...
                        actualVal, targetVal, unitStr);

                case 'NeutronCrossSection'
                    advice = sprintf('Thermal neutron capture is too high (%.2f barns vs target %.2f %s). Eliminate or replace Co (37 b), Hf (104 b), or Ta (21 b) with Zr (0.18 b), Al (0.23 b), or Fe.', ...
                        actualVal, targetVal, unitStr);

                case 'CorrosionRate_NaCl'
                    advice = sprintf('Aqueous corrosion rate in 3.5%% NaCl is elevated (%.4f mm/yr vs target %.4f %s). Eliminate micro-galvanic segregation and ensure single-phase solid solution stability.', ...
                        actualVal, targetVal, unitStr);

                otherwise
                    advice = sprintf('Optimize alloy stoichiometry to raise the lowest property (%s = %.2f %s) toward the target of %.2f %s.', ...
                        bottleneckProp, actualVal, unitStr, targetVal, unitStr);
            end
        end

    end
end
