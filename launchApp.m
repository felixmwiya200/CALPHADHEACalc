% LAUNCHAPP Convenient Instant Desktop Launcher
% CALPHADHEACalc 2026 - High-Entropy Alloys & Thermodynamics Multi-Physics Platform
%
% Usage:
%   launchApp
%
% Behavior:
%   1. Configures required paths.
%   2. Pops up the instant dark-themed launch screen (<150ms).
%   3. Displays real-time step-by-step progress as each engine mounts:
%      - [Security Vault]
%      - [45 Elements]
%      - [Lit Benchmark]
%      - [Laser Optics]
%      - [Desktop CAE UI]
%   4. Smoothly transitions to the main application window.

addpath(fullfile(pwd, 'App'));
addpath(pwd);

% Instantly spawn the native desktop splash screen (<30ms)
MaterialSplash.start();

fprintf('\n=======================================================================\n');
fprintf('  CALPHADHEACALC 2026 (v3.4.0) — HIGH-ENTROPY ALLOY SOFTWARE\n');
fprintf('  Materials computational research engineer and lead developer: Felix Mwiya\n');
fprintf('  Research Guide: Prof. (Dr.) Sheela Singh\n');
fprintf('  Department of Mechanical Engineering, School of Engineering and Sciences\n');
fprintf('  SRM University-AP, Andhra Pradesh, India\n');
fprintf('=======================================================================\n');

appInstance = MaterialPropertiesApp([], false);
try, MaterialSplash.close(); catch, end

fprintf('  [OK] CALPHADHEACalc 2026 is active!\n\n');
