// <copyright file="ExportFormatters.cs" company="PyCALPHAD Materials CAE">
// Reusable publication-grade CSV graph export and complete ASCII .dat builders.
// </copyright>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Core.Services
{
    public static class PlotCsvFormatter
    {
        public static string BuildCsvContent(
            string plotTitle,
            string xAxisTitle,
            string yAxisTitle,
            IReadOnlyList<(string Name, double[] Xs, double[] Ys)> series,
            IReadOnlyList<string>? metadata = null)
        {
            if (series == null || series.Count == 0) return string.Empty;

            var sb = new StringBuilder();
            string xTitle = string.IsNullOrWhiteSpace(xAxisTitle) ? "X" : xAxisTitle;
            string yTitle = string.IsNullOrWhiteSpace(yAxisTitle) ? "Y" : yAxisTitle;

            sb.AppendLine($"# Plot Title: {plotTitle}");
            sb.AppendLine($"# X-Axis: {xTitle}");
            sb.AppendLine($"# Y-Axis: {yTitle}");
            sb.AppendLine($"# Series Count: {series.Count}");

            if (metadata != null && metadata.Count > 0)
            {
                sb.AppendLine("# =========================================================================");
                sb.AppendLine("# METADATA & CRITICAL THERMODYNAMIC PROPERTIES");
                sb.AppendLine("# =========================================================================");
                foreach (var line in metadata)
                {
                    if (string.IsNullOrWhiteSpace(line)) continue;
                    if (line.StartsWith("#"))
                    {
                        sb.AppendLine(line);
                    }
                    else
                    {
                        sb.AppendLine($"# {line}");
                    }
                }
                sb.AppendLine("# =========================================================================");
            }

            sb.AppendLine($"# Legends: {string.Join(" | ", series.Select(s => s.Name))}");

            bool isTernary = (plotTitle != null && (plotTitle.Contains("Ternary", StringComparison.OrdinalIgnoreCase)
                                                || plotTitle.Contains("Isothermal Section", StringComparison.OrdinalIgnoreCase)
                                                || plotTitle.Contains("Gibbs", StringComparison.OrdinalIgnoreCase)))
                             || (xAxisTitle != null && xAxisTitle.Contains("Barycentric", StringComparison.OrdinalIgnoreCase))
                             || (yAxisTitle != null && yAxisTitle.Contains("Barycentric", StringComparison.OrdinalIgnoreCase));

            var headers = new List<string>();
            int maxRows = 0;

            if (isTernary)
            {
                var (elemA, elemB, elemC) = ParseTernaryElements(plotTitle ?? "", metadata);
                foreach (var s in series)
                {
                    headers.Add(EscapeCsv($"{s.Name} [Cartesian_X]"));
                    headers.Add(EscapeCsv($"{s.Name} [Cartesian_Y]"));
                    headers.Add(EscapeCsv($"{s.Name} [x({elemA})]"));
                    headers.Add(EscapeCsv($"{s.Name} [x({elemB})]"));
                    headers.Add(EscapeCsv($"{s.Name} [x({elemC})]"));
                    maxRows = Math.Max(maxRows, Math.Min(s.Xs.Length, s.Ys.Length));
                }
                sb.AppendLine(string.Join(",", headers));

                double h = Math.Sqrt(3.0) / 2.0;
                for (int r = 0; r < maxRows; r++)
                {
                    var rowCells = new List<string>();
                    foreach (var s in series)
                    {
                        if (r < s.Xs.Length && r < s.Ys.Length)
                        {
                            double x = s.Xs[r];
                            double y = s.Ys[r];
                            double cFrac = Math.Clamp(y / h, 0.0, 1.0);
                            double bFrac = Math.Clamp(x - 0.5 * cFrac, 0.0, 1.0);
                            double aFrac = Math.Clamp(1.0 - bFrac - cFrac, 0.0, 1.0);

                            rowCells.Add(x.ToString("G7", CultureInfo.InvariantCulture));
                            rowCells.Add(y.ToString("G7", CultureInfo.InvariantCulture));
                            rowCells.Add(aFrac.ToString("G7", CultureInfo.InvariantCulture));
                            rowCells.Add(bFrac.ToString("G7", CultureInfo.InvariantCulture));
                            rowCells.Add(cFrac.ToString("G7", CultureInfo.InvariantCulture));
                        }
                        else
                        {
                            rowCells.Add("");
                            rowCells.Add("");
                            rowCells.Add("");
                            rowCells.Add("");
                            rowCells.Add("");
                        }
                    }
                    sb.AppendLine(string.Join(",", rowCells));
                }
            }
            else
            {
                foreach (var s in series)
                {
                    headers.Add(EscapeCsv($"{s.Name} [{xTitle}]"));
                    headers.Add(EscapeCsv($"{s.Name} [{yTitle}]"));
                    maxRows = Math.Max(maxRows, Math.Min(s.Xs.Length, s.Ys.Length));
                }
                sb.AppendLine(string.Join(",", headers));

                for (int r = 0; r < maxRows; r++)
                {
                    var rowCells = new List<string>();
                    foreach (var s in series)
                    {
                        if (r < s.Xs.Length && r < s.Ys.Length)
                        {
                            rowCells.Add(s.Xs[r].ToString("G7", CultureInfo.InvariantCulture));
                            rowCells.Add(s.Ys[r].ToString("G7", CultureInfo.InvariantCulture));
                        }
                        else
                        {
                            rowCells.Add("");
                            rowCells.Add("");
                        }
                    }
                    sb.AppendLine(string.Join(",", rowCells));
                }
            }

            return sb.ToString();
        }

        private static (string elemA, string elemB, string elemC) ParseTernaryElements(string plotTitle, IReadOnlyList<string>? metadata)
        {
            string systemCandidate = string.Empty;
            if (metadata != null)
            {
                foreach (var line in metadata)
                {
                    if (line.StartsWith("System:", StringComparison.OrdinalIgnoreCase) || line.StartsWith("# System:", StringComparison.OrdinalIgnoreCase))
                    {
                        var parts = line.Split(':', 2);
                        if (parts.Length > 1)
                        {
                            systemCandidate = parts[1].Trim();
                            break;
                        }
                    }
                }
            }

            if (string.IsNullOrEmpty(systemCandidate) && !string.IsNullOrEmpty(plotTitle))
            {
                int spaceIdx = plotTitle.IndexOf(' ');
                systemCandidate = spaceIdx > 0 ? plotTitle.Substring(0, spaceIdx).Trim() : plotTitle.Trim();
            }

            if (!string.IsNullOrEmpty(systemCandidate))
            {
                var el = systemCandidate.Split(new[] { '-', '_' }, StringSplitOptions.RemoveEmptyEntries);
                if (el.Length == 3)
                {
                    return (el[0].Trim(), el[1].Trim(), el[2].Trim());
                }
            }

            return ("A", "B", "C");
        }

        public static string EscapeCsv(string field)
        {
            if (string.IsNullOrEmpty(field)) return string.Empty;
            if (field.Contains(',') || field.Contains('"') || field.Contains('\n') || field.Contains('\r'))
            {
                return $"\"{field.Replace("\"", "\"\"")}\"";
            }
            return field;
        }
    }

    public readonly record struct RenderedPlotSnapshot(
        string Key,
        string PlotTitle,
        string XAxisTitle,
        string YAxisTitle,
        IReadOnlyList<(string Name, double[] Xs, double[] Ys)> Series,
        IReadOnlyList<string>? Metadata = null);

    public static class DatReportBuilder
    {
        public static string BuildValidationCsv(EquilibriumResult res)
        {
            var sb = new StringBuilder();
            sb.AppendLine("Property,Calculated,Experimental,Deviation,ErrorPercent,Reference,DOI");
            foreach (var r in res.ValidationTable)
            {
                sb.AppendLine(
                    $"{PlotCsvFormatter.EscapeCsv(r.Property)}," +
                    $"{PlotCsvFormatter.EscapeCsv(r.Calculated?.ToString() ?? "")}," +
                    $"{PlotCsvFormatter.EscapeCsv(r.Experimental?.ToString() ?? "")}," +
                    $"{PlotCsvFormatter.EscapeCsv(r.Deviation?.ToString() ?? "")}," +
                    $"{PlotCsvFormatter.EscapeCsv(r.ErrorPercent?.ToString() ?? "")}," +
                    $"{PlotCsvFormatter.EscapeCsv(r.Reference)}," +
                    $"{PlotCsvFormatter.EscapeCsv(r.Doi)}");
            }
            return sb.ToString();
        }

        public static string BuildSectorScoresCsv(EquilibriumResult res)
        {
            var sb = new StringBuilder();
            sb.AppendLine("Rank,Sector,Application,Score_Pct,Tier,Bottleneck,Advice");
            foreach (var a in res.ApplicationScores)
            {
                sb.AppendLine(
                    $"{a.Rank}," +
                    $"{PlotCsvFormatter.EscapeCsv(a.Sector)}," +
                    $"{PlotCsvFormatter.EscapeCsv(a.Name)}," +
                    $"{a.Score.ToString("F2", CultureInfo.InvariantCulture)}," +
                    $"{PlotCsvFormatter.EscapeCsv(a.Tier)}," +
                    $"{PlotCsvFormatter.EscapeCsv(a.Bottleneck)}," +
                    $"{PlotCsvFormatter.EscapeCsv(a.Advice)}");
            }
            return sb.ToString();
        }

        public static string BuildCompleteDatContent(
            EquilibriumResult res,
            SavedCompositionProfile profile,
            IReadOnlyList<RenderedPlotSnapshot>? renderedPlots = null)
        {
            var sb = new StringBuilder();
            string alloyName = string.IsNullOrWhiteSpace(res.AlloyName) ? profile.Name : res.AlloyName;
            string dbName = string.IsNullOrWhiteSpace(res.DatabaseName) ? profile.DatabaseName : res.DatabaseName;
            string basis = string.IsNullOrWhiteSpace(profile.Basis) ? res.Basis : profile.Basis;
            var inv = CultureInfo.InvariantCulture;

            sb.AppendLine("# =========================================================================");
            sb.AppendLine("# PYCALPHAD COMPLETE CALPHAD MATERIAL & GRAPH DATA EXPORT (.dat)");
            sb.AppendLine("# =========================================================================");
            sb.AppendLine($"# Exported_UTC: {DateTime.UtcNow:O}");
            sb.AppendLine($"# Alloy: {alloyName}");
            sb.AppendLine($"# Database: {dbName}");
            sb.AppendLine($"# Basis: {basis}");
            sb.AppendLine($"# GrainSize_um: {profile.GrainSizeUm.ToString("G6", inv)}");
            sb.AppendLine($"# ProcessType: {profile.ProcessType}");
            sb.AppendLine($"# CalcMode: {res.CalcMode}");
            sb.AppendLine($"# TStart_K: {profile.TStart.ToString("G6", inv)}");
            sb.AppendLine($"# TStop_K: {profile.TStop.ToString("G6", inv)}");
            sb.AppendLine($"# TStep_K: {profile.TStep.ToString("G6", inv)}");
            sb.AppendLine($"# Elapsed_ms: {res.ElapsedMs.ToString("F2", inv)}");
            sb.AppendLine();

            sb.AppendLine("[CHEMISTRY]");
            var compSource = profile.Composition.Count > 0 ? profile.Composition : res.Composition;
            foreach (var kv in compSource)
            {
                sb.AppendLine($"{kv.Key} = {kv.Value.ToString("G6", inv)} {basis}");
            }
            sb.AppendLine();

            if (res.AtomicComposition.Count > 0 || res.Composition.Count > 0)
            {
                sb.AppendLine("[ATOMIC_AND_WEIGHT_CHEMISTRY]");
                foreach (var kv in res.Composition)
                {
                    sb.AppendLine($"{kv.Key}_wt_pct = {kv.Value.ToString("G6", inv)}");
                }
                foreach (var kv in res.AtomicComposition)
                {
                    sb.AppendLine($"{kv.Key}_at_pct = {kv.Value.ToString("G6", inv)}");
                }
                sb.AppendLine();
            }

            AppendDatSection(sb, "THERMODYNAMICS", res.Thermo, new[] { "PhaseFractions", "Transport", "composition", "atomic_composition" });
            AppendDatSection(sb, "TRANSFORMATIONS", res.Transformations);
            AppendDatSection(sb, "MECHANICAL", res.Mechanical);
            AppendDatSection(sb, "TRANSPORT", res.Transport);
            AppendDatSection(sb, "ENVIRONMENTAL", res.Environmental);
            if (res.Coating != null && res.Coating.Count > 0)
            {
                AppendDatSection(sb, "COATING", res.Coating);
            }

            if (res.Processability != null && res.Processability.Axes.Count > 0)
            {
                sb.AppendLine("[PROCESSABILITY]");
                int n = Math.Min(res.Processability.Axes.Count, res.Processability.Scores.Count);
                for (int i = 0; i < n; i++)
                {
                    sb.AppendLine($"{res.Processability.Axes[i]} = {res.Processability.Scores[i].ToString("F3", inv)}");
                }
                sb.AppendLine();
            }

            if (res.ApplicationScores.Count > 0)
            {
                sb.AppendLine("[INDUSTRIAL_SUITABILITY]");
                sb.Append(BuildSectorScoresCsv(res));
                sb.AppendLine();
            }

            if (res.ValidationTable.Count > 0)
            {
                sb.AppendLine("[VALIDATION_PARITY]");
                sb.Append(BuildValidationCsv(res));
                sb.AppendLine();
            }

            if (res.Piecewise.Count > 0)
            {
                sb.AppendLine("[COMSOL_PIECEWISE_21_PROPERTIES]");
                foreach (var pw in res.Piecewise)
                {
                    sb.AppendLine($"# Property: {pw.Property}");
                    if (!string.IsNullOrWhiteSpace(pw.SmoothExpr))
                    {
                        sb.AppendLine($"# SmoothExpr: {pw.SmoothExpr}");
                    }
                    sb.AppendLine(pw.Code);
                    sb.AppendLine();
                }
            }

            sb.AppendLine("[CALCULATION_LOG]");
            if (res.CalcLog.Count > 0)
            {
                foreach (var line in res.CalcLog)
                {
                    sb.AppendLine(line);
                }
            }
            else
            {
                sb.AppendLine("# No iteration log entries recorded.");
            }
            sb.AppendLine();

            var emittedKeys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            if (renderedPlots != null)
            {
                foreach (var snap in renderedPlots)
                {
                    if (snap.Series == null || snap.Series.Count == 0) continue;
                    string normKey = NormalizeGraphKey(snap.Key);
                    emittedKeys.Add(normKey);
                    sb.AppendLine($"[GRAPH_DATA_{normKey}]");
                    sb.Append(PlotCsvFormatter.BuildCsvContent(snap.PlotTitle, snap.XAxisTitle, snap.YAxisTitle, snap.Series, snap.Metadata));
                    sb.AppendLine();
                }
            }

            EmitMissingDtoGraphs(sb, res, emittedKeys);
            return sb.ToString();
        }

        public static string NormalizeGraphKey(string key)
        {
            var invalid = Path.GetInvalidFileNameChars();
            var sb = new StringBuilder();
            foreach (char c in key ?? string.Empty)
            {
                sb.Append(char.IsLetterOrDigit(c) && !invalid.Contains(c) ? char.ToUpperInvariant(c) : '_');
            }
            return sb.ToString().Trim('_');
        }

        private static void AppendDatSection(StringBuilder sb, string sectionName, Dictionary<string, object> dict, string[]? skipKeys = null)
        {
            sb.AppendLine($"[{sectionName}]");
            foreach (var kv in dict)
            {
                if (skipKeys != null && skipKeys.Contains(kv.Key)) continue;
                sb.AppendLine($"{kv.Key} = {FormatDatValue(kv.Value)}");
            }
            sb.AppendLine();
        }

        private static string FormatDatValue(object? val)
        {
            if (val == null) return string.Empty;
            if (val is IFormattable formattable)
            {
                return formattable.ToString(null, CultureInfo.InvariantCulture);
            }
            return val.ToString() ?? string.Empty;
        }

        private static bool HasMatchingEmittedKey(HashSet<string> emittedKeys, params string[] keywords)
        {
            foreach (var k in emittedKeys)
            {
                if (keywords.All(w => k.Contains(w, StringComparison.OrdinalIgnoreCase)))
                {
                    return true;
                }
            }
            return false;
        }

        private static void EmitMissingDtoGraphs(StringBuilder sb, EquilibriumResult res, HashSet<string> emittedKeys)
        {
            if (res.PhaseCurves != null && res.PhaseCurves.TK.Count > 0 && res.PhaseCurves.Series.Count > 0
                && !HasMatchingEmittedKey(emittedKeys, "PHASE", "EQUILIBRIUM"))
            {
                var xs = res.PhaseCurves.TK.ToArray();
                var names = res.PhaseCurves.Series.Keys.ToList();
                var ys = names.Select(n => res.PhaseCurves.Series[n].ToArray()).ToList();
                AppendDatGraphTable(sb, "PHASE_EQUILIBRIUM", "Phase Fraction vs Temperature", "Temperature (K)", "Phase Fraction (-)", names, xs, ys);
            }

            if (res.Scheil != null && res.Scheil.Fs.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "SCHEIL"))
            {
                AppendDatGraphTable(
                    sb,
                    "SCHEIL_SOLIDIFICATION",
                    "Scheil-Gulliver vs Lever-Rule Solidification",
                    "Solid Fraction f_s (-)",
                    "Temperature (C)",
                    new[] { "Equilibrium Lever Rule", "Scheil-Gulliver Non-Equilibrium" },
                    res.Scheil.Fs.ToArray(),
                    new[] { res.Scheil.TLeverC.ToArray(), res.Scheil.TScheilC.ToArray() });
            }

            if (res.Isopleth != null && res.Isopleth.XSweep.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "ISOPLETH"))
            {
                AppendDatGraphTable(
                    sb,
                    "ISOPLETH_PSEUDO_BINARY",
                    $"Pseudo-Binary Isopleth ({res.Isopleth.Solute})",
                    $"Solute Addition {res.Isopleth.Solute} (mol%)",
                    "Temperature (K)",
                    new[] { "Liquidus T_L (K)", "Solidus T_S (K)" },
                    res.Isopleth.XSweep.ToArray(),
                    new[] { res.Isopleth.TLiqK.ToArray(), res.Isopleth.TSolK.ToArray() });
            }

            if (res.TempSeries != null && res.TempSeries.TK.Count > 0)
            {
                var ts = res.TempSeries;
                if (ts.Density.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "DENSITY"))
                {
                    AppendDatGraphTable(sb, "DENSITY_VS_T", "Density vs Temperature", "Temperature (K)", "Density (g/cm3)",
                        new[] { "Bulk Density" }, ts.TK.ToArray(), new[] { ts.Density.ToArray() });
                }
                if (ts.Cte.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "CTE") && !HasMatchingEmittedKey(emittedKeys, "EXPANSION"))
                {
                    AppendDatGraphTable(sb, "CTE_VS_T", "Thermal Expansion Coefficient vs Temperature", "Temperature (K)", "CTE (1e-6 / K)",
                        new[] { "Linear CTE" }, ts.TK.ToArray(), new[] { ts.Cte.ToArray() });
                }
                if (ts.ThermalCond.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "THERMAL", "COND"))
                {
                    AppendDatGraphTable(sb, "THERMAL_CONDUCTIVITY_VS_T", "Thermal Conductivity vs Temperature", "Temperature (K)", "Thermal Conductivity (W/m*K)",
                        new[] { "Thermal Conductivity" }, ts.TK.ToArray(), new[] { ts.ThermalCond.ToArray() });
                }
                if (ts.Resistivity.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "RESISTIVITY"))
                {
                    AppendDatGraphTable(sb, "ELECTRICAL_RESISTIVITY_VS_T", "Electrical Resistivity vs Temperature", "Temperature (K)", "Resistivity (uOhm*cm)",
                        new[] { "Electrical Resistivity" }, ts.TK.ToArray(), new[] { ts.Resistivity.ToArray() });
                }
                if (ts.TMechK.Count > 0 && ts.YieldStrength.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "YIELD"))
                {
                    var names = new List<string> { "Yield Strength (MPa)" };
                    var ys = new List<double[]> { ts.YieldStrength.ToArray() };
                    if (ts.Uts.Count > 0)
                    {
                        names.Add("Ultimate Tensile Strength (MPa)");
                        ys.Add(ts.Uts.ToArray());
                    }
                    if (ts.HardnessHv.Count > 0)
                    {
                        names.Add("Vickers Hardness (HV)");
                        ys.Add(ts.HardnessHv.ToArray());
                    }
                    if (ts.HardnessHrc.Count > 0)
                    {
                        names.Add("Rockwell Hardness (HRC)");
                        ys.Add(ts.HardnessHrc.ToArray());
                    }
                    if (ts.HardnessHrb.Count > 0)
                    {
                        names.Add("Rockwell Hardness (HRB)");
                        ys.Add(ts.HardnessHrb.ToArray());
                    }
                    AppendDatGraphTable(sb, "YIELD_UTS_HARDNESS_VS_T", "Yield Strength, UTS & Hardness vs Temperature", "Temperature (K)", "Stress (MPa) / Hardness (HV, HRC, HRB)", names, ts.TMechK.ToArray(), ys);
                }
            }

            if (res.FlowStress != null && res.FlowStress.StrainPct.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "FLOW"))
            {
                AppendDatGraphTable(
                    sb,
                    "FLOW_STRESS_CURVES",
                    "Tensile Flow Stress Curves (Hollomon vs Voce)",
                    "Plastic Strain (%)",
                    "True Stress (MPa)",
                    new[] { "Hollomon Power Law", "Voce Saturation Model" },
                    res.FlowStress.StrainPct.ToArray(),
                    new[] { res.FlowStress.SigmaHollomon.ToArray(), res.FlowStress.SigmaVoce.ToArray() });
            }

            if (res.OxidationCurve != null && res.OxidationCurve.TimeH.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "OXIDATION"))
            {
                AppendDatGraphTable(
                    sb,
                    "OXIDATION_KINETICS",
                    "Parabolic Oxidation Kinetics",
                    "Exposure Time (h)",
                    "Specific Mass Gain (mg/cm2)",
                    new[] { $"Parabolic Oxidation (kp={res.OxidationCurve.Kp:G4})" },
                    res.OxidationCurve.TimeH.ToArray(),
                    new[] { res.OxidationCurve.MassGain.ToArray() });
            }

            if (res.Ellingham != null && res.Ellingham.TC.Count > 0 && res.Ellingham.Oxides.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "ELLINGHAM"))
            {
                var names = res.Ellingham.Oxides.Keys.ToList();
                var ys = names.Select(n => res.Ellingham.Oxides[n].DgKj.ToArray()).ToList();
                AppendDatGraphTable(sb, "ELLINGHAM_STABILITY", "Ellingham Oxide Stability Diagram", "Temperature (C)", "Delta G0 (kJ/mol O2)",
                    names, res.Ellingham.TC.ToArray(), ys);
            }

            if (res.CorrosionTafel != null && res.CorrosionTafel.LogI.Count > 0 && !HasMatchingEmittedKey(emittedKeys, "CORROSION") && !HasMatchingEmittedKey(emittedKeys, "TAFEL"))
            {
                AppendDatGraphTable(
                    sb,
                    "CORROSION_TAFEL",
                    "Potentiodynamic Polarization (Tafel)",
                    "log10(Current Density) [A/cm2]",
                    "Potential E (V vs SCE)",
                    new[] { $"Tafel Curve (Ecorr={res.CorrosionTafel.Ecorr:F3} V)" },
                    res.CorrosionTafel.LogI.ToArray(),
                    new[] { res.CorrosionTafel.ETafel.ToArray() });
            }

            if (res.Xrd != null && res.Xrd.TwoTheta.Count > 0)
            {
                if (!HasMatchingEmittedKey(emittedKeys, "XRD"))
                {
                    AppendDatGraphTable(sb, "XRD_PATTERN", $"Simulated XRD Pattern ({res.Xrd.Radiation})", "Diffraction Angle 2-Theta (deg)", "Relative Intensity (%)",
                        new[] { "Simulated XRD Profile" }, res.Xrd.TwoTheta.ToArray(), new[] { res.Xrd.IntensityPct.ToArray() });
                }
                if (res.Xrd.Peaks.Count > 0)
                {
                    var inv = CultureInfo.InvariantCulture;
                    sb.AppendLine("[GRAPH_DATA_XRD_BRAGG_PEAKS]");
                    sb.AppendLine("# Plot Title: Indexed XRD Bragg Peaks");
                    sb.AppendLine("# X-Axis: Diffraction Angle 2-Theta (deg)");
                    sb.AppendLine("# Y-Axis: Relative Intensity (%)");
                    sb.AppendLine("# Legends (1): Bragg Peaks");
                    sb.AppendLine("TwoTheta_deg,Intensity_pct,HKL,Phase");
                    foreach (var p in res.Xrd.Peaks)
                    {
                        sb.AppendLine($"{p.TwoTheta.ToString("F3", inv)},{p.Intensity.ToString("F2", inv)},{PlotCsvFormatter.EscapeCsv(p.Hkl)},{PlotCsvFormatter.EscapeCsv(p.Phase)}");
                    }
                    sb.AppendLine();
                }
            }
        }

        private static void AppendDatGraphTable(
            StringBuilder sb,
            string key,
            string plotTitle,
            string xAxisTitle,
            string yAxisTitle,
            IReadOnlyList<string> legendNames,
            double[] xValues,
            IReadOnlyList<double[]> ySeriesList)
        {
            int count = Math.Min(legendNames.Count, ySeriesList.Count);
            if (count == 0 || xValues.Length == 0) return;

            var tuples = new List<(string Name, double[] Xs, double[] Ys)>();
            for (int i = 0; i < count; i++)
            {
                tuples.Add((legendNames[i], xValues, ySeriesList[i]));
            }
            sb.AppendLine($"[GRAPH_DATA_{key}]");
            sb.Append(PlotCsvFormatter.BuildCsvContent(plotTitle, xAxisTitle, yAxisTitle, tuples));
            sb.AppendLine();
        }
    }
}
