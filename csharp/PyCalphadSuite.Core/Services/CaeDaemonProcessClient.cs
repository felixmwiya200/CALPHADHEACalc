// <copyright file="CaeDaemonProcessClient.cs" company="PyCALPHAD Materials CAE">
// Robust IPC process communication client managing the headless Python CAE daemon.
// </copyright>

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Core.Services
{
    public class CaeDaemonProcessClient : IDisposable
    {
        private readonly Process _process;
        private readonly StreamWriter _stdin;
        private readonly ConcurrentDictionary<long, TaskCompletionSource<string>> _pendingRequests = new();
        private readonly CancellationTokenSource _cts = new();
        private readonly StringBuilder _stderrHistory = new();
        private long _requestIdCounter = 0;
        private bool _isDisposed = false;

        public event Action<string>? LogReceived;
        public event Action<string>? ErrorReceived;
        public event Action<string>? CalcLogReceived;
        public event Action<double, Dictionary<string, double>>? StepProgressReceived;

        public CaeDaemonProcessClient(string pythonExecutable = "python", string? scriptPath = null)
        {
            var resolvedScript = ResolveDaemonScript(scriptPath);
            var workspaceDir = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(resolvedScript)!, "..", ".."));
            var resolvedPython = ResolvePythonExecutable(pythonExecutable, workspaceDir);

            var psi = new ProcessStartInfo
            {
                FileName = resolvedPython,
                Arguments = $"-u -X utf8 \"{resolvedScript}\"",
                WorkingDirectory = workspaceDir,
                UseShellExecute = false,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            // Ensure UTF-8 I/O in Python subprocess even when launched from Explorer shortcuts
            psi.Environment["PYTHONIOENCODING"] = "utf-8";
            psi.Environment["PYTHONUTF8"] = "1";

            _process = new Process { StartInfo = psi };
            if (!_process.Start())
            {
                throw new InvalidOperationException($"Failed to launch Python CAE daemon ({resolvedPython}) at: {resolvedScript}");
            }

            _stdin = new StreamWriter(_process.StandardInput.BaseStream, new UTF8Encoding(false))
            {
                AutoFlush = true
            };

            Task.Run(ReadStdoutLoop, _cts.Token);
            Task.Run(ReadStderrLoop, _cts.Token);
        }

        private static string ResolvePythonExecutable(string? preferred, string workspaceDir)
        {
            // 1. Check virtual environment inside workspace
            var venvCandidates = new[]
            {
                Path.Combine(workspaceDir, ".venv", "Scripts", "python.exe"),
                Path.Combine(workspaceDir, "venv", "Scripts", "python.exe"),
            };
            foreach (var v in venvCandidates)
            {
                if (File.Exists(v)) return v;
            }

            // 2. If preferred is an explicit existing file path
            if (!string.IsNullOrWhiteSpace(preferred) && File.Exists(preferred))
            {
                return preferred;
            }

            // 3. Probe PATH excluding Microsoft Store WindowsApps stub
            var pathVar = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
            foreach (var dir in pathVar.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
            {
                if (dir.Contains("WindowsApps", StringComparison.OrdinalIgnoreCase)) continue;
                var candidate = Path.Combine(dir.Trim(), "python.exe");
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }

            // 4. Probe common Windows Python installation directories (User & ProgramData)
            var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            var progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);

            var searchRoots = new[]
            {
                Path.Combine(localAppData, "Programs", "Python"),
                Path.Combine(userProfile, "anaconda3"),
                Path.Combine(userProfile, "miniconda3"),
                progFiles,
                @"C:\"
            };

            foreach (var root in searchRoots)
            {
                if (!Directory.Exists(root)) continue;
                var directPy = Path.Combine(root, "python.exe");
                if (File.Exists(directPy)) return directPy;

                try
                {
                    var subDirs = Directory.GetDirectories(root, "Python3*")
                        .OrderByDescending(d => d);
                    foreach (var sd in subDirs)
                    {
                        var py = Path.Combine(sd, "python.exe");
                        if (File.Exists(py)) return py;
                    }
                }
                catch
                {
                    // Skip restricted system folders
                }
            }

            // 5. Fallback to preferred command name
            return string.IsNullOrWhiteSpace(preferred) ? "python" : preferred;
        }

        private static string ResolveDaemonScript(string? explicitPath)
        {
            if (!string.IsNullOrEmpty(explicitPath) && File.Exists(explicitPath))
            {
                return Path.GetFullPath(explicitPath);
            }

            var dir = AppDomain.CurrentDomain.BaseDirectory;
            while (!string.IsNullOrEmpty(dir))
            {
                var candidate = Path.Combine(dir, "pycalphad_app", "server", "cae_daemon.py");
                if (File.Exists(candidate))
                {
                    return Path.GetFullPath(candidate);
                }
                var parent = Directory.GetParent(dir);
                if (parent == null || parent.FullName == dir) break;
                dir = parent.FullName;
            }

            var localFallback = Path.GetFullPath("pycalphad_app/server/cae_daemon.py");
            if (File.Exists(localFallback))
            {
                return localFallback;
            }

            throw new FileNotFoundException("Unable to locate pycalphad_app/server/cae_daemon.py in workspace tree.");
        }

        private async Task ReadStdoutLoop()
        {
            var reader = _process.StandardOutput;
            while (!_cts.IsCancellationRequested && !_process.HasExited)
            {
                var line = await reader.ReadLineAsync();
                if (line == null) break;
                if (string.IsNullOrWhiteSpace(line)) continue;

                try
                {
                    using var doc = JsonDocument.Parse(line);
                    if (doc.RootElement.TryGetProperty("id", out var idProp) && idProp.TryGetInt64(out var id))
                    {
                        if (_pendingRequests.TryRemove(id, out var tcs))
                        {
                            tcs.TrySetResult(line);
                        }
                    }
                    else if (doc.RootElement.TryGetProperty("type", out var typeProp))
                    {
                        var evType = typeProp.GetString();
                        if (evType == "log" && doc.RootElement.TryGetProperty("message", out var msgProp))
                        {
                            CalcLogReceived?.Invoke(msgProp.GetString() ?? string.Empty);
                        }
                        else if (evType == "step" && doc.RootElement.TryGetProperty("temperature", out var tProp))
                        {
                            double tK = tProp.GetDouble();
                            var phases = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
                            if (doc.RootElement.TryGetProperty("phases", out var phObj) && phObj.ValueKind == JsonValueKind.Object)
                            {
                                foreach (var kv in phObj.EnumerateObject())
                                {
                                    if (kv.Value.TryGetDouble(out var fv))
                                    {
                                        phases[kv.Name] = fv;
                                    }
                                }
                            }
                            StepProgressReceived?.Invoke(tK, phases);
                        }
                    }
                }
                catch (Exception ex)
                {
                    ErrorReceived?.Invoke($"Failed to parse JSON response: {ex.Message}");
                }
            }

            var exitCode = _process.HasExited ? _process.ExitCode : -1;
            var stderrTail = _stderrHistory.ToString();
            foreach (var kvp in _pendingRequests)
            {
                if (_pendingRequests.TryRemove(kvp.Key, out var pendingTcs))
                {
                    pendingTcs.TrySetException(new InvalidOperationException(
                        $"Python daemon exited prematurely with code {exitCode}.\n{stderrTail}"));
                }
            }
        }

        private async Task ReadStderrLoop()
        {
            var reader = _process.StandardError;
            while (!_cts.IsCancellationRequested && !_process.HasExited)
            {
                var line = await reader.ReadLineAsync();
                if (line == null) break;
                if (_stderrHistory.Length < 4096)
                {
                    _stderrHistory.AppendLine(line);
                }
                LogReceived?.Invoke(line);
            }
        }

        public async Task<T> SendRequestAsync<T>(string method, object? parameters = null, TimeSpan? timeout = null, CancellationToken ct = default)
        {
            var id = Interlocked.Increment(ref _requestIdCounter);
            var req = new CaeRequest
            {
                Id = id,
                Method = method,
                Params = parameters
            };

            var json = JsonSerializer.Serialize(req);
            var tcs = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
            _pendingRequests[id] = tcs;

            using var timeoutCts = new CancellationTokenSource(timeout ?? TimeSpan.FromSeconds(45));
            using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(ct, timeoutCts.Token);

            using var reg = linkedCts.Token.Register(() =>
            {
                if (_pendingRequests.TryRemove(id, out var removedTcs))
                {
                    if (timeoutCts.IsCancellationRequested)
                    {
                        removedTcs.TrySetException(new TimeoutException($"Request '{method}' (id: {id}) timed out."));
                    }
                    else
                    {
                        removedTcs.TrySetCanceled(ct);
                    }
                }
            });

            await _stdin.WriteLineAsync(json);

            var rawJson = await tcs.Task;
            var response = JsonSerializer.Deserialize<CaeResponse<T>>(rawJson);

            if (response == null)
            {
                throw new InvalidOperationException("Null response received from CAE daemon.");
            }

            if (!string.IsNullOrEmpty(response.Error))
            {
                throw new InvalidOperationException($"CAE Daemon Error: {response.Error}");
            }

            return response.Result!;
        }

        public Task<PingResult> PingAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<PingResult>("ping", null, timeout: TimeSpan.FromSeconds(30), ct: ct);
        }

        public Task<DatabaseCatalogResult> GetDatabasesAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<DatabaseCatalogResult>("get_databases", null, timeout: TimeSpan.FromSeconds(60), ct: ct);
        }

        public Task<ElementsResult> GetElementsAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<ElementsResult>("get_elements", null, timeout: TimeSpan.FromSeconds(45), ct: ct);
        }

        public Task<EquilibriumResult> CalculateEquilibriumAsync(EquilibriumRequest request, CancellationToken ct = default)
        {
            return SendRequestAsync<EquilibriumResult>("calculate_equilibrium", request, timeout: TimeSpan.FromSeconds(180), ct: ct);
        }

        public async Task InterruptCalculationAsync()
        {
            try
            {
                await SendRequestAsync<Dictionary<string, object>>("interrupt", null, timeout: TimeSpan.FromSeconds(5));
            }
            catch
            {
                // Ignore if daemon already completed or stopped
            }
        }

        public Task<SingleStepResult> CalculateSingleStepAsync(
            string dbName,
            Dictionary<string, double> comp,
            double temperatureK,
            double grainSizeUm = 25.0,
            string processType = "HVOF Thermal Spray",
            string basis = "wt%",
            double hatchPitchUm = 80.0,
            double laserPowerW = 275.0,
            double scanSpeedMmS = 800.0,
            double layerThicknessUm = 30.0,
            double coldWorkPct = 0.0,
            CancellationToken ct = default)
        {
            var p = new
            {
                database_name = dbName,
                composition = comp,
                basis = basis,
                temperature = temperatureK,
                grain_size_um = grainSizeUm,
                hatch_pitch_um = hatchPitchUm,
                laser_power_w = laserPowerW,
                scan_speed_mm_s = scanSpeedMmS,
                layer_thickness_um = layerThicknessUm,
                cold_work_pct = coldWorkPct,
                process_type = processType
            };
            return SendRequestAsync<SingleStepResult>("calculate_single_step", p, ct: ct);
        }

        public Task<SimulationModuleResult> RunSimulationModuleAsync(string module, string dbName, Dictionary<string, double> comp, object? moduleParams = null, CancellationToken ct = default)
        {
            var p = new Dictionary<string, object>
            {
                ["module"] = module,
                ["database_name"] = dbName,
                ["composition"] = comp,
                ["params"] = moduleParams ?? new object()
            };
            return SendRequestAsync<SimulationModuleResult>("run_simulation_module", p, timeout: TimeSpan.FromSeconds(45), ct: ct);
        }

        public Task<CaeExportResult> ExportCaeCardAsync(string format, string alloyName, Dictionary<string, double> comp, object? thermo = null, object? mech = null, CancellationToken ct = default)
        {
            var p = new
            {
                format = format,
                alloy_name = alloyName,
                composition = comp,
                thermo = thermo,
                mechanical = mech
            };
            return SendRequestAsync<CaeExportResult>("export_cae_card", p, ct: ct);
        }

        public Task<CrystalStructuresResponse> GetCrystalStructuresAsync(
            string dbName,
            Dictionary<string, double> comp,
            double temperatureK = 300.0,
            int supercellN = 2,
            double grainSizeUm = 25.0,
            string processType = "HVOF Thermal Spray",
            string basis = "wt%",
            CancellationToken ct = default)
        {
            var p = new
            {
                database_name = dbName,
                composition = comp,
                basis = basis,
                temperature = temperatureK,
                supercell_n = supercellN,
                grain_size_um = grainSizeUm,
                process_type = processType
            };
            return SendRequestAsync<CrystalStructuresResponse>("get_crystal_structures", p, timeout: TimeSpan.FromSeconds(45), ct: ct);
        }

        public Task<TdatDatabaseCatalogResponse> GetTdatDatabasesAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<TdatDatabaseCatalogResponse>("get_tdat_databases", new { }, ct: ct);
        }

        public Task<TdatSearchResponse> SearchTdatSpeciesAsync(string dbName, string query, int limit = 150, CancellationToken ct = default)
        {
            var p = new
            {
                database_name = dbName,
                query = query,
                limit = limit
            };
            return SendRequestAsync<TdatSearchResponse>("search_tdat_species", p, ct: ct);
        }

        public Task<PourbaixDiagramDto> CalculatePourbaixAsync(
            Dictionary<string, double> comp,
            string dbName = "thermo.com.V8.R6+.tdat",
            double temperatureC = 25.0,
            double ionActivity = 1e-6,
            string basis = "at%",
            CancellationToken ct = default)
        {
            var p = new
            {
                composition = comp,
                database_name = dbName,
                temperature_c = temperatureC,
                ion_activity = ionActivity,
                basis = basis
            };
            return SendRequestAsync<PourbaixDiagramDto>("calculate_pourbaix", p, timeout: TimeSpan.FromSeconds(30), ct: ct);
        }

        public Task<HeaLiteratureSearchResponseDto> SearchHeaLiteratureAsync(
            string query = "",
            string phase = "",
            string solutionType = "",
            string studyType = "",
            int limit = 50,
            int offset = 0,
            CancellationToken ct = default)
        {
            var p = new
            {
                query = query,
                phase = phase,
                solution_type = solutionType,
                study_type = studyType,
                limit = limit,
                offset = offset
            };
            return SendRequestAsync<HeaLiteratureSearchResponseDto>("search_hea_literature", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<HeaLiteratureSearchResponseDto> FindNearestHeaLiteratureAsync(
            string targetOrFormula,
            int topK = 10,
            CancellationToken ct = default)
        {
            var p = new
            {
                target = targetOrFormula,
                top_k = topK
            };
            return SendRequestAsync<HeaLiteratureSearchResponseDto>("find_nearest_hea_literature", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<HeaLiteratureItemDto> GetHeaLiteratureDetailsAsync(int alloyId, CancellationToken ct = default)
        {
            var p = new { id = alloyId };
            return SendRequestAsync<HeaLiteratureItemDto>("get_hea_literature_details", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<HeaLiteratureStatsDto> GetHeaLiteratureStatsAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<HeaLiteratureStatsDto>("get_hea_literature_stats", new { }, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<SdatDatabaseCatalogResponse> GetSdatDatabasesAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<SdatDatabaseCatalogResponse>("get_sdat_databases", new { }, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<SdatDetailDto> GetSdatDetailsAsync(string filename, CancellationToken ct = default)
        {
            var p = new { filename = filename };
            return SendRequestAsync<SdatDetailDto>("get_sdat_details", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<SdatSurfaceSpeciationDto> CalculateSdatSurfaceSpeciationAsync(
            string filename = "FeOH.sdat",
            double temperatureC = 25.0,
            CancellationToken ct = default)
        {
            var p = new
            {
                filename = filename,
                temperature_c = temperatureC
            };
            return SendRequestAsync<SdatSurfaceSpeciationDto>("calculate_sdat_surface_speciation", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<OadStreamsCatalogResponse> GetOadStreamsAsync(CancellationToken ct = default)
        {
            return SendRequestAsync<OadStreamsCatalogResponse>("get_oad_streams", new { }, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<ElectrolyteConductivityDto> CalculateElectrolyteConductivityAsync(
            double temperatureC = 25.0,
            Dictionary<string, double>? molarities = null,
            CancellationToken ct = default)
        {
            var p = new
            {
                temperature_c = temperatureC,
                molarities = molarities
            };
            return SendRequestAsync<ElectrolyteConductivityDto>("calculate_electrolyte_conductivity", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        #region Compound Energy Formalism (CEF) & Advanced CALPHAD Methods

        public Task<CefCalculationResultDto> CalculateCefEnergyAsync(
            string phaseName,
            List<CefSublatticeDto> sublattices,
            Dictionary<string, Dictionary<string, double>>? endMembers = null,
            Dictionary<string, List<List<double>>>? binaryInteractions = null,
            Dictionary<string, double>? magneticParams = null,
            double tStartC = 25.0,
            double tEndC = 1200.0,
            double tStepC = 25.0,
            CancellationToken ct = default)
        {
            var p = new
            {
                phase_name = phaseName,
                sublattices = sublattices,
                end_members = endMembers,
                binary_interactions = binaryInteractions,
                magnetic_params = magneticParams,
                t_start_c = tStartC,
                t_end_c = tEndC,
                t_step_c = tStepC
            };
            return SendRequestAsync<CefCalculationResultDto>("calculate_cef_energy", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<TernaryExtrapolationResultDto> CalculateExtrapolationAsync(
            double x3Fixed = 0.2,
            double temperatureC = 1000.0,
            List<List<double>>? rk12 = null,
            List<List<double>>? rk23 = null,
            List<List<double>>? rk13 = null,
            int numPoints = 50,
            CancellationToken ct = default)
        {
            var p = new
            {
                x3_fixed = x3Fixed,
                temperature_c = temperatureC,
                rk_12 = rk12,
                rk_23 = rk23,
                rk_13 = rk13,
                num_points = numPoints
            };
            return SendRequestAsync<TernaryExtrapolationResultDto>("calculate_extrapolation", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<UhtcWettingResultDto> CalculateUhtcWettingAsync(
            string substrate = "ZrB2",
            Dictionary<string, double>? initialLiquid = null,
            double temperatureC = 1130.0,
            int steps = 100,
            double coolingRateKS = 10.0,
            CancellationToken ct = default)
        {
            var p = new
            {
                substrate = substrate,
                initial_liquid_composition = initialLiquid,
                temperature_c = temperatureC,
                steps = steps,
                cooling_rate_k_s = coolingRateKS
            };
            return SendRequestAsync<UhtcWettingResultDto>("calculate_uhtc_wetting", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        #region Refractory High Entropy Alloys (RHEA) Methods

        public async Task<List<RheaBenchmarkDto>> GetRheaBenchmarksAsync(CancellationToken ct = default)
        {
            var p = new { };
            var res = await SendRequestAsync<Dictionary<string, JsonElement>>("get_rhea_benchmarks", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
            if (res != null && res.TryGetValue("benchmarks", out var elem))
            {
                var list = JsonSerializer.Deserialize<List<RheaBenchmarkDto>>(elem.GetRawText());
                return list ?? new List<RheaBenchmarkDto>();
            }
            return new List<RheaBenchmarkDto>();
        }

        public Task<RheaBenchmarkDto> GetRheaBenchmarkDetailAsync(string key, CancellationToken ct = default)
        {
            var p = new { key = key };
            return SendRequestAsync<RheaBenchmarkDto>("get_rhea_benchmarks", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<Dictionary<string, RheaStrengthCurveItemDto>> GetRheaStrengthCurvesAsync(List<string>? keys = null, CancellationToken ct = default)
        {
            var p = new { keys = keys };
            return SendRequestAsync<Dictionary<string, RheaStrengthCurveItemDto>>("get_rhea_strength_curves", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        public Task<RheaLiteratureQueryResultDto> QueryRheaLiteratureAsync(
            List<string>? elements = null,
            string phase = "",
            int limit = 50,
            int offset = 0,
            CancellationToken ct = default)
        {
            var p = new
            {
                elements = elements,
                phase = phase,
                limit = limit,
                offset = offset
            };
            return SendRequestAsync<RheaLiteratureQueryResultDto>("query_rhea_literature", p, timeout: TimeSpan.FromSeconds(10), ct: ct);
        }

        #endregion

        #region Binary Phase Diagram Methods

        public async Task<List<string>> GetBinarySystemsAsync(List<string>? activeElements = null, string? databaseName = null, CancellationToken ct = default)
        {
            var p = new { active_elements = activeElements, database_name = databaseName };
            var res = await SendRequestAsync<BinarySystemsResultDto>("get_binary_systems", p, timeout: TimeSpan.FromSeconds(25), ct: ct);
            return res?.Systems ?? new List<string>();
        }

        public Task<BinaryDiagramDto> CalculateBinaryDiagramAsync(
            string systemName,
            string tempUnit = "C",
            int nPoints = 120,
            CancellationToken ct = default)
        {
            var p = new
            {
                system_name = systemName,
                temp_unit = tempUnit,
                n_points = nPoints
            };
            return SendRequestAsync<BinaryDiagramDto>("calculate_binary_diagram", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<BinaryLeverRuleDto> EvaluateBinaryLeverRuleAsync(
            string systemName,
            double xQuery,
            double tQuery,
            string tempUnit = "C",
            CancellationToken ct = default)
        {
            var p = new
            {
                system_name = systemName,
                x_query = xQuery,
                t_query = tQuery,
                temp_unit = tempUnit
            };
            return SendRequestAsync<BinaryLeverRuleDto>("evaluate_binary_lever_rule", p, timeout: TimeSpan.FromSeconds(25), ct: ct);
        }

        public async Task<List<TernarySystemSummaryDto>> GetTernarySystemsAsync(CancellationToken ct = default)
        {
            var res = await SendRequestAsync<TernarySystemsContainerDto>("get_ternary_systems", new { }, timeout: TimeSpan.FromSeconds(10), ct: ct);
            return res?.Systems ?? new List<TernarySystemSummaryDto>();
        }

        public Task<TernaryDiagramDto> CalculateTernaryDiagramAsync(
            string systemName,
            string diagramType = "isothermal",
            double temperatureC = 800.0,
            string tempUnit = "C",
            CancellationToken ct = default)
        {
            var p = new
            {
                system_name = systemName,
                diagram_type = diagramType,
                temperature_c = temperatureC,
                temp_unit = tempUnit
            };
            return SendRequestAsync<TernaryDiagramDto>("calculate_ternary_diagram", p, timeout: TimeSpan.FromSeconds(20), ct: ct);
        }

        #region Kaufman-Mallik Phase Diagram Formalism Methods (Mallik 1986)

        public Task<KaufmanMallikBinaryResultDto> CalculateKaufmanMallikBinaryAsync(
            double tKelvin,
            double deltaGa,
            double deltaGb,
            double eAlpha,
            double eBeta,
            bool useCalories = false,
            double[]? initialGuess = null,
            CancellationToken ct = default)
        {
            var p = new
            {
                t_kelvin = tKelvin,
                delta_g_a = deltaGa,
                delta_g_b = deltaGb,
                e_alpha = eAlpha,
                e_beta = eBeta,
                use_calories = useCalories,
                initial_guess = initialGuess ?? new[] { 0.1, 0.9 }
            };
            return SendRequestAsync<KaufmanMallikBinaryResultDto>("calculate_kaufman_mallik_binary", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<ParameterInversionResultDto> InvertInteractionParametersAsync(
            double tKelvin,
            double xAlpha,
            double xBeta,
            double deltaGa,
            double deltaGb,
            bool useCalories = false,
            CancellationToken ct = default)
        {
            var p = new
            {
                t_kelvin = tKelvin,
                x_alpha = xAlpha,
                x_beta = xBeta,
                delta_g_a = deltaGa,
                delta_g_b = deltaGb,
                use_calories = useCalories
            };
            return SendRequestAsync<ParameterInversionResultDto>("invert_interaction_parameters", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public Task<MiscibilityGapResultDto> CalculateMiscibilityGapAsync(
            double interactionParameter,
            double tKelvin,
            bool useCalories = false,
            CancellationToken ct = default)
        {
            var p = new
            {
                interaction_parameter = interactionParameter,
                t_kelvin = tKelvin,
                use_calories = useCalories
            };
            return SendRequestAsync<MiscibilityGapResultDto>("calculate_miscibility_gap", p, timeout: TimeSpan.FromSeconds(15), ct: ct);
        }

        public async Task<Dictionary<string, KaufmanMallikPresetDto>> GetKaufmanMallikPresetsAsync(CancellationToken ct = default)
        {
            var res = await SendRequestAsync<KaufmanMallikPresetsContainerDto>("get_kaufman_mallik_presets", new { }, timeout: TimeSpan.FromSeconds(10), ct: ct);
            return res?.Presets ?? new Dictionary<string, KaufmanMallikPresetDto>();
        }

        #endregion

        #endregion

        #endregion

        public void Dispose()
        {
            if (_isDisposed) return;
            _isDisposed = true;

            _cts.Cancel();
            try
            {
                _stdin.Close();
                if (!_process.HasExited)
                {
                    _process.Kill(entireProcessTree: true);
                }
                _process.Dispose();
            }
            catch
            {
                // Suppress shutdown race exceptions
            }
            _cts.Dispose();
        }
    }
}
