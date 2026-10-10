% fit_piecewise_functions.m
% Reads tabular .dat files, applies physics-based SI scaling and unified melting point,
% and outputs precise COMSOL Multiphysics piecewise definitions.

clear; clc; close all;

if exist('materials_data', 'dir')
    data_folder = 'materials_data';
elseif exist(fullfile('..', 'materials_data'), 'dir')
    data_folder = fullfile('..', 'materials_data');
else
    data_folder = 'materials_data';
end
dat_files = dir(fullfile(data_folder, '*.dat'));

% Filter out example files
dat_files = dat_files(~startsWith({dat_files.name}, 'sample') & ~startsWith({dat_files.name}, 'example'));

if isempty(dat_files)
    disp('No material .dat files found.');
    return;
end

for k = 1:length(dat_files)
    filename = fullfile(data_folder, dat_files(k).name);
    [~, mat_name, ~] = fileparts(filename);
    
    opts = detectImportOptions(filename, 'Delimiter', '\t');
    opts.VariableNamingRule = 'preserve';
    try
        data = readtable(filename, opts);
        for i = 1:width(data)
            if iscell(data{:,i})
                data{:,i} = str2double(data{:,i});
            end
        end
    catch ME
        warning('Could not read %s.', dat_files(k).name);
        continue;
    end
    
    vNames = data.Properties.VariableNames;
    
    % Standardize Thermal Expansion name
    expIdx = find(contains(vNames, 'Linear expansion', 'IgnoreCase', true));
    if ~isempty(expIdx)
        vNames{expIdx(1)} = 'Coefficient of thermal expansion (%)';
    end
    
    % Dynamic Viscosity: Average Total and Liquid Viscosity if both present
    totViscIdx = find(contains(vNames, 'Total viscosity', 'IgnoreCase', true));
    liqViscIdx = find(contains(vNames, 'Liquid viscosity', 'IgnoreCase', true));
    
    if ~isempty(totViscIdx)
        if ~isempty(liqViscIdx)
            totVals = data{:, totViscIdx(1)};
            liqVals = data{:, liqViscIdx(1)};
            avgVals = totVals;
            bothValid = ~isnan(totVals) & ~isnan(liqVals) & (totVals > 0) & (liqVals > 0);
            avgVals(bothValid) = (totVals(bothValid) + liqVals(bothValid)) / 2;
            data{:, totViscIdx(1)} = avgVals;
            
            data(:, liqViscIdx(1)) = [];
            vNames = data.Properties.VariableNames;
            totViscIdx = find(contains(vNames, 'Total viscosity', 'IgnoreCase', true));
        end
        vNames{totViscIdx(1)} = 'Dynamic viscosity (Pa*s)';
    elseif ~isempty(liqViscIdx)
        vNames{liqViscIdx(1)} = 'Dynamic viscosity (Pa*s)';
    end
    
    % Unit Scaling to SI for COMSOL
    % Density: g/cm^3 -> kg/m^3 (* 1000)
    rhoIdx = find(contains(vNames, 'Density', 'IgnoreCase', true));
    if ~isempty(rhoIdx)
        data{:, rhoIdx(1)} = data{:, rhoIdx(1)} * 1000;
        vNames{rhoIdx(1)} = 'Density (kg/m^3)';
    end
    
    % Viscosity: mPa*s -> Pa*s (/ 1000)
    viscIdx = find(contains(vNames, 'Dynamic viscosity', 'IgnoreCase', true));
    if ~isempty(viscIdx)
        data{:, viscIdx(1)} = data{:, viscIdx(1)} / 1000;
    end
    
    % Surface Tension: mN/m -> N/m (/ 1000)
    stIdx = find(contains(vNames, 'Surface Tension', 'IgnoreCase', true));
    if ~isempty(stIdx)
        data{:, stIdx(1)} = data{:, stIdx(1)} / 1000;
        vNames{stIdx(1)} = 'Surface Tension (N/m)';
    end
    
    % Young's Modulus: GPa -> Pa (* 1e9)
    ymIdx = find(contains(vNames, 'Young', 'IgnoreCase', true));
    if ~isempty(ymIdx)
        data{:, ymIdx(1)} = data{:, ymIdx(1)} * 1e9;
        vNames{ymIdx(1)} = 'Young''s modulus (Pa)';
    end
    
    % Compute temperature-dependent electrical resistivity and laser absorptivity (lambda = 1.064 um)
    T_all = data{:, 1};
    resIdx = find(contains(vNames, 'Electrical resistivity', 'IgnoreCase', true));
    rho_val = [];
    if ~isempty(resIdx)
        rho_val = data{:, resIdx(1)};
        if max(rho_val, [], 'omitnan') > 1e-4
            rho_val = rho_val * 1e-6; % Normalize from micro-Ohm*m to Ohm*m
        end
    end
    if isempty(rho_val) || all(isnan(rho_val)) || all(rho_val <= 0)
        % Derive via Wiedemann-Franz law when resistivity column is absent
        tcIdx = find(contains(vNames, 'Thermal conductivity', 'IgnoreCase', true));
        if ~isempty(tcIdx)
            k_val = data{:, tcIdx(1)};
            L0 = 2.44e-8; % Lorentz number [W*Ohm/K^2]
            valid_tc = (k_val > 0) & ~isnan(k_val) & (T_all > 0);
            rho_val = NaN(size(T_all));
            rho_val(valid_tc) = (L0 .* T_all(valid_tc)) ./ k_val(valid_tc);
        end
    end
    if ~isempty(rho_val) && any(~isnan(rho_val))
        lambda_um = 1.064; % 1064 nm Fiber/Nd:YAG laser
        rho_uOhm_m = rho_val * 1e6;
        A_bulk = 0.365 * sqrt(max(0, rho_uOhm_m) ./ lambda_um);
        A_bulk = min(0.95, max(0.01, A_bulk));
        data.('Laser Absorptivity A(T)') = A_bulk;

        % Total hemispherical surface emissivity
        eps_base = min(0.92, max(0.05, 0.751 * sqrt(max(1e-12, rho_val .* T_all .* 1e-2))));
        data.('Surface Emissivity eps(T)') = eps_base;
        vNames = data.Properties.VariableNames;
    end

    data.Properties.VariableNames = vNames;
    
    % Detect Single Physical Melting Point (Tm) for the Material
    T_all = data{:, 1};
    T_min = min(T_all);
    T_max = max(T_all);
    Tm = (T_min + T_max) / 2;
    
    ymIdx = find(contains(vNames, 'Young', 'IgnoreCase', true));
    if ~isempty(ymIdx)
        ymVals = data{:, ymIdx(1)};
        valid = ~isnan(T_all) & ~isnan(ymVals);
        Tv = T_all(valid); YMv = ymVals(valid);
        [Tv, sIdx] = sort(Tv); YMv = YMv(sIdx);
        solidIdxs = find(YMv > 1e8);
        if ~isempty(solidIdxs) && max(solidIdxs) < length(Tv)
            Tm = Tv(max(solidIdxs));
        end
    end
    
    fprintf('\nFitting material: %s  (Detected Tm = %.1f K)\n', mat_name, Tm);
    
    for p = 2:length(vNames)
        propName = vNames{p};
        Y_raw = data{:, p};
        
        valid = ~isnan(T_all) & ~isnan(Y_raw);
        T = T_all(valid); Y = Y_raw(valid);
        
        if isempty(T) || all(Y == 0)
            continue;
        end
        
        [T, sIdx] = sort(T);
        Y = Y(sIdx);
        
        fprintf('\n>> Property: %s\n', propName);
        fprintf('%-10s %-10s %-45s\n', 'Start (K)', 'End (K)', 'Function (COMSOL Definition)');
        
        lowerProp = lower(propName);
        
        if contains(lowerProp, 'viscosity')
            % Dynamic Viscosity: 3-interval Krieger-Dougherty suspension model + Arrhenius melt
            Ts = Tm - 75;
            Tl = Tm + 75;
            idx_liq = T >= Tl & Y > 0;
            if sum(idx_liq) < 2
                idx_liq = T > Tm & Y > 0;
            end
            if sum(idx_liq) >= 2
                p_exp = polyfit(1 ./ T(idx_liq), log(Y(idx_liq)), 1);
                B = p_exp(1); A = exp(p_exp(2));
                f_liq = sprintf('%.4e * exp(%.2f / T)', A, B);
            else
                f_liq = 'N/A';
            end
            
            % Bounded Krieger-Dougherty expression (prevents imaginary roots and caps at 1000 Pa*s)
            f_mush = sprintf('min(1.0e+03, (%.4e*exp(%.2f/T)) * (max(1e-4, 1 - min((%.1f-T)/%.1f, 0.649)/0.65)^(-1.625)))', ...
                A, B, Tl, Tl - Ts);
            
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Ts, '1.0e+03 (Rigid solid plateau)');
            fprintf('%-10.1f %-10.1f %-45s\n', Ts, Tl, f_mush);
            fprintf('%-10.1f %-10.1f %-45s\n', Tl, T_max, f_liq);
            fprintf('  -> COMSOL flc2hs formulation: mu_app(T) = %s + (1.0e+03 - (%s)) * flc2hs(%.1f - T, %.1f)\n', ...
                f_liq, f_liq, Tl, (Tl - Ts)/2);
            
        elseif contains(lowerProp, 'young')
            % Young's Modulus: Solid Linear, Liquid = 0 Pa
            idx_sol = T <= Tm;
            p_sol = polyfit(T(idx_sol), Y(idx_sol), 1);
            f_sol = sprintf('%.4e*T + %.4e', p_sol(1), p_sol(2));
            f_sol = strrep(f_sol, '+ -', '- ');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Tm, f_sol);
            fprintf('%-10.1f %-10.1f %-45s\n', Tm, T_max, '0 (No liquid stiffness)');
            
        elseif contains(lowerProp, 'poisson')
            % Poisson's Ratio: Solid Linear, Liquid = 0.5 (Incompressible)
            idx_sol = T <= Tm;
            p_sol = polyfit(T(idx_sol), Y(idx_sol), 1);
            f_sol = sprintf('%.6g*T + %.6g', p_sol(1), p_sol(2));
            f_sol = strrep(f_sol, '+ -', '- ');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Tm, f_sol);
            fprintf('%-10.1f %-10.1f %-45s\n', Tm, T_max, '0.5 (Incompressible fluid)');
            
        elseif contains(lowerProp, 'surface tension')
            % Surface tension: Liquid only (> Tm)
            idx_liq = T > Tm;
            p_liq = polyfit(T(idx_liq), Y(idx_liq), 1);
            f_liq = sprintf('%.6g*T + %.6g', p_liq(1), p_liq(2));
            f_liq = strrep(f_liq, '+ -', '- ');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Tm, '0 (No solid surface tension)');
            fprintf('%-10.1f %-10.1f %-45s\n', Tm, T_max, f_liq);
            
        elseif contains(lowerProp, 'expansion')
            % Thermal Expansion: 2nd-degree Quadratic Fit
            idx_sol = T <= Tm;
            idx_liq = T > Tm;
            p_sol = polyfit(T(idx_sol), Y(idx_sol), 2);
            f_sol = sprintf('%.4e*T^2 + %.4e*T + %.4e', p_sol(1), p_sol(2), p_sol(3));
            f_sol = strrep(f_sol, '+ -', '- ');
            
            if sum(idx_liq) >= 3
                p_liq = polyfit(T(idx_liq), Y(idx_liq), 2);
                f_liq = sprintf('%.4e*T^2 + %.4e*T + %.4e', p_liq(1), p_liq(2), p_liq(3));
                f_liq = strrep(f_liq, '+ -', '- ');
            else
                f_liq = 'N/A';
            end
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Tm, f_sol);
            fprintf('%-10.1f %-10.1f %-45s\n', Tm, T_max, f_liq);
            
        elseif contains(lowerProp, 'absorptivity')
            % Temperature-dependent Laser Absorptivity A(T)
            Ts = Tm - 75;
            Tl = Tm + 75;
            dT_half = (Tl - Ts) / 2;
            T_mid = (Ts + Tl) / 2;
            
            % Laser Hardening (Solid-State: T <= Ts)
            idx_sol = T <= Ts;
            if sum(idx_sol) >= 2
                p_sol = polyfit(T(idx_sol), Y(idx_sol), 1);
                f_sol = sprintf('%.4e*T + %.4e', p_sol(1), p_sol(2));
                f_sol = strrep(f_sol, '+ -', '- ');
            else
                f_sol = sprintf('%.4f', mean(Y));
            end
            fprintf('  [Laser Hardening: Solid State (T < Ts)]:\n');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Ts, f_sol);
            fprintf('%-10.1f %-10.1f %-45s\n', Ts, T_max, 'MELTING HAZARD (T >= Ts)');
            
            % Laser Remelting (Rough substrate transitioning to specular melt pool)
            eta_rough = 1.35;
            A_sol_remelt = min(0.95, eta_rough * Y);
            idx_liq = T >= Tl;
            if sum(idx_liq) >= 2
                p_liq = polyfit(T(idx_liq), Y(idx_liq), 1);
                f_liq = sprintf('%.4e*T + %.4e', p_liq(1), p_liq(2));
                f_liq = strrep(f_liq, '+ -', '- ');
            else
                f_liq = sprintf('%.4f', mean(Y));
            end
            if sum(idx_sol) >= 2
                p_sol_r = polyfit(T(idx_sol), A_sol_remelt(idx_sol), 1);
                f_sol_r = sprintf('%.4e*T + %.4e', p_sol_r(1), p_sol_r(2));
                f_sol_r = strrep(f_sol_r, '+ -', '- ');
            else
                f_sol_r = sprintf('%.4f', mean(A_sol_remelt));
            end
            f_mush_opt = sprintf('(%s) + ((%s) - (%s))*flc2hs(T - %.1f, %.1f)', f_sol_r, f_liq, f_sol_r, T_mid, dT_half);
            fprintf('  [Laser Remelting: Continuous Transition to Specular Melt Pool]:\n');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Ts, f_sol_r);
            fprintf('%-10.1f %-10.1f %-45s\n', Ts, Tl, f_mush_opt);
            fprintf('%-10.1f %-10.1f %-45s\n', Tl, T_max, f_liq);
            fprintf('  -> COMSOL flc2hs formulation: A_app(T) = %s + ((%s) - (%s)) * flc2hs(T - %.1f, %.1f)\n', ...
                f_sol_r, f_liq, f_sol_r, T_mid, dT_half);
            
        elseif contains(lowerProp, 'emissivity')
            % Temperature-dependent Surface Emissivity eps(T)
            Ts = Tm - 75;
            Tl = Tm + 75;
            dT_half = (Tl - Ts) / 2;
            T_mid = (Ts + Tl) / 2;
            
            % Laser Hardening (Solid-State: T <= Ts)
            idx_sol = T <= Ts;
            if sum(idx_sol) >= 2
                p_sol = polyfit(T(idx_sol), Y(idx_sol), 1);
                f_sol = sprintf('%.4e*T + %.4e', p_sol(1), p_sol(2));
                f_sol = strrep(f_sol, '+ -', '- ');
            else
                f_sol = sprintf('%.4f', mean(Y));
            end
            fprintf('  [Surface Emissivity - Laser Hardening (T < Ts)]:\n');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Ts, f_sol);
            fprintf('%-10.1f %-10.1f %-45s\n', Ts, T_max, 'MELTING HAZARD (T >= Ts)');
            
            % Laser Remelting (Rough solid -> Molten liquid pool)
            eta_rough = 1.35;
            eps_sol_remelt = min(0.92, eta_rough * Y);
            idx_liq = T >= Tl;
            if sum(idx_liq) >= 2
                p_liq = polyfit(T(idx_liq), Y(idx_liq), 1);
                f_liq = sprintf('%.4e*T + %.4e', p_liq(1), p_liq(2));
                f_liq = strrep(f_liq, '+ -', '- ');
            else
                f_liq = sprintf('%.4f', mean(Y));
            end
            if sum(idx_sol) >= 2
                p_sol_r = polyfit(T(idx_sol), eps_sol_remelt(idx_sol), 1);
                f_sol_r = sprintf('%.4e*T + %.4e', p_sol_r(1), p_sol_r(2));
                f_sol_r = strrep(f_sol_r, '+ -', '- ');
            else
                f_sol_r = sprintf('%.4f', mean(eps_sol_remelt));
            end
            f_mush_eps = sprintf('(%s) + ((%s) - (%s))*flc2hs(T - %.1f, %.1f)', f_sol_r, f_liq, f_sol_r, T_mid, dT_half);
            fprintf('  [Surface Emissivity - Laser Remelting (Transition to Melt Pool)]:\n');
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Ts, f_sol_r);
            fprintf('%-10.1f %-10.1f %-45s\n', Ts, Tl, f_mush_eps);
            fprintf('%-10.1f %-10.1f %-45s\n', Tl, T_max, f_liq);
            fprintf('  -> COMSOL flc2hs formulation: eps_app(T) = %s + ((%s) - (%s)) * flc2hs(T - %.1f, %.1f)\n', ...
                f_sol_r, f_liq, f_sol_r, T_mid, dT_half);
            
        else
            % Default: Piecewise Linear split at Tm (Density, Thermal Conductivity, Specific Heat)
            idx_sol = T <= Tm;
            idx_liq = T > Tm;
            
            if sum(idx_sol) >= 2
                p_sol = polyfit(T(idx_sol), Y(idx_sol), 1);
                f_sol = sprintf('%.6g*T + %.6g', p_sol(1), p_sol(2));
                f_sol = strrep(f_sol, '+ -', '- ');
            else
                f_sol = 'N/A';
            end
            
            if sum(idx_liq) >= 2
                p_liq = polyfit(T(idx_liq), Y(idx_liq), 1);
                f_liq = sprintf('%.6g*T + %.6g', p_liq(1), p_liq(2));
                f_liq = strrep(f_liq, '+ -', '- ');
            else
                f_liq = 'N/A';
            end
            fprintf('%-10.1f %-10.1f %-45s\n', T_min, Tm, f_sol);
            fprintf('%-10.1f %-10.1f %-45s\n', Tm, T_max, f_liq);
        end
    end
    fprintf('\n');
end
