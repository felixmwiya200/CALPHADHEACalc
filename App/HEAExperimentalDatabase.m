classdef HEAExperimentalDatabase < handle
    % HEAExperimentalDatabase
    % Ingests and queries the peer-reviewed High Entropy Alloys (HEA) experimental
    % database (12,427+ alloy compositions, phase structures, processing routes, and DOIs).
    %
    % Source: Open HEA Database repository (Vladimirchizh/hea_database)
    % Papers indexed from: ScienceDirect (Materials Letters, MSEA, Corrosion Science,
    % Surface & Coatings Tech, Vacuum, Intermetallics, Acta Materialia).
    
    properties (Constant)
        CSV_FILE = 'App/data/database_of_HEAs.csv'
    end
    
    properties
        IsLoaded = false
        RowCount = 0
        Alloys = {}
        Phases = {}
        NbPhases = []
        StudyTypes = {}
        ExpDetails = {}
        TheoDetails = {}
        SolutionTypes = {}
        Papers = {}
        
        % Normalized element presence index for ultra-fast lookup (<1 ms)
        AlloyElemMap containers.Map
        FormulaLookupMap containers.Map
    end
    
    methods (Static)
        function instance = getInstance(forceLoad)
            persistent dbInstance;
            if nargin < 1, forceLoad = false; end
            if isempty(dbInstance) || ~isvalid(dbInstance)
                dbInstance = HEAExperimentalDatabase();
            end
            if forceLoad && ~dbInstance.IsLoaded
                dbInstance.loadDatabase();
            end
            instance = dbInstance;
        end
        
        function res = query(elements, at_fractions, forceLoad)
            % Static convenience query method - lazy: only loads on command
            if nargin < 3, forceLoad = false; end
            db = HEAExperimentalDatabase.getInstance(forceLoad);
            if ~db.IsLoaded
                res = struct('Matched', false, 'TotalMatches', 0, 'ObservedPhases', '', 'DOI', '', 'Alloy', '');
                return;
            end
            res = db.findMatch(elements, at_fractions);
        end
    end
    
    methods
        function obj = HEAExperimentalDatabase()
            obj.AlloyElemMap = containers.Map('KeyType', 'char', 'ValueType', 'any');
            obj.FormulaLookupMap = containers.Map('KeyType', 'char', 'ValueType', 'any');
        end
        
        function loadDatabase(obj)
            thisDir = fileparts(mfilename('fullpath'));
            matPath = fullfile(thisDir, 'data', 'database_of_HEAs.mat');
            if isfile(matPath)
                try
                    cached = load(matPath);
                    obj.RowCount = cached.RowCount;
                    obj.Papers = cached.Papers;
                    obj.Alloys = cached.Alloys;
                    obj.NbPhases = cached.NbPhases;
                    obj.Phases = cached.Phases;
                    obj.StudyTypes = cached.StudyTypes;
                    obj.ExpDetails = cached.ExpDetails;
                    obj.TheoDetails = cached.TheoDetails;
                    obj.SolutionTypes = cached.SolutionTypes;
                    obj.AlloyElemMap = cached.AlloyElemMap;
                    obj.FormulaLookupMap = cached.FormulaLookupMap;
                    obj.IsLoaded = true;
                    return;
                catch
                end
            end

            % Ultra-fast vectorized CSV parse using textscan
            csvPath = obj.CSV_FILE;
            if ~isfile(csvPath)
                csvPath = fullfile(thisDir, 'data', 'database_of_HEAs.csv');
            end
            if ~isfile(csvPath)
                fprintf('Warning: HEA database file not found at %s\n', csvPath);
                return;
            end
            
            fid = fopen(csvPath, 'r', 'n', 'UTF-8');
            if fid < 0
                return;
            end
            
            try
                % id, Paper, Name, Alloy, Nb of phase, Phase, Experimental or theoretical,
                % Experimental details, Theoretical details, Special conditions, Type of solution
                data = textscan(fid, '%f%q%q%q%f%q%q%q%q%q%q', ...
                    'Delimiter', ',', 'HeaderLines', 1, 'ReturnOnError', false);
                fclose(fid);
            catch
                fclose(fid);
                return;
            end
            
            obj.RowCount = numel(data{1});
            obj.Papers = data{2};
            obj.Alloys = data{4};
            obj.NbPhases = data{5};
            obj.Phases = data{6};
            obj.StudyTypes = data{7};
            obj.ExpDetails = data{8};
            obj.TheoDetails = data{9};
            obj.SolutionTypes = data{11};
            
            % Build fast index
            obj.buildIndices();
            obj.IsLoaded = true;

            % Cache to .mat for instant sub-100ms loading on subsequent runs
            try
                RowCount = obj.RowCount;
                Papers = obj.Papers;
                Alloys = obj.Alloys;
                NbPhases = obj.NbPhases;
                Phases = obj.Phases;
                StudyTypes = obj.StudyTypes;
                ExpDetails = obj.ExpDetails;
                TheoDetails = obj.TheoDetails;
                SolutionTypes = obj.SolutionTypes;
                AlloyElemMap = obj.AlloyElemMap;
                FormulaLookupMap = obj.FormulaLookupMap;
                save(matPath, 'RowCount', 'Papers', 'Alloys', 'NbPhases', 'Phases', ...
                    'StudyTypes', 'ExpDetails', 'TheoDetails', 'SolutionTypes', ...
                    'AlloyElemMap', 'FormulaLookupMap', '-v7.3');
            catch
            end
        end
        
        function buildIndices(obj)
            % Builds inverted index mapping sorted element keys (e.g. 'Al_Co_Cr_Fe_Ni')
            % and cleaned chemical formulas to record row indices.
            for row = 1:obj.RowCount
                alloyStr = strtrim(obj.Alloys{row});
                if isempty(alloyStr)
                    continue;
                end
                
                % Standardize formula key (lowercase, alphanumeric only)
                cleanKey = lower(regexprep(alloyStr, '[^a-zA-Z0-9]', ''));
                if ~isKey(obj.FormulaLookupMap, cleanKey)
                    obj.FormulaLookupMap(cleanKey) = row;
                end
                
                % Parse elements in formula
                elems = obj.extractElements(alloyStr);
                if ~isempty(elems)
                    elemsSorted = sort(elems);
                    elemKey = strjoin(elemsSorted, '_');
                    if isKey(obj.AlloyElemMap, elemKey)
                        arr = obj.AlloyElemMap(elemKey);
                        arr(end+1) = row; %#ok<AGROW>
                        obj.AlloyElemMap(elemKey) = arr;
                    else
                        obj.AlloyElemMap(elemKey) = row;
                    end
                end
            end
        end
        
        function elems = extractElements(~, formulaStr)
            % Extracts elemental symbols from formula string (e.g. 'Al0.3CoCrFeNi' -> {'Al', 'Co', 'Cr', 'Fe', 'Ni'})
            elems = {};
            tokens = regexp(formulaStr, '([A-Z][a-z]?)', 'tokens');
            for k = 1:numel(tokens)
                sym = tokens{k}{1};
                if ~ismember(sym, elems)
                    elems{end+1} = sym; %#ok<AGROW>
                end
            end
        end
        
        function res = findMatch(obj, elements, at_fractions)
            % Finds the closest peer-reviewed experimental literature match
            % for the specified alloy composition.
            res = struct();
            res.Matched = false;
            res.AlloyFormula = '';
            res.ObservedPhases = '';
            res.NbOfPhases = 0;
            res.StudyType = '';
            res.ExperimentalDetails = '';
            res.SolutionType = '';
            res.DOI = '';
            res.TotalMatches = 0;
            res.AllMatches = {};
            
            if ~obj.IsLoaded || isempty(elements)
                return;
            end
            
            % Generate formula variations to check
            sortedElems = sort(elements);
            elemKey = strjoin(sortedElems, '_');
            
            % Check if this elemental system exists in our database
            matchingRows = [];
            if isKey(obj.AlloyElemMap, elemKey)
                matchingRows = obj.AlloyElemMap(elemKey);
            end
            
            if isempty(matchingRows)
                % Fallback: try subset search if >4 elements
                return;
            end
            
            res.TotalMatches = numel(matchingRows);
            
            % Find the most relevant row:
            % 1. Prioritize rows where StudyType is 'experimental' or 'Experimental'
            % 2. Prioritize rows with detailed phase description
            bestRow = matchingRows(1);
            bestScore = -1;
            
            for idx = 1:min(numel(matchingRows), 40)
                r = matchingRows(idx);
                score = 0;
                st = lower(strtrim(obj.StudyTypes{r}));
                if contains(st, 'exp')
                    score = score + 10;
                end
                
                ph = strtrim(obj.Phases{r});
                if ~isempty(ph) && ~strcmp(ph, 'N/A')
                    score = score + 5;
                end
                
                det = strtrim(obj.ExpDetails{r});
                if ~isempty(det) && ~strcmp(det, 'N/A') && length(det) > 15
                    score = score + 5;
                end
                
                if score > bestScore
                    bestScore = score;
                    bestRow = r;
                end
            end
            
            % Clean DOI from paper string (e.g. '10.1016-j.matlet.2018.01.017.txt' -> '10.1016/j.matlet.2018.01.017')
            paperStr = obj.Papers{bestRow};
            doiStr = regexprep(paperStr, '\.txt$', '');
            doiStr = regexprep(doiStr, '^(\d{2}\.\d{4,5})-', '$1/');
            doiStr = regexprep(doiStr, '-([a-z])', '/$1');
            
            res.Matched = true;
            res.AlloyFormula = obj.Alloys{bestRow};
            res.ObservedPhases = obj.Phases{bestRow};
            res.NbOfPhases = obj.NbPhases(bestRow);
            res.StudyType = obj.StudyTypes{bestRow};
            res.ExperimentalDetails = obj.ExpDetails{bestRow};
            res.SolutionType = obj.SolutionTypes{bestRow};
            res.DOI = doiStr;
            
            % Collect up to 3 literature citation summaries
            allMatches = {};
            for idx = 1:min(numel(matchingRows), 3)
                r = matchingRows(idx);
                pStr = obj.Papers{r};
                dClean = regexprep(regexprep(regexprep(pStr, '\.txt$', ''), '^(\d{2}\.\d{4,5})-', '$1/'), '-([a-z])', '/$1');
                m = struct('Alloy', obj.Alloys{r}, ...
                           'Phase', obj.Phases{r}, ...
                           'DOI', dClean, ...
                           'Details', obj.ExpDetails{r});
                allMatches{end+1} = m; %#ok<AGROW>
            end
            res.AllMatches = allMatches;
        end
    end
end
