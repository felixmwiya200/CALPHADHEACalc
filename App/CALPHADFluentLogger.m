classdef CALPHADFluentLogger < handle
    % CALPHADFLUENTLOGGER Formats and streams solver iteration diagnostics
    % adhering strictly to the ANSYS Fluent TUI and transcript standard.
    %
    % Columns: Step | T (K) | Iter | Mass-Res | dG-Res | dMu-Tol (J) | dPhi-Max | Damp(a) | Active Phases | CPU (ms)
    %
    % Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)
    
    properties
        TranscriptFilePath = ''
        TranscriptFileID = -1
        StartTime = 0
        LastIterTime = 0
        TotalIterations = 0
        TotalPoints = 0
        ConvergedPoints = 0
        EchoToStdout = true
        HeaderInterval = 25
        RowsSinceHeader = 0
        ConvergenceCriteria = struct(...
            'MassRes', 1.0e-8, ...
            'dGRes', 1.0e-9, ...
            'dMuTol', 1.0e-6, ...
            'dPhiMax', 1.0e-7 ...
        )
    end
    
    methods
        function obj = CALPHADFluentLogger(transcriptPath, echoStdout)
            if nargin >= 1 && ~isempty(transcriptPath)
                obj.TranscriptFilePath = transcriptPath;
                folder = fileparts(transcriptPath);
                if ~isempty(folder) && ~exist(folder, 'dir')
                    mkdir(folder);
                end
                obj.TranscriptFileID = fopen(transcriptPath, 'w');
            end
            if nargin >= 2
                obj.EchoToStdout = echoStdout;
            end
            obj.StartTime = tic;
        end
        
        function delete(obj)
            obj.closeTranscript();
        end
        
        function closeTranscript(obj)
            if obj.TranscriptFileID > 0
                try
                    fclose(obj.TranscriptFileID);
                catch
                end
                obj.TranscriptFileID = -1;
            end
        end
        
        function writeLine(obj, str)
            if obj.EchoToStdout
                fprintf('%s\n', str);
            end
            if obj.TranscriptFileID > 0
                fprintf(obj.TranscriptFileID, '%s\r\n', str);
            end
        end
        
        function printBanner(obj, alloyName, compStr, dbInfo, modeStr)
            banner = sprintf([...
                '========================================================================================================================\n', ...
                '                 CALPHADHEACalc Multicomponent Thermodynamic Equilibrium Solver v3.4                    \n', ...
                '                             Alloy: %-40s                \n', ...
                '                 Composition: %-60s      \n', ...
                '                 Databases: %-62s        \n', ...
                '========================================================================================================================\n', ...
                '  Stepping Mode: %s\n', ...
                '  Convergence Criteria:\n', ...
                '    Mass Balance Continuity (Mass-Res)    : < %.4e mol\n', ...
                '    Gibbs Energy Stationarity (dG-Res)    : < %.4e\n', ...
                '    Chemical Potential Tolerance (dMu-Tol): < %.4e J/mol\n', ...
                '    Max Phase Fraction Step (dPhi-Max)    : < %.4e\n', ...
                '========================================================================================================================'], ...
                alloyName, compStr, dbInfo, modeStr, ...
                obj.ConvergenceCriteria.MassRes, obj.ConvergenceCriteria.dGRes, ...
                obj.ConvergenceCriteria.dMuTol, obj.ConvergenceCriteria.dPhiMax);
            obj.writeLine(banner);
            obj.printTableHeader();
        end
        
        function printTableHeader(obj)
            hdr = sprintf([...
                ' Step   T (K)   Iter    Mass-Res       dG-Res      dMu-Tol (J)    dPhi-Max    Damp(a)   Active Phases         CPU (ms)\n', ...
                '------------------------------------------------------------------------------------------------------------------------']);
            obj.writeLine(hdr);
            obj.RowsSinceHeader = 0;
        end
        
        function printIteration(obj, stepIdx, TKelvin, iterIdx, massRes, dGRes, dMuTol, dPhiMax, dampAlpha, activePhasesStr, cpuMs)
            if obj.RowsSinceHeader >= obj.HeaderInterval
                obj.printTableHeader();
            end
            
            % Check if Armijo damping occurred
            dampFlag = ' ';
            if dampAlpha < 0.999
                dampFlag = '*';
            end
            
            % Truncate or pad active phases
            if length(activePhasesStr) > 20
                phasesDisplay = [activePhasesStr(1:17) '...'];
            else
                phasesDisplay = activePhasesStr;
            end
            
            rowStr = sprintf(' [%02d]  %7.1f  %4d  %12.4e  %12.4e  %13.4e  %12.4e   %5.3f%s  %-20s  %8.2f', ...
                stepIdx, TKelvin, iterIdx, massRes, dGRes, dMuTol, dPhiMax, dampAlpha, dampFlag, phasesDisplay, cpuMs);
            obj.writeLine(rowStr);
            obj.RowsSinceHeader = obj.RowsSinceHeader + 1;
            obj.TotalIterations = obj.TotalIterations + 1;
        end
        
        function printDiagnostic(obj, diagType, message)
            switch upper(diagType)
                case 'TRANSITION'
                    prefix = ' >>> PHASE TRANSITION DETECTED:';
                case 'ACTIVE_SET'
                    prefix = ' >>> ACTIVE SET UPDATED:';
                case 'DAMPING'
                    prefix = ' !!! LINE SEARCH:';
                case 'HESSIAN'
                    prefix = ' *** ILL-CONDITIONED HESSIAN:';
                case 'SOLIDUS'
                    prefix = ' >>> SOLIDUS BOUNDARY:';
                case 'LIQUIDUS'
                    prefix = ' >>> LIQUIDUS BOUNDARY:';
                otherwise
                    prefix = ' >>> INFO:';
            end
            obj.writeLine(sprintf('%s %s', prefix, message));
        end
        
        function printPointConverged(obj, stepIdx, TKelvin, iters, totalMs, phaseSummaryStr)
            convStr = sprintf('------- equilibrium converged at T = %6.1f K (%d iters, %5.2f ms) [%s] -------', ...
                TKelvin, iters, totalMs, phaseSummaryStr);
            obj.writeLine(convStr);
            obj.TotalPoints = obj.TotalPoints + 1;
            obj.ConvergedPoints = obj.ConvergedPoints + 1;
        end
        
        function printSummary(obj)
            totalElapsedSec = toc(obj.StartTime);
            avgMs = 0;
            if obj.TotalPoints > 0
                avgMs = (totalElapsedSec * 1000) / obj.TotalPoints;
            end
            sumStr = sprintf([...
                '========================================================================================================================\n', ...
                ' STEPPING SWEEP SUMMARY: %d Equilibrium Points Converged in %.2f s (Avg %.2f ms/point, %d Iterations Total)\n', ...
                '========================================================================================================================'], ...
                obj.ConvergedPoints, totalElapsedSec, avgMs, obj.TotalIterations);
            obj.writeLine(sumStr);
        end
    end
end
