// <copyright file="CompositionLibraryService.cs" company="PyCALPHAD Materials CAE">
// Manages saving, loading, listing, and file serialization of custom alloy compositions.
// </copyright>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Core.Services
{
    public class CompositionLibraryService
    {
        private static readonly JsonSerializerOptions JsonOpts = new()
        {
            WriteIndented = true
        };

        private readonly string _libraryPath;

        public CompositionLibraryService(string? customDirectory = null)
        {
            string baseDir = !string.IsNullOrWhiteSpace(customDirectory)
                ? customDirectory
                : Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "PyCALPHAD_Suite");

            Directory.CreateDirectory(baseDir);
            _libraryPath = Path.Combine(baseDir, "saved_compositions.json");
        }

        public string LibraryFilePath => _libraryPath;

        public static string BuildDefaultAlloyName(Dictionary<string, double> comp)
        {
            if (comp == null || comp.Count == 0) return "Custom_Alloy";
            var parts = comp
                .Where(kv => kv.Value > 0)
                .Select(kv => $"{kv.Key}{kv.Value:G3}");
            var joined = string.Join("-", parts);
            return string.IsNullOrWhiteSpace(joined) ? "Custom_Alloy" : joined;
        }

        public List<SavedCompositionProfile> LoadLibrary()
        {
            if (!File.Exists(_libraryPath))
            {
                return new List<SavedCompositionProfile>();
            }

            try
            {
                var json = File.ReadAllText(_libraryPath, Encoding.UTF8);
                return JsonSerializer.Deserialize<List<SavedCompositionProfile>>(json, JsonOpts) ?? new List<SavedCompositionProfile>();
            }
            catch
            {
                return new List<SavedCompositionProfile>();
            }
        }

        public void SaveToLibrary(SavedCompositionProfile profile)
        {
            if (string.IsNullOrWhiteSpace(profile.Name))
            {
                profile.Name = BuildDefaultAlloyName(profile.Composition);
            }
            profile.SavedAtUtc = DateTime.UtcNow;

            var items = LoadLibrary();
            items.RemoveAll(p => string.Equals(p.Name, profile.Name, StringComparison.OrdinalIgnoreCase));
            items.Insert(0, profile);

            var json = JsonSerializer.Serialize(items, JsonOpts);
            File.WriteAllText(_libraryPath, json, Encoding.UTF8);
        }

        public bool DeleteFromLibrary(string name)
        {
            var items = LoadLibrary();
            int removed = items.RemoveAll(p => string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase));
            if (removed > 0)
            {
                File.WriteAllText(_libraryPath, JsonSerializer.Serialize(items, JsonOpts), Encoding.UTF8);
                return true;
            }
            return false;
        }

        public static void SaveProfileToFile(SavedCompositionProfile profile, string filePath)
        {
            var ext = Path.GetExtension(filePath).ToLowerInvariant();
            if (ext == ".csv")
            {
                var sb = new StringBuilder();
                sb.AppendLine($"# PyCALPHAD Saved Alloy Composition: {profile.Name}");
                sb.AppendLine($"# Database: {profile.DatabaseName}");
                sb.AppendLine($"# Basis: {profile.Basis}");
                sb.AppendLine($"# GrainSize_um: {profile.GrainSizeUm.ToString(CultureInfo.InvariantCulture)}");
                sb.AppendLine($"# ProcessType: {profile.ProcessType}");
                sb.AppendLine($"# TStart_K: {profile.TStart.ToString(CultureInfo.InvariantCulture)}");
                sb.AppendLine($"# TStop_K: {profile.TStop.ToString(CultureInfo.InvariantCulture)}");
                sb.AppendLine($"# TStep_K: {profile.TStep.ToString(CultureInfo.InvariantCulture)}");
                if (!string.IsNullOrWhiteSpace(profile.Notes))
                {
                    sb.AppendLine($"# Notes: {profile.Notes.Replace('\n', ' ').Replace('\r', ' ')}");
                }
                sb.AppendLine("Element,Fraction,Basis");
                foreach (var kv in profile.Composition)
                {
                    sb.AppendLine($"{kv.Key},{kv.Value.ToString("G6", CultureInfo.InvariantCulture)},{profile.Basis}");
                }
                File.WriteAllText(filePath, sb.ToString(), Encoding.UTF8);
                return;
            }

            var json = JsonSerializer.Serialize(profile, JsonOpts);
            File.WriteAllText(filePath, json, Encoding.UTF8);
        }

        public static SavedCompositionProfile LoadProfileFromFile(string filePath)
        {
            var ext = Path.GetExtension(filePath).ToLowerInvariant();
            if (ext is ".csv" or ".dat")
            {
                var profile = new SavedCompositionProfile
                {
                    Name = Path.GetFileNameWithoutExtension(filePath),
                    Composition = new Dictionary<string, double>()
                };

                bool inChemistrySection = false;
                foreach (var raw in File.ReadAllLines(filePath, Encoding.UTF8))
                {
                    var line = raw.Trim();
                    if (string.IsNullOrEmpty(line)) continue;
                    if (line.StartsWith("["))
                    {
                        inChemistrySection = line.Equals("[CHEMISTRY]", StringComparison.OrdinalIgnoreCase);
                        continue;
                    }

                    if (line.StartsWith("# Database:", StringComparison.OrdinalIgnoreCase))
                        profile.DatabaseName = line.Split(':', 2)[1].Trim();
                    else if (line.StartsWith("# Basis:", StringComparison.OrdinalIgnoreCase))
                        profile.Basis = line.Split(':', 2)[1].Trim();
                    else if (line.StartsWith("# Alloy:", StringComparison.OrdinalIgnoreCase) || line.StartsWith("# Profile:", StringComparison.OrdinalIgnoreCase))
                        profile.Name = line.Split(':', 2)[1].Trim();
                    else if (line.StartsWith("# GrainSize_um:", StringComparison.OrdinalIgnoreCase) && double.TryParse(line.Split(':', 2)[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var gs))
                        profile.GrainSizeUm = gs;
                    else if (line.StartsWith("# ProcessType:", StringComparison.OrdinalIgnoreCase))
                        profile.ProcessType = line.Split(':', 2)[1].Trim();
                    else if (line.StartsWith("# TStart_K:", StringComparison.OrdinalIgnoreCase) && double.TryParse(line.Split(':', 2)[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var ts))
                        profile.TStart = ts;
                    else if (line.StartsWith("# TStop_K:", StringComparison.OrdinalIgnoreCase) && double.TryParse(line.Split(':', 2)[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var te))
                        profile.TStop = te;
                    else if (line.StartsWith("# TStep_K:", StringComparison.OrdinalIgnoreCase) && double.TryParse(line.Split(':', 2)[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var td))
                        profile.TStep = td;
                    else if (line.StartsWith("#")) continue;
                    else if (line.StartsWith("Element,", StringComparison.OrdinalIgnoreCase)) continue;
                    else if (inChemistrySection && line.Contains('='))
                    {
                        var kv = line.Split('=', 2);
                        var sym = kv[0].Trim();
                        var numToken = kv[1].Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? "";
                        if (!string.IsNullOrEmpty(sym) && double.TryParse(numToken, NumberStyles.Float, CultureInfo.InvariantCulture, out var fv))
                        {
                            profile.Composition[sym] = fv;
                        }
                    }
                    else if (ext == ".csv")
                    {
                        var parts = line.Split(',');
                        if (parts.Length >= 2 && double.TryParse(parts[1].Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out var frac))
                        {
                            var sym = parts[0].Trim();
                            if (!string.IsNullOrEmpty(sym)) profile.Composition[sym] = frac;
                        }
                    }
                }
                return profile;
            }

            var content = File.ReadAllText(filePath, Encoding.UTF8);
            return JsonSerializer.Deserialize<SavedCompositionProfile>(content, JsonOpts)
                ?? throw new InvalidDataException("Invalid saved composition file.");
        }
    }
}
