% test_hea_applications_engine.m - Comprehensive Verification of HEA Applications Engine
function test_hea_applications_engine()
    fprintf('=================================================================\n');
    fprintf('    TESTING HEA APPLICATIONS DATABASE & SCORING ENGINE IN MATLAB\n');
    fprintf('=================================================================\n\n');

    % Test 1: Database Catalog Integrity
    fprintf('--- Test 1: HEA Application Database Integrity ---\n');
    apps = HEAApplicationDatabase.getAllApplications();
    assert(numel(apps) == 10, sprintf('Expected 10 curated applications, found %d.', numel(apps)));
    
    sectors = HEAApplicationDatabase.getSectors();
    assert(~isempty(sectors), 'Sector list must not be empty.');
    fprintf('  Verified 10 applications across %d engineering sectors:\n', numel(sectors));
    for s = 1:numel(sectors)
        fprintf('    - Sector: %s\n', sectors{s});
    end

    % Verify criteria weights sum to 1.0 for all applications
    for i = 1:numel(apps)
        if iscell(apps)
            app = apps{i};
        else
            app = apps(i);
        end
        assert(~isempty(app.ID), 'Application ID cannot be empty');
        assert(~isempty(app.Name), 'Application Name cannot be empty');
        assert(~isempty(app.Criteria), 'Application Criteria cannot be empty');
        
        weights = cell2mat(app.Criteria(:, 2));
        wSum = sum(weights);
        assert(abs(wSum - 1.0) < 1e-4, sprintf('Weights for application %s must sum to 1.0, got %.4f', app.ID, wSum));
    end
    fprintf('  All 10 applications have normalized criteria weights summing to 1.0.\n');

    % Test 2: Cantor Equiatomic Alloy (CoCrFeMnNi) Evaluation
    fprintf('\n--- Test 2: Cantor Equiatomic Alloy (CoCrFeMnNi) Benchmark ---\n');
    cantorElems = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    cantorFracs = [0.2, 0.2, 0.2, 0.2, 0.2];

    thermoCantor = HEAThermoEngine.computeThermodynamics(cantorElems, cantorFracs);
    mechCantor   = HEAMechanicalEngine.computeMechanicalProperties(cantorElems, cantorFracs, thermoCantor);
    oxCantor     = HEAOxidationEngine.computeOxidationKinetics(cantorElems, cantorFracs, thermoCantor);

    scoresCantor = HEAApplicationScorer.scoreAlloy(cantorElems, cantorFracs, thermoCantor, mechCantor, oxCantor);
    assert(numel(scoresCantor) == 10, 'Must return evaluation for all 10 applications.');

    % Display Cantor rankings
    fprintf('  Cantor Alloy Application Rankings:\n');
    for r = 1:numel(scoresCantor)
        res = scoresCantor(r);
        fprintf('    #%2d: %-42s | Score: %5.1f%% | Tier: %-20s\n', ...
            res.Rank, res.Name, res.Score_pct, res.Tier);
    end

    % Cryogenic LNG Vessel should be the top match or >= 85%
    cryoIdx = find(strcmp({scoresCantor.ID}, 'CRYO_LNG_VESSEL'), 1);
    assert(~isempty(cryoIdx), 'CRYO_LNG_VESSEL must be evaluated.');
    cryoScore = scoresCantor(cryoIdx);
    assert(cryoScore.Score_pct >= 85.0, sprintf('Cantor cryogenic score must be >= 85%%, got %.1f%%', cryoScore.Score_pct));
    assert(strcmp(cryoScore.Tier, 'Prime Candidate'), 'Cantor must be Prime Candidate for Cryogenic LNG Vessels.');
    fprintf('  Cryogenic application correctly scored as Prime Candidate (%.1f%%)!\n', cryoScore.Score_pct);

    % Biomedical Orthopedic Implant must be VETOED due to Co and Ni
    bioIdx = find(strcmp({scoresCantor.ID}, 'BIOMED_ORTHO_IMPLANT'), 1);
    assert(~isempty(bioIdx), 'BIOMED_ORTHO_IMPLANT must be evaluated.');
    bioScore = scoresCantor(bioIdx);
    assert(bioScore.VetoTriggered, 'Cantor alloy must trigger hard veto for biomedical implant.');
    assert(bioScore.Score_pct == 0.0, 'Disqualified application score must be exactly 0.0%.');
    assert(contains(bioScore.VetoReason, 'Ni') && contains(bioScore.VetoReason, 'Co'), ...
        'Veto reason must cite prohibited Ni and Co.');
    fprintf('  Biomedical veto successfully enforced: Score = 0%% (%s)\n', bioScore.VetoReason);

    % Test 3: Tooling Alloy Al1.0CoCrFeNi Evaluation
    fprintf('\n--- Test 3: Wear-Resistant Alloy Al1.0CoCrFeNi Benchmark ---\n');
    al1Elems = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    al1Fracs = [0.2, 0.2, 0.2, 0.2, 0.2];

    thermoAl1 = HEAThermoEngine.computeThermodynamics(al1Elems, al1Fracs);
    mechAl1   = HEAMechanicalEngine.computeMechanicalProperties(al1Elems, al1Fracs, thermoAl1);
    oxAl1     = HEAOxidationEngine.computeOxidationKinetics(al1Elems, al1Fracs, thermoAl1);

    scoresAl1 = HEAApplicationScorer.scoreAlloy(al1Elems, al1Fracs, thermoAl1, mechAl1, oxAl1);

    toolingIdx = find(strcmp({scoresAl1.ID}, 'TOOLING_HOT_DIE'), 1);
    assert(~isempty(toolingIdx), 'TOOLING_HOT_DIE must be present.');
    toolingScore = scoresAl1(toolingIdx);
    assert(toolingScore.Score_pct >= 75.0, sprintf('Al1.0 tooling score must be >= 75%%, got %.1f%%', toolingScore.Score_pct));
    fprintf('  Tooling & Hot Die application scored %.1f%% (%s) with Hardness %d HV!\n', ...
        toolingScore.Score_pct, toolingScore.Tier, mechAl1.VickersHardness_HV);

    % Test 4: Refractory RHEA (NbMoTaW) for High-Temperature Furnaces
    fprintf('\n--- Test 4: Refractory RHEA (NbMoTaW) Ultra-High Temp Benchmark ---\n');
    rheaElems = {'Nb', 'Mo', 'Ta', 'W'};
    rheaFracs = [0.25, 0.25, 0.25, 0.25];

    thermoRhea = HEAThermoEngine.computeThermodynamics(rheaElems, rheaFracs);
    mechRhea   = HEAMechanicalEngine.computeMechanicalProperties(rheaElems, rheaFracs, thermoRhea);
    oxRhea     = HEAOxidationEngine.computeOxidationKinetics(rheaElems, rheaFracs, thermoRhea);

    scoresRhea = HEAApplicationScorer.scoreAlloy(rheaElems, rheaFracs, thermoRhea, mechRhea, oxRhea);

    furnaceIdx = find(strcmp({scoresRhea.ID}, 'REFRACTORY_FURNACE'), 1);
    assert(~isempty(furnaceIdx), 'REFRACTORY_FURNACE must be present.');
    furnaceScore = scoresRhea(furnaceIdx);
    assert(furnaceScore.Score_pct >= 75.0, sprintf('NbMoTaW furnace score must be >= 75%%, got %.1f%%', furnaceScore.Score_pct));
    fprintf('  Refractory Vacuum Furnace application scored %.1f%% (%s) with Solidus %.0f K!\n', ...
        furnaceScore.Score_pct, furnaceScore.Tier, thermoRhea.T_Solidus);

    % Test 5: Biocompatible Bio-HEA (TiZrNbTa) Evaluation
    fprintf('\n--- Test 5: Biocompatible Bio-HEA (TiZrNbTa) Validation ---\n');
    bioElems = {'Ti', 'Zr', 'Nb', 'Ta'};
    bioFracs = [0.25, 0.25, 0.25, 0.25];

    thermoBio = HEAThermoEngine.computeThermodynamics(bioElems, bioFracs);
    mechBio   = HEAMechanicalEngine.computeMechanicalProperties(bioElems, bioFracs, thermoBio);
    oxBio     = HEAOxidationEngine.computeOxidationKinetics(bioElems, bioFracs, thermoBio);

    scoresBio = HEAApplicationScorer.scoreAlloy(bioElems, bioFracs, thermoBio, mechBio, oxBio);

    bioOrthoIdx = find(strcmp({scoresBio.ID}, 'BIOMED_ORTHO_IMPLANT'), 1);
    assert(~isempty(bioOrthoIdx), 'BIOMED_ORTHO_IMPLANT must be present.');
    bioOrthoScore = scoresBio(bioOrthoIdx);
    assert(~bioOrthoScore.VetoTriggered, 'Biocompatible TiZrNbTa must NOT trigger any hard veto.');
    assert(bioOrthoScore.Score_pct >= 75.0, sprintf('TiZrNbTa orthopedic score must be >= 75%%, got %.1f%%', bioOrthoScore.Score_pct));
    fprintf('  Orthopedic Implant application scored %.1f%% (%s) with zero toxic elements!\n', ...
        bioOrthoScore.Score_pct, bioOrthoScore.Tier);

    % Test 6: Bottleneck Diagnostics & Tuning Advice Validation
    fprintf('\n--- Test 6: Bottleneck Diagnostics & Metallurgical Tuning Advice ---\n');
    for i = 1:min(3, numel(scoresCantor))
        res = scoresCantor(i);
        assert(~isempty(res.BottleneckProperty), 'Bottleneck property must be identified.');
        assert(~isempty(res.TuningAdvice), 'Tuning advice must be generated.');
        fprintf('  App: %-32s | Bottleneck: %-18s | Advice: %s\n', ...
            res.Name, res.BottleneckProperty, res.TuningAdvice(1:min(70, length(res.TuningAdvice))));
    end

    fprintf('\n=================================================================\n');
    fprintf('    ALL HEA APPLICATION DATABASE & SCORER TESTS PASSED (100%%)    \n');
    fprintf('=================================================================\n');
end
