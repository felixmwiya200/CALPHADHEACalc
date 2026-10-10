% snapshot_licenses_dialogs.m - Export visual snapshots of About and License Inspector dialogs
function snapshot_licenses_dialogs()
    addpath(pwd);
    addpath(fullfile(pwd, 'App'));
    
    app = CALPHADHEACalc('Cantor (CoCrFeMnNi)', true);
    
    % 1. About Dialog Snapshot
    aDlg = app.showAboutDialog();
    drawnow;
    pause(0.5);
    out1 = fullfile(pwd, 'calphad_hea_calc_about_dialog_snapshot.png');
    exportapp(aDlg, out1);
    fprintf('[OK] Exported About dialog snapshot using exportapp: %s\n', out1);
    delete(aDlg);
    
    % 2. Third-Party Licenses Inspector Snapshot
    licDlg = app.showThirdPartyLicensesDialog();
    drawnow;
    pause(0.5);
    out2 = fullfile(pwd, 'calphad_hea_calc_licenses_dialog_snapshot.png');
    exportapp(licDlg, out2);
    fprintf('[OK] Exported Licenses inspector snapshot using exportapp: %s\n', out2);
    delete(licDlg);
    
    delete(app.UIFigure);
end
