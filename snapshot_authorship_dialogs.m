% snapshot_authorship_dialogs.m - Export visual snapshots of Authorship & Citation dialogs
function snapshot_authorship_dialogs()
    addpath(pwd);
    addpath(fullfile(pwd, 'App'));
    
    app = CALPHADHEACalc('Cantor (CoCrFeMnNi)', true);
    
    % 1. About Dialog Snapshot showing Authors & Academic Credits (Tab 1)
    aDlg = app.showAboutDialog();
    drawnow;
    pause(0.5);
    out1 = fullfile(pwd, 'calphad_hea_calc_authors_tab_snapshot.png');
    exportapp(aDlg, out1);
    fprintf('[OK] Exported Authors & Credits tab snapshot: %s\n', out1);
    delete(aDlg);
    
    % 2. How to Cite CALPHADHEACalc Dialog Snapshot
    cDlg = app.showCitationDialog();
    drawnow;
    pause(0.5);
    out2 = fullfile(pwd, 'calphad_hea_calc_citation_dialog_snapshot.png');
    exportapp(cDlg, out2);
    fprintf('[OK] Exported Citation Dialog snapshot: %s\n', out2);
    delete(cDlg);
    
    delete(app.UIFigure);
end
