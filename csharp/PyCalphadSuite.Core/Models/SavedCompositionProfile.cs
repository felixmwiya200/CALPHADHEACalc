// <copyright file="SavedCompositionProfile.cs" company="PyCALPHAD Materials CAE">
// Reusable user alloy composition profile contract for library persistence and file interchange.
// </copyright>

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PyCalphadSuite.Core.Models
{
    public class SavedCompositionProfile
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("database_name")]
        public string DatabaseName { get; set; } = "High Entropy Alloys";

        [JsonPropertyName("basis")]
        public string Basis { get; set; } = "wt%";

        [JsonPropertyName("composition")]
        public Dictionary<string, double> Composition { get; set; } = new();

        [JsonPropertyName("grain_size_um")]
        public double GrainSizeUm { get; set; } = 25.0;

        [JsonPropertyName("hatch_pitch_um")]
        public double HatchPitchUm { get; set; } = 80.0;

        [JsonPropertyName("laser_power_w")]
        public double LaserPowerW { get; set; } = 275.0;

        [JsonPropertyName("scan_speed_mm_s")]
        public double ScanSpeedMmS { get; set; } = 800.0;

        [JsonPropertyName("layer_thickness_um")]
        public double LayerThicknessUm { get; set; } = 30.0;

        [JsonPropertyName("cold_work_pct")]
        public double ColdWorkPercent { get; set; } = 0.0;

        [JsonPropertyName("process_type")]
        public string ProcessType { get; set; } = "HVOF Thermal Spray";

        [JsonPropertyName("calc_mode")]
        public string CalcMode { get; set; } = "Thorough";

        [JsonPropertyName("t_start")]
        public double TStart { get; set; } = 300.0;

        [JsonPropertyName("t_stop")]
        public double TStop { get; set; } = 1800.0;

        [JsonPropertyName("t_step")]
        public double TStep { get; set; } = 25.0;

        [JsonPropertyName("notes")]
        public string Notes { get; set; } = string.Empty;

        [JsonPropertyName("saved_at_utc")]
        public DateTime SavedAtUtc { get; set; } = DateTime.UtcNow;
    }
}
