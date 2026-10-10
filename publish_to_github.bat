@echo off
setlocal
echo =========================================================================
echo  CALPHADHEACalc - One-Click Git and GitHub Publishing Automation
echo  Lead Architect: Felix Mwiya (felixmwiya200)
echo  Supervisor:     Prof. (Dr.) Sheela Singh, SRM University-AP
echo =========================================================================
echo.
echo [1/4] Checking Git repository status...
git status
echo.
echo [2/4] Configuring remote origin to https://github.com/felixmwiya200/CALPHADHEACalc.git...
git remote remove origin 2>nul
git remote add origin https://github.com/felixmwiya200/CALPHADHEACalc.git
git branch -M main
echo.
echo [3/4] Pushing authoritative main branch to GitHub...
git push -u origin main
if %ERRORLEVEL% equ 0 (
    echo.
    echo =========================================================================
    echo  [SUCCESS] CALPHADHEACalc repository successfully published to GitHub!
    echo  Repository:   https://github.com/felixmwiya200/CALPHADHEACalc
    echo  Live Web App: https://felixmwiya200.github.io/CALPHADHEACalc/
    echo =========================================================================
    echo.
    echo Next Steps:
    echo 1. Open https://github.com/felixmwiya200/CALPHADHEACalc/settings/pages
    echo    and set Source: Deploy from branch -> main -> /docs
    echo 2. Open https://github.com/felixmwiya200/CALPHADHEACalc/settings/branches
    echo    and configure branch protection on 'main' (see BRANCH_PROTECTION.md)
    echo.
) else (
    echo.
    echo =========================================================================
    echo  [NOTE] Push did not complete automatically.
    echo  If the repository does not exist on GitHub yet:
    echo  1. Visit https://github.com/new
    echo  2. Name the repository: CALPHADHEACalc
    echo  3. Set to Public and do NOT initialize with README (already present)
    echo  4. Re-run this script or run: git push -u origin main
    echo =========================================================================
    echo.
)
pause
