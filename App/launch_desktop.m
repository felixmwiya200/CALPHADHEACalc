% launch_desktop.m
% Launcher script for desktop shortcut
try
    % Ensure we are in the directory of this script
    script_dir = fileparts(mfilename('fullpath'));
    if ~isempty(script_dir)
        cd(script_dir);
    end
    
    app = MaterialPropertiesApp();
    waitfor(app.UIFigure);
catch ME
    errordlg(ME.message, 'Launch Error');
end
