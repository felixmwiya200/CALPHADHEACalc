function test_oxides()
    try
        % Read lines from HEAOxideDatabase.m
        fid = fopen('HEAOxideDatabase.m');
        lines = {};
        while ~feof(fid)
            lines{end+1} = fgetl(fid);
        end
        fclose(fid);

        % Extract lines between list = [ and ];
        startIdx = 0; endIdx = 0;
        for i = 1:numel(lines)
            if contains(lines{i}, 'list = [')
                startIdx = i + 1;
            end
            if startIdx > 0 && strcmp(strtrim(lines{i}), '];')
                endIdx = i - 1;
                break;
            end
        end

        block = strjoin(lines(startIdx:endIdx), newline);
        % Split by 'struct('
        items = strsplit(block, 'struct(');
        allStructs = {};
        for k = 2:numel(items)
            chunk = items{k};
            % clean up trailing commas and dots
            chunk = regexprep(chunk, '[\,\s\.\.]*$', '');
            chunk = ['struct(' chunk];
            try
                st = eval(chunk);
                allStructs{end+1} = st;
            catch err
                fprintf('Eval error on struct #%d: %s\n', k-1, err.message);
            end
        end
        fprintf('Successfully evaluated %d structs\n', numel(allStructs));

        % Now test accumulating into array
        arr = allStructs{1};
        for k = 2:numel(allStructs)
            try
                arr = [arr, allStructs{k}];
            catch err
                fprintf('Concatenation failure at struct #%d: %s\n', k, err.message);
                disp(allStructs{k});
                return;
            end
        end
        fprintf('All %d structs concatenated successfully into arr!\n', numel(arr));
    catch err
        disp(err.message);
    end
end
