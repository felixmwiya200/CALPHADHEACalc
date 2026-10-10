opts = weboptions('Timeout', 5.0, 'UserAgent', 'MaterialPropertiesApp/2.0 (mailto:researcher@matlab.org)');
testQueries = {
    'Co-Al alloy density temperature',
    'Ni-Al alloy thermal conductivity',
    'Al-1.0 superalloy gamma prime',
    'Cobalt specific heat temperature'
};

for i = 1:numel(testQueries)
    q = urlencode(testQueries{i});
    url = sprintf('https://api.openalex.org/works?search=%s&per_page=1', q);
    try
        res = webread(url, opts);
        if ~isempty(res.results)
            it = res.results(1);
            if iscell(it), it = it{1}; end
            venue = 'ScienceDirect / Scopus Indexed';
            if isfield(it, 'primary_location') && ~isempty(it.primary_location) && isfield(it.primary_location, 'source') && ~isempty(it.primary_location.source)
                venue = it.primary_location.source.display_name;
            end
            fprintf('Query: %s\n', testQueries{i});
            fprintf('  Title: %s\n', it.title);
            fprintf('  DOI:   %s\n', it.doi);
            fprintf('  Cites: %d\n', it.cited_by_count);
            fprintf('  Venue: %s\n', venue);
        end
    catch ME
        fprintf('Query: %s -> Error: %s\n', testQueries{i}, ME.message);
    end
end
