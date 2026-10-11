% compile_calphad_exe.m - Automates Compilation of Standalone Windows .EXE
% Builds CALPHADHEACalc.exe for end-users.
% End-users run the executable using the free royalty-free MATLAB Runtime (MCR).

function compile_calphad_exe()
    fprintf('=================================================================\n');
    fprintf('    BUILDING STANDALONE WINDOWS EXECUTABLE (CALPHADHEACalc.exe)  \n');
    fprintf('=================================================================\n\n');

    rootDir = fileparts(mfilename('fullpath'));
    if isempty(rootDir), rootDir = pwd; end
    appDir = fullfile(rootDir, 'App');
    if exist(appDir, 'dir')
        cd(appDir);
    end

    mainFile = 'CALPHADHEACalc.m';
    appName = 'CALPHADHEACalc';
    iconFile = fullfile(rootDir, 'App', 'resources', 'app_icon.ico');
    if ~exist(iconFile, 'file')
        iconFile = fullfile(rootDir, 'app_icon.ico');
    end

    fprintf('Checking MATLAB Compiler license...\n');
    hasCompiler = license('test', 'Compiler');
    if ~hasCompiler
        warning(['MATLAB Compiler toolbox license not detected on this machine.\n', ...
                 'Generating Windows Desktop Launcher and Web Distribution packages instead.']);
        fprintf('End-users can run the application via:\n');
        fprintf('  1. GitHub Pages live web URL\n');
        fprintf('  2. CALPHADHEACalc_Desktop.bat (Native Windows desktop window)\n');
        fprintf('  3. Double-clicking index.html in any web browser\n');
        return;
    end

    fprintf('Compiling standalone executable with mcc...\n');
    cmd = sprintf('mcc -m -v -o %s %s -a resources -a legal -a materials_data', appName, mainFile);
    if exist(iconFile, 'file')
        cmd = sprintf('%s -r "%s"', cmd, iconFile);
    end

    fprintf('Executing: %s\n', cmd);
    eval(cmd);

    fprintf('\nCompilation complete! Standalone executable generated:\n');
    fprintf('  CALPHADHEACalc.exe\n');
    fprintf('\nEnd-users do NOT need MATLAB installed. They only need the free MATLAB Runtime:\n');
    fprintf('  https://www.mathworks.com/products/compiler/matlab-runtime.html\n');
end
