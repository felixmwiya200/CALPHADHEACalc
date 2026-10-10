% test_git_database_integrations.m
% Comprehensive Verification Test for Git Database Integrations:
% 1. Vladimirchizh/hea_database: 12,427+ peer-reviewed experimental HEA records
% 2. OpenCALPHAD / NIST assessed multicomponent .TDB files (Al-Co-Cr-Fe-Ni & COST507)
% 3. Friedel-Eshelby elastic strain enthalpy (MiedCalc / Prog. Mater. Sci. model)
% 4. End-to-end integration into HEAThermoEngine and MaterialPropertiesApp

fprintf('========================================================================\n');
fprintf('  STARTING GIT DATABASE & ADVANCED THERMODYNAMICS VERIFICATION TEST\n');
fprintf('========================================================================\n\n');

numPass = 0;
numFail = 0;

function check(cond, testName, detailStr)
    if cond
        fprintf('  [PASS] %s\n', testName);
        if nargin >= 3 && ~isempty(detailStr)
            fprintf('         %s\n', detailStr);
        end
    else
        fprintf('  [FAIL] %s\n', testName);
        if nargin >= 3 && ~isempty(detailStr)
            fprintf('         ERROR: %s\n', detailStr);
        end
        error('Assertion failed: %s', testName);
    end
end

try
    %% TEST 1: Experimental HEA Database Loading (12,427 Records)
    fprintf('--- TEST 1: Peer-Reviewed Experimental HEA Database (12,427 Records) ---\n');
    db = HEAExperimentalDatabase.getInstance();
    check(db.IsLoaded, 'Database Singleton Loaded', sprintf('Loaded %d records from %s', db.RowCount, db.CSV_FILE));
    check(db.RowCount >= 12400, 'Database Record Count Check', sprintf('Total rows: %d', db.RowCount));
    numPass = numPass + 2;

    %% TEST 2: Fast Query Matching for AlCoCrFeNi, Cantor, and RHEA
    fprintf('\n--- TEST 2: Fast Inverted-Index Query for Benchmark Alloys ---\n');
    tic;
    q1 = HEAExperimentalDatabase.query({'Al', 'Co', 'Cr', 'Fe', 'Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
    tQuery1 = toc;
    check(q1.Matched, 'AlCoCrFeNi Matched in Database', ...
        sprintf('Found %d studies in %.3f ms. Observed Phase: "%s", DOI: "%s"', ...
        q1.TotalMatches, tQuery1 * 1000, q1.ObservedPhases, q1.DOI));
    check(q1.TotalMatches >= 500, 'AlCoCrFeNi Rich Match Count', sprintf('Matches: %d', q1.TotalMatches));

    tic;
    q2 = HEAExperimentalDatabase.query({'Co', 'Cr', 'Fe', 'Mn', 'Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
    tQuery2 = toc;
    check(q2.Matched, 'Cantor CoCrFeMnNi Matched in Database', ...
        sprintf('Found %d studies in %.3f ms. Observed Phase: "%s", DOI: "%s"', ...
        q2.TotalMatches, tQuery2 * 1000, q2.ObservedPhases, q2.DOI));

    tic;
    q3 = HEAExperimentalDatabase.query({'Nb', 'Mo', 'Ta', 'W'}, [0.25, 0.25, 0.25, 0.25]);
    tQuery3 = toc;
    check(q3.Matched, 'Refractory NbMoTaW Matched in Database', ...
        sprintf('Found %d studies in %.3f ms. Observed Phase: "%s"', ...
        q3.TotalMatches, tQuery3 * 1000, q3.ObservedPhases));
    numPass = numPass + 4;

    %% TEST 3: Friedel-Eshelby Elastic Strain Enthalpy Formulation
    fprintf('\n--- TEST 3: Friedel-Eshelby Elastic Strain Enthalpy Formulation ---\n');
    [dH_strain_cantor, ~] = HEAThermoEngine.computeElasticStrainEnthalpy({'Co','Cr','Fe','Mn','Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
    [dH_strain_alhea, ~]  = HEAThermoEngine.computeElasticStrainEnthalpy({'Al','Co','Cr','Fe','Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
    [dH_strain_refract, ~] = HEAThermoEngine.computeElasticStrainEnthalpy({'Ti','Zr','Hf','Nb','Ta'}, [0.2, 0.2, 0.2, 0.2, 0.2]);

    fprintf('         Cantor CoCrFeMnNi Strain Enthalpy:   %.3f kJ/mol\n', dH_strain_cantor);
    fprintf('         AlCoCrFeNi Strain Enthalpy:          %.3f kJ/mol\n', dH_strain_alhea);
    fprintf('         Refractory TiZrHfNbTa Strain Enthalpy: %.3f kJ/mol\n', dH_strain_refract);

    check(dH_strain_cantor >= 0 && dH_strain_cantor < 3.0, ...
        'Cantor Alloy Low Strain Check', sprintf('Cantor size mismatch strain is low: %.3f kJ/mol', dH_strain_cantor));
    check(dH_strain_alhea > dH_strain_cantor, ...
        'Al Addition Strain Increase Check', sprintf('Al increases strain enthalpy to %.3f kJ/mol due to larger molar volume', dH_strain_alhea));
    check(dH_strain_refract > 0, ...
        'Refractory HEA Positive Strain Check', sprintf('TiZrHfNbTa strain: %.3f kJ/mol', dH_strain_refract));
    numPass = numPass + 3;

    %% TEST 4: OpenCALPHAD .TDB Parser & Parameter Overlay
    fprintf('\n--- TEST 4: OpenCALPHAD .TDB Database Parser & Overlays ---\n');
    HEAThermoEngine.clearCustomTDB();
    tdbFile1 = 'App/databases/OpenCALPHAD_Al_Co_Cr_Fe_Ni.tdb';
    check(isfile(tdbFile1), 'TDB File Exists Check', tdbFile1);
    
    info1 = HEAThermoEngine.importTDB(tdbFile1);
    check(info1.Loaded, 'OpenCALPHAD Al-Co-Cr-Fe-Ni TDB Ingestion', ...
        sprintf('Parsed %d binary parameters, %d ternary parameters across %d phases', ...
        info1.BinaryCount, info1.TernaryCount, numel(info1.Phases)));
    check(info1.BinaryCount >= 20, 'Binary Parameter Count in TDB', sprintf('Count: %d', info1.BinaryCount));
    check(info1.TernaryCount >= 8, 'Ternary Parameter Count in TDB', sprintf('Count: %d', info1.TernaryCount));

    % Verify overlay into Redlich-Kister parameter map
    rk = HEAThermoEngine.getRedlichKisterParameters();
    check(isKey(rk, 'LIQUID_Al_Co'), 'Imported Binary Parameter Active in RK Map');
    valRk = rk('LIQUID_Al_Co');
    fprintf('         LIQUID_Al_Co L0 = %.1f J/mol\n', valRk(1,1));
    
    % Verify overlay into Ternary parameter map
    ter = HEAThermoEngine.getTernaryInteractionParameters();
    check(isKey(ter, 'FCC_A1_Al_Co_Ni'), 'Imported Ternary Parameter Active in Ternary Map');
    valTer = ter('FCC_A1_Al_Co_Ni');
    fprintf('         FCC_A1_Al_Co_Ni L_ijk = %.1f J/mol\n', valTer(1));

    % Ingest COST 507 Light Alloys TDB
    tdbFile2 = 'App/databases/COST507_LightAlloys.tdb';
    info2 = HEAThermoEngine.importTDB(tdbFile2);
    check(info2.Loaded, 'COST 507 Light Alloys TDB Ingestion', ...
        sprintf('Parsed %d binary parameters, %d ternary parameters', info2.BinaryCount, info2.TernaryCount));
    numPass = numPass + 6;

    %% TEST 5: End-to-End Multicomponent Thermodynamics with Database Validation
    fprintf('\n--- TEST 5: End-to-End Thermodynamic Calculation with Experimental Validation ---\n');
    m1 = HEAThermoEngine.computeThermodynamics({'Al','Co','Cr','Fe','Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
    check(isfield(m1, 'CALPHAD'), 'CALPHAD Struct Present', m1.CALPHAD.StablePhase);
    check(isfield(m1, 'DeltaH_chem'), 'DeltaH_chem Present', sprintf('%.2f kJ/mol', m1.DeltaH_chem));
    check(isfield(m1, 'DeltaH_elastic'), 'DeltaH_elastic Present', sprintf('%.2f kJ/mol', m1.DeltaH_elastic));
    check(isfield(m1, 'DeltaH_total'), 'DeltaH_total Present', sprintf('%.2f kJ/mol', m1.DeltaH_total));
    check(isfield(m1, 'ExperimentalValidation'), 'ExperimentalValidation Present', ...
        sprintf('Matched: %d, Total: %d, Phase: "%s", DOI: "%s"', ...
        m1.ExperimentalValidation.Matched, m1.ExperimentalValidation.TotalMatches, ...
        m1.ExperimentalValidation.ObservedPhases, m1.ExperimentalValidation.DOI));
    check(m1.ExperimentalValidation.Matched == true, 'Experimental Database Matched Truth Value', 'Confirmed match');

    % Cantor alloy end-to-end
    m2 = HEAThermoEngine.computeThermodynamics({'Co','Cr','Fe','Mn','Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
    check(m2.ExperimentalValidation.Matched == true, 'Cantor Experimental Validation', ...
        sprintf('Observed Phase: "%s", Total Matches: %d', ...
        m2.ExperimentalValidation.ObservedPhases, m2.ExperimentalValidation.TotalMatches));
    numPass = numPass + 7;

    fprintf('\n========================================================================\n');
    fprintf('  ALL %d TESTS PASSED! Git Databases and TDB Engine 100%% Operational.\n', numPass);
    fprintf('========================================================================\n');

catch ME
    numFail = numFail + 1;
    fprintf('\nERROR in Test Execution:\n%s\n', ME.message);
    if ~isempty(ME.stack)
        for s = 1:numel(ME.stack)
            fprintf('  in %s at line %d\n', ME.stack(s).name, ME.stack(s).line);
        end
    end
end
