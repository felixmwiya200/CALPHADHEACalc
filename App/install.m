function install()
% =========================================================================
%   CALPHADHEACalc: Software Installation & Path Configuration (MATLAB)
%   Authors: Felix Mwiya & Prof. (Dr.) Sheela Singh
%   Affiliation: Department of Mechanical Engineering, SRM University-AP (2026)
% =========================================================================

    fprintf('=============================================================================\n');
    fprintf('  CALPHADHEACalc: Software Installation & Path Configuration (MATLAB)        \n');
    fprintf('  Authors: Felix Mwiya & Prof. (Dr.) Sheela Singh, SRM University-AP (2026)  \n');
    fprintf('=============================================================================\n\n');

    scriptPath = fileparts(mfilename('fullpath'));
    appPath = fullfile(scriptPath, 'App');
    dataPath = fullfile(scriptPath, 'materials_data');
    scriptsPath = fullfile(scriptPath, 'scripts');

    fprintf('[1/4] Registering CALPHADHEACalc directories in MATLAB search path...\n');
    addpath(scriptPath);
    if exist(appPath, 'dir')
        addpath(genpath(appPath));
    end
    if exist(dataPath, 'dir')
        addpath(genpath(dataPath));
    end
    if exist(scriptsPath, 'dir')
        addpath(scriptsPath);
    end

    % Safe path saving to user directory or system path
    saved = false;
    try
        uPath = userpath;
        if ~isempty(uPath)
            uParts = split(uPath, pathsep);
            uDir = uParts{1};
            if exist(uDir, 'dir')
                targetPathDef = fullfile(uDir, 'pathdef.m');
                res = savepath(targetPathDef);
                if res == 0
                    fprintf('  [SUCCESS] Permanent MATLAB search path saved to: %s\n', targetPathDef);
                    saved = true;
                end
            end
        end
    catch
    end

    if ~saved
        try
            res = savepath();
            if res == 0
                fprintf('  [SUCCESS] Permanent MATLAB search path saved.\n');
                saved = true;
            end
        catch
        end
    end

    if ~saved
        fprintf('  [NOTICE] Search path configured for current session. (To save permanently, run savepath as Administrator).\n');
    end
    fprintf('\n');

    fprintf('[2/4] Verifying thermodynamic and physics calculation modules...\n');
    requiredClasses = {
        'CALPHADHEACalc', 'Main App Designer CAE Interface';
        'HEAThermoEngine', 'CALPHAD & Miedema Thermodynamic Core';
        'HEAMechanicalEngine', 'Varvenne-Curtin & Hall-Petch Strength Engine';
        'HEAOxidationEngine', 'Wagner Parabolic & Ellingham Oxidation Engine';
        'HEAXRDEngine', 'Bragg-Brentano Kinematic XRD Diffraction Engine';
        'CALPHADHeadlessSolver', 'Decoupled Numerical Worker';
        'CALPHADFluentLogger', 'ANSYS Fluent Convergence Logging Engine';
        'HEAApplicationScorer', 'Multi-Criteria Industrial Application Scorer'
    };

    allPassed = true;
    for i = 1:size(requiredClasses, 1)
        cls = requiredClasses{i, 1};
        desc = requiredClasses{i, 2};
        if exist(cls, 'class') == 8 || exist(cls, 'file') == 2
            fprintf('  [OK] %-24s : %s\n', cls, desc);
        else
            fprintf('  [FAIL] %-22s : NOT FOUND (%s)\n', cls, desc);
            allPassed = false;
        end
    end
    fprintf('\n');

    fprintf('[3/4] Running automated engine self-test...\n');
    try
        metrics = HEAThermoEngine.computeThermodynamics({'Al', 'Co', 'Cr', 'Fe', 'Ni'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
        fprintf('  [PASS] Thermodynamic Enthalpy Calculation: H_mix = %.2f kJ/mol, Solidus = %.1f K, Liquidus = %.1f K\n', ...
            metrics.DeltaHmix, metrics.T_Solidus, metrics.T_Liquidus);
    catch ME
        fprintf('  [FAIL] Engine self-test encountered an error: %s\n', ME.message);
        allPassed = false;
    end
    fprintf('\n');

    fprintf('[4/4] Installation Summary\n');
    if allPassed
        fprintf('=============================================================================\n');
        fprintf('  CALPHADHEACalc v3.4.0 is successfully installed and verified!\n');
        fprintf('  \n');
        fprintf('  HOW TO LAUNCH:\n');
        fprintf('  >> CALPHADHEACalc                    %% Launches full interactive GUI\n');
        fprintf('  >> CALPHADHEACalc(''Cantor'')           %% Launches with Cantor alloy preset\n');
        fprintf('  >> CALPHADHEACalc(''Al0.3CoCrFeNi'')   %% Launches with Al0.3CoCrFeNi preset\n');
        fprintf('=============================================================================\n\n');
    else
        fprintf('  Installation completed with warnings. Please review the missing modules above.\n\n');
    end
end
