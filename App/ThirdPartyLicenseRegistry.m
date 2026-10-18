classdef ThirdPartyLicenseRegistry
    % ThirdPartyLicenseRegistry - Compliance & Legal Registry Engine
    % Manages third-party open-source licenses, thermodynamic database attributions,
    % and scientific model notices for CALPHADHEACalc.
    % Conforms to ISO/IEC 5230:2020 (OpenChain).

    methods (Static)

        function legalDir = getLegalDir()
            % Resolves the absolute path to the local offline legal directory
            baseDir = fileparts(mfilename('fullpath'));
            legalDir = fullfile(baseDir, 'legal');
            if ~exist(legalDir, 'dir')
                mkdir(legalDir);
            end
        end

        function data = getRegistry()
            % Loads and returns canonical registry data from JSON
            persistent cachedRegistry;
            if ~isempty(cachedRegistry)
                data = cachedRegistry;
                return;
            end

            legalDir = ThirdPartyLicenseRegistry.getLegalDir();
            jsonFile = fullfile(legalDir, 'third_party_licenses.json');
            if ~exist(jsonFile, 'file')
                error('ThirdPartyLicenseRegistry:MissingDatabase', ...
                    'Canonical license database not found at: %s', jsonFile);
            end

            raw = fileread(jsonFile);
            data = jsondecode(raw);
            cachedRegistry = data;
        end

        function tbl = getSummaryTable()
            % Formats tabular data matching the Thermo-Calc 2026b About Dialog:
            % Columns: Package | Version | License
            data = ThirdPartyLicenseRegistry.getRegistry();
            items = data.registry;
            n = numel(items);

            Package = cell(n, 1);
            Version = cell(n, 1);
            License = cell(n, 1);

            for i = 1:n
                Package{i} = items(i).package;
                Version{i} = items(i).version;
                License{i} = items(i).license;
            end

            tbl = table(Package, Version, License);
        end

        function tbl = getDetailedTable()
            % Detailed table for full license inspector
            data = ThirdPartyLicenseRegistry.getRegistry();
            items = data.registry;
            n = numel(items);

            Package   = cell(n, 1);
            Version   = cell(n, 1);
            License   = cell(n, 1);
            SPDX_ID   = cell(n, 1);
            Category  = cell(n, 1);

            for i = 1:n
                Package{i}   = items(i).package;
                Version{i}   = items(i).version;
                License{i}   = items(i).license;
                SPDX_ID{i}   = items(i).spdx;
                Category{i}  = items(i).category;
            end

            tbl = table(Package, Version, License, SPDX_ID, Category);
        end

        function txt = getFullLicenseText(idOrIndex)
            % Retrieves the full unedited license text from disk
            data = ThirdPartyLicenseRegistry.getRegistry();
            items = data.registry;
            legalDir = ThirdPartyLicenseRegistry.getLegalDir();

            targetItem = [];
            if isnumeric(idOrIndex) && idOrIndex >= 1 && idOrIndex <= numel(items)
                targetItem = items(idOrIndex);
            elseif ischar(idOrIndex) || isstring(idOrIndex)
                for i = 1:numel(items)
                    if strcmpi(items(i).id, char(idOrIndex)) || ...
                       strcmpi(items(i).package, char(idOrIndex))
                        targetItem = items(i);
                        break;
                    end
                end
            end

            if isempty(targetItem)
                txt = sprintf('[ERROR] License entry not found for identifier: %s', string(idOrIndex));
                return;
            end

            licPath = fullfile(legalDir, targetItem.licenseFile);
            if exist(licPath, 'file')
                txt = fileread(licPath);
            else
                txt = sprintf('[LOCAL LICENSE FILE NOT FOUND: %s]\n\nNotice:\n%s\n\nCopyright:\n%s\n\nURL:\n%s', ...
                    targetItem.licenseFile, targetItem.noticeSummary, targetItem.copyright, targetItem.url);
            end
        end

        function targetPath = exportAllNotices(targetPath)
            % Exports the aggregated third-party notices file to targetPath
            legalDir = ThirdPartyLicenseRegistry.getLegalDir();
            srcFile = fullfile(legalDir, 'THIRDPARTYNOTICES.txt');

            if nargin < 1 || isempty(targetPath)
                targetPath = fullfile(pwd, 'CALPHADHEACalc_THIRDPARTYNOTICES.txt');
            end

            if exist(srcFile, 'file')
                copyfile(srcFile, targetPath);
            else
                % Regenerate dynamically
                fid = fopen(targetPath, 'w', 'n', 'UTF-8');
                if fid ~= -1
                    data = ThirdPartyLicenseRegistry.getRegistry();
                    items = data.registry;
                    fprintf(fid, '================================================================================\n');
                    fprintf(fid, 'CALPHADHEACalc 2026 - THIRD-PARTY SOFTWARE, DATABASE & LEGAL NOTICES\n');
                    fprintf(fid, 'Lead Developer: Felix Mwiya (Materials computational research engineer and lead developer)\n');
                    fprintf(fid, 'Academic Guide: Prof. (Dr.) Sheela Singh, SRM University-AP\n');
                    fprintf(fid, 'Date: %s\n', char(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss')));
                    fprintf(fid, '================================================================================\n\n');
                    for k = 1:numel(items)
                        fprintf(fid, '--------------------------------------------------------------------------------\n');
                        fprintf(fid, 'PACKAGE: %s (v%s)\n', items(k).package, items(k).version);
                        fprintf(fid, 'SPDX: %s | LICENSE: %s\n', items(k).spdx, items(k).license);
                        fprintf(fid, 'COPYRIGHT: %s\n', items(k).copyright);
                        fprintf(fid, '--------------------------------------------------------------------------------\n');
                        fprintf(fid, '%s\n\n', ThirdPartyLicenseRegistry.getFullLicenseText(items(k).id));
                    end
                    fclose(fid);
                end
            end
        end

        function isCompliant = validateCompliance()
            % Verifies that all 14+ items have valid local license files
            data = ThirdPartyLicenseRegistry.getRegistry();
            items = data.registry;
            legalDir = ThirdPartyLicenseRegistry.getLegalDir();

            assert(numel(items) >= 14, 'Registry must contain at least 14 third-party items.');
            for i = 1:numel(items)
                it = items(i);
                licPath = fullfile(legalDir, it.licenseFile);
                assert(exist(licPath, 'file') == 2, ...
                    'Missing local license file for %s: %s', it.package, licPath);
                fInfo = dir(licPath);
                assert(fInfo.bytes >= 20, ...
                    'License file %s is empty or corrupt.', licPath);
            end
            isCompliant = true;
        end

    end
end
