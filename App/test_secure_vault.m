function test_secure_vault()
    % Comprehensive verification suite for SecureDataVault 4-layer security
    fprintf('=================================================================\n');
    fprintf('  TESTING SECUREDATAVAULT (4-LAYER DEFENSE-IN-DEPTH)\n');
    fprintf('=================================================================\n');
    
    numPassed = 0;
    numTotal  = 0;
    
    function check(cond, msg)
        numTotal = numTotal + 1;
        if cond
            numPassed = numPassed + 1;
            fprintf('  [PASS] %s\n', msg);
        else
            fprintf('  [FAIL] %s\n', msg);
            error('Test failed: %s', msg);
        end
    end

    %% TEST 1: Layer 1 - Telemetry Suppression
    fprintf('\n--- Test 1: Layer 1 Telemetry Suppression ---\n');
    try
        SecureDataVault.applyTelemetrySuppression();
        check(true, 'Telemetry suppression invoked without error');
    catch ME
        check(false, sprintf('Telemetry suppression error: %s', ME.message));
    end

    %% TEST 2: Layer 2 - DLP Egress Sanitizer
    fprintf('\n--- Test 2: Layer 2 DLP Egress Sanitizer ---\n');
    safeUrl1 = 'https://api.openalex.org/works?search=CoCrFeMnNi+density&per_page=5';
    safeUrl2 = 'https://api.crossref.org/works?query=NbMoTaW+thermal+conductivity&rows=5';
    badUrl1  = 'http://insecure.api.com/works?search=alloy'; % Insecure HTTP
    badUrl2  = 'https://api.openalex.org/works?search=Co20Cr20Fe20Mn20Ni20+at%25'; % Contains concentration
    badUrl3  = 'https://malicious.server.com/upload'; % Unauthorized domain

    check(SecureDataVault.validateOutboundUrl(safeUrl1), 'Legitimate OpenAlex element query allowed');
    check(SecureDataVault.validateOutboundUrl(safeUrl2), 'Legitimate Crossref element query allowed');
    check(~SecureDataVault.validateOutboundUrl(badUrl1), 'Non-HTTPS protocol blocked');
    check(~SecureDataVault.validateOutboundUrl(badUrl2), 'Proprietary percentage pattern blocked');
    check(~SecureDataVault.validateOutboundUrl(badUrl3), 'Unauthorized domain blocked');

    %% TEST 3: Layer 3 - SHA-256 Hashing & AES-256-GCM Encryption
    fprintf('\n--- Test 3: Layer 3 Cryptographic Encryption & Integrity ---\n');
    testDir = fullfile(pwd, 'test_vault_scratch');
    if ~exist(testDir, 'dir'), mkdir(testDir); end
    
    rawFile = fullfile(testDir, 'sample_hea_data.dat');
    sampleContent = sprintf('T (K)\tDensity\tCp\tThermalCond\n293.15\t8050.2\t450.0\t11.5\n500.00\t7990.1\t480.0\t14.2\n1000.0\t7820.0\t550.0\t20.1\n');
    writelines(sampleContent, rawFile);
    
    origHash = SecureDataVault.computeSHA256(rawFile);
    check(~isempty(origHash) && length(origHash) == 64, sprintf('Original SHA-256 computed: %s', origHash(1:16)));

    passphrase = 'MasterResearchKey#2026';
    vaultFile = fullfile(testDir, 'sample_hea_data.hea.vault');
    decryptedFile = fullfile(testDir, 'sample_hea_data_decrypted.dat');

    % Encrypt
    tEnc = tic;
    SecureDataVault.encryptFile(rawFile, vaultFile, passphrase);
    encElapsed = toc(tEnc);
    check(isfile(vaultFile), sprintf('Vault file created successfully (in %.2fs)', encElapsed));
    
    % Verify vault file is NOT plaintext
    fidV = fopen(vaultFile, 'rb');
    vBytes = fread(fidV, '*uint8');
    fclose(fidV);
    check(~contains(char(vBytes'), '293.15'), 'Ciphertext does not contain plaintext data');

    % Decrypt with correct passphrase
    tDec = tic;
    SecureDataVault.decryptFile(vaultFile, decryptedFile, passphrase);
    decElapsed = toc(tDec);
    check(isfile(decryptedFile), sprintf('File decrypted successfully (in %.2fs)', decElapsed));

    decHash = SecureDataVault.computeSHA256(decryptedFile);
    check(strcmp(origHash, decHash), 'Decrypted file matches original SHA-256 byte-for-byte');

    %% TEST 4: Layer 3 - Anti-Tampering & Wrong Passphrase Rejection
    fprintf('\n--- Test 4: Anti-Tampering & Authentication Rejection ---\n');
    wrongPass = 'WrongPassword#999';
    wrongAttemptPassed = false;
    try
        SecureDataVault.decryptFile(vaultFile, fullfile(testDir, 'fail.dat'), wrongPass);
        wrongAttemptPassed = true;
    catch
        % Expected failure
    end
    check(~wrongAttemptPassed, 'Decryption rejected when wrong passphrase supplied');

    % Tamper with 1 byte of ciphertext
    tamperedVault = fullfile(testDir, 'tampered.hea.vault');
    copyfile(vaultFile, tamperedVault);
    fidT = fopen(tamperedVault, 'r+b');
    fseek(fidT, -10, 'eof');
    b = fread(fidT, 1, '*uint8');
    fseek(fidT, -10, 'eof');
    fwrite(fidT, bitxor(b, uint8(1)), 'uint8');
    fclose(fidT);
    
    tamperAttemptPassed = false;
    try
        SecureDataVault.decryptFile(tamperedVault, fullfile(testDir, 'tamper_out.dat'), passphrase);
        tamperAttemptPassed = true;
    catch
        % Expected failure due to AEAD bad tag or checksum
    end
    check(~tamperAttemptPassed, 'Decryption rejected when ciphertext was tampered with');

    %% TEST 5: Layer 3 - NIST SP 800-88 Rev 1 Secure Shredding
    fprintf('\n--- Test 5: NIST SP 800-88 File Overwrite Shredding ---\n');
    fileToShred = fullfile(testDir, 'temp_sensitive_export.dat');
    writelines('PROPRIETARY ALLOY RESEARCH DATA 12345', fileToShred);
    check(isfile(fileToShred), 'Temporary sensitive file exists prior to shredding');
    
    SecureDataVault.secureShred(fileToShred);
    check(~isfile(fileToShred), 'Temporary file successfully sanitized and unlinked from disk');

    %% TEST 6: Layer 4 - In-Memory Sanitization
    fprintf('\n--- Test 6: Layer 4 In-Memory Sanitization ---\n');
    secretMatrix = rand(100, 100);
    check(sum(secretMatrix(:)) > 0, 'Secret matrix populated in memory');
    SecureDataVault.zeroCallerVar('secretMatrix');
    check(all(secretMatrix(:) == 0), 'Secret matrix in-place memory zeroed via zeroCallerVar');
    
    testArr = SecureDataVault.zeroArray(rand(20, 20));
    check(all(testArr(:) == 0), 'zeroArray returns zeroed memory buffer');

    % Clean up scratch directory
    if exist(testDir, 'dir'), rmdir(testDir, 's'); end

    %% SUMMARY
    fprintf('\n=================================================================\n');
    fprintf('  ALL %d/%d SECURE VAULT TESTS PASSED PERFECTLY!\n', numPassed, numTotal);
    fprintf('=================================================================\n');
end
