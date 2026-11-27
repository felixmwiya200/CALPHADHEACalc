// <copyright file="AlloyModels.cs" company="PyCALPHAD Materials CAE">
// Academic and commercial metallurgical CAE data contracts conforming to CALPHAD standards.
// </copyright>

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PyCalphadSuite.Core.Models
{
    public class CaeRequest
    {
        [JsonPropertyName("id")]
        public long Id { get; set; }

        [JsonPropertyName("method")]
        public string Method { get; set; } = string.Empty;

        [JsonPropertyName("params")]
        public object? Params { get; set; }
    }

    public class CaeResponse<T>
    {
        [JsonPropertyName("id")]
        public long? Id { get; set; }

        [JsonPropertyName("result")]
        public T? Result { get; set; }

        [JsonPropertyName("error")]
        public string? Error { get; set; }

        [JsonIgnore]
        public bool IsSuccess => string.IsNullOrEmpty(Error) && Result != null;
    }

    public class PingResult
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("version")]
        public string Version { get; set; } = string.Empty;

        [JsonPropertyName("pycalphad_ready")]
        public bool PyCalphadReady { get; set; }

        [JsonPropertyName("modules_preloaded")]
        public bool ModulesPreloaded { get; set; }
    }

    public class PublishedMaterialDto
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;
    }

    public class TdbFileInfoDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("phases")]
        public List<string> Phases { get; set; } = new();

        [JsonPropertyName("num_elements")]
        public int NumElements { get; set; }

        [JsonPropertyName("num_phases")]
        public int NumPhases { get; set; }

        [JsonPropertyName("is_valid")]
        public bool IsValid { get; set; }
    }

    public class DatabaseCatalogResult
    {
        [JsonPropertyName("names")]
        public List<string> Names { get; set; } = new();

        [JsonPropertyName("databases")]
        public Dictionary<string, DatabaseSpecDto> Databases { get; set; } = new();

        [JsonPropertyName("published_materials")]
        public List<PublishedMaterialDto> PublishedMaterials { get; set; } = new();

        [JsonPropertyName("tdb_catalog")]
        public List<TdbFileInfoDto> TdbCatalog { get; set; } = new();
    }

    public class DatabaseSpecDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("default_alloy")]
        public string DefaultAlloy { get; set; } = string.Empty;

        [JsonPropertyName("basis")]
        public string Basis { get; set; } = "wt%";

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("presets")]
        public Dictionary<string, Dictionary<string, double>> Presets { get; set; } = new();

        [JsonPropertyName("tdb_file")]
        public string? TdbFile { get; set; }

        [JsonPropertyName("available_tdbs")]
        public List<string> AvailableTdbs { get; set; } = new();
    }

    public class ElementDto
    {
        [JsonPropertyName("z")]
        public int Z { get; set; }

        [JsonPropertyName("symbol")]
        public string Symbol { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("atomic_mass")]
        public double AtomicMass { get; set; }

        [JsonPropertyName("radius_pm")]
        public double RadiusPm { get; set; }

        [JsonPropertyName("electronegativity")]
        public double Electronegativity { get; set; }

        [JsonPropertyName("vec")]
        public double Vec { get; set; }

        [JsonPropertyName("crystal_structure")]
        public string CrystalStructure { get; set; } = string.Empty;

        [JsonPropertyName("tm_k")]
        public double TmK { get; set; }

        [JsonPropertyName("density_g_cm3")]
        public double DensityGCm3 { get; set; }

        [JsonPropertyName("youngs_modulus_gpa")]
        public double YoungsModulusGpa { get; set; }

        [JsonPropertyName("grid_row")]
        public int GridRow { get; set; }

        [JsonPropertyName("grid_col")]
        public int GridCol { get; set; }

        [JsonPropertyName("category")]
        public string Category { get; set; } = "transition";

        [JsonPropertyName("color_hex")]
        public string ColorHex { get; set; } = "#3B82F6";
    }

    public class ElementsResult
    {
        [JsonPropertyName("elements")]
        public List<ElementDto> Elements { get; set; } = new();
    }

    public class EquilibriumRequest
    {
        [JsonPropertyName("database_name")]
        public string DatabaseName { get; set; } = "High Entropy Alloys";

        [JsonPropertyName("composition")]
        public Dictionary<string, double> Composition { get; set; } = new();

        [JsonPropertyName("basis")]
        public string Basis { get; set; } = "wt%";

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

        [JsonPropertyName("process_type")]
        public string ProcessType { get; set; } = "HVOF";

        [JsonPropertyName("calc_mode")]
        public string CalcMode { get; set; } = "thorough";

        [JsonPropertyName("t_start")]
        public double TStart { get; set; } = 300.0;

        [JsonPropertyName("t_stop")]
        public double TStop { get; set; } = 1800.0;

        [JsonPropertyName("t_step")]
        public double TStep { get; set; } = 25.0;

        [JsonPropertyName("dft_input")]
        public DftInputDto DftInput { get; set; } = new();
    }

    public class PhaseCurvesDto
    {
        [JsonPropertyName("t_k")]
        public List<double> TK { get; set; } = new();

        [JsonPropertyName("series")]
        public Dictionary<string, List<double>> Series { get; set; } = new();

        [JsonPropertyName("kinetic_solvus_k")]
        public double? KineticSolvusK { get; set; }

        [JsonPropertyName("equilibrium_solvus_k")]
        public double? EquilibriumSolvusK { get; set; }

        [JsonPropertyName("gibbs_thomson_shift_c")]
        public double? GibbsThomsonShiftC { get; set; }

        [JsonPropertyName("kinetic_phase_diagram")]
        public KineticPhaseDiagramDto? KineticPhaseDiagram { get; set; }
    }

    public class ScheilDataDto
    {
        [JsonPropertyName("fs")]
        public List<double> Fs { get; set; } = new();

        [JsonPropertyName("t_lever_c")]
        public List<double> TLeverC { get; set; } = new();

        [JsonPropertyName("t_scheil_c")]
        public List<double> TScheilC { get; set; } = new();

        [JsonPropertyName("t_liq_c")]
        public double TLiqC { get; set; }

        [JsonPropertyName("t_sol_c")]
        public double TSolC { get; set; }

        [JsonPropertyName("eutectic_pct")]
        public double EutecticPct { get; set; }
    }

    public class IsoplethDataDto
    {
        [JsonPropertyName("solute")]
        public string Solute { get; set; } = "Al";

        [JsonPropertyName("x_sweep")]
        public List<double> XSweep { get; set; } = new();

        [JsonPropertyName("t_liq_k")]
        public List<double> TLiqK { get; set; } = new();

        [JsonPropertyName("t_sol_k")]
        public List<double> TSolK { get; set; } = new();

        [JsonPropertyName("t_solvus_k")]
        public double? TSolvusK { get; set; }

        [JsonPropertyName("t_solvus_kin_k")]
        public double? TSolvusKinK { get; set; }

        [JsonPropertyName("precipitate_phase")]
        public string? PrecipitatePhase { get; set; }
    }

    public class TempSeriesDto
    {
        [JsonPropertyName("t_k")]
        public List<double> TK { get; set; } = new();

        [JsonPropertyName("density")]
        public List<double> Density { get; set; } = new();

        [JsonPropertyName("cte")]
        public List<double> Cte { get; set; } = new();

        [JsonPropertyName("thermal_cond")]
        public List<double> ThermalCond { get; set; } = new();

        [JsonPropertyName("resistivity")]
        public List<double> Resistivity { get; set; } = new();

        [JsonPropertyName("specific_heat_cp")]
        public List<double> SpecificHeatCp { get; set; } = new();

        [JsonPropertyName("enthalpy_h")]
        public List<double> EnthalpyH { get; set; } = new();

        [JsonPropertyName("thermal_diffusivity")]
        public List<double> ThermalDiffusivity { get; set; } = new();

        [JsonPropertyName("electrical_conductivity")]
        public List<double> ElectricalConductivity { get; set; } = new();

        [JsonPropertyName("viscosity")]
        public List<double> Viscosity { get; set; } = new();

        [JsonPropertyName("surface_tension")]
        public List<double> SurfaceTension { get; set; } = new();

        [JsonPropertyName("youngs_modulus")]
        public List<double> YoungsModulus { get; set; } = new();

        [JsonPropertyName("bulk_modulus")]
        public List<double> BulkModulus { get; set; } = new();

        [JsonPropertyName("shear_modulus")]
        public List<double> ShearModulus { get; set; } = new();

        [JsonPropertyName("poissons_ratio")]
        public List<double> PoissonsRatio { get; set; } = new();

        [JsonPropertyName("t_mech_k")]
        public List<double> TMechK { get; set; } = new();

        [JsonPropertyName("yield_strength")]
        public List<double> YieldStrength { get; set; } = new();

        [JsonPropertyName("uts")]
        public List<double> Uts { get; set; } = new();

        [JsonPropertyName("hardness_hv")]
        public List<double> HardnessHv { get; set; } = new();

        [JsonPropertyName("hardness_hrc")]
        public List<double> HardnessHrc { get; set; } = new();

        [JsonPropertyName("hardness_hrb")]
        public List<double> HardnessHrb { get; set; } = new();

        [JsonPropertyName("yield_strength_enhanced")]
        public List<double> YieldStrengthEnhanced { get; set; } = new();

        [JsonPropertyName("uts_enhanced")]
        public List<double> UtsEnhanced { get; set; } = new();

        [JsonPropertyName("hardness_hv_enhanced")]
        public List<double> HardnessHvEnhanced { get; set; } = new();

        [JsonPropertyName("thermal_cond_enhanced")]
        public List<double> ThermalCondEnhanced { get; set; } = new();

        [JsonPropertyName("resistivity_enhanced")]
        public List<double> ResistivityEnhanced { get; set; } = new();
    }

    public class FlowStressDto
    {
        [JsonPropertyName("strain_pct")]
        public List<double> StrainPct { get; set; } = new();

        [JsonPropertyName("sigma_hollomon")]
        public List<double> SigmaHollomon { get; set; } = new();

        [JsonPropertyName("sigma_voce")]
        public List<double> SigmaVoce { get; set; } = new();

        [JsonPropertyName("k_coeff")]
        public double KCoeff { get; set; }

        [JsonPropertyName("n_work")]
        public double NWork { get; set; }
    }

    public class OxidationCurveDto
    {
        [JsonPropertyName("time_h")]
        public List<double> TimeH { get; set; } = new();

        [JsonPropertyName("mass_gain")]
        public List<double> MassGain { get; set; } = new();

        [JsonPropertyName("kp")]
        public double Kp { get; set; }
    }

    public class EllinghamOxideLineDto
    {
        [JsonPropertyName("dg_kj")]
        public List<double> DgKj { get; set; } = new();

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#1D4ED8";

        [JsonPropertyName("pbr")]
        public double Pbr { get; set; }

        [JsonPropertyName("class")]
        public string ClassName { get; set; } = string.Empty;
    }

    public class EllinghamDataDto
    {
        [JsonPropertyName("t_c")]
        public List<double> TC { get; set; } = new();

        [JsonPropertyName("oxides")]
        public Dictionary<string, EllinghamOxideLineDto> Oxides { get; set; } = new();

        [JsonPropertyName("dominant_scale")]
        public string DominantScale { get; set; } = "Cr2O3";
    }

    public class CorrosionTafelDto
    {
        [JsonPropertyName("log_i")]
        public List<double> LogI { get; set; } = new();

        [JsonPropertyName("e_tafel")]
        public List<double> ETafel { get; set; } = new();

        [JsonPropertyName("ecorr")]
        public double Ecorr { get; set; }

        [JsonPropertyName("icorr")]
        public double Icorr { get; set; }
    }

    public class XrdPeakDto
    {
        [JsonPropertyName("TwoTheta")]
        public double TwoTheta { get; set; }

        [JsonPropertyName("Intensity")]
        public double Intensity { get; set; }

        [JsonPropertyName("HKL")]
        public string Hkl { get; set; } = string.Empty;

        [JsonPropertyName("Phase")]
        public string Phase { get; set; } = string.Empty;
    }

    public class XrdDataDto
    {
        [JsonPropertyName("two_theta")]
        public List<double> TwoTheta { get; set; } = new();

        [JsonPropertyName("intensity_pct")]
        public List<double> IntensityPct { get; set; } = new();

        [JsonPropertyName("peaks")]
        public List<XrdPeakDto> Peaks { get; set; } = new();

        [JsonPropertyName("phases")]
        public List<string> Phases { get; set; } = new();

        [JsonPropertyName("lattice_params")]
        public Dictionary<string, double> LatticeParams { get; set; } = new();

        [JsonPropertyName("radiation")]
        public string Radiation { get; set; } = "Cu-Ka (1.5406 A)";

        [JsonPropertyName("has_benchmark")]
        public bool HasBenchmark { get; set; }

        [JsonPropertyName("benchmark_citation")]
        public string BenchmarkCitation { get; set; } = string.Empty;

        [JsonPropertyName("benchmark_two_theta")]
        public List<double> BenchmarkTwoTheta { get; set; } = new();

        [JsonPropertyName("benchmark_intensity")]
        public List<double> BenchmarkIntensity { get; set; } = new();
    }

    public class ProcessabilityDto
    {
        [JsonPropertyName("axes")]
        public List<string> Axes { get; set; } = new();

        [JsonPropertyName("scores")]
        public List<double> Scores { get; set; } = new();

        [JsonPropertyName("route_costs_usd_kg")]
        public List<double> RouteCostsUsdKg { get; set; } = new();

        [JsonPropertyName("raw_alloy_cost_usd_kg")]
        public double RawAlloyCostUsdKg { get; set; }
    }

    public class DftSublatticeDto
    {
        [JsonPropertyName("site")]
        public string Site { get; set; } = string.Empty;

        [JsonPropertyName("multiplicity")]
        public int Multiplicity { get; set; }

        [JsonPropertyName("coordination")]
        public int Coordination { get; set; }

        [JsonPropertyName("geometry")]
        public string Geometry { get; set; } = string.Empty;

        [JsonPropertyName("preferred_elements")]
        public string PreferredElements { get; set; } = string.Empty;

        [JsonPropertyName("fe_cr_ratio")]
        public string FeCrRatio { get; set; } = string.Empty;
    }

    public class DftInputDto
    {
        [JsonPropertyName("enabled")]
        public bool Enabled { get; set; } = true;

        [JsonPropertyName("enthalpy_bcc_kj")]
        public double EnthalpyBccKj { get; set; } = -8.50;

        [JsonPropertyName("enthalpy_fcc_kj")]
        public double EnthalpyFccKj { get; set; } = -8.28;

        [JsonPropertyName("enthalpy_hcp_kj")]
        public double EnthalpyHcpKj { get; set; } = -8.18;

        [JsonPropertyName("enthalpy_sigma_kj")]
        public double EnthalpySigmaKj { get; set; } = 7.20;

        [JsonPropertyName("bo_avg")]
        public double BoAvg { get; set; } = 0.857;

        [JsonPropertyName("md_avg")]
        public double MdAvg { get; set; } = 0.858;

        [JsonPropertyName("radius_avg_pm")]
        public double RadiusAvgPm { get; set; } = 126.0;

        [JsonPropertyName("sfe_mj_m2")]
        public double SfeMjM2 { get; set; } = 28.0;

        [JsonPropertyName("ground_state")]
        public string GroundState { get; set; } = "BCC_A2";

        [JsonPropertyName("source")]
        public string Source { get; set; } = "First-Principles DFT (0 K) / Morinaga Orbital Theory";

        [JsonPropertyName("custom_override")]
        public bool CustomOverride { get; set; } = false;
    }

    public class DftElectronicDto
    {
        [JsonPropertyName("bo_avg")]
        public double BoAvg { get; set; }

        [JsonPropertyName("md_avg")]
        public double MdAvg { get; set; }

        [JsonPropertyName("md_crit")]
        public double MdCrit { get; set; }

        [JsonPropertyName("radius_avg_pm")]
        public double RadiusAvgPm { get; set; }

        [JsonPropertyName("sigma_instability_ratio")]
        public double SigmaInstabilityRatio { get; set; }

        [JsonPropertyName("sigma_risk")]
        public string SigmaRisk { get; set; } = string.Empty;

        [JsonPropertyName("sigma_color")]
        public string SigmaColor { get; set; } = string.Empty;

        [JsonPropertyName("gamma_vector")]
        public double GammaVector { get; set; }

        [JsonPropertyName("matrix_prediction")]
        public string MatrixPrediction { get; set; } = string.Empty;

        [JsonPropertyName("sfe_mj_m2")]
        public double SfeMjM2 { get; set; }

        [JsonPropertyName("deformation_mode")]
        public string DeformationMode { get; set; } = string.Empty;

        [JsonPropertyName("dft_ground_state")]
        public string DftGroundState { get; set; } = string.Empty;

        [JsonPropertyName("enthalpy_bcc_kj")]
        public double EnthalpyBccKj { get; set; }

        [JsonPropertyName("enthalpy_fcc_kj")]
        public double EnthalpyFccKj { get; set; }

        [JsonPropertyName("enthalpy_hcp_kj")]
        public double EnthalpyHcpKj { get; set; }

        [JsonPropertyName("enthalpy_sigma_kj")]
        public double EnthalpySigmaKj { get; set; }

        [JsonPropertyName("sublattices")]
        public List<DftSublatticeDto> Sublattices { get; set; } = new();

        [JsonPropertyName("citation")]
        public string Citation { get; set; } = string.Empty;
    }

    public class ApplicationScoreDto
    {
        [JsonPropertyName("rank")]
        public int Rank { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("sector")]
        public string Sector { get; set; } = string.Empty;

        [JsonPropertyName("score")]
        public double Score { get; set; }

        [JsonPropertyName("tier")]
        public string Tier { get; set; } = string.Empty;

        [JsonPropertyName("benchmark")]
        public string Benchmark { get; set; } = string.Empty;

        [JsonPropertyName("git_reference")]
        public string GitReference { get; set; } = string.Empty;

        [JsonPropertyName("bottleneck")]
        public string Bottleneck { get; set; } = string.Empty;

        [JsonPropertyName("advice")]
        public string Advice { get; set; } = string.Empty;

        [JsonPropertyName("alloy_cost_usd_kg")]
        public double AlloyCostUsdKg { get; set; }

        [JsonPropertyName("benchmark_cost_usd_kg")]
        public double BenchmarkCostUsdKg { get; set; }

        [JsonPropertyName("cost_savings_pct")]
        public double CostSavingsPct { get; set; }

        [JsonPropertyName("cost_recommendation")]
        public string CostRecommendation { get; set; } = string.Empty;
    }

    public class ValidationRowDto
    {
        [JsonPropertyName("Property")]
        public string Property { get; set; } = string.Empty;

        [JsonPropertyName("Calculated")]
        public object? Calculated { get; set; }

        [JsonPropertyName("Experimental")]
        public object? Experimental { get; set; }

        [JsonPropertyName("Deviation")]
        public object? Deviation { get; set; }

        [JsonPropertyName("ErrorPercent")]
        public object? ErrorPercent { get; set; }

        [JsonPropertyName("RomCalculated")]
        public object? RomCalculated { get; set; }

        [JsonPropertyName("RomDeviation")]
        public object? RomDeviation { get; set; }

        [JsonPropertyName("RomErrorPercent")]
        public object? RomErrorPercent { get; set; }

        [JsonPropertyName("CalphadVsRomDeviation")]
        public object? CalphadVsRomDeviation { get; set; }

        [JsonPropertyName("CalphadVsRomErrorPercent")]
        public object? CalphadVsRomErrorPercent { get; set; }

        [JsonPropertyName("CalphadVsRomDevDisplay")]
        public string CalphadVsRomDevDisplay
        {
            get
            {
                if (TryGetDouble(Calculated, out double c) && TryGetDouble(RomCalculated, out double r))
                {
                    double diff = c - r;
                    double pct = Math.Abs(r) > 1e-6 ? (Math.Abs(diff) / Math.Abs(r)) * 100.0 : 0.0;
                    return $"{diff:+0.00;-0.00;0.00} ({pct:F1}%)";
                }
                return "-";
            }
        }

        [JsonPropertyName("RomVsExpDeviation")]
        public object? RomVsExpDeviation { get; set; }

        [JsonPropertyName("RomVsExpErrorPercent")]
        public object? RomVsExpErrorPercent { get; set; }

        [JsonPropertyName("RomVsExpDevDisplay")]
        public string RomVsExpDevDisplay
        {
            get
            {
                if (TryGetDouble(RomCalculated, out double r) && TryGetDouble(Experimental, out double e))
                {
                    double diff = r - e;
                    double pct = Math.Abs(e) > 1e-6 ? (Math.Abs(diff) / Math.Abs(e)) * 100.0 : 0.0;
                    return $"{diff:+0.00;-0.00;0.00} ({pct:F1}%)";
                }
                if (RomDeviation != null)
                {
                    string errStr = RomErrorPercent != null ? $" ({RomErrorPercent}%)" : "";
                    return $"{RomDeviation}{errStr}";
                }
                return "-";
            }
        }

        [JsonPropertyName("PbmMcEnhanced")]
        public object? PbmMcEnhanced { get; set; }

        [JsonPropertyName("EnhancedDeviation")]
        public object? EnhancedDeviation { get; set; }

        [JsonPropertyName("EnhancedErrorPercent")]
        public object? EnhancedErrorPercent { get; set; }

        [JsonPropertyName("ReasonForDeviation")]
        public string ReasonForDeviation { get; set; } = string.Empty;

        [JsonPropertyName("Reference")]
        public string Reference { get; set; } = string.Empty;

        [JsonPropertyName("DOI")]
        public string Doi { get; set; } = string.Empty;

        private static bool TryGetDouble(object? val, out double result)
        {
            result = 0.0;
            if (val == null) return false;
            if (val is double d) { result = d; return true; }
            if (val is float f) { result = f; return true; }
            if (val is int i) { result = i; return true; }
            if (val is long l) { result = l; return true; }
            if (val is System.Text.Json.JsonElement je)
            {
                if (je.ValueKind == System.Text.Json.JsonValueKind.Number && je.TryGetDouble(out var jd))
                {
                    result = jd; return true;
                }
                if (je.ValueKind == System.Text.Json.JsonValueKind.String && double.TryParse(je.GetString(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var js))
                {
                    result = js; return true;
                }
            }
            return double.TryParse(val.ToString(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out result);
        }
    }

    public class PiecewiseItemDto
    {
        [JsonPropertyName("property")]
        public string Property { get; set; } = string.Empty;

        [JsonPropertyName("smooth_expr")]
        public string SmoothExpr { get; set; } = string.Empty;

        [JsonPropertyName("code")]
        public string Code { get; set; } = string.Empty;
    }

    public class EquilibriumResult
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("elapsed_ms")]
        public double ElapsedMs { get; set; }

        [JsonPropertyName("database_name")]
        public string DatabaseName { get; set; } = string.Empty;

        [JsonPropertyName("alloy_name")]
        public string AlloyName { get; set; } = string.Empty;

        [JsonPropertyName("composition")]
        public Dictionary<string, double> Composition { get; set; } = new();

        [JsonPropertyName("atomic_composition")]
        public Dictionary<string, double> AtomicComposition { get; set; } = new();

        [JsonPropertyName("basis")]
        public string Basis { get; set; } = "wt%";

        [JsonPropertyName("grain_size_um")]
        public double GrainSizeUm { get; set; }

        [JsonPropertyName("hatch_pitch_um")]
        public double HatchPitchUm { get; set; } = 80.0;

        [JsonPropertyName("laser_power_w")]
        public double LaserPowerW { get; set; } = 275.0;

        [JsonPropertyName("scan_speed_mm_s")]
        public double ScanSpeedMmS { get; set; } = 800.0;

        [JsonPropertyName("layer_thickness_um")]
        public double LayerThicknessUm { get; set; } = 30.0;

        [JsonPropertyName("volumetric_energy_density_j_mm3")]
        public double VolumetricEnergyDensityJmm3 { get; set; }

        [JsonPropertyName("estimated_cooling_rate_k_s")]
        public double EstimatedCoolingRateKS { get; set; }

        [JsonPropertyName("cellular_spacing_um")]
        public double CellularSpacingUm { get; set; }

        [JsonPropertyName("process_type")]
        public string ProcessType { get; set; } = string.Empty;

        [JsonPropertyName("calc_mode")]
        public string CalcMode { get; set; } = string.Empty;

        [JsonPropertyName("transformations")]
        public Dictionary<string, object> Transformations { get; set; } = new();

        [JsonPropertyName("thermo")]
        public Dictionary<string, object> Thermo { get; set; } = new();

        [JsonPropertyName("mechanical")]
        public Dictionary<string, object> Mechanical { get; set; } = new();

        [JsonPropertyName("transport")]
        public Dictionary<string, object> Transport { get; set; } = new();

        [JsonPropertyName("environmental")]
        public Dictionary<string, object> Environmental { get; set; } = new();

        [JsonPropertyName("benchmarks")]
        public Dictionary<string, JsonElement> Benchmarks { get; set; } = new();

        [JsonPropertyName("phase_curves")]
        public PhaseCurvesDto? PhaseCurves { get; set; }

        [JsonPropertyName("scheil")]
        public ScheilDataDto? Scheil { get; set; }

        [JsonPropertyName("isopleth")]
        public IsoplethDataDto? Isopleth { get; set; }

        [JsonPropertyName("temp_series")]
        public TempSeriesDto? TempSeries { get; set; }

        [JsonPropertyName("flow_stress")]
        public FlowStressDto? FlowStress { get; set; }

        [JsonPropertyName("oxidation_curve")]
        public OxidationCurveDto? OxidationCurve { get; set; }

        [JsonPropertyName("ellingham")]
        public EllinghamDataDto? Ellingham { get; set; }

        [JsonPropertyName("corrosion_tafel")]
        public CorrosionTafelDto? CorrosionTafel { get; set; }

        [JsonPropertyName("xrd")]
        public XrdDataDto? Xrd { get; set; }

        [JsonPropertyName("crystal_structures")]
        public List<CrystalStructureDto> CrystalStructures { get; set; } = new();

        [JsonPropertyName("processability")]
        public ProcessabilityDto? Processability { get; set; }

        [JsonPropertyName("dft_electronic")]
        public DftElectronicDto? DftElectronic { get; set; }

        [JsonPropertyName("application_scores")]
        public List<ApplicationScoreDto> ApplicationScores { get; set; } = new();

        [JsonPropertyName("validation_table")]
        public List<ValidationRowDto> ValidationTable { get; set; } = new();

        [JsonPropertyName("coating")]
        public Dictionary<string, object>? Coating { get; set; }

        [JsonPropertyName("piecewise")]
        public List<PiecewiseItemDto> Piecewise { get; set; } = new();

        [JsonPropertyName("microstructure")]
        public MicrostructureDto? Microstructure { get; set; }

        [JsonPropertyName("rule_of_mixtures")]
        public RuleOfMixturesDto? RuleOfMixtures { get; set; }

        [JsonPropertyName("rom_comparison")]
        public RomComparisonDto? RomComparison { get; set; }

        [JsonPropertyName("literature_matches")]
        public List<HeaLiteratureItemDto> LiteratureMatches { get; set; } = new();

        [JsonPropertyName("pourbaix_diagram")]
        public PourbaixDiagramDto? PourbaixDiagram { get; set; }

        [JsonPropertyName("aqueous_corrosion")]
        public PourbaixMetricsDto? AqueousCorrosion { get; set; }

        [JsonPropertyName("calc_log")]
        public List<string> CalcLog { get; set; } = new();
    }

    public class SingleStepResult
    {
        [JsonPropertyName("temperature")]
        public double Temperature { get; set; }

        [JsonPropertyName("phases")]
        public Dictionary<string, double> Phases { get; set; } = new();

        [JsonPropertyName("dominant_phase")]
        public string DominantPhase { get; set; } = string.Empty;

        [JsonPropertyName("gibbs_energy_j_mol")]
        public double GibbsEnergyJMol { get; set; }

        [JsonPropertyName("yield_strength_mpa")]
        public double YieldStrengthMpa { get; set; }

        [JsonPropertyName("hardness_hv")]
        public double HardnessHv { get; set; }

        [JsonPropertyName("hardness_hrc")]
        public double HardnessHrc { get; set; }

        [JsonPropertyName("hardness_hrb")]
        public double HardnessHrb { get; set; }

        [JsonPropertyName("rockwell_hardness")]
        public string RockwellHardness { get; set; } = string.Empty;
    }

    public class SimulationCurveDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("x")]
        public List<double> X { get; set; } = new();

        [JsonPropertyName("y")]
        public List<double> Y { get; set; } = new();

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#1D4ED8";
    }

    public class SimulationModuleResult
    {
        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("x_label")]
        public string XLabel { get; set; } = string.Empty;

        [JsonPropertyName("y_label")]
        public string YLabel { get; set; } = string.Empty;

        [JsonPropertyName("curves")]
        public List<SimulationCurveDto> Curves { get; set; } = new();

        [JsonPropertyName("summary")]
        public string Summary { get; set; } = string.Empty;

        [JsonPropertyName("oxides")]
        public List<Dictionary<string, JsonElement>>? Oxides { get; set; }

        [JsonPropertyName("imcs")]
        public List<Dictionary<string, JsonElement>>? Imcs { get; set; }

        [JsonPropertyName("alloys")]
        public List<Dictionary<string, JsonElement>>? Alloys { get; set; }
    }

    public class CaeExportResult
    {
        [JsonPropertyName("format")]
        public string Format { get; set; } = string.Empty;

        [JsonPropertyName("alloy_name")]
        public string AlloyName { get; set; } = string.Empty;

        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;
    }

    public class LatticeParamsDto
    {
        [JsonPropertyName("a")]
        public double A { get; set; }

        [JsonPropertyName("b")]
        public double B { get; set; }

        [JsonPropertyName("c")]
        public double C { get; set; }

        [JsonPropertyName("alpha")]
        public double Alpha { get; set; } = 90.0;

        [JsonPropertyName("beta")]
        public double Beta { get; set; } = 90.0;

        [JsonPropertyName("gamma")]
        public double Gamma { get; set; } = 90.0;
    }

    public class SublatticeInfoDto
    {
        [JsonPropertyName("sublattice_id")]
        public string SublatticeId { get; set; } = string.Empty;

        [JsonPropertyName("wyckoff_sites")]
        public string WyckoffSites { get; set; } = string.Empty;

        [JsonPropertyName("site_count_per_cell")]
        public int SiteCountPerCell { get; set; }

        [JsonPropertyName("sublattice_colour")]
        public string SublatticeColour { get; set; } = "#2563EB";

        [JsonPropertyName("occupancy_summary")]
        public string OccupancySummary { get; set; } = string.Empty;

        [JsonPropertyName("element_fractions")]
        public Dictionary<string, double> ElementFractions { get; set; } = new();
    }

    public class CrystalAtomDto
    {
        [JsonPropertyName("index")]
        public int Index { get; set; }

        [JsonPropertyName("symbol")]
        public string Symbol { get; set; } = string.Empty;

        [JsonPropertyName("element_name")]
        public string ElementName { get; set; } = string.Empty;

        [JsonPropertyName("wyckoff")]
        public string Wyckoff { get; set; } = string.Empty;

        [JsonPropertyName("sublattice")]
        public string Sublattice { get; set; } = string.Empty;

        [JsonPropertyName("sublattice_colour")]
        public string SublatticeColour { get; set; } = "#2563EB";

        [JsonPropertyName("colour_hex")]
        public string ColourHex { get; set; } = "#3B82F6";

        [JsonPropertyName("radius_pm")]
        public double RadiusPm { get; set; } = 130.0;

        [JsonPropertyName("radius_a")]
        public double RadiusA { get; set; } = 1.3;

        [JsonPropertyName("frac")]
        public List<double> Frac { get; set; } = new();

        [JsonPropertyName("is_image")]
        public bool IsImage { get; set; }

        [JsonPropertyName("x")]
        public double X { get; set; }

        [JsonPropertyName("y")]
        public double Y { get; set; }

        [JsonPropertyName("z")]
        public double Z { get; set; }

        [JsonIgnore]
        public string FracDisplay => Frac.Count >= 3 ? $"({Frac[0]:F3}, {Frac[1]:F3}, {Frac[2]:F3})" : string.Empty;

        [JsonIgnore]
        public string CartDisplay => $"({X:F3}, {Y:F3}, {Z:F3})";
    }

    public class CrystalBondDto
    {
        [JsonPropertyName("a")]
        public int A { get; set; }

        [JsonPropertyName("b")]
        public int B { get; set; }

        [JsonPropertyName("length_a")]
        public double LengthA { get; set; }
    }

    public class UnitCellBoxDto
    {
        [JsonPropertyName("vertices")]
        public List<List<double>> Vertices { get; set; } = new();

        [JsonPropertyName("edges")]
        public List<List<int>> Edges { get; set; } = new();
    }

    public class CrystalStructureDto
    {
        [JsonPropertyName("phase_name")]
        public string PhaseName { get; set; } = string.Empty;

        [JsonPropertyName("archetype")]
        public string Archetype { get; set; } = string.Empty;

        [JsonPropertyName("phase_fraction")]
        public double PhaseFraction { get; set; }

        [JsonPropertyName("crystal_system")]
        public string CrystalSystem { get; set; } = string.Empty;

        [JsonPropertyName("space_group")]
        public string SpaceGroup { get; set; } = string.Empty;

        [JsonPropertyName("pearson_symbol")]
        public string PearsonSymbol { get; set; } = string.Empty;

        [JsonPropertyName("strukturbericht")]
        public string Strukturbericht { get; set; } = string.Empty;

        [JsonPropertyName("prototype")]
        public string Prototype { get; set; } = string.Empty;

        [JsonPropertyName("lattice_params")]
        public LatticeParamsDto? LatticeParams { get; set; }

        [JsonPropertyName("apf")]
        public double Apf { get; set; }

        [JsonPropertyName("coordination_number")]
        public int CoordinationNumber { get; set; }

        [JsonPropertyName("slip_system")]
        public string SlipSystem { get; set; } = string.Empty;

        [JsonPropertyName("burgers_vector_a")]
        public double BurgersVectorA { get; set; }

        [JsonPropertyName("nn_distance_a")]
        public double NnDistanceA { get; set; }

        [JsonPropertyName("z_formula_units")]
        public int ZFormulaUnits { get; set; }

        [JsonPropertyName("supercell")]
        public string Supercell { get; set; } = "2x2x2";

        [JsonPropertyName("configuration_mode")]
        public string ConfigurationMode { get; set; } = string.Empty;

        [JsonPropertyName("configuration_summary")]
        public string ConfigurationSummary { get; set; } = string.Empty;

        [JsonPropertyName("sublattices")]
        public List<SublatticeInfoDto> Sublattices { get; set; } = new();

        [JsonPropertyName("species_counts")]
        public Dictionary<string, int> SpeciesCounts { get; set; } = new();

        [JsonPropertyName("unit_cell_box")]
        public UnitCellBoxDto? UnitCellBox { get; set; }

        [JsonPropertyName("slip_plane_polygon")]
        public List<List<double>> SlipPlanePolygon { get; set; } = new();

        [JsonPropertyName("atoms")]
        public List<CrystalAtomDto> Atoms { get; set; } = new();

        [JsonPropertyName("bonds")]
        public List<CrystalBondDto> Bonds { get; set; } = new();

        [JsonIgnore]
        public string PhaseFractionDisplay => $"{PhaseFraction * 100.0:F1}%";

        [JsonIgnore]
        public string LatticeSummaryDisplay => LatticeParams == null
            ? string.Empty
            : $"{LatticeParams.A:F3}, {LatticeParams.B:F3}, {LatticeParams.C:F3}";
    }

    public class CrystalStructuresResponse
    {
        [JsonPropertyName("database_name")]
        public string DatabaseName { get; set; } = string.Empty;

        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; }

        [JsonPropertyName("supercell_n")]
        public int SupercellN { get; set; } = 2;

        [JsonPropertyName("atomic_composition")]
        public Dictionary<string, double> AtomicComposition { get; set; } = new();

        [JsonPropertyName("crystal_structures")]
        public List<CrystalStructureDto> CrystalStructures { get; set; } = new();
    }

    #region Mesoscale Layer 2: Population Balance & Monte Carlo DTOs

    public class MicrostructureDto
    {
        [JsonPropertyName("heat_treatment_temp_k")]
        public double HeatTreatmentTempK { get; set; }

        [JsonPropertyName("heat_treatment_hours")]
        public double HeatTreatmentHours { get; set; }

        [JsonPropertyName("primary_precipitate_phase")]
        public string PrimaryPrecipitatePhase { get; set; } = string.Empty;

        [JsonPropertyName("population_balance")]
        public PopulationBalanceDto? PopulationBalance { get; set; }

        [JsonPropertyName("monte_carlo_grain_growth")]
        public MonteCarloGrainGrowthDto? MonteCarloGrainGrowth { get; set; }

        [JsonPropertyName("strengthening_breakdown")]
        public StrengtheningBreakdownDto? StrengtheningBreakdown { get; set; }

        [JsonPropertyName("enhanced_properties")]
        public EnhancedPropertiesDto? EnhancedProperties { get; set; }

        [JsonPropertyName("kinetic_phase_diagram")]
        public KineticPhaseDiagramDto? KineticPhaseDiagram { get; set; }
    }

    public class PopulationBalanceDto
    {
        [JsonPropertyName("phase_name")]
        public string PhaseName { get; set; } = string.Empty;

        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; }

        [JsonPropertyName("mean_radius_nm_final")]
        public double MeanRadiusNmFinal { get; set; }

        [JsonPropertyName("volume_fraction_final")]
        public double VolumeFractionFinal { get; set; }

        [JsonPropertyName("number_density_m3_final")]
        public double NumberDensityM3Final { get; set; }

        [JsonPropertyName("critical_radius_nm_final")]
        public double CriticalRadiusNmFinal { get; set; }

        [JsonPropertyName("orowan_strengthening_final_mpa")]
        public double OrowanStrengtheningFinalMpa { get; set; }

        [JsonPropertyName("shearing_strengthening_final_mpa")]
        public double ShearingStrengtheningFinalMpa { get; set; }

        [JsonPropertyName("total_precip_strengthening_mpa")]
        public double TotalPrecipStrengtheningMpa { get; set; }

        [JsonPropertyName("trajectories")]
        public PbmTrajectoriesDto? Trajectories { get; set; }

        [JsonPropertyName("psd_histogram")]
        public PsdHistogramDto? PsdHistogram { get; set; }
    }

    public class PbmTrajectoriesDto
    {
        [JsonPropertyName("time_hours")]
        public List<double> TimeHours { get; set; } = new();

        [JsonPropertyName("mean_radius_nm")]
        public List<double> MeanRadiusNm { get; set; } = new();

        [JsonPropertyName("volume_fraction")]
        public List<double> VolumeFraction { get; set; } = new();

        [JsonPropertyName("number_density_m3")]
        public List<double> NumberDensityM3 { get; set; } = new();

        [JsonPropertyName("critical_radius_nm")]
        public List<double> CriticalRadiusNm { get; set; } = new();

        [JsonPropertyName("precipitation_strength_mpa")]
        public List<double> PrecipitationStrengthMpa { get; set; } = new();
    }

    public class PsdHistogramDto
    {
        [JsonPropertyName("radius_nm")]
        public List<double> RadiusNm { get; set; } = new();

        [JsonPropertyName("number_density_m4")]
        public List<double> NumberDensityM4 { get; set; } = new();

        [JsonPropertyName("normalized_frequency")]
        public List<double> NormalizedFrequency { get; set; } = new();
    }

    public class MonteCarloGrainGrowthDto
    {
        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; }

        [JsonPropertyName("initial_grain_size_um")]
        public double InitialGrainSizeUm { get; set; }

        [JsonPropertyName("final_grain_size_um")]
        public double FinalGrainSizeUm { get; set; }

        [JsonPropertyName("zener_pinning_pressure_kpa")]
        public double ZenerPinningPressureKpa { get; set; }

        [JsonPropertyName("zener_limit_grain_size_um")]
        public double? ZenerLimitGrainSizeUm { get; set; }

        [JsonPropertyName("is_zener_pinned")]
        public bool IsZenerPinned { get; set; }

        [JsonPropertyName("hall_petch_strength_final_mpa")]
        public double HallPetchStrengthFinalMpa { get; set; }

        [JsonPropertyName("trajectories")]
        public McTrajectoriesDto? Trajectories { get; set; }

        [JsonPropertyName("potts_simulation")]
        public PottsSimulationDto? PottsSimulation { get; set; }
    }

    public class McTrajectoriesDto
    {
        [JsonPropertyName("time_hours")]
        public List<double> TimeHours { get; set; } = new();

        [JsonPropertyName("grain_size_um")]
        public List<double> GrainSizeUm { get; set; } = new();

        [JsonPropertyName("hall_petch_strength_mpa")]
        public List<double> HallPetchStrengthMpa { get; set; } = new();

        [JsonPropertyName("net_driving_pressure_kpa")]
        public List<double> NetDrivingPressureKpa { get; set; } = new();
    }

    public class PottsSimulationDto
    {
        [JsonPropertyName("num_grains_simulated")]
        public int NumGrainsSimulated { get; set; }

        [JsonPropertyName("mean_lattice_diameter")]
        public double MeanLatticeDiameter { get; set; }

        [JsonPropertyName("lattice_grid")]
        public List<List<int>> LatticeGrid { get; set; } = new();

        [JsonPropertyName("gsd_histogram")]
        public GsdHistogramDto? GsdHistogram { get; set; }

        [JsonPropertyName("topological_distribution")]
        public TopologicalDistributionDto? TopologicalDistribution { get; set; }

        [JsonPropertyName("brand_palette")]
        public List<string> BrandPalette { get; set; } = new();
    }

    public class GsdHistogramDto
    {
        [JsonPropertyName("u_normalized_diameter")]
        public List<double> UNormalizedDiameter { get; set; } = new();

        [JsonPropertyName("p_density")]
        public List<double> PDensity { get; set; } = new();

        [JsonPropertyName("hillert_theoretical_p")]
        public List<double> HillertTheoreticalP { get; set; } = new();

        [JsonPropertyName("u_theory")]
        public List<double> UTheory { get; set; } = new();
    }

    public class TopologicalDistributionDto
    {
        [JsonPropertyName("polygon_sides")]
        public List<int> PolygonSides { get; set; } = new();

        [JsonPropertyName("frequency")]
        public List<double> Frequency { get; set; } = new();
    }

    public class StrengtheningBreakdownDto
    {
        [JsonPropertyName("matrix_friction_stress_mpa")]
        public double MatrixFrictionStressMpa { get; set; }

        [JsonPropertyName("solid_solution_strengthening_mpa")]
        public double SolidSolutionStrengtheningMpa { get; set; }

        [JsonPropertyName("hall_petch_grain_boundary_mpa")]
        public double HallPetchGrainBoundaryMpa { get; set; }

        [JsonPropertyName("orowan_precipitation_hardening_mpa")]
        public double OrowanPrecipitationHardeningMpa { get; set; }

        [JsonPropertyName("total_resolved_yield_strength_mpa")]
        public double TotalResolvedYieldStrengthMpa { get; set; }
    }

    public class EnhancedPropertiesDto
    {
        [JsonPropertyName("base_yield_strength_mpa")]
        public double BaseYieldStrengthMpa { get; set; }

        [JsonPropertyName("enhanced_yield_strength_mpa")]
        public double EnhancedYieldStrengthMpa { get; set; }

        [JsonPropertyName("delta_yield_strength_mpa")]
        public double DeltaYieldStrengthMpa { get; set; }

        [JsonPropertyName("base_hardness_hv")]
        public double BaseHardnessHv { get; set; }

        [JsonPropertyName("enhanced_hardness_hv")]
        public double EnhancedHardnessHv { get; set; }

        [JsonPropertyName("delta_hardness_hv")]
        public double DeltaHardnessHv { get; set; }

        [JsonPropertyName("base_uts_mpa")]
        public double BaseUtsMpa { get; set; }

        [JsonPropertyName("enhanced_uts_mpa")]
        public double EnhancedUtsMpa { get; set; }

        [JsonPropertyName("delta_uts_mpa")]
        public double DeltaUtsMpa { get; set; }

        [JsonPropertyName("base_elongation_pct")]
        public double BaseElongationPct { get; set; }

        [JsonPropertyName("enhanced_elongation_pct")]
        public double EnhancedElongationPct { get; set; }

        [JsonPropertyName("base_fracture_toughness_mpa_m05")]
        public double BaseFractureToughnessMpaM05 { get; set; }

        [JsonPropertyName("enhanced_fracture_toughness_mpa_m05")]
        public double EnhancedFractureToughnessMpaM05 { get; set; }

        [JsonPropertyName("base_creep_rupture_hours")]
        public double BaseCreepRuptureHours { get; set; }

        [JsonPropertyName("enhanced_creep_rupture_hours")]
        public double EnhancedCreepRuptureHours { get; set; }

        [JsonPropertyName("enhanced_fatigue_limit_mpa")]
        public double EnhancedFatigueLimitMpa { get; set; }

        [JsonPropertyName("base_electrical_resistivity_uohm_cm")]
        public double BaseElectricalResistivityUohmCm { get; set; }

        [JsonPropertyName("enhanced_electrical_resistivity_uohm_cm")]
        public double EnhancedElectricalResistivityUohmCm { get; set; }

        [JsonPropertyName("delta_electrical_resistivity_uohm_cm")]
        public double DeltaElectricalResistivityUohmCm { get; set; }

        [JsonPropertyName("base_thermal_conductivity_w_mk")]
        public double BaseThermalConductivityWMk { get; set; }

        [JsonPropertyName("enhanced_thermal_conductivity_w_mk")]
        public double EnhancedThermalConductivityWMk { get; set; }

        [JsonPropertyName("delta_thermal_conductivity_w_mk")]
        public double DeltaThermalConductivityWMk { get; set; }
    }

    public class KineticPhaseDiagramDto
    {
        [JsonPropertyName("phase_name")]
        public string PhaseName { get; set; } = string.Empty;

        [JsonPropertyName("equilibrium_solvus_k")]
        public double EquilibriumSolvusK { get; set; }

        [JsonPropertyName("equilibrium_solvus_c")]
        public double EquilibriumSolvusC { get; set; }

        [JsonPropertyName("kinetic_solvus_k")]
        public double KineticSolvusK { get; set; }

        [JsonPropertyName("kinetic_solvus_c")]
        public double KineticSolvusC { get; set; }

        [JsonPropertyName("gibbs_thomson_shift_c")]
        public double GibbsThomsonShiftC { get; set; }

        [JsonPropertyName("ttt_nose_temperature_c")]
        public double TttNoseTemperatureC { get; set; }

        [JsonPropertyName("ttt_nose_time_seconds")]
        public double TttNoseTimeSeconds { get; set; }

        [JsonPropertyName("critical_cooling_rate_k_s")]
        public double CriticalCoolingRateKS { get; set; }

        [JsonPropertyName("ttt_temperatures_c")]
        public List<double> TttTemperaturesC { get; set; } = new();

        [JsonPropertyName("ttt_time_1pct_seconds")]
        public List<double> TttTime1PctSeconds { get; set; } = new();

        [JsonPropertyName("ttt_time_50pct_seconds")]
        public List<double> TttTime50PctSeconds { get; set; } = new();

        [JsonPropertyName("ttt_time_99pct_seconds")]
        public List<double> TttTime99PctSeconds { get; set; } = new();

        [JsonPropertyName("temperature_sweep_c")]
        public List<double> TemperatureSweepC { get; set; } = new();

        [JsonPropertyName("equilibrium_phase_fraction")]
        public List<double> EquilibriumPhaseFraction { get; set; } = new();

        [JsonPropertyName("kinetic_phase_fraction_moderate_cool")]
        public List<double> KineticPhaseFractionModerateCool { get; set; } = new();

        [JsonPropertyName("kinetic_phase_fraction_fast_cool")]
        public List<double> KineticPhaseFractionFastCool { get; set; } = new();
    }

    #region Rule of Mixtures (ROM) & Continuum Composite Bounds DTOs

    public class RuleOfMixturesDto
    {
        [JsonPropertyName("density_g_cm3")]
        public double DensityGCm3 { get; set; }

        [JsonPropertyName("molar_mass_g_mol")]
        public double MolarMassGMol { get; set; }

        [JsonPropertyName("molar_volume_cm3_mol")]
        public double MolarVolumeCm3Mol { get; set; }

        [JsonPropertyName("atomic_radius_pm")]
        public double AtomicRadiusPm { get; set; }

        [JsonPropertyName("vec")]
        public double Vec { get; set; }

        [JsonPropertyName("electronegativity")]
        public double Electronegativity { get; set; }

        [JsonPropertyName("liquidus_k")]
        public double LiquidusK { get; set; }

        [JsonPropertyName("solidus_k")]
        public double SolidusK { get; set; }

        [JsonPropertyName("delta_h_mix_kj_mol")]
        public double DeltaHMixKjMol { get; set; }

        [JsonPropertyName("delta_s_mix_ideal_j_mol_k")]
        public double DeltaSMixIdealJMolK { get; set; }

        [JsonPropertyName("youngs_modulus_gpa")]
        public double YoungsModulusGpa { get; set; }

        [JsonPropertyName("youngs_modulus_voigt_gpa")]
        public double YoungsModulusVoigtGpa { get; set; }

        [JsonPropertyName("youngs_modulus_reuss_gpa")]
        public double YoungsModulusReussGpa { get; set; }

        [JsonPropertyName("shear_modulus_gpa")]
        public double ShearModulusGpa { get; set; }

        [JsonPropertyName("bulk_modulus_gpa")]
        public double BulkModulusGpa { get; set; }

        [JsonPropertyName("poissons_ratio")]
        public double PoissonsRatio { get; set; }

        [JsonPropertyName("yield_strength_mpa")]
        public double YieldStrengthMpa { get; set; }

        [JsonPropertyName("uts_mpa")]
        public double UtsMpa { get; set; }

        [JsonPropertyName("hardness_hv")]
        public double HardnessHv { get; set; }

        [JsonPropertyName("thermal_conductivity_w_mk")]
        public double ThermalConductivityWMk { get; set; }

        [JsonPropertyName("electrical_resistivity_uohm_cm")]
        public double ElectricalResistivityUohmCm { get; set; }

        [JsonPropertyName("cte_1e6_k")]
        public double Cte1E6K { get; set; }

        [JsonPropertyName("cte_turner_1e6_k")]
        public double CteTurner1E6K { get; set; }
    }

    public class RomComparisonRowDto
    {
        [JsonPropertyName("property")]
        public string Property { get; set; } = string.Empty;

        [JsonPropertyName("units")]
        public string Units { get; set; } = string.Empty;

        [JsonPropertyName("calphad_value")]
        public double CalphadValue { get; set; }

        [JsonPropertyName("rom_value")]
        public double RomValue { get; set; }

        [JsonPropertyName("rom_voigt")]
        public double RomVoigt { get; set; }

        [JsonPropertyName("rom_reuss")]
        public double RomReuss { get; set; }

        [JsonPropertyName("diff_absolute")]
        public double DiffAbsolute { get; set; }

        [JsonPropertyName("diff_relative_pct")]
        public double DiffRelativePct { get; set; }

        [JsonPropertyName("mechanism")]
        public string Mechanism { get; set; } = string.Empty;

        [JsonPropertyName("reason_for_deviation")]
        public string ReasonForDeviation
        {
            get => string.IsNullOrEmpty(_reasonForDeviation) ? Mechanism : _reasonForDeviation;
            set => _reasonForDeviation = value;
        }
        private string _reasonForDeviation = string.Empty;
    }

    public class RomComparativeSeriesDto
    {
        [JsonPropertyName("t_k")]
        public List<double> TK { get; set; } = new();

        [JsonPropertyName("rom_yield_strength")]
        public List<double> RomYieldStrength { get; set; } = new();

        [JsonPropertyName("rom_hardness_hv")]
        public List<double> RomHardnessHv { get; set; } = new();

        [JsonPropertyName("rom_thermal_conductivity")]
        public List<double> RomThermalConductivity { get; set; } = new();

        [JsonPropertyName("rom_electrical_resistivity")]
        public List<double> RomElectricalResistivity { get; set; } = new();

        [JsonPropertyName("rom_cte")]
        public List<double> RomCte { get; set; } = new();

        [JsonPropertyName("rom_density")]
        public List<double> RomDensity { get; set; } = new();
    }

    public class RomComparisonDto
    {
        [JsonPropertyName("comparison_table")]
        public List<RomComparisonRowDto> ComparisonTable { get; set; } = new();

        [JsonPropertyName("comparative_series")]
        public RomComparativeSeriesDto? ComparativeSeries { get; set; }

        [JsonPropertyName("summary")]
        public Dictionary<string, double> Summary { get; set; } = new();
    }

    #endregion

    #region Aqueous Pourbaix & TDAT Database DTOs

    public class WaterLinesDto
    {
        [JsonPropertyName("temp_c")]
        public double TempC { get; set; } = 25.0;

        [JsonPropertyName("temp_k")]
        public double TempK { get; set; } = 298.15;

        [JsonPropertyName("nernst_slope_v_ph")]
        public double NernstSlopeVPerPh { get; set; } = 0.05916;

        [JsonPropertyName("ph")]
        public List<double> Ph { get; set; } = new();

        [JsonPropertyName("e_her")]
        public List<double> EHer { get; set; } = new();

        [JsonPropertyName("e_oer")]
        public List<double> EOer { get; set; } = new();

        [JsonPropertyName("e0_oer")]
        public double E0Oer { get; set; } = 1.229;

        [JsonPropertyName("e0_her")]
        public double E0Her { get; set; } = 0.0;
    }

    public class PourbaixCompositeEnvelopeDto
    {
        [JsonPropertyName("e_pass_lower")]
        public List<double> EPassLower { get; set; } = new();

        [JsonPropertyName("e_trans_upper")]
        public List<double> ETransUpper { get; set; } = new();

        [JsonPropertyName("e_immunity")]
        public List<double> EImmunity { get; set; } = new();

        [JsonPropertyName("ph_pass_min")]
        public double PhPassMin { get; set; } = 2.4;

        [JsonPropertyName("is_passivating")]
        public bool IsPassivating { get; set; } = true;

        [JsonPropertyName("dominant_oxide")]
        public string DominantOxide { get; set; } = string.Empty;

        [JsonPropertyName("dominant_formula")]
        public string DominantFormula { get; set; } = string.Empty;
    }

    public class PourbaixPassivatingMineralDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("log_k")]
        public double LogK { get; set; } = 0.0;
    }

    public class PourbaixMetricsDto
    {
        [JsonPropertyName("E_pass_V_SHE")]
        public double EPassVSHE { get; set; } = 0.0;

        [JsonPropertyName("E_trans_V_SHE")]
        public double ETransVSHE { get; set; } = 0.0;

        [JsonPropertyName("Delta_E_pass_V")]
        public double DeltaEPassV { get; set; } = 0.0;

        [JsonPropertyName("pH_pass_min")]
        public double PhPassMin { get; set; } = 0.0;

        [JsonPropertyName("PassivityWindowQuality")]
        public string PassivityWindowQuality { get; set; } = string.Empty;

        [JsonPropertyName("HydrothermalStability")]
        public string HydrothermalStability { get; set; } = string.Empty;

        [JsonPropertyName("TemperatureCoefficient_mV_K")]
        public double TemperatureCoefficientMvK { get; set; } = -0.85;
    }

    public class PourbaixDiagramDto
    {
        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("database_name")]
        public string DatabaseName { get; set; } = string.Empty;

        [JsonPropertyName("temperature_c")]
        public double TemperatureC { get; set; } = 25.0;

        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; } = 298.15;

        [JsonPropertyName("pressure_bar")]
        public double PressureBar { get; set; } = 1.0;

        [JsonPropertyName("ion_activity")]
        public double IonActivity { get; set; } = 1e-6;

        [JsonPropertyName("water_lines")]
        public WaterLinesDto? WaterLines { get; set; }

        [JsonPropertyName("ph_grid")]
        public List<double> PhGrid { get; set; } = new();

        [JsonPropertyName("composite_envelope")]
        public PourbaixCompositeEnvelopeDto? CompositeEnvelope { get; set; }

        [JsonPropertyName("passivating_minerals")]
        public List<PourbaixPassivatingMineralDto> PassivatingMinerals { get; set; } = new();

        [JsonPropertyName("metrics")]
        public PourbaixMetricsDto Metrics { get; set; } = new();
    }

    public class TdatSpeciesDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("phase_type")]
        public string PhaseType { get; set; } = string.Empty;

        [JsonPropertyName("subtype")]
        public string Subtype { get; set; } = string.Empty;

        [JsonPropertyName("mole_wt")]
        public double MoleWt { get; set; } = 0.0;

        [JsonPropertyName("mole_vol_cc")]
        public double MoleVolCc { get; set; } = 0.0;

        [JsonPropertyName("log_k_25c")]
        public double? LogK25C { get; set; }

        [JsonPropertyName("log_k_100c")]
        public double? LogK100C { get; set; }

        [JsonPropertyName("reaction")]
        public string Reaction { get; set; } = string.Empty;

        [JsonPropertyName("delg0f_kj")]
        public double? DelG0fKj { get; set; }
    }

    public class TdatDatabaseSummaryDto
    {
        [JsonPropertyName("filename")]
        public string Filename { get; set; } = string.Empty;

        [JsonPropertyName("filepath")]
        public string Filepath { get; set; } = string.Empty;

        [JsonPropertyName("size_kb")]
        public double SizeKb { get; set; } = 0.0;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("provider")]
        public string Provider { get; set; } = string.Empty;

        [JsonPropertyName("scope")]
        public string Scope { get; set; } = string.Empty;

        [JsonPropertyName("standard")]
        public string Standard { get; set; } = string.Empty;

        [JsonPropertyName("activity_model")]
        public string ActivityModel { get; set; } = string.Empty;
    }

    public class TdatDatabaseCatalogResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("databases")]
        public List<TdatDatabaseSummaryDto> Databases { get; set; } = new();
    }

    public class TdatSearchResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("database_name")]
        public string DatabaseName { get; set; } = string.Empty;

        [JsonPropertyName("query")]
        public string Query { get; set; } = string.Empty;

        [JsonPropertyName("total_matches")]
        public int TotalMatches { get; set; }

        [JsonPropertyName("species")]
        public List<TdatSpeciesDto> Species { get; set; } = new();
    }

    #region HEA Literature Database DTOs

    public class HeaLiteratureItemDto
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("alloy")]
        public string Alloy { get; set; } = string.Empty;

        [JsonPropertyName("paper")]
        public string Paper { get; set; } = string.Empty;

        [JsonPropertyName("nb_phase")]
        public string NbPhase { get; set; } = string.Empty;

        [JsonPropertyName("phase")]
        public string Phase { get; set; } = string.Empty;

        [JsonPropertyName("study_type")]
        public string StudyType { get; set; } = string.Empty;

        [JsonPropertyName("synthesis_details")]
        public string SynthesisDetails { get; set; } = string.Empty;

        [JsonPropertyName("theoretical_details")]
        public string TheoreticalDetails { get; set; } = string.Empty;

        [JsonPropertyName("special_conditions")]
        public string SpecialConditions { get; set; } = string.Empty;

        [JsonPropertyName("solution_type")]
        public string SolutionType { get; set; } = string.Empty;

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("doi")]
        public string Doi { get; set; } = string.Empty;

        [JsonPropertyName("distance")]
        public double Distance { get; set; }

        [JsonPropertyName("match_percent")]
        public double MatchPercent { get; set; }
    }

    public class HeaLiteratureSearchResponseDto
    {
        [JsonPropertyName("total")]
        public int Total { get; set; }

        [JsonPropertyName("count")]
        public int Count { get; set; }

        [JsonPropertyName("limit")]
        public int Limit { get; set; }

        [JsonPropertyName("offset")]
        public int Offset { get; set; }

        [JsonPropertyName("items")]
        public List<HeaLiteratureItemDto> Items { get; set; } = new();
    }

    public class HeaLiteratureStatsDto
    {
        [JsonPropertyName("total_records")]
        public int TotalRecords { get; set; }

        [JsonPropertyName("unique_alloys")]
        public int UniqueAlloys { get; set; }

        [JsonPropertyName("top_phases")]
        public List<Dictionary<string, object>> TopPhases { get; set; } = new();

        [JsonPropertyName("solution_types")]
        public List<Dictionary<string, object>> SolutionTypes { get; set; } = new();

        [JsonPropertyName("study_types")]
        public List<Dictionary<string, object>> StudyTypes { get; set; } = new();
    }

    #endregion

    #region Surface Complexation & Sorption (SDAT) DTOs

    public class SdatDatabaseSummaryDto
    {
        [JsonPropertyName("filename")]
        public string Filename { get; set; } = string.Empty;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("category")]
        public string Category { get; set; } = string.Empty;

        [JsonPropertyName("surface_type")]
        public string SurfaceType { get; set; } = string.Empty;

        [JsonPropertyName("model_type")]
        public string ModelType { get; set; } = string.Empty;

        [JsonPropertyName("mineral_count")]
        public int MineralCount { get; set; }

        [JsonPropertyName("species_count")]
        public int SpeciesCount { get; set; }
    }

    public class SdatDatabaseCatalogResponse
    {
        [JsonPropertyName("databases")]
        public List<SdatDatabaseSummaryDto> Databases { get; set; } = new();
    }

    public class SdatReactionSpeciesDto
    {
        [JsonPropertyName("species")]
        public string Species { get; set; } = string.Empty;

        [JsonPropertyName("coeff")]
        public double Coeff { get; set; }
    }

    public class SdatSurfaceSpeciesDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("charge")]
        public double Charge { get; set; }

        [JsonPropertyName("mole_wt")]
        public double MoleWt { get; set; }

        [JsonPropertyName("log_k_a")]
        public double LogKA { get; set; }

        [JsonPropertyName("log_k_b")]
        public double LogKB { get; set; }

        [JsonPropertyName("reaction")]
        public List<SdatReactionSpeciesDto> Reaction { get; set; } = new();

        public string BalancedEquation
        {
            get
            {
                if (Reaction == null || Reaction.Count == 0) return Name;
                var reactants = new List<string>();
                var products = new List<string>();
                foreach (var r in Reaction)
                {
                    if (r.Coeff < 0)
                        reactants.Add(Math.Abs(r.Coeff) == 1.0 ? r.Species : $"{Math.Abs(r.Coeff)} {r.Species}");
                    else
                        products.Add(r.Coeff == 1.0 ? r.Species : $"{r.Coeff} {r.Species}");
                }
                string lhs = reactants.Count > 0 ? string.Join(" + ", reactants) : "";
                string rhs = products.Count > 0 ? string.Join(" + ", products) : "";
                return $"{lhs} \u2194 {rhs}".Trim();
            }
        }
    }

    public class SdatSorbingSiteDto
    {
        [JsonPropertyName("site_name")]
        public string SiteName { get; set; } = string.Empty;

        [JsonPropertyName("site_density")]
        public double SiteDensity { get; set; }

        [JsonPropertyName("unit")]
        public string Unit { get; set; } = string.Empty;
    }

    public class SdatMineralDto
    {
        [JsonPropertyName("mineral")]
        public string Mineral { get; set; } = string.Empty;

        [JsonPropertyName("surface_area_m2_g")]
        public double SurfaceAreaM2G { get; set; }

        [JsonPropertyName("sites")]
        public List<SdatSorbingSiteDto> Sites { get; set; } = new();
    }

    public class SdatDetailDto
    {
        [JsonPropertyName("filename")]
        public string Filename { get; set; } = string.Empty;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("category")]
        public string Category { get; set; } = string.Empty;

        [JsonPropertyName("header")]
        public Dictionary<string, object> Header { get; set; } = new();

        [JsonPropertyName("sorbing_minerals")]
        public List<SdatMineralDto> SorbingMinerals { get; set; } = new();

        [JsonPropertyName("surface_species")]
        public List<SdatSurfaceSpeciesDto> SurfaceSpecies { get; set; } = new();
    }

    public class SdatSurfaceSpeciationDto
    {
        [JsonPropertyName("surface_type")]
        public string SurfaceType { get; set; } = string.Empty;

        [JsonPropertyName("model_type")]
        public string ModelType { get; set; } = string.Empty;

        [JsonPropertyName("ph_pzc")]
        public double PhPzc { get; set; }

        [JsonPropertyName("log_k_protonation")]
        public double LogKProtonation { get; set; }

        [JsonPropertyName("log_k_deprotonation")]
        public double LogKDeprotonation { get; set; }

        [JsonPropertyName("ph_values")]
        public List<double> PhValues { get; set; } = new();

        [JsonPropertyName("fraction_protonated_oh2")]
        public List<double> FractionProtonatedOh2 { get; set; } = new();

        [JsonPropertyName("fraction_neutral_oh")]
        public List<double> FractionNeutralOh { get; set; } = new();

        [JsonPropertyName("fraction_deprotonated_o")]
        public List<double> FractionDeprotonatedO { get; set; } = new();

        [JsonPropertyName("surface_charge_density_uC_cm2")]
        public List<double> SurfaceChargeDensityUC_Cm2 { get; set; } = new();
    }

    #endregion

    #region OLI Studio Electrolyte Streams DTOs

    public class OadInflowDto
    {
        [JsonPropertyName("species")]
        public string Species { get; set; } = string.Empty;

        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("conc_ppm")]
        public double ConcPpm { get; set; }

        [JsonPropertyName("role")]
        public string Role { get; set; } = string.Empty;
    }

    public class OadStreamSummaryDto
    {
        [JsonPropertyName("stream_id")]
        public string StreamId { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("industry")]
        public string Industry { get; set; } = string.Empty;

        [JsonPropertyName("ph")]
        public double Ph { get; set; }

        [JsonPropertyName("temperature_c")]
        public double TemperatureC { get; set; }

        [JsonPropertyName("ionic_strength_m")]
        public double IonicStrengthM { get; set; }

        [JsonPropertyName("redox_potential_mv")]
        public double RedoxPotentialMv { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("major_inflows")]
        public List<OadInflowDto> MajorInflows { get; set; } = new();
    }

    public class OadStreamsCatalogResponse
    {
        [JsonPropertyName("streams")]
        public List<OadStreamSummaryDto> Streams { get; set; } = new();
    }

    #endregion

    #region USGS Electrolyte Conductivity DTO

    public class ElectrolyteConductivityDto
    {
        [JsonPropertyName("temperature_c")]
        public double TemperatureC { get; set; }

        [JsonPropertyName("ionic_strength_mol_L")]
        public double IonicStrengthMolL { get; set; }

        [JsonPropertyName("conductivity_uS_cm")]
        public double ConductivityUS_Cm { get; set; }

        [JsonPropertyName("conductivity_mS_cm")]
        public double ConductivityMS_Cm { get; set; }

        [JsonPropertyName("resistivity_ohm_cm")]
        public double ResistivityOhmCm { get; set; }

        [JsonPropertyName("species_contributions_uS_cm")]
        public Dictionary<string, double> SpeciesContributions { get; set; } = new();
    }

    #endregion

    #region Compound Energy Formalism (CEF) & Advanced CALPHAD DTOs

    public class CefSublatticeDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("multiplicity")]
        public double Multiplicity { get; set; } = 1.0;

        [JsonPropertyName("constituents")]
        public List<string> Constituents { get; set; } = new();

        [JsonPropertyName("site_fractions")]
        public Dictionary<string, double> SiteFractions { get; set; } = new();
    }

    public class CefTemperatureSeriesDto
    {
        [JsonPropertyName("temperatures_C")]
        public List<double> TemperaturesC { get; set; } = new();

        [JsonPropertyName("temperatures_K")]
        public List<double> TemperaturesK { get; set; } = new();

        [JsonPropertyName("G_ref")]
        public List<double> GRef { get; set; } = new();

        [JsonPropertyName("G_id")]
        public List<double> GId { get; set; } = new();

        [JsonPropertyName("G_ex")]
        public List<double> GEx { get; set; } = new();

        [JsonPropertyName("G_mag")]
        public List<double> GMag { get; set; } = new();

        [JsonPropertyName("G_m")]
        public List<double> Gm { get; set; } = new();
    }

    public class CefCalculationResultDto
    {
        [JsonPropertyName("phase_name")]
        public string PhaseName { get; set; } = string.Empty;

        [JsonPropertyName("overall_composition")]
        public Dictionary<string, double> OverallComposition { get; set; } = new();

        [JsonPropertyName("temperature_series")]
        public CefTemperatureSeriesDto TemperatureSeries { get; set; } = new();

        [JsonPropertyName("num_sublattices")]
        public int NumSublattices { get; set; }

        [JsonPropertyName("total_multiplicity")]
        public double TotalMultiplicity { get; set; }
    }

    public class TernaryExtrapolationResultDto
    {
        [JsonPropertyName("x1")]
        public List<double> X1 { get; set; } = new();

        [JsonPropertyName("x2")]
        public List<double> X2 { get; set; } = new();

        [JsonPropertyName("x3")]
        public List<double> X3 { get; set; } = new();

        [JsonPropertyName("G_ex_muggianu")]
        public List<double> GExMuggianu { get; set; } = new();

        [JsonPropertyName("G_ex_kohler")]
        public List<double> GExKohler { get; set; } = new();

        [JsonPropertyName("G_ex_toop")]
        public List<double> GExToop { get; set; } = new();
    }

    public class UhtcReactionDataDto
    {
        [JsonPropertyName("dissolution_extent")]
        public List<double> DissolutionExtent { get; set; } = new();

        [JsonPropertyName("x_Ni")]
        public List<double> XNi { get; set; } = new();

        [JsonPropertyName("x_B")]
        public List<double> XB { get; set; } = new();

        [JsonPropertyName("x_Metal")]
        public List<double> XMetal { get; set; } = new();

        [JsonPropertyName("transient_tau_fraction")]
        public List<double> TransientTauFraction { get; set; } = new();

        [JsonPropertyName("driving_force_kJ_mol")]
        public List<double> DrivingForceKjMol { get; set; } = new();
    }

    public class UhtcIsothermalResultDto
    {
        [JsonPropertyName("substrate")]
        public string Substrate { get; set; } = string.Empty;

        [JsonPropertyName("transient_compound")]
        public string TransientCompound { get; set; } = string.Empty;

        [JsonPropertyName("temperature_C")]
        public double TemperatureC { get; set; }

        [JsonPropertyName("summary")]
        public string Summary { get; set; } = string.Empty;

        [JsonPropertyName("data")]
        public UhtcReactionDataDto Data { get; set; } = new();
    }

    public class UhtcCoolingResultDto
    {
        [JsonPropertyName("substrate")]
        public string Substrate { get; set; } = string.Empty;

        [JsonPropertyName("transient_compound")]
        public string TransientCompound { get; set; } = string.Empty;

        [JsonPropertyName("liquidus_temperature_C")]
        public double LiquidusTemperatureC { get; set; }

        [JsonPropertyName("eutectic_temperature_C")]
        public double EutecticTemperatureC { get; set; }

        [JsonPropertyName("temperatures_C")]
        public List<double> TemperaturesC { get; set; } = new();

        [JsonPropertyName("liquid_fraction")]
        public List<double> LiquidFraction { get; set; } = new();

        [JsonPropertyName("zrb2_fraction")]
        public List<double> Zrb2Fraction { get; set; } = new();

        [JsonPropertyName("tau_fraction")]
        public List<double> TauFraction { get; set; } = new();

        [JsonPropertyName("ni3b_fraction")]
        public List<double> Ni3bFraction { get; set; } = new();

        [JsonPropertyName("niss_fraction")]
        public List<double> NissFraction { get; set; } = new();
    }

    public class UhtcWettingResultDto
    {
        [JsonPropertyName("isothermal_reaction")]
        public UhtcIsothermalResultDto IsothermalReaction { get; set; } = new();

        [JsonPropertyName("cooling_solidification")]
        public UhtcCoolingResultDto CoolingSolidification { get; set; } = new();
    }

    #endregion

    #region Refractory High Entropy Alloys (RHEA) DTOs

    public class RheaYieldStrengthPointDto
    {
        [JsonPropertyName("temperature_c")]
        public double TemperatureC { get; set; }

        [JsonPropertyName("yield_strength_mpa")]
        public double YieldStrengthMpa { get; set; }

        [JsonPropertyName("uts_mpa")]
        public double? UtsMpa { get; set; }

        [JsonPropertyName("elongation_pct")]
        public double? ElongationPct { get; set; }
    }

    public class RheaBenchmarkDto
    {
        [JsonPropertyName("key")]
        public string Key { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("category")]
        public string Category { get; set; } = string.Empty;

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("mole_fractions")]
        public Dictionary<string, double> MoleFractions { get; set; } = new();

        [JsonPropertyName("weight_fractions")]
        public Dictionary<string, double> WeightFractions { get; set; } = new();

        [JsonPropertyName("density_exp_g_cm3")]
        public double DensityExpGCm3 { get; set; }

        [JsonPropertyName("density_calc_g_cm3")]
        public double DensityCalcGCm3 { get; set; }

        [JsonPropertyName("crystal_structure")]
        public string CrystalStructure { get; set; } = string.Empty;

        [JsonPropertyName("lattice_parameter_a_angstrom")]
        public double? LatticeParameterAAngstrom { get; set; }

        [JsonPropertyName("solidus_k")]
        public double? SolidusK { get; set; }

        [JsonPropertyName("liquidus_k")]
        public double? LiquidusK { get; set; }

        [JsonPropertyName("hardness_hv")]
        public double? HardnessHv { get; set; }

        [JsonPropertyName("elongation_rt_pct")]
        public double? ElongationRtPct { get; set; }

        [JsonPropertyName("oxidation_kp_800c")]
        public double? OxidationKp800c { get; set; }

        [JsonPropertyName("oxidation_scale_type")]
        public string? OxidationScaleType { get; set; }

        [JsonPropertyName("yield_strength_curve")]
        public List<RheaYieldStrengthPointDto> YieldStrengthCurve { get; set; } = new();

        [JsonPropertyName("citations")]
        public Dictionary<string, string> Citations { get; set; } = new();

        [JsonPropertyName("doi")]
        public string Doi { get; set; } = string.Empty;

        [JsonPropertyName("notes")]
        public string Notes { get; set; } = string.Empty;
    }

    public class RheaStrengthCurveItemDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("density")]
        public double Density { get; set; }

        [JsonPropertyName("temperatures_c")]
        public List<double> TemperaturesC { get; set; } = new();

        [JsonPropertyName("yield_strengths_mpa")]
        public List<double> YieldStrengthsMpa { get; set; } = new();

        [JsonPropertyName("reference")]
        public string Reference { get; set; } = string.Empty;

        [JsonPropertyName("doi")]
        public string Doi { get; set; } = string.Empty;
    }

    public class RheaLiteratureQueryResultDto
    {
        [JsonPropertyName("total")]
        public int Total { get; set; }

        [JsonPropertyName("count")]
        public int Count { get; set; }

        [JsonPropertyName("offset")]
        public int Offset { get; set; }

        [JsonPropertyName("limit")]
        public int Limit { get; set; }

        [JsonPropertyName("alloys")]
        public List<Dictionary<string, object>> Alloys { get; set; } = new();
    }

    #endregion

    #region Binary Phase Diagram Models

    public class BinaryCurveDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("xs")]
        public List<double> Xs { get; set; } = new();

        [JsonPropertyName("ys")]
        public List<double> Ys { get; set; } = new();

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#0F172A";

        [JsonPropertyName("width")]
        public double Width { get; set; } = 1.5;

        [JsonPropertyName("dash")]
        public string Dash { get; set; } = "solid";
    }

    public class BinaryInvariantDto
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("temp")]
        public double Temp { get; set; }

        [JsonPropertyName("x_reaction")]
        public double XReaction { get; set; }

        [JsonPropertyName("x_start")]
        public double XStart { get; set; }

        [JsonPropertyName("x_end")]
        public double XEnd { get; set; }

        [JsonPropertyName("equation")]
        public string Equation { get; set; } = string.Empty;
    }

    public class BinaryRegionDto
    {
        [JsonPropertyName("label")]
        public string Label { get; set; } = string.Empty;

        [JsonPropertyName("x")]
        public double X { get; set; }

        [JsonPropertyName("y")]
        public double Y { get; set; }

        [JsonPropertyName("font_size")]
        public double FontSize { get; set; } = 11.0;

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#1E293B";
    }

    public class BinaryDiagramDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("element_a")]
        public string ElementA { get; set; } = string.Empty;

        [JsonPropertyName("element_b")]
        public string ElementB { get; set; } = string.Empty;

        [JsonPropertyName("x_axis_label")]
        public string XAxisLabel { get; set; } = "Composition X";

        [JsonPropertyName("y_axis_label")]
        public string YAxisLabel { get; set; } = "Temperature";

        [JsonPropertyName("temp_unit")]
        public string TempUnit { get; set; } = "Â°C";

        [JsonPropertyName("x_min")]
        public double XMin { get; set; } = 0.0;

        [JsonPropertyName("x_max")]
        public double XMax { get; set; } = 1.0;

        [JsonPropertyName("y_min")]
        public double YMin { get; set; }

        [JsonPropertyName("y_max")]
        public double YMax { get; set; }

        [JsonPropertyName("curves")]
        public List<BinaryCurveDto> Curves { get; set; } = new();

        [JsonPropertyName("invariants")]
        public List<BinaryInvariantDto> Invariants { get; set; } = new();

        [JsonPropertyName("regions")]
        public List<BinaryRegionDto> Regions { get; set; } = new();
    }

    public class BinaryLeverRuleDto
    {
        [JsonPropertyName("state")]
        public string State { get; set; } = string.Empty;

        [JsonPropertyName("temperature")]
        public double Temperature { get; set; }

        [JsonPropertyName("composition")]
        public double Composition { get; set; }

        [JsonPropertyName("phase1_name")]
        public string Phase1Name { get; set; } = string.Empty;

        [JsonPropertyName("phase1_fraction")]
        public double Phase1Fraction { get; set; }

        [JsonPropertyName("phase1_comp")]
        public double? Phase1Comp { get; set; }

        [JsonPropertyName("phase2_name")]
        public string Phase2Name { get; set; } = string.Empty;

        [JsonPropertyName("phase2_fraction")]
        public double Phase2Fraction { get; set; }

        [JsonPropertyName("phase2_comp")]
        public double? Phase2Comp { get; set; }
    }

    public class BinarySystemsResultDto
    {
        [JsonPropertyName("systems")]
        public List<string> Systems { get; set; } = new();
    }

    #region Ternary Phase Diagram Formalism Models (Gibbs Equilateral Triangle)
    public class TernarySystemSummaryDto
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("category")]
        public string Category { get; set; } = string.Empty;

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("topology")]
        public string Topology { get; set; } = string.Empty;

        [JsonPropertyName("citation")]
        public string Citation { get; set; } = string.Empty;
    }

    public class TernarySystemsContainerDto
    {
        [JsonPropertyName("systems")]
        public List<TernarySystemSummaryDto> Systems { get; set; } = new();
    }

    public class TernaryCurveDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("xs")]
        public List<double> Xs { get; set; } = new();

        [JsonPropertyName("ys")]
        public List<double> Ys { get; set; } = new();

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#1D4ED8";

        [JsonPropertyName("line_style")]
        public string LineStyle { get; set; } = "Solid";

        [JsonPropertyName("line_width")]
        public double LineWidth { get; set; } = 2.0;
    }

    public class TernaryGridLineDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("xs")]
        public List<double> Xs { get; set; } = new();

        [JsonPropertyName("ys")]
        public List<double> Ys { get; set; } = new();

        [JsonPropertyName("frac")]
        public double Frac { get; set; }

        [JsonPropertyName("axis")]
        public string Axis { get; set; } = string.Empty;
    }

    public class TernaryTieLineDto
    {
        [JsonPropertyName("xs")]
        public List<double> Xs { get; set; } = new();

        [JsonPropertyName("ys")]
        public List<double> Ys { get; set; } = new();

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#64748B";
    }

    public class TernaryTieTriangleDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("v1")]
        public List<double> V1 { get; set; } = new();

        [JsonPropertyName("v2")]
        public List<double> V2 { get; set; } = new();

        [JsonPropertyName("v3")]
        public List<double> V3 { get; set; } = new();

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#FEE2E2";

        [JsonPropertyName("border_color")]
        public string BorderColor { get; set; } = "#DC2626";
    }

    public class TernaryPhaseLabelDto
    {
        [JsonPropertyName("text")]
        public string Text { get; set; } = string.Empty;

        [JsonPropertyName("x")]
        public double X { get; set; }

        [JsonPropertyName("y")]
        public double Y { get; set; }

        [JsonPropertyName("color")]
        public string Color { get; set; } = "#0F172A";

        [JsonPropertyName("bold")]
        public bool Bold { get; set; } = true;
    }

    public class TernaryApexLabelDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("x")]
        public double X { get; set; }

        [JsonPropertyName("y")]
        public double Y { get; set; }

        [JsonPropertyName("align")]
        public string Align { get; set; } = "Center";
    }

    public class TernaryInvariantDto
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("temp_c")]
        public double TempC { get; set; }

        [JsonPropertyName("temp_formatted")]
        public string TempFormatted { get; set; } = string.Empty;

        [JsonPropertyName("equation")]
        public string Equation { get; set; } = string.Empty;

        [JsonPropertyName("composition")]
        public string Composition { get; set; } = string.Empty;

        [JsonPropertyName("desc")]
        public string Desc { get; set; } = string.Empty;
    }

    public class TernaryDiagramDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("element_a")]
        public string ElementA { get; set; } = string.Empty;

        [JsonPropertyName("element_b")]
        public string ElementB { get; set; } = string.Empty;

        [JsonPropertyName("element_c")]
        public string ElementC { get; set; } = string.Empty;

        [JsonPropertyName("diagram_type")]
        public string DiagramType { get; set; } = "isothermal";

        [JsonPropertyName("temperature")]
        public double Temperature { get; set; }

        [JsonPropertyName("temp_unit")]
        public string TempUnit { get; set; } = "°C";

        [JsonPropertyName("triangle_border_x")]
        public List<double> TriangleBorderX { get; set; } = new();

        [JsonPropertyName("triangle_border_y")]
        public List<double> TriangleBorderY { get; set; } = new();

        [JsonPropertyName("grid_lines")]
        public List<TernaryGridLineDto> GridLines { get; set; } = new();

        [JsonPropertyName("apex_labels")]
        public Dictionary<string, TernaryApexLabelDto> ApexLabels { get; set; } = new();

        [JsonPropertyName("curves")]
        public List<TernaryCurveDto> Curves { get; set; } = new();

        [JsonPropertyName("tie_lines")]
        public List<TernaryTieLineDto> TieLines { get; set; } = new();

        [JsonPropertyName("tie_triangles")]
        public List<TernaryTieTriangleDto> TieTriangles { get; set; } = new();

        [JsonPropertyName("phase_labels")]
        public List<TernaryPhaseLabelDto> PhaseLabels { get; set; } = new();

        [JsonPropertyName("invariants")]
        public List<TernaryInvariantDto> Invariants { get; set; } = new();

        [JsonPropertyName("literature_notes")]
        public string LiteratureNotes { get; set; } = string.Empty;
    }
    #endregion

    #region Kaufman-Mallik Phase Diagram Formalism Models (Mallik 1986)

    public class KaufmanMallikBinaryResultDto
    {
        [JsonPropertyName("converged")]
        public bool Converged { get; set; }

        [JsonPropertyName("iterations")]
        public int Iterations { get; set; }

        [JsonPropertyName("t_kelvin")]
        public double TKelvin { get; set; }

        [JsonPropertyName("x_alpha")]
        public double XAlpha { get; set; }

        [JsonPropertyName("x_beta")]
        public double XBeta { get; set; }

        [JsonPropertyName("residual_norm")]
        public double ResidualNorm { get; set; }

        [JsonPropertyName("unit")]
        public string Unit { get; set; } = "J/mol";
    }

    public class ParameterInversionResultDto
    {
        [JsonPropertyName("t_kelvin")]
        public double TKelvin { get; set; }

        [JsonPropertyName("x_alpha")]
        public double XAlpha { get; set; }

        [JsonPropertyName("x_beta")]
        public double XBeta { get; set; }

        [JsonPropertyName("e_alpha")]
        public double EAlpha { get; set; }

        [JsonPropertyName("e_beta")]
        public double EBeta { get; set; }

        [JsonPropertyName("determinant")]
        public double Determinant { get; set; }

        [JsonPropertyName("residual_f")]
        public double ResidualF { get; set; }

        [JsonPropertyName("residual_g")]
        public double ResidualG { get; set; }

        [JsonPropertyName("unit")]
        public string Unit { get; set; } = "J/mol";
    }

    public class MiscibilityGapResultDto
    {
        [JsonPropertyName("miscible")]
        public bool Miscible { get; set; }

        [JsonPropertyName("t_kelvin")]
        public double TKelvin { get; set; }

        [JsonPropertyName("t_critical")]
        public double TCritical { get; set; }

        [JsonPropertyName("binodal_x1")]
        public double BinodalX1 { get; set; }

        [JsonPropertyName("binodal_x2")]
        public double BinodalX2 { get; set; }

        [JsonPropertyName("spinodal_x1")]
        public double SpinodalX1 { get; set; }

        [JsonPropertyName("spinodal_x2")]
        public double SpinodalX2 { get; set; }

        [JsonPropertyName("gap_width")]
        public double GapWidth { get; set; }

        [JsonPropertyName("unit")]
        public string Unit { get; set; } = "J/mol";
    }

    public class KaufmanMallikPresetDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("topology")]
        public string Topology { get; set; } = string.Empty;

        [JsonPropertyName("unit")]
        public string Unit { get; set; } = "cal/mol";
    }

    public class KaufmanMallikPresetsContainerDto
    {
        [JsonPropertyName("presets")]
        public Dictionary<string, KaufmanMallikPresetDto> Presets { get; set; } = new();
    }

    #endregion

    #region Redlich-Kister Parameter Inversion Formalism Models

    public class RedlichKisterParameterDto
    {
        [JsonPropertyName("term_order")]
        public int TermOrder { get; set; }

        [JsonPropertyName("L_k_expression")]
        public string Expression { get; set; } = string.Empty;

        [JsonPropertyName("a_enthalpy_J_mol")]
        public double AEnthalpyJMol { get; set; }

        [JsonPropertyName("b_entropy_J_mol_K")]
        public double BEntropyJMolK { get; set; }
    }

    public class RedlichKisterInversionStatisticsDto
    {
        [JsonPropertyName("chi2_metric")]
        public double Chi2Metric { get; set; }

        [JsonPropertyName("rmse_chemical_potential_J_mol")]
        public double RmseChemicalPotentialJMol { get; set; }

        [JsonPropertyName("mae_chemical_potential_J_mol")]
        public double MaeChemicalPotentialJMol { get; set; }

        [JsonPropertyName("data_points_fitted")]
        public int DataPointsFitted { get; set; }

        [JsonPropertyName("annealing_steps_executed")]
        public int AnnealingStepsExecuted { get; set; }
    }

    public class RedlichKisterSolvusOverlayDto
    {
        [JsonPropertyName("temperature_C")]
        public List<double> TemperatureC { get; set; } = new();

        [JsonPropertyName("x_alpha_solvus")]
        public List<double> XAlphaSolvus { get; set; } = new();

        [JsonPropertyName("x_beta_solvus")]
        public List<double> XBetaSolvus { get; set; } = new();

        [JsonPropertyName("has_miscibility_gap")]
        public bool HasMiscibilityGap { get; set; }
    }

    public class RedlichKisterInversionResultDto
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("fitted_parameters")]
        public List<RedlichKisterParameterDto> FittedParameters { get; set; } = new();

        [JsonPropertyName("statistics")]
        public RedlichKisterInversionStatisticsDto? Statistics { get; set; }

        [JsonPropertyName("solvus_overlay")]
        public RedlichKisterSolvusOverlayDto? SolvusOverlay { get; set; }
    }

    #region ESPEI Datasets Models

    public class EspeiStatisticsDto
    {
        [JsonPropertyName("total_datasets")]
        public int TotalDatasets { get; set; }

        [JsonPropertyName("total_systems")]
        public int TotalSystems { get; set; }

        [JsonPropertyName("binary_systems_count")]
        public int BinarySystemsCount { get; set; }

        [JsonPropertyName("ternary_systems_count")]
        public int TernarySystemsCount { get; set; }

        [JsonPropertyName("total_references")]
        public int TotalReferences { get; set; }

        [JsonPropertyName("zpf_dataset_count")]
        public int ZpfDatasetCount { get; set; }

        [JsonPropertyName("thermochemical_dataset_count")]
        public int ThermochemicalDatasetCount { get; set; }

        [JsonPropertyName("unique_phases_count")]
        public int UniquePhasesCount { get; set; }

        [JsonPropertyName("systems")]
        public List<string> Systems { get; set; } = new();
    }

    public class EspeiSystemSummaryDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("tier")]
        public string Tier { get; set; } = string.Empty;

        [JsonPropertyName("dataset_count")]
        public int DatasetCount { get; set; }

        [JsonPropertyName("zpf_dataset_count")]
        public int ZpfDatasetCount { get; set; }

        [JsonPropertyName("thermochemical_dataset_count")]
        public int ThermochemicalDatasetCount { get; set; }

        [JsonPropertyName("outputs")]
        public List<string> Outputs { get; set; } = new();

        [JsonPropertyName("phases")]
        public List<string> Phases { get; set; } = new();

        [JsonPropertyName("references")]
        public List<string> References { get; set; } = new();
    }

    public class EspeiSystemsContainerDto
    {
        [JsonPropertyName("systems")]
        public List<EspeiSystemSummaryDto> Systems { get; set; } = new();

        [JsonPropertyName("total")]
        public int Total { get; set; }
    }

    public class EspeiZpfPointDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; }

        [JsonPropertyName("temperature_c")]
        public double TemperatureC { get; set; }

        [JsonPropertyName("phase")]
        public string Phase { get; set; } = string.Empty;

        [JsonPropertyName("element")]
        public string Element { get; set; } = string.Empty;

        [JsonPropertyName("composition")]
        public double Composition { get; set; }

        [JsonPropertyName("reference")]
        public string Reference { get; set; } = string.Empty;

        [JsonPropertyName("source_file")]
        public string SourceFile { get; set; } = string.Empty;
    }

    public class EspeiZpfContainerDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("points")]
        public List<EspeiZpfPointDto> Points { get; set; } = new();

        [JsonPropertyName("count")]
        public int Count { get; set; }
    }

    public class EspeiThermochemicalPointDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("property")]
        public string Property { get; set; } = string.Empty;

        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; }

        [JsonPropertyName("phase")]
        public string Phase { get; set; } = string.Empty;

        [JsonPropertyName("value_si")]
        public double ValueSi { get; set; }

        [JsonPropertyName("unit")]
        public string Unit { get; set; } = string.Empty;

        [JsonPropertyName("reference")]
        public string Reference { get; set; } = string.Empty;

        [JsonPropertyName("source_file")]
        public string SourceFile { get; set; } = string.Empty;
    }

    public class EspeiThermochemicalContainerDto
    {
        [JsonPropertyName("system")]
        public string System { get; set; } = string.Empty;

        [JsonPropertyName("property")]
        public string? Property { get; set; }

        [JsonPropertyName("points")]
        public List<EspeiThermochemicalPointDto> Points { get; set; } = new();

        [JsonPropertyName("count")]
        public int Count { get; set; }
    }

    #region HEA Master Datasets Models

    public class HeaMasterStatisticsDto
    {
        [JsonPropertyName("total_mpea_experimental_records")]
        public int TotalMpeaExperimentalRecords { get; set; }

        [JsonPropertyName("total_phase_stability_records")]
        public int TotalPhaseStabilityRecords { get; set; }

        [JsonPropertyName("total_high_temperature_mechanical_records")]
        public int TotalHighTemperatureMechanicalRecords { get; set; }

        [JsonPropertyName("total_synthesis_process_records")]
        public int TotalSynthesisProcessRecords { get; set; }

        [JsonPropertyName("total_aggregate_records")]
        public int TotalAggregateRecords { get; set; }

        [JsonPropertyName("alloys_with_yield_strength")]
        public int AlloysWithYieldStrength { get; set; }

        [JsonPropertyName("alloys_with_hardness")]
        public int AlloysWithHardness { get; set; }

        [JsonPropertyName("alloys_with_uts")]
        public int AlloysWithUts { get; set; }

        [JsonPropertyName("alloys_with_youngs_modulus")]
        public int AlloysWithYoungsModulus { get; set; }

        [JsonPropertyName("element_coverage_count")]
        public int ElementCoverageCount { get; set; }

        [JsonPropertyName("unique_elements_modeled")]
        public List<string> UniqueElementsModeled { get; set; } = new();
    }

    public class HeaRecordDto
    {
        [JsonPropertyName("source")]
        public string Source { get; set; } = string.Empty;

        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("elements")]
        public List<string> Elements { get; set; } = new();

        [JsonPropertyName("phase_structure")]
        public string? PhaseStructure { get; set; }

        [JsonPropertyName("microstructure")]
        public string? Microstructure { get; set; }

        [JsonPropertyName("processing_method")]
        public string? ProcessingMethod { get; set; }

        [JsonPropertyName("yield_strength_mpa")]
        public double? YieldStrengthMpa { get; set; }

        [JsonPropertyName("uts_mpa")]
        public double? UtsMpa { get; set; }

        [JsonPropertyName("hardness_hv")]
        public double? HardnessHv { get; set; }

        [JsonPropertyName("elongation_pct")]
        public double? ElongationPct { get; set; }

        [JsonPropertyName("youngs_modulus_gpa")]
        public double? YoungsModulusGpa { get; set; }

        [JsonPropertyName("density_exp_g_cm3")]
        public double? DensityExpGCm3 { get; set; }

        [JsonPropertyName("test_temperature_c")]
        public double? TestTemperatureC { get; set; }

        [JsonPropertyName("experimental_details")]
        public string? ExperimentalDetails { get; set; }

        [JsonPropertyName("reference_id")]
        public string? ReferenceId { get; set; }

        [JsonPropertyName("vec")]
        public double? Vec { get; set; }

        [JsonPropertyName("mixing_enthalpy_kj_mol")]
        public double? MixingEnthalpyKjMol { get; set; }

        [JsonPropertyName("mixing_entropy_j_mol_k")]
        public double? MixingEntropyJMolK { get; set; }
    }

    public class HeaSearchResultsContainerDto
    {
        [JsonPropertyName("results")]
        public List<HeaRecordDto> Results { get; set; } = new();

        [JsonPropertyName("count")]
        public int Count { get; set; }
    }

    public class HeaTemperatureYieldPointDto
    {
        [JsonPropertyName("temperature_c")]
        public double TemperatureC { get; set; }

        [JsonPropertyName("temperature_k")]
        public double TemperatureK { get; set; }

        [JsonPropertyName("yield_strength_mpa")]
        public double YieldStrengthMpa { get; set; }

        [JsonPropertyName("condition")]
        public string Condition { get; set; } = string.Empty;
    }

    public class HeaTemperatureYieldCurveDto
    {
        [JsonPropertyName("formula")]
        public string Formula { get; set; } = string.Empty;

        [JsonPropertyName("data_points")]
        public List<HeaTemperatureYieldPointDto> DataPoints { get; set; } = new();

        [JsonPropertyName("count")]
        public int Count { get; set; }
    }

    #endregion

    #endregion

    #endregion

    #endregion

    #endregion

    #endregion
}
