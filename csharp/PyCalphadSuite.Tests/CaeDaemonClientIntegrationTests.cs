// <copyright file="CaeDaemonClientIntegrationTests.cs" company="PyCALPHAD Materials CAE">
// End-to-end integration tests between C# IPC client and Python calculation daemon.
// </copyright>

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using PyCalphadSuite.Core.Models;
using PyCalphadSuite.Core.Services;
using Xunit;

namespace PyCalphadSuite.Tests
{
    public class DaemonFixture : IDisposable
    {
        public CaeDaemonProcessClient Client { get; }

        public DaemonFixture()
        {
            Client = new CaeDaemonProcessClient("python");
        }

        public void Dispose()
        {
            Client.Dispose();
        }
    }

    public class CaeDaemonClientIntegrationTests : IClassFixture<DaemonFixture>
    {
        private readonly CaeDaemonProcessClient _client;

        public CaeDaemonClientIntegrationTests(DaemonFixture fixture)
        {
            _client = fixture.Client;
        }

        [Fact]
        public async Task TestPingReturnsReady()
        {
            var res = await _client.PingAsync();
            Assert.NotNull(res);
            Assert.Equal("ok", res.Status);
            Assert.True(res.PyCalphadReady);
            Assert.False(string.IsNullOrEmpty(res.Version));
        }

        [Fact]
        public async Task TestGetDatabasesReturnsCatalog()
        {
            var res = await _client.GetDatabasesAsync();
            Assert.NotNull(res);
            Assert.Equal(14, res.Names.Count);
            Assert.Contains("High Entropy Alloys", res.Names);
            Assert.Contains("Thermal Spray Coatings", res.Names);
            Assert.Contains("Nickel Based Superalloy", res.Names);
            Assert.Contains("Solder Alloy", res.Names);

            var hea = res.Databases["High Entropy Alloys"];
            Assert.NotNull(hea);
            Assert.Contains("CoCrFeMnNi (Cantor Alloy)", hea.Presets.Keys);
        }

        [Fact]
        public async Task TestCalculateEquilibriumCantorAlloy()
        {
            var req = new EquilibriumRequest
            {
                DatabaseName = "High Entropy Alloys",
                Composition = new Dictionary<string, double>
                {
                    { "Co", 20 }, { "Cr", 20 }, { "Fe", 20 }, { "Mn", 20 }, { "Ni", 20 }
                },
                Basis = "at%",
                CalcMode = "fast",
                GrainSizeUm = 30.0
            };

            var res = await _client.CalculateEquilibriumAsync(req);
            Assert.NotNull(res);
            Assert.Equal("success", res.Status);
            Assert.Equal("High Entropy Alloys", res.DatabaseName);
            Assert.NotNull(res.Thermo);
            Assert.NotNull(res.Transformations);
            Assert.NotNull(res.Mechanical);
            Assert.NotNull(res.PhaseCurves);
            Assert.NotEmpty(res.PhaseCurves!.Series);
            Assert.NotNull(res.TempSeries);
            Assert.NotEmpty(res.TempSeries!.Density);
            Assert.NotNull(res.Xrd);
            Assert.NotEmpty(res.Xrd!.TwoTheta);
            Assert.NotEmpty(res.ValidationTable);
            Assert.NotEmpty(res.ApplicationScores);
            Assert.Equal(21, res.Piecewise.Count);
            Assert.All(res.Piecewise, pw =>
            {
                Assert.False(string.IsNullOrWhiteSpace(pw.Property));
                Assert.False(string.IsNullOrWhiteSpace(pw.Code));
                Assert.False(string.IsNullOrWhiteSpace(pw.SmoothExpr));
            });
        }

        [Fact]
        public async Task TestGetElementsReturns118IupacElements()
        {
            var res = await _client.GetElementsAsync();
            Assert.NotNull(res);
            Assert.Equal(118, res.Elements.Count);
            Assert.Contains(res.Elements, e => e.Symbol == "Co" && e.Z == 27);
            Assert.Contains(res.Elements, e => e.Symbol == "Ti" && e.Z == 22);
        }

        [Fact]
        public async Task TestRunSimulationModuleTttCct()
        {
            var comp = new Dictionary<string, double>
            {
                { "Fe", 98.0 }, { "Cr", 1.2 }, { "C", 0.4 }, { "Mn", 0.4 }
            };
            var res = await _client.RunSimulationModuleAsync("ttt_cct", "General Steel", comp);
            Assert.NotNull(res);
            Assert.Equal(2, res.Curves.Count);
            Assert.Contains("Ms =", res.Summary);
        }

        [Fact]
        public async Task TestCalculateSingleStepCantorAlloy()
        {
            var comp = new Dictionary<string, double>
            {
                { "Co", 20 }, { "Cr", 20 }, { "Fe", 20 }, { "Mn", 20 }, { "Ni", 20 }
            };

            var res = await _client.CalculateSingleStepAsync("High Entropy Alloys", comp, 1400.0);
            Assert.NotNull(res);
            Assert.Equal(1400.0, res.Temperature);
            Assert.NotEmpty(res.Phases);
        }

        [Fact]
        public async Task TestExportCaeCardAbaqus()
        {
            var comp = new Dictionary<string, double>
            {
                { "Co", 20 }, { "Cr", 20 }, { "Fe", 20 }, { "Mn", 20 }, { "Ni", 20 }
            };

            var res = await _client.ExportCaeCardAsync("abaqus", "Cantor_HEA", comp);
            Assert.NotNull(res);
            Assert.Equal("abaqus", res.Format);
            Assert.Contains("*MATERIAL, NAME=Cantor_HEA", res.Content);
            Assert.Contains("*ELASTIC", res.Content);

            var simufact = await _client.ExportCaeCardAsync("simufact", "Cantor_HEA", comp);
            Assert.NotNull(simufact);
            Assert.Equal("simufact", simufact.Format);
            Assert.Contains("<SimufactMaterial", simufact.Content);
            Assert.Contains("format=\"MatildA\"", simufact.Content);
            Assert.Contains("</SimufactMaterial>", simufact.Content);

            var forge = await _client.ExportCaeCardAsync("forge", "Cantor_HEA", comp);
            Assert.Contains("TRANSVALOR FORGE", forge.Content);

            var deform = await _client.ExportCaeCardAsync("deform", "Cantor_HEA", comp);
            Assert.Contains("SFTC DEFORM-3D", deform.Content);
        }

        [Fact]
        public void TestCompositionLibrarySaveLoadAndCsvRoundTrip()
        {
            var tmpDir = Path.Combine(Path.GetTempPath(), "PyCalphadTest_" + Guid.NewGuid().ToString("N"));
            try
            {
                var svc = new CompositionLibraryService(tmpDir);
                var profile = new SavedCompositionProfile
                {
                    Name = "Custom_Cantor_Nb",
                    DatabaseName = "High Entropy Alloys",
                    Basis = "at%",
                    Composition = new Dictionary<string, double> { { "Co", 19 }, { "Cr", 19 }, { "Fe", 19 }, { "Mn", 19 }, { "Ni", 19 }, { "Nb", 5 } },
                    GrainSizeUm = 18.5,
                    Notes = "Laves C14 reinforced alloy"
                };

                svc.SaveToLibrary(profile);
                var loadedLib = svc.LoadLibrary();
                Assert.Single(loadedLib);
                Assert.Equal("Custom_Cantor_Nb", loadedLib[0].Name);
                Assert.Equal(5.0, loadedLib[0].Composition["Nb"]);

                // File round-trip (.comp.json + .csv)
                var jsonFile = Path.Combine(tmpDir, "test.comp.json");
                CompositionLibraryService.SaveProfileToFile(profile, jsonFile);
                var fromJson = CompositionLibraryService.LoadProfileFromFile(jsonFile);
                Assert.Equal("at%", fromJson.Basis);
                Assert.Equal(18.5, fromJson.GrainSizeUm);

                var csvFile = Path.Combine(tmpDir, "test.csv");
                CompositionLibraryService.SaveProfileToFile(profile, csvFile);
                var fromCsv = CompositionLibraryService.LoadProfileFromFile(csvFile);
                Assert.Equal(6, fromCsv.Composition.Count);
                Assert.Equal(5.0, fromCsv.Composition["Nb"]);
            }
            finally
            {
                if (Directory.Exists(tmpDir)) Directory.Delete(tmpDir, true);
            }
        }

        [Fact]
        public async Task TestRunSimulationModuleImcLavesDbAndLavesEquilibrium()
        {
            var simRes = await _client.RunSimulationModuleAsync(
                "imc_laves_db",
                "High Entropy Alloys",
                new Dictionary<string, double> { { "Co", 0.222 }, { "Cr", 0.222 }, { "Fe", 0.222 }, { "Ni", 0.222 }, { "Nb", 0.112 } });

            Assert.NotNull(simRes.Imcs);
            Assert.True(simRes.Imcs!.Count >= 20);
            Assert.Contains(simRes.Imcs, row => row.TryGetValue("PhaseId", out var el) && el.GetString() == "LAVES_C14");
            Assert.Contains(simRes.Imcs, row => row.TryGetValue("PhaseId", out var el) && el.GetString() == "SIGMA");

            var eqReq = new EquilibriumRequest
            {
                DatabaseName = "High Entropy Alloys",
                Composition = new Dictionary<string, double> { { "Co", 22.2 }, { "Cr", 22.2 }, { "Fe", 22.2 }, { "Ni", 22.2 }, { "Nb", 11.2 } },
                Basis = "at%",
                CalcMode = "fast",
                TStart = 400.0,
                TStop = 1800.0
            };
            var eqRes = await _client.CalculateEquilibriumAsync(eqReq);

            Assert.Equal("success", eqRes.Status);
            Assert.NotNull(eqRes.PhaseCurves);
            Assert.True(eqRes.PhaseCurves!.Series.ContainsKey("Laves_C14"));
            Assert.True(eqRes.PhaseCurves.Series["Laves_C14"].Max() > 0.08);
        }

        [Fact]
        public async Task TestGitTdbCatalogRockwellVickersAndCalcLog()
        {
            var cat = await _client.GetDatabasesAsync();
            Assert.True(cat.TdbCatalog.Count >= 40);
            Assert.Contains(cat.TdbCatalog, t => t.Name == "LibreCALPHAD_mf_steel.tdb");
            Assert.Contains(cat.TdbCatalog, t => t.Name == "MatCalc_mc_fe_v2062_clean.tdb");
            Assert.Contains(cat.TdbCatalog, t => t.Name == "OpenCALPHAD_Al_Co_Cr_Fe_Ni.tdb");

            var eq = await _client.CalculateEquilibriumAsync(new EquilibriumRequest
            {
                DatabaseName = "General Steel",
                Composition = new Dictionary<string, double> { { "Fe", 98.0 }, { "C", 0.8 }, { "Mn", 0.7 }, { "Si", 0.5 } },
                Basis = "wt%",
                CalcMode = "fast"
            });

            Assert.Equal("success", eq.Status);
            Assert.NotEmpty(eq.CalcLog);
            Assert.Contains(eq.CalcLog, l => l.Contains("Calculating...to interrupt press the 's' key"));
            Assert.Contains(eq.CalcLog, l => l.Contains("T(K) ="));
            Assert.True(eq.Mechanical.ContainsKey("VickersHardness_HV"));
            Assert.True(eq.Mechanical.ContainsKey("RockwellHardness_HRC"));
            Assert.True(eq.Mechanical.ContainsKey("RockwellHardness_HRB"));
            Assert.True(eq.Mechanical.ContainsKey("RockwellHardness"));
            Assert.NotEmpty(eq.TempSeries!.HardnessHv);
            Assert.NotEmpty(eq.TempSeries.HardnessHrc);
            Assert.NotEmpty(eq.TempSeries.HardnessHrb);

            var step = await _client.CalculateSingleStepAsync("General Steel",
                new Dictionary<string, double> { { "Fe", 98.0 }, { "C", 0.8 }, { "Mn", 0.7 }, { "Si", 0.5 } },
                300.0, 25.0, "Wrought", "wt%");
            Assert.True(step.HardnessHv > 0);
            Assert.False(string.IsNullOrWhiteSpace(step.RockwellHardness));
        }

        [Fact]
        public async Task TestCompleteDatExportAndPlotCsvFormatterRoundTrip()
        {
            var eq = await _client.CalculateEquilibriumAsync(new EquilibriumRequest
            {
                DatabaseName = "High Entropy Alloys",
                Composition = new Dictionary<string, double> { { "Co", 20 }, { "Cr", 20 }, { "Fe", 20 }, { "Mn", 20 }, { "Ni", 20 } },
                Basis = "at%",
                CalcMode = "fast"
            });

            var profile = new SavedCompositionProfile
            {
                Name = "Cantor_Test_HEA",
                DatabaseName = "High Entropy Alloys",
                Basis = "at%",
                Composition = new Dictionary<string, double> { { "Co", 20 }, { "Cr", 20 }, { "Fe", 20 }, { "Mn", 20 }, { "Ni", 20 } },
                GrainSizeUm = 25.0
            };

            string dat = DatReportBuilder.BuildCompleteDatContent(eq, profile);
            Assert.Contains("[CHEMISTRY]", dat);
            Assert.Contains("[THERMODYNAMICS]", dat);
            Assert.Contains("[MECHANICAL]", dat);
            Assert.Contains("RockwellHardness_HRC =", dat);
            Assert.Contains("VickersHardness_HV =", dat);
            Assert.Contains("[TRANSPORT]", dat);
            Assert.Contains("[ENVIRONMENTAL]", dat);
            Assert.Contains("[COMSOL_PIECEWISE_21_PROPERTIES]", dat);
            Assert.Contains("[CALCULATION_LOG]", dat);
            Assert.Contains("[GRAPH_DATA_PHASE_EQUILIBRIUM]", dat);
            Assert.Contains("[GRAPH_DATA_SCHEIL_SOLIDIFICATION]", dat);
            Assert.Contains("[GRAPH_DATA_ELLINGHAM_STABILITY]", dat);
            Assert.Contains("[GRAPH_DATA_XRD_PATTERN]", dat);

            var tmpDat = Path.Combine(Path.GetTempPath(), $"test_export_{Guid.NewGuid():N}.dat");
            try
            {
                File.WriteAllText(tmpDat, dat);
                var reloaded = CompositionLibraryService.LoadProfileFromFile(tmpDat);
                Assert.Equal("at%", reloaded.Basis);
                Assert.Equal(5, reloaded.Composition.Count);
                Assert.Equal(20.0, reloaded.Composition["Co"]);
            }
            finally
            {
                if (File.Exists(tmpDat)) File.Delete(tmpDat);
            }

            string csv = PlotCsvFormatter.BuildCsvContent(
                "Equilibrium Phase Stability",
                "Temperature (K)",
                "Phase Mole Fraction f_φ",
                new List<(string Name, double[] Xs, double[] Ys)>
                {
                    ("FCC_A1", new[] { 300.0, 900.0 }, new[] { 1.0, 0.95 }),
                    ("Exp. DSC (Laplanche)", new[] { 1553.0, 1608.0 }, new[] { 0.0, 1.0 })
                });
            Assert.Contains("# Plot Title: Equilibrium Phase Stability", csv);
            Assert.Contains("# X-Axis: Temperature (K)", csv);
            Assert.Contains("# Y-Axis: Phase Mole Fraction f_φ", csv);
            Assert.Contains("FCC_A1 [Temperature (K)]", csv);
            Assert.Contains("Exp. DSC (Laplanche) [Phase Mole Fraction f_φ]", csv);
        }

        [Fact]
        public void TestPlotCsvFormatterEnhancedMetadataAndTernaryBarycentric()
        {
            // Verify enhanced CSV metadata injection for binary invariants
            string csvWithMeta = PlotCsvFormatter.BuildCsvContent(
                "Ni-Al Binary Phase Diagram",
                "Atomic Fraction of Al, x(Al)",
                "Temperature (°C)",
                new List<(string Name, double[] Xs, double[] Ys)>
                {
                    ("Liquidus", new[] { 0.0, 0.5 }, new[] { 1455.0, 1638.0 }),
                    ("TieLine_Eutectic_1385°C", new[] { 0.12, 0.24 }, new[] { 1385.0, 1385.0 })
                },
                new List<string>
                {
                    "System: Ni-Al",
                    "Invariant [Eutectic]: T = 1385.0 °C, x = 0.2400 (Range: 0.1200 - 0.2400) | Reaction: Liquid -> γ + γ'"
                });
            Assert.Contains("# METADATA & CRITICAL THERMODYNAMIC PROPERTIES", csvWithMeta);
            Assert.Contains("# Invariant [Eutectic]: T = 1385.0 °C", csvWithMeta);
            Assert.Contains("TieLine_Eutectic_1385°C [Atomic Fraction of Al, x(Al)]", csvWithMeta);

            // Verify automatic ternary barycentric decomposition (Cartesian + xA, xB, xC)
            double h = Math.Sqrt(3.0) / 2.0;
            string ternaryCsv = PlotCsvFormatter.BuildCsvContent(
                "Co-Cr-Ni Isothermal Section (800 °C)",
                "Barycentric Projection X",
                "Barycentric Projection Y",
                new List<(string Name, double[] Xs, double[] Ys)>
                {
                    ("FCC Solvus", new[] { 0.0, 0.5 }, new[] { 0.0, h })
                },
                new List<string>
                {
                    "System: Co-Cr-Ni",
                    "Gibbs Triangle Vertices: A = Co, B = Cr, C = Ni"
                });
            Assert.Contains("FCC Solvus [Cartesian_X]", ternaryCsv);
            Assert.Contains("FCC Solvus [Cartesian_Y]", ternaryCsv);
            Assert.Contains("FCC Solvus [x(Co)]", ternaryCsv);
            Assert.Contains("FCC Solvus [x(Cr)]", ternaryCsv);
            Assert.Contains("FCC Solvus [x(Ni)]", ternaryCsv);
            Assert.Contains("FCC Solvus [Cartesian_X]", ternaryCsv);
            Assert.Contains("FCC Solvus [Cartesian_Y]", ternaryCsv);
            Assert.Contains("FCC Solvus [x(Co)]", ternaryCsv);
            Assert.Contains("FCC Solvus [x(Cr)]", ternaryCsv);
            Assert.Contains("FCC Solvus [x(Ni)]", ternaryCsv);
        }

        [Fact]
        public async Task TestCrystalStructuresAndAtomicConfigurationRpc()
        {
            var resp = await _client.GetCrystalStructuresAsync(
                "Nickel Based Superalloy",
                new Dictionary<string, double>
                {
                    { "Ni", 52.5 }, { "Cr", 19.0 }, { "Fe", 18.5 },
                    { "Nb", 5.1 }, { "Mo", 3.0 }, { "Ti", 0.9 }, { "Al", 0.5 }
                },
                temperatureK: 300.0,
                supercellN: 2,
                basis: "wt%");

            Assert.NotNull(resp);
            Assert.NotEmpty(resp.CrystalStructures);
            Assert.Contains(resp.CrystalStructures, p => p.PhaseName == "Gamma_Matrix" && p.Archetype == "FCC_A1");
            Assert.Contains(resp.CrystalStructures, p => p.PhaseName == "Gamma_Prime" && p.Archetype == "L12_CU3AU");

            foreach (var ph in resp.CrystalStructures)
            {
                Assert.NotEmpty(ph.Atoms);
                Assert.NotEmpty(ph.Sublattices);
                Assert.NotNull(ph.UnitCellBox);
                Assert.Equal(8, ph.UnitCellBox!.Vertices.Count);
                Assert.Equal(12, ph.UnitCellBox.Edges.Count);
                Assert.False(string.IsNullOrWhiteSpace(ph.ConfigurationMode));
            }
        }

        [Fact]
        public async Task TestSigmaCrystalModelAndHeaUpgrades()
        {
            var resp = await _client.GetCrystalStructuresAsync(
                "High Entropy Alloys",
                new Dictionary<string, double>
                {
                    { "Co", 23.25 }, { "Cr", 23.25 }, { "Fe", 23.25 }, { "Ni", 23.25 }, { "Mo", 7.0 }
                },
                temperatureK: 300.0,
                supercellN: 1,
                basis: "at%");

            Assert.NotNull(resp);
            Assert.Contains(resp.CrystalStructures, p => p.Archetype == "SIGMA_D8B" && p.PearsonSymbol == "tP30");
            var sigma = resp.CrystalStructures.First(p => p.Archetype == "SIGMA_D8B");
            Assert.Equal(30, sigma.Atoms.Count);

            var eq = await _client.CalculateEquilibriumAsync(new EquilibriumRequest
            {
                DatabaseName = "High Entropy Alloys",
                Composition = new Dictionary<string, double>
                {
                    { "Co", 23.25 }, { "Cr", 23.25 }, { "Fe", 23.25 }, { "Ni", 23.25 }, { "Mo", 7.0 }
                },
                Basis = "at%",
                GrainSizeUm = 20.0,
                CalcMode = "fast"
            });
            Assert.Equal("success", eq.Status);
            Assert.NotNull(eq.Transformations);
            Assert.True(eq.Transformations.ContainsKey("StackingFaultEnergy_mJ_m2"));
            Assert.NotNull(eq.TempSeries);
            Assert.True(eq.TempSeries.YieldStrength[0] > eq.TempSeries.YieldStrength[^1]);
        }

        [Fact]
        public async Task TestGetBinarySystemsAndAssessedBenchmarks()
        {
            // All assessed benchmark systems returned when active elements is null or empty
            var allSystems = await _client.GetBinarySystemsAsync(null);
            Assert.NotNull(allSystems);
            Assert.Contains("Ni-Al", allSystems);
            Assert.Contains("Fe-Cr", allSystems);
            Assert.Contains("Cu-Ni", allSystems);
            Assert.Contains("Fe-C", allSystems);
            Assert.Contains("Mn-Ni", allSystems);
            Assert.Contains("Fe-Ni", allSystems);
            Assert.Contains("Al-Co", allSystems);
            Assert.Contains("Cr-Mn", allSystems);
            Assert.Contains("Al-Zn", allSystems);
            Assert.Contains("Sn-Ag", allSystems);
            Assert.Contains("Fe-Si", allSystems);
            Assert.Contains("Ti-Mo", allSystems);
            Assert.Contains("Zr-Nb", allSystems);
            Assert.Contains("Mo-W", allSystems);
            Assert.All(allSystems, s => Assert.DoesNotContain("(", s));
            Assert.All(allSystems, s => Assert.DoesNotContain(")", s));

            // Database filtered binary systems when composition has fewer than 2 elements
            var solderSystems = await _client.GetBinarySystemsAsync(null, "Solder Alloy");
            Assert.NotNull(solderSystems);
            Assert.Contains("Sn-Ag", solderSystems);
            Assert.Contains("Sn-Pb", solderSystems);
            Assert.Contains("Sn-Bi", solderSystems);

            var alSystems = await _client.GetBinarySystemsAsync(null, "Aluminium Alloy");
            Assert.NotNull(alSystems);
            Assert.Contains("Al-Zn", alSystems);
            Assert.Contains("Al-Fe", alSystems);
            Assert.Contains("Al-Mn", alSystems);

            var steelSystems = await _client.GetBinarySystemsAsync(null, "General Steel");
            Assert.NotNull(steelSystems);
            Assert.Contains("Fe-Si", steelSystems);
            Assert.Contains("Fe-Mo", steelSystems);
            Assert.Contains("Fe-V", steelSystems);

            // Filtered binary systems: strictly returns pairs formed by elements present in the active alloy composition
            var filtered = await _client.GetBinarySystemsAsync(new List<string> { "Fe", "Ni", "Cr" });
            Assert.NotNull(filtered);
            Assert.Contains("Fe-Ni", filtered);
            Assert.Contains("Fe-Cr", filtered);
            Assert.Contains("Cr-Ni", filtered);
            Assert.DoesNotContain("Cu-Ni", filtered);
            Assert.DoesNotContain("Fe-C", filtered);
            Assert.DoesNotContain("NaF-AlF3", filtered);
            Assert.Equal(3, filtered.Count);
            Assert.All(filtered, s => Assert.DoesNotContain("(", s));
            Assert.All(filtered, s => Assert.DoesNotContain(")", s));
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramMnNi()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Mn-Ni", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Mn-Ni", diag.System);
            Assert.Equal("Mn", diag.ElementA);
            Assert.Equal("Ni", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.NotEmpty(diag.Invariants);
            Assert.NotEmpty(diag.Regions);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Congruent Minimum");
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramAlCo()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Al-Co", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Al-Co", diag.System);
            Assert.Equal("Al", diag.ElementA);
            Assert.Equal("Co", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.NotEmpty(diag.Invariants);
            Assert.NotEmpty(diag.Regions);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Congruent Melting");
            Assert.Contains(diag.Invariants, inv => inv.Temp == 1640.0);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramCrMn()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Cr-Mn", "K", 100);
            Assert.NotNull(diag);
            Assert.Equal("Cr-Mn", diag.System);
            Assert.Equal("Mn", diag.ElementA);
            Assert.Equal("Cr", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.NotEmpty(diag.Invariants);
            Assert.NotEmpty(diag.Regions);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Peritectic");
            Assert.Contains(diag.Invariants, inv => inv.Type == "Peritectoid");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 1581.0) < 0.1);
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 1271.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramAlZn()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Al-Zn", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Al-Zn", diag.System);
            Assert.Equal("Al", diag.ElementA);
            Assert.Equal("Zn", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.NotEmpty(diag.Invariants);
            Assert.NotEmpty(diag.Regions);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Eutectic");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 381.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramNiAl()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Ni-Al", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Ni-Al", diag.System);
            Assert.Equal("Ni", diag.ElementA);
            Assert.Equal("Al", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.NotEmpty(diag.Invariants);
            Assert.NotEmpty(diag.Regions);

            // Invariants should include eutectic, peritectic, and congruent points
            Assert.Contains(diag.Invariants, inv => inv.Type == "Eutectic");
            Assert.Contains(diag.Invariants, inv => inv.Type == "Congruent");

            // Verify curves have valid coordinate points
            var liq = diag.Curves.FirstOrDefault(c => c.Name == "Liquidus");
            Assert.NotNull(liq);
            Assert.True(liq.Xs.Count > 10);
            Assert.True(liq.Ys.Count > 10);
        }

        [Fact]
        public async Task TestBinaryLeverRuleEquilibriumEvaluation()
        {
            // Liquid state evaluation above liquidus
            var liqRes = await _client.EvaluateBinaryLeverRuleAsync("Ni-Al", 0.50, 1700.0, "C");
            Assert.NotNull(liqRes);
            Assert.Contains("Liquid", liqRes.State);
            Assert.Equal(1.0, liqRes.Phase1Fraction, 3);

            // Two-phase lever rule evaluation
            var twoPhaseRes = await _client.EvaluateBinaryLeverRuleAsync("Ni-Al", 0.20, 1100.0, "C");
            Assert.NotNull(twoPhaseRes);
            Assert.True(twoPhaseRes.Phase1Fraction + twoPhaseRes.Phase2Fraction > 0.99);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramCoMn()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Co-Mn", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Co-Mn", diag.System);
            Assert.Equal("Co", diag.ElementA);
            Assert.Equal("Mn", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Eutectic");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 1161.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramTiV()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Ti-V", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Ti-V", diag.System);
            Assert.Equal("Ti", diag.ElementA);
            Assert.Equal("V", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Congruent Minimum");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 1620.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramAlMg()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Al-Mg", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Al-Mg", diag.System);
            Assert.Equal("Al", diag.ElementA);
            Assert.Equal("Mg", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Eutectic");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 450.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramAlSi()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Al-Si", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Al-Si", diag.System);
            Assert.Equal("Al", diag.ElementA);
            Assert.Equal("Si", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Eutectic");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 577.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramNiTi()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Ni-Ti", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Ni-Ti", diag.System);
            Assert.Equal("Ti", diag.ElementA);
            Assert.Equal("Ni", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Congruent Summit");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 1310.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramCuZn()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Cu-Zn", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Cu-Zn", diag.System);
            Assert.Equal("Cu", diag.ElementA);
            Assert.Equal("Zn", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Peritectic");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 902.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramCuSn()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Cu-Sn", "C", 100);
            Assert.NotNull(diag);
            Assert.Equal("Cu-Sn", diag.System);
            Assert.Equal("Cu", diag.ElementA);
            Assert.Equal("Sn", diag.ElementB);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Invariants, inv => inv.Type == "Peritectic");
            Assert.Contains(diag.Invariants, inv => Math.Abs(inv.Temp - 798.0) < 0.1);
        }

        [Fact]
        public async Task TestCalculateBinaryDiagramArbitraryEutectic()
        {
            var diag = await _client.CalculateBinaryDiagramAsync("Cu-Ag", "C", 80);
            Assert.NotNull(diag);
            Assert.Equal("Cu-Ag", diag.System);
            Assert.NotEmpty(diag.Curves);
            Assert.Contains(diag.Curves, c => c.Name.Contains("Solvus"));
            Assert.Contains(diag.Curves, c => c.Name == "Eutectic Invariant Tie-Line");
        }
    }
}
