% export_verification_snapshots.m
% Generates high-resolution PNG verification snapshots for CALPHADHEACalc
function export_verification_snapshots()
    artDir = 'C:\Users\Dell\.gemini\antigravity\brain\4a040a8a-1de2-4dac-ae93-9ec24252248a';
    if ~exist(artDir, 'dir')
        artDir = pwd;
    end
    
    fprintf('Initializing CALPHADHEACalc in interactive visible mode for snapshot export...\n');
    app = CALPHADHEACalc('Cantor (CoCrFeMnNi)', false, true);
    app.calculateAll();
    drawnow;
    pause(0.5);

    % 1. Export Main Software View (Cantor alloy, Tab 1)
    mainPath = fullfile(artDir, 'calphad_software_main_view.png');
    exportapp(app.UIFigure, mainPath);
    fprintf('Exported: %s\n', mainPath);

    % 2. Switch to Tab 4: Mechanical Properties View
    app.switchToTab(app.TabMechanical);
    drawnow;
    pause(0.5);
    mechPath = fullfile(artDir, 'calphad_mechanical_properties_view.png');
    exportapp(app.UIFigure, mechPath);
    fprintf('Exported: %s\n', mechPath);

    % 3. Switch to Tab 8: Validation & Export View with Dynamic COMSOL Dropdown
    app.switchToTab(app.TabValidation);
    app.DropdownComsolProperty.Value = 'Thermal Conductivity k(T) [W/(m*K)]';
    app.generateComsolPiecewise();
    drawnow;
    pause(0.5);
    comsolPath = fullfile(artDir, 'calphad_comsol_dynamic_piecewise.png');
    exportapp(app.UIFigure, comsolPath);
    fprintf('Exported: %s\n', comsolPath);

    % 4. Open IUPAC Periodic Table Dialog
    dlg = app.openPeriodicTableDialog();
    dlg.WindowStyle = 'normal'; % Non-modal for capture
    drawnow;
    pause(0.5);
    ptPath = fullfile(artDir, 'calphad_iupac_periodic_table.png');
    exportapp(dlg, ptPath);
    fprintf('Exported: %s\n', ptPath);
    delete(dlg);

    % Close app
    delete(app.UIFigure);
    fprintf('All verification snapshots successfully generated!\n');
end
