// <copyright file="ExperimentalProcessOptions.cs" company="PyCALPHAD Materials CAE">
// Configurable experimental and additive manufacturing process parameters across all alloy calculations.
// </copyright>

using System;
using System.Text.Json.Serialization;

namespace PyCalphadSuite.Core.Models
{
    public class ExperimentalProcessOptions
    {
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

        [JsonPropertyName("beam_spot_diameter_um")]
        public double BeamSpotDiameterUm { get; set; } = 75.0;

        [JsonPropertyName("cold_work_pct")]
        public double ColdWorkPercent { get; set; } = 0.0;

        [JsonPropertyName("heat_treatment_temp_k")]
        public double HeatTreatmentTempK { get; set; } = 973.15;

        [JsonPropertyName("heat_treatment_hours")]
        public double HeatTreatmentHours { get; set; } = 20.0;

        [JsonIgnore]
        public double VolumetricEnergyDensity =>
            (ScanSpeedMmS > 0 && HatchPitchUm > 0 && LayerThicknessUm > 0)
                ? (LaserPowerW / (ScanSpeedMmS * (HatchPitchUm * 1e-3) * (LayerThicknessUm * 1e-3)))
                : 0.0; // J/mm³

        [JsonIgnore]
        public double EstimatedCoolingRateKS =>
            (HatchPitchUm > 0)
                ? Math.Clamp(2.5e5 * (ScanSpeedMmS / 800.0) * (80.0 / HatchPitchUm), 1e3, 1e7)
                : 1e4; // K/s

        [JsonIgnore]
        public double EstimatedCellularSpacingUm =>
            50.0 * Math.Pow(Math.Max(100.0, EstimatedCoolingRateKS), -0.33); // µm

        [JsonIgnore]
        public double HallPetchStrengtheningMpa =>
            GrainSizeUm > 0 ? (450.0 / Math.Sqrt(GrainSizeUm)) : 0.0; // MPa

        [JsonIgnore]
        public double CellularStrengtheningMpa =>
            EstimatedCellularSpacingUm > 0 ? (185.0 / Math.Sqrt(EstimatedCellularSpacingUm)) : 0.0; // MPa

        [JsonIgnore]
        public string PorosityRegime
        {
            get
            {
                double ved = VolumetricEnergyDensity;
                if (ved < 50.0) return "Lack-of-Fusion Risk (Insufficient Overlap)";
                if (ved <= 160.0) return "Optimal Conduction Window (>99.8% Relative Density)";
                return "Keyhole Porosity Risk (Excessive Vaporization)";
            }
        }

        public ExperimentalProcessOptions Clone()
        {
            return (ExperimentalProcessOptions)MemberwiseClone();
        }
    }
}
