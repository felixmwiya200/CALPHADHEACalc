function varargout = launchApp()
% LAUNCHAPP Convenient Instant Desktop Launcher
% CALPHADHEACalc 2026 - High-Entropy Alloys & Thermodynamics Multi-Physics Platform
%
% Usage:
%   launchApp
%   app = launchApp();

addpath(fullfile(pwd, 'App'));
addpath(pwd);

fprintf('\n=======================================================================\n');
fprintf('  CALPHADHEACALC 2026 (v3.4.0) — HIGH-ENTROPY ALLOY SOFTWARE\n');
fprintf('  Materials computational research engineer and lead developer: Felix Mwiya\n');
fprintf('  Research Guide: Prof. (Dr.) Sheela Singh\n');
fprintf('  Department of Mechanical Engineering, School of Engineering and Sciences\n');
fprintf('  SRM University-AP, Andhra Pradesh, India\n');
fprintf('=======================================================================\n');

% Direct, lightweight instant launch (pure in-process, zero preloading)
appInstance = MaterialPropertiesApp([], false);

% Retain handle in MATLAB base workspace so the window never collapses on function return
assignin('base', 'app', appInstance);

if nargout > 0
    varargout{1} = appInstance;
end

fprintf('  [OK] CALPHADHEACalc 2026 is active!\n\n');
end
