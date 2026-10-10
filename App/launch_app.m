% launch_app.m
% Run this script to launch the Material Properties COMSOL Fitter App
% Works regardless of MATLAB current directory

% 1. Navigate to the App folder
script_dir = fileparts(mfilename('fullpath'));
if ~isempty(script_dir)
    cd(script_dir);
end

% 2. Clear cached class definitions so theme changes apply immediately
clear classes %#ok<CLCLS>

% 3. Launch
app = MaterialPropertiesApp();
disp('Material Properties Fitter launched successfully.');
