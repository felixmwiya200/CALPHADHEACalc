// <copyright file="ExperimentalOptionsWindow.xaml.cs" company="PyCALPHAD Materials CAE">
// Interactive dialogue for configuring experimental options of hatch pitch, grain size, and additive manufacturing processing parameters.
// </copyright>

using System;
using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Desktop.Dialogs
{
    public partial class ExperimentalOptionsWindow : Window
    {
        private bool _isUpdatingUi = false;
        private bool _isInitialized = false;
        public ExperimentalProcessOptions Options { get; private set; }

        public static bool IsLaserProcess(string? processName)
        {
            if (string.IsNullOrWhiteSpace(processName)) return true;
            var p = processName.ToLowerInvariant();
            return p.Contains("laser") || p.Contains("l-pbf") || p.Contains("lpbf") || p.Contains("slm") || p.Contains("ded") || p.Contains("cladding");
        }

        public void UpdateLaserVisibility(bool isLaser)
        {
            var vis = isLaser ? Visibility.Visible : Visibility.Collapsed;
            if (GroupLaserParams != null) GroupLaserParams.Visibility = vis;
            if (GroupLaserIndicators != null) GroupLaserIndicators.Visibility = vis;
        }

        public ExperimentalOptionsWindow(ExperimentalProcessOptions? currentOptions = null, string? processName = null)
        {
            Options = currentOptions?.Clone() ?? new ExperimentalProcessOptions();
            _isUpdatingUi = true;
            InitializeComponent();
            _isInitialized = true;
            _isUpdatingUi = false;

            bool isLaser = IsLaserProcess(processName);
            if (!string.IsNullOrWhiteSpace(processName) && !isLaser)
            {
                _isUpdatingUi = true;
                if (processName.Contains("Cast", StringComparison.OrdinalIgnoreCase) || processName.Contains("VAR", StringComparison.OrdinalIgnoreCase))
                {
                    if (CmbPreset != null) CmbPreset.SelectedIndex = 3; // Cast / Ingot
                    Options.GrainSizeUm = 85.0;
                }
                else
                {
                    if (CmbPreset != null) CmbPreset.SelectedIndex = 4; // Wrought / Annealed
                    Options.GrainSizeUm = 25.0;
                }
                _isUpdatingUi = false;
            }

            LoadOptionsToUi();
            UpdateLaserVisibility(isLaser);
        }

        private void LoadOptionsToUi()
        {
            if (!_isInitialized || Options == null) return;
            _isUpdatingUi = true;
            try
            {
                if (SliderGrainSize != null) SliderGrainSize.Value = Options.GrainSizeUm;
                if (TxtGrainSize != null) TxtGrainSize.Text = Options.GrainSizeUm.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderHatchPitch != null) SliderHatchPitch.Value = Options.HatchPitchUm;
                if (TxtHatchPitch != null) TxtHatchPitch.Text = Options.HatchPitchUm.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderLaserPower != null) SliderLaserPower.Value = Options.LaserPowerW;
                if (TxtLaserPower != null) TxtLaserPower.Text = Options.LaserPowerW.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderScanSpeed != null) SliderScanSpeed.Value = Options.ScanSpeedMmS;
                if (TxtScanSpeed != null) TxtScanSpeed.Text = Options.ScanSpeedMmS.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderLayerThickness != null) SliderLayerThickness.Value = Options.LayerThicknessUm;
                if (TxtLayerThickness != null) TxtLayerThickness.Text = Options.LayerThicknessUm.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderSpotDiameter != null) SliderSpotDiameter.Value = Options.BeamSpotDiameterUm;
                if (TxtSpotDiameter != null) TxtSpotDiameter.Text = Options.BeamSpotDiameterUm.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderColdWork != null) SliderColdWork.Value = Options.ColdWorkPercent;
                if (TxtColdWork != null) TxtColdWork.Text = Options.ColdWorkPercent.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderHeatTreatTemp != null) SliderHeatTreatTemp.Value = Options.HeatTreatmentTempK;
                if (TxtHeatTreatTemp != null) TxtHeatTreatTemp.Text = Options.HeatTreatmentTempK.ToString("F1", CultureInfo.InvariantCulture);

                if (SliderHeatTreatHours != null) SliderHeatTreatHours.Value = Options.HeatTreatmentHours;
                if (TxtHeatTreatHours != null) TxtHeatTreatHours.Text = Options.HeatTreatmentHours.ToString("F1", CultureInfo.InvariantCulture);

                UpdateDerivedIndicators();
            }
            finally
            {
                _isUpdatingUi = false;
            }
        }

        private void Parameter_Changed(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (!_isInitialized || _isUpdatingUi || Options == null) return;

            if (sender == SliderGrainSize)
            {
                Options.GrainSizeUm = SliderGrainSize.Value;
                if (TxtGrainSize != null)
                    TxtGrainSize.Text = SliderGrainSize.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderHatchPitch)
            {
                Options.HatchPitchUm = SliderHatchPitch.Value;
                if (TxtHatchPitch != null)
                    TxtHatchPitch.Text = SliderHatchPitch.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderLaserPower)
            {
                Options.LaserPowerW = SliderLaserPower.Value;
                if (TxtLaserPower != null)
                    TxtLaserPower.Text = SliderLaserPower.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderScanSpeed)
            {
                Options.ScanSpeedMmS = SliderScanSpeed.Value;
                if (TxtScanSpeed != null)
                    TxtScanSpeed.Text = SliderScanSpeed.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderLayerThickness)
            {
                Options.LayerThicknessUm = SliderLayerThickness.Value;
                if (TxtLayerThickness != null)
                    TxtLayerThickness.Text = SliderLayerThickness.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderSpotDiameter)
            {
                Options.BeamSpotDiameterUm = SliderSpotDiameter.Value;
                if (TxtSpotDiameter != null)
                    TxtSpotDiameter.Text = SliderSpotDiameter.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderColdWork)
            {
                Options.ColdWorkPercent = SliderColdWork.Value;
                if (TxtColdWork != null)
                    TxtColdWork.Text = SliderColdWork.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderHeatTreatTemp)
            {
                Options.HeatTreatmentTempK = SliderHeatTreatTemp.Value;
                if (TxtHeatTreatTemp != null)
                    TxtHeatTreatTemp.Text = SliderHeatTreatTemp.Value.ToString("F1", CultureInfo.InvariantCulture);
            }
            else if (sender == SliderHeatTreatHours)
            {
                Options.HeatTreatmentHours = SliderHeatTreatHours.Value;
                if (TxtHeatTreatHours != null)
                    TxtHeatTreatHours.Text = SliderHeatTreatHours.Value.ToString("F1", CultureInfo.InvariantCulture);
            }

            UpdateDerivedIndicators();
        }

        private void TextBox_LostFocus(object sender, RoutedEventArgs e)
        {
            if (!_isInitialized || _isUpdatingUi || Options == null) return;

            if (sender == TxtGrainSize && double.TryParse(TxtGrainSize.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double dVal))
            {
                if (SliderGrainSize != null)
                {
                    Options.GrainSizeUm = Math.Clamp(dVal, SliderGrainSize.Minimum, SliderGrainSize.Maximum);
                    SliderGrainSize.Value = Options.GrainSizeUm;
                }
            }
            else if (sender == TxtHatchPitch && double.TryParse(TxtHatchPitch.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double hVal))
            {
                if (SliderHatchPitch != null)
                {
                    Options.HatchPitchUm = Math.Clamp(hVal, SliderHatchPitch.Minimum, SliderHatchPitch.Maximum);
                    SliderHatchPitch.Value = Options.HatchPitchUm;
                }
            }
            else if (sender == TxtLaserPower && double.TryParse(TxtLaserPower.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double pVal))
            {
                if (SliderLaserPower != null)
                {
                    Options.LaserPowerW = Math.Clamp(pVal, SliderLaserPower.Minimum, SliderLaserPower.Maximum);
                    SliderLaserPower.Value = Options.LaserPowerW;
                }
            }
            else if (sender == TxtScanSpeed && double.TryParse(TxtScanSpeed.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double vVal))
            {
                if (SliderScanSpeed != null)
                {
                    Options.ScanSpeedMmS = Math.Clamp(vVal, SliderScanSpeed.Minimum, SliderScanSpeed.Maximum);
                    SliderScanSpeed.Value = Options.ScanSpeedMmS;
                }
            }
            else if (sender == TxtLayerThickness && double.TryParse(TxtLayerThickness.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double tVal))
            {
                if (SliderLayerThickness != null)
                {
                    Options.LayerThicknessUm = Math.Clamp(tVal, SliderLayerThickness.Minimum, SliderLayerThickness.Maximum);
                    SliderLayerThickness.Value = Options.LayerThicknessUm;
                }
            }
            else if (sender == TxtSpotDiameter && double.TryParse(TxtSpotDiameter.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double sVal))
            {
                if (SliderSpotDiameter != null)
                {
                    Options.BeamSpotDiameterUm = Math.Clamp(sVal, SliderSpotDiameter.Minimum, SliderSpotDiameter.Maximum);
                    SliderSpotDiameter.Value = Options.BeamSpotDiameterUm;
                }
            }
            else if (sender == TxtColdWork && double.TryParse(TxtColdWork.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double cwVal))
            {
                if (SliderColdWork != null)
                {
                    Options.ColdWorkPercent = Math.Clamp(cwVal, SliderColdWork.Minimum, SliderColdWork.Maximum);
                    SliderColdWork.Value = Options.ColdWorkPercent;
                }
            }
            else if (sender == TxtHeatTreatTemp && double.TryParse(TxtHeatTreatTemp.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double htVal))
            {
                if (SliderHeatTreatTemp != null)
                {
                    Options.HeatTreatmentTempK = Math.Clamp(htVal, SliderHeatTreatTemp.Minimum, SliderHeatTreatTemp.Maximum);
                    SliderHeatTreatTemp.Value = Options.HeatTreatmentTempK;
                }
            }
            else if (sender == TxtHeatTreatHours && double.TryParse(TxtHeatTreatHours.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double hrVal))
            {
                if (SliderHeatTreatHours != null)
                {
                    Options.HeatTreatmentHours = Math.Clamp(hrVal, SliderHeatTreatHours.Minimum, SliderHeatTreatHours.Maximum);
                    SliderHeatTreatHours.Value = Options.HeatTreatmentHours;
                }
            }

            UpdateDerivedIndicators();
        }

        private void UpdateDerivedIndicators()
        {
            if (!_isInitialized || Options == null || LblHpPreview == null || LblVedMetric == null ||
                LblCoolingRateMetric == null || LblCellSpacingMetric == null || LblCellStrengthMetric == null ||
                BadgePorosityRegime == null || TxtPorosityBadge == null) return;

            // 1. Hall-Petch increment
            double hpVal = Options.HallPetchStrengtheningMpa;
            LblHpPreview.Text = $"Hall-Petch Δσ_gb: +{hpVal:F1} MPa";

            // 2. Volumetric Energy Density
            double ved = Options.VolumetricEnergyDensity;
            LblVedMetric.Text = $"{ved:F1} J/mm³";

            // 3. Cooling Rate
            double cr = Options.EstimatedCoolingRateKS;
            LblCoolingRateMetric.Text = cr >= 1e6 ? $"{cr / 1e6:F2} × 10⁶ K/s" : $"{cr / 1e5:F2} × 10⁵ K/s";

            // 4. Cellular Spacing
            double cellSpacing = Options.EstimatedCellularSpacingUm;
            LblCellSpacingMetric.Text = $"{cellSpacing:F2} µm";

            // 5. Cellular Strengthening
            double cellStrength = Options.CellularStrengtheningMpa;
            LblCellStrengthMetric.Text = $"+{cellStrength:F0} MPa";

            // 6. Porosity Regime Badge
            if (ved < 50.0)
            {
                BadgePorosityRegime.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FEE2E2"));
                TxtPorosityBadge.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#991B1B"));
                TxtPorosityBadge.Text = "Lack-of-Fusion Risk (Hatch Spacing too wide / Low VED)";
            }
            else if (ved <= 160.0)
            {
                BadgePorosityRegime.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#D1FAE5"));
                TxtPorosityBadge.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#065F46"));
                TxtPorosityBadge.Text = "Optimal Conduction Window (>99.8% Relative Density)";
            }
            else
            {
                BadgePorosityRegime.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FEF3C7"));
                TxtPorosityBadge.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#92400E"));
                TxtPorosityBadge.Text = "Keyhole Porosity Risk (High VED / Vaporization)";
            }
        }

        private void CmbPreset_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (!_isInitialized || _isUpdatingUi || Options == null || CmbPreset == null) return;
            bool isLaser = true;
            switch (CmbPreset.SelectedIndex)
            {
                case 0: // L-PBF Standard
                    Options.GrainSizeUm = 15.0;
                    Options.HatchPitchUm = 80.0;
                    Options.LaserPowerW = 275.0;
                    Options.ScanSpeedMmS = 800.0;
                    Options.LayerThicknessUm = 30.0;
                    Options.BeamSpotDiameterUm = 75.0;
                    Options.ColdWorkPercent = 0.0;
                    isLaser = true;
                    break;
                case 1: // L-PBF High Productivity
                    Options.GrainSizeUm = 22.0;
                    Options.HatchPitchUm = 120.0;
                    Options.LaserPowerW = 400.0;
                    Options.ScanSpeedMmS = 1000.0;
                    Options.LayerThicknessUm = 50.0;
                    Options.BeamSpotDiameterUm = 90.0;
                    Options.ColdWorkPercent = 0.0;
                    isLaser = true;
                    break;
                case 2: // DED
                    Options.GrainSizeUm = 45.0;
                    Options.HatchPitchUm = 180.0;
                    Options.LaserPowerW = 900.0;
                    Options.ScanSpeedMmS = 500.0;
                    Options.LayerThicknessUm = 80.0;
                    Options.BeamSpotDiameterUm = 120.0;
                    Options.ColdWorkPercent = 0.0;
                    isLaser = true;
                    break;
                case 3: // Cast / Ingot (Non-laser)
                    Options.GrainSizeUm = 85.0;
                    Options.ColdWorkPercent = 0.0;
                    isLaser = false;
                    break;
                case 4: // Wrought / Annealed (Non-laser)
                    Options.GrainSizeUm = 25.0;
                    Options.ColdWorkPercent = 0.0;
                    isLaser = false;
                    break;
                case 5: // UFG (Non-laser)
                    Options.GrainSizeUm = 1.5;
                    Options.ColdWorkPercent = 60.0;
                    isLaser = false;
                    break;
                case 6: // Custom
                    isLaser = GroupLaserParams?.Visibility == Visibility.Visible;
                    break;
                default:
                    return;
            }
            UpdateLaserVisibility(isLaser);
            LoadOptionsToUi();
        }

        private void BtnReset_Click(object sender, RoutedEventArgs e)
        {
            Options = new ExperimentalProcessOptions();
            if (CmbPreset != null)
            {
                _isUpdatingUi = true;
                CmbPreset.SelectedIndex = 0;
                _isUpdatingUi = false;
            }
            UpdateLaserVisibility(true);
            LoadOptionsToUi();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private void BtnApply_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = true;
            Close();
        }
    }
}
