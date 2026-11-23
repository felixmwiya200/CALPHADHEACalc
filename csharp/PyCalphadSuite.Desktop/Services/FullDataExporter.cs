// <copyright file="FullDataExporter.cs" company="PyCALPHAD Materials CAE">
// Comprehensive all-in-one scientific data, raw curve CSV, 1400x850 plot PNG, and CAE card exporter.
// </copyright>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using PyCalphadSuite.Core.Models;
using PyCalphadSuite.Core.Services;
using PyCalphadSuite.Desktop.Controls;

namespace PyCalphadSuite.Desktop.Services
{
    public static class FullDataExporter
    {
        private static readonly JsonSerializerOptions JsonPretty = new() { WriteIndented = true };

        public static async Task<int> ExportAllAsync(
            string outputPath,
            EquilibriumResult res,
            SavedCompositionProfile activeProfile,
            IReadOnlyList<(string Key, PlotCanvasHost Host)> plotHosts,
            CaeDaemonProcessClient? daemonClient)
        {
            var ext = Path.GetExtension(outputPath).ToLowerInvariant();
            if (ext == ".dat")
            {
                var datContent = BuildCompleteDatContent(res, activeProfile, plotHosts);
                await File.WriteAllTextAsync(outputPath, datContent, Encoding.UTF8);
                return 1;
            }

            if (ext == ".json")
            {
                var bundle = new
                {
                    exported_at_utc = DateTime.UtcNow,
                    composition_profile = activeProfile,
                    simulation_result = res
                };
                await File.WriteAllTextAsync(outputPath, JsonSerializer.Serialize(bundle, JsonPretty), Encoding.UTF8);
                return 1;
            }

            if (ext == ".csv")
            {
                var unifiedCsv = BuildUnifiedWorkbookCsv(res, activeProfile, plotHosts);
                await File.WriteAllTextAsync(outputPath, unifiedCsv, Encoding.UTF8);
                return 1;
            }

            // Default: Self-contained .zip archive with organized folders
            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }

            int exportedFileCount = 0;
            using var archive = ZipFile.Open(outputPath, ZipArchiveMode.Create);

            // 1. Manifest
            await AddTextEntryAsync(archive, "00_README_Manifest.txt", BuildManifestText(res, activeProfile));
            exportedFileCount++;

            // 2. Reusable Saved Composition JSON & Complete ASCII .dat
            await AddTextEntryAsync(archive, "01_Saved_Composition.comp.json", JsonSerializer.Serialize(activeProfile, JsonPretty));
            exportedFileCount++;

            await AddTextEntryAsync(archive, "02_Complete_CALPHAD_Data.dat", BuildCompleteDatContent(res, activeProfile, plotHosts));
            exportedFileCount++;

            // 3. Master Scalar Properties CSV
            await AddTextEntryAsync(archive, "02_Master_Properties_Summary.csv", BuildMasterPropertiesCsv(res, activeProfile));
            exportedFileCount++;

            // 4. Validation Literature Parity CSV
            await AddTextEntryAsync(archive, "03_Validation_Literature_Parity.csv", BuildValidationCsv(res));
            exportedFileCount++;

            // 5. Industrial Sector Scores CSV
            await AddTextEntryAsync(archive, "04_Industrial_Sector_Scores.csv", BuildSectorScoresCsv(res));
            exportedFileCount++;

            // 6. Complete JSON Simulation Payload
            await AddTextEntryAsync(archive, "05_Full_Simulation_Result.json", JsonSerializer.Serialize(res, JsonPretty));
            exportedFileCount++;

            // 7. All 16 Raw Curve Data CSVs + Publication PNG Figures
            int idx = 1;
            foreach (var (key, host) in plotHosts)
            {
                string prefix = $"{idx:D2}_{SanitizeFileName(key)}";
                if (host.HasExportSeries)
                {
                    await AddTextEntryAsync(archive, $"06_Raw_Curve_Data/{prefix}.csv", host.BuildCsvContent());
                    exportedFileCount++;
                }

                try
                {
                    byte[] pngBytes = host.RenderPngBytes(1400, 850);
                    await AddBytesEntryAsync(archive, $"07_Publication_Plots_PNG/{prefix}.png", pngBytes);
                    exportedFileCount++;
                }
                catch
                {
                    // Skip image if unrendered tab threw Skia initialization exception
                }
                idx++;
            }

            // 8. COMSOL Piecewise 21 Formulations + FEA Material Cards
            if (res.Piecewise.Count > 0)
            {
                var pwSb = new StringBuilder();
                foreach (var pw in res.Piecewise)
                {
                    pwSb.AppendLine(pw.Code);
                    pwSb.AppendLine();
                }
                await AddTextEntryAsync(archive, "08_CAE_Material_Cards/COMSOL_Piecewise_21_Properties.txt", pwSb.ToString());
                exportedFileCount++;
            }

            if (daemonClient != null)
            {
                var formats = new (string Fmt, string FileName)[]
                {
                    ("abaqus", "Abaqus_Material.inp"),
                    ("ansys", "ANSYS_APDL_Material.txt"),
                    ("comsol", "COMSOL_MaterialDeck.txt"),
                    ("deform", "SFTC_DEFORM_Material.dat"),
                    ("forge", "Transvalor_FORGE_Material.mat"),
                    ("simufact", "Simufact_MatildA.xml")
                };

                foreach (var (fmt, fileName) in formats)
                {
                    try
                    {
                        var card = await daemonClient.ExportCaeCardAsync(
                            fmt,
                            string.IsNullOrWhiteSpace(res.AlloyName) ? activeProfile.Name : res.AlloyName,
                            activeProfile.Composition,
                            res.Thermo,
                            res.Mechanical);
                        await AddTextEntryAsync(archive, $"08_CAE_Material_Cards/{fileName}", card.Content);
                        exportedFileCount++;
                    }
                    catch
                    {
                        // Non-fatal if single exporter unavailable
                    }
                }
            }

            return exportedFileCount;
        }

        private static string BuildManifestText(EquilibriumResult res, SavedCompositionProfile profile)
        {
            var sb = new StringBuilder();
            sb.AppendLine("========================================================================");
            sb.AppendLine("  CALPHAD XOC MATERIALS ENGINEERING SUITE >> FULL SIMULATION DATA ARCHIVE");
            sb.AppendLine("========================================================================");
            sb.AppendLine($"Exported UTC:     {DateTime.UtcNow:O}");
            sb.AppendLine($"Alloy Profile:    {profile.Name}");
            sb.AppendLine($"Database Engine:  {res.DatabaseName}");
            sb.AppendLine($"Basis:            {profile.Basis}");
            sb.AppendLine($"Grain Size (μm):  {profile.GrainSizeUm:F1}");
            sb.AppendLine($"Process Route:    {profile.ProcessType}");
            sb.AppendLine($"Calc Mode:        {res.CalcMode}");
            sb.AppendLine($"Solver Latency:   {res.ElapsedMs:F1} ms");
            sb.AppendLine("\n[Chemistry]");
            foreach (var kv in profile.Composition)
            {
                sb.AppendLine($"  {kv.Key,-4}: {kv.Value:G6} {profile.Basis}");
            }
            sb.AppendLine("\n[Archive Contents]");
            sb.AppendLine("  01_Saved_Composition.comp.json          Reusable chemistry preset file");
            sb.AppendLine("  02_Complete_CALPHAD_Data.dat            Complete material properties, equations, log, and all graph tables");
            sb.AppendLine("  02_Master_Properties_Summary.csv        Scalar thermomechanical properties");
            sb.AppendLine("  03_Validation_Literature_Parity.csv     Peer-reviewed benchmark table");
            sb.AppendLine("  04_Industrial_Sector_Scores.csv         12-sector engineering rankings");
            sb.AppendLine("  05_Full_Simulation_Result.json          Complete raw JSON state");
            sb.AppendLine("  06_Raw_Curve_Data/*.csv                 All plotted XY curve datasets");
            sb.AppendLine("  07_Publication_Plots_PNG/*.png          1400x850 publication graphics");
            sb.AppendLine("  08_CAE_Material_Cards/*                 Abaqus/ANSYS/COMSOL/DEFORM/FORGE/Simufact");
            return sb.ToString();
        }

        private static string BuildMasterPropertiesCsv(EquilibriumResult res, SavedCompositionProfile profile)
        {
            var sb = new StringBuilder();
            sb.AppendLine("Category,Property,Value");
            foreach (var kv in profile.Composition)
            {
                sb.AppendLine($"Composition,{EscapeCsv(kv.Key)},{kv.Value.ToString("G6", CultureInfo.InvariantCulture)}");
            }
            AppendDictRows(sb, "Thermodynamics", res.Thermo, new[] { "PhaseFractions", "Transport", "composition" });
            AppendDictRows(sb, "Transformations", res.Transformations);
            AppendDictRows(sb, "Mechanical", res.Mechanical);
            AppendDictRows(sb, "Transport", res.Transport);
            return sb.ToString();
        }

        private static void AppendDictRows(StringBuilder sb, string category, Dictionary<string, object> dict, string[]? skipKeys = null)
        {
            foreach (var kv in dict)
            {
                if (skipKeys != null && skipKeys.Contains(kv.Key)) continue;
                sb.AppendLine($"{EscapeCsv(category)},{EscapeCsv(kv.Key)},{EscapeCsv(kv.Value?.ToString() ?? "")}");
            }
        }

        private static string BuildUnifiedWorkbookCsv(
            EquilibriumResult res,
            SavedCompositionProfile profile,
            IReadOnlyList<(string Key, PlotCanvasHost Host)> plotHosts)
        {
            var sb = new StringBuilder();
            sb.AppendLine("# =====================================================================");
            sb.AppendLine($"# CALPHAD XOC COMPLETE UNIFIED EXPORT >> {profile.Name} ({res.DatabaseName})");
            sb.AppendLine("# =====================================================================");
            sb.AppendLine();
            sb.AppendLine("[MASTER_PROPERTIES]");
            sb.Append(BuildMasterPropertiesCsv(res, profile));
            sb.AppendLine();
            sb.AppendLine("[VALIDATION_LITERATURE_PARITY]");
            sb.Append(DatReportBuilder.BuildValidationCsv(res));
            sb.AppendLine();
            sb.AppendLine("[INDUSTRIAL_SUITABILITY_SCORES]");
            sb.Append(DatReportBuilder.BuildSectorScoresCsv(res));

            foreach (var (key, host) in plotHosts)
            {
                if (!host.HasExportSeries) continue;
                sb.AppendLine();
                sb.AppendLine($"[PLOT_DATA_{SanitizeFileName(key).ToUpperInvariant()}]");
                sb.Append(host.BuildCsvContent());
            }
            return sb.ToString();
        }

        /// <summary>
        /// Delegates comprehensive .dat serialization to DatReportBuilder, passing rendered PlotCanvasHost snapshots.
        /// </summary>
        public static string BuildCompleteDatContent(
            EquilibriumResult res,
            SavedCompositionProfile profile,
            IReadOnlyList<(string Key, PlotCanvasHost Host)>? plotHosts = null)
        {
            var snapshots = plotHosts?
                .Select(p => new RenderedPlotSnapshot(p.Key, p.Host.PlotTitle, p.Host.XAxisTitle, p.Host.YAxisTitle, p.Host.ExportSeries))
                .ToList();
            return DatReportBuilder.BuildCompleteDatContent(res, profile, snapshots);
        }

        private static string BuildValidationCsv(EquilibriumResult res) => DatReportBuilder.BuildValidationCsv(res);
        private static string BuildSectorScoresCsv(EquilibriumResult res) => DatReportBuilder.BuildSectorScoresCsv(res);

        private static async Task AddTextEntryAsync(ZipArchive archive, string entryName, string content)
        {
            var entry = archive.CreateEntry(entryName, CompressionLevel.Optimal);
            await using var stream = entry.Open();
            await using var writer = new StreamWriter(stream, new UTF8Encoding(false));
            await writer.WriteAsync(content);
        }

        private static async Task AddBytesEntryAsync(ZipArchive archive, string entryName, byte[] data)
        {
            var entry = archive.CreateEntry(entryName, CompressionLevel.Optimal);
            await using var stream = entry.Open();
            await stream.WriteAsync(data, 0, data.Length);
        }

        private static string EscapeCsv(string raw) => PlotCsvFormatter.EscapeCsv(raw);

        private static string SanitizeFileName(string name)
        {
            var invalid = Path.GetInvalidFileNameChars();
            return new string(name.Select(ch => invalid.Contains(ch) || ch == ' ' ? '_' : ch).ToArray());
        }
    }
}
