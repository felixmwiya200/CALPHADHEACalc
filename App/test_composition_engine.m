% Test script for composition parsing and live database querying
compStr = 'Al 1.0, Co 99.0';
compBasis = 'wt%';

% 1. Periodic Table Atomic Masses
elemMap = containers.Map(...
    {'Al', 'Co', 'Ni', 'Fe', 'Cr', 'Ti', 'V', 'Mo', 'W', 'Nb', 'Ta', 'C', 'Si', 'Mn', 'Cu', 'Zr', 'Mg', 'Zn', 'Sn', 'Hf', 'Re'}, ...
    [26.982, 58.933, 58.693, 55.845, 51.996, 47.867, 50.942, 95.95, 183.84, 92.906, 180.95, 12.011, 28.085, 54.938, 63.546, 91.224, 24.305, 65.38, 118.71, 178.49, 186.21]);

% 2. Parse elements and percentages
tokens = regexp(compStr, '([A-Za-z]{1,2})\s*[:=]?\s*([0-9\.]+|[Bb]al(?:ance)?)', 'tokens');
elems = {}; vals = []; hasBal = false; balElem = '';
for k = 1:numel(tokens)
    el = [upper(tokens{k}{1}(1)), lower(tokens{k}{1}(2:end))];
    valStr = tokens{k}{2};
    if strcmpi(valStr, 'bal') || strcmpi(valStr, 'balance')
        hasBal = true;
        balElem = el;
    else
        v = str2double(valStr);
        if ~isnan(v)
            elems{end+1} = el;
            vals(end+1) = v;
        end
    end
end

if hasBal
    remainder = max(0, 100 - sum(vals));
    elems{end+1} = balElem;
    vals(end+1) = remainder;
end

% Normalize
sumVal = sum(vals);
if sumVal > 0 && abs(sumVal - 100) > 0.01
    vals = vals / sumVal * 100;
end

% 3. Convert between wt% and at%
atPct = zeros(size(vals));
wtPct = zeros(size(vals));

if strcmpi(compBasis, 'wt%')
    wtPct = vals;
    moles = zeros(size(vals));
    for k = 1:numel(elems)
        if isKey(elemMap, elems{k})
            M = elemMap(elems{k});
        else
            M = 50.0;
        end
        moles(k) = wtPct(k) / M;
    end
    atPct = moles / sum(moles) * 100;
else
    atPct = vals;
    masses = zeros(size(vals));
    for k = 1:numel(elems)
        if isKey(elemMap, elems{k})
            M = elemMap(elems{k});
        else
            M = 50.0;
        end
        masses(k) = atPct(k) * M;
    end
    wtPct = masses / sum(masses) * 100;
end

% Display Results
disp('Parsed Composition:');
for k = 1:numel(elems)
    fprintf('  %s: %.2f wt%% | %.2f at%%\n', elems{k}, wtPct(k), atPct(k));
end

% Formulate clean alloy formula string
partsWt = {};
partsAt = {};
for k = 1:numel(elems)
    partsWt{end+1} = sprintf('%s-%.1f', elems{k}, wtPct(k));
    partsAt{end+1} = sprintf('%s-%.1f', elems{k}, atPct(k));
end
formulaStr = sprintf('%s (wt%%)  <=>  %s (at%%)', strjoin(partsWt, ' '), strjoin(partsAt, ' '));
disp(['Formula: ' formulaStr]);
