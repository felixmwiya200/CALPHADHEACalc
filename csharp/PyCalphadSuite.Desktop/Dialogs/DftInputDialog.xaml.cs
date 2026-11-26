// <copyright file="DftInputDialog.xaml.cs" company="PyCALPHAD Materials CAE">
// Academic and commercial metallurgical CAE data contracts conforming to CALPHAD standards.
// </copyright>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Desktop.Dialogs
{
    /// <summary>
    /// Interaction logic for DftInputDialog.xaml.
    /// Provides dedicated configuration of first-principles DFT ground-state formation enthalpies,
    /// d-electron orbital parameters, and defect energies as primary inputs for CALPHAD calculations.
    /// </summary>
    public partial class DftInputDialog : Window
    {
        private readonly Dictionary<string, double>? _composition;

        public DftInputDto DftInput { get; private set; }

        public DftInputDialog(DftInputDto currentInput, Dictionary<string, double>? composition = null)
        {
            InitializeComponent();
            _composition = composition;
            DftInput = currentInput != null ? CloneDto(currentInput) : new DftInputDto();

            LoadValuesToUi();
        }

        private static DftInputDto CloneDto(DftInputDto src)
        {
            return new DftInputDto
            {
                Enabled = src.Enabled,
                EnthalpyBccKj = src.EnthalpyBccKj,
                EnthalpyFccKj = src.EnthalpyFccKj,
                EnthalpyHcpKj = src.EnthalpyHcpKj,
                EnthalpySigmaKj = src.EnthalpySigmaKj,
                BoAvg = src.BoAvg,
                MdAvg = src.MdAvg,
                RadiusAvgPm = src.RadiusAvgPm,
                SfeMjM2 = src.SfeMjM2,
                GroundState = src.GroundState,
                Source = src.Source,
                CustomOverride = src.CustomOverride
            };
        }

        private void LoadValuesToUi()
        {
            ChkEnableDft.IsChecked = DftInput.Enabled;
            TxtBccH.Text = DftInput.EnthalpyBccKj.ToString("F2", CultureInfo.InvariantCulture);
            TxtFccH.Text = DftInput.EnthalpyFccKj.ToString("F2", CultureInfo.InvariantCulture);
            TxtHcpH.Text = DftInput.EnthalpyHcpKj.ToString("F2", CultureInfo.InvariantCulture);
            TxtSigmaH.Text = DftInput.EnthalpySigmaKj.ToString("F2", CultureInfo.InvariantCulture);

            TxtBo.Text = DftInput.BoAvg.ToString("F3", CultureInfo.InvariantCulture);
            TxtMd.Text = DftInput.MdAvg.ToString("F3", CultureInfo.InvariantCulture);
            TxtRadius.Text = DftInput.RadiusAvgPm.ToString("F1", CultureInfo.InvariantCulture);
            TxtSfe.Text = DftInput.SfeMjM2.ToString("F1", CultureInfo.InvariantCulture);

            TxtProvenance.Text = string.IsNullOrEmpty(DftInput.Source)
                ? "First-Principles DFT (0 K VASP / Materials Project) & Morinaga Model"
                : DftInput.Source;
            ChkCustomOverride.IsChecked = DftInput.CustomOverride;

            string gs = DftInput.GroundState;
            if (string.IsNullOrEmpty(gs)) gs = "FCC_A1";
            for (int i = 0; i < CmbGroundState.Items.Count; i++)
            {
                if (CmbGroundState.Items[i] is ComboBoxItem item &&
                    item.Content?.ToString()?.Contains(gs) == true)
                {
                    CmbGroundState.SelectedIndex = i;
                    break;
                }
            }
            if (CmbGroundState.SelectedIndex < 0) CmbGroundState.SelectedIndex = 1;
        }

        private void BtnAutoCalculate_Click(object sender, RoutedEventArgs e)
        {
            if (_composition == null || _composition.Count == 0)
            {
                MessageBox.Show("Active alloy composition is empty. Please define elements first.", "DFT Auto-Calculation", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            // Standard elemental Morinaga d-electron and DFT reference table
            var refTable = new Dictionary<string, (double Md, double Bo, double Radius, double H_Bcc, double H_Fcc, double H_Hcp)>(StringComparer.OrdinalIgnoreCase)
            {
                ["Fe"] = (0.858, 0.857, 126.0, -8.31, -8.28, -8.18),
                ["Cr"] = (1.142, 1.278, 128.0, -9.51, -9.05, -9.10),
                ["Mn"] = (0.957, 1.001, 127.0, -8.90, -8.96, -8.88),
                ["Ni"] = (0.717, 0.531, 124.0, -4.38, -4.45, -4.41),
                ["Co"] = (0.777, 0.697, 125.0, -7.03, -7.09, -7.11),
                ["Mo"] = (1.550, 1.626, 139.0, -10.94, -10.52, -10.60),
                ["W"]  = (1.655, 1.670, 139.0, -12.98, -12.42, -12.50),
                ["V"]  = (1.340, 1.350, 134.0, -9.00,  -8.70,  -8.75),
                ["Nb"] = (2.110, 1.700, 146.0, -10.22, -9.85,  -9.92),
                ["Ta"] = (2.220, 1.730, 146.0, -11.85, -11.45, -11.52),
                ["Ti"] = (2.271, 1.098, 147.0, -7.69,  -7.63,  -7.75),
                ["Al"] = (1.900, 0.520, 143.0, -3.25,  -3.36,  -3.34),
                ["Cu"] = (0.615, 0.350, 128.0, -3.42,  -3.49,  -3.47)
            };

            double total = _composition.Values.Sum();
            if (total <= 0) total = 1.0;

            double boAvg = 0.0, mdAvg = 0.0, radAvg = 0.0;
            double hBcc = 0.0, hFcc = 0.0, hHcp = 0.0;

            foreach (var kvp in _composition)
            {
                double frac = kvp.Value / total;
                if (refTable.TryGetValue(kvp.Key, out var p))
                {
                    boAvg += frac * p.Bo;
                    mdAvg += frac * p.Md;
                    radAvg += frac * p.Radius;
                    hBcc += frac * p.H_Bcc;
                    hFcc += frac * p.H_Fcc;
                    hHcp += frac * p.H_Hcp;
                }
                else
                {
                    boAvg += frac * 1.0;
                    mdAvg += frac * 1.0;
                    radAvg += frac * 130.0;
                    hBcc += frac * -7.0;
                    hFcc += frac * -7.0;
                    hHcp += frac * -7.0;
                }
            }

            double sfe = Math.Max(12.0, Math.Min(95.0, 22.0 + 35.0 * (mdAvg - 0.70)));
            double hSigma = 7.20 + 15.0 * Math.Max(0.0, mdAvg - 0.90);

            TxtBo.Text = boAvg.ToString("F3", CultureInfo.InvariantCulture);
            TxtMd.Text = mdAvg.ToString("F3", CultureInfo.InvariantCulture);
            TxtRadius.Text = radAvg.ToString("F1", CultureInfo.InvariantCulture);
            TxtBccH.Text = hBcc.ToString("F2", CultureInfo.InvariantCulture);
            TxtFccH.Text = hFcc.ToString("F2", CultureInfo.InvariantCulture);
            TxtHcpH.Text = hHcp.ToString("F2", CultureInfo.InvariantCulture);
            TxtSigmaH.Text = hSigma.ToString("F2", CultureInfo.InvariantCulture);
            TxtSfe.Text = sfe.ToString("F1", CultureInfo.InvariantCulture);

            if (hBcc < hFcc - 0.15) CmbGroundState.SelectedIndex = 0;
            else if (hHcp < hFcc - 0.15 && hHcp < hBcc - 0.15) CmbGroundState.SelectedIndex = 2;
            else CmbGroundState.SelectedIndex = 1;

            TxtProvenance.Text = "Auto-Calculated from DFT Elemental Ground-State Database (0 K)";
            ChkCustomOverride.IsChecked = false;
        }

        private void BtnImportJson_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "DFT Parameters JSON (*.json)|*.json|All Files (*.*)|*.*",
                Title = "Import First-Principles DFT Calculation Inputs"
            };
            if (dlg.ShowDialog() == true)
            {
                try
                {
                    string json = File.ReadAllText(dlg.FileName);
                    using var doc = JsonDocument.Parse(json);
                    var root = doc.RootElement;

                    if (root.TryGetProperty("enthalpy_bcc_kj", out var pBcc)) TxtBccH.Text = pBcc.GetDouble().ToString("F2", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("enthalpy_fcc_kj", out var pFcc)) TxtFccH.Text = pFcc.GetDouble().ToString("F2", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("enthalpy_hcp_kj", out var pHcp)) TxtHcpH.Text = pHcp.GetDouble().ToString("F2", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("enthalpy_sigma_kj", out var pSig)) TxtSigmaH.Text = pSig.GetDouble().ToString("F2", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("bo_avg", out var pBo)) TxtBo.Text = pBo.GetDouble().ToString("F3", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("md_avg", out var pMd)) TxtMd.Text = pMd.GetDouble().ToString("F3", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("sfe_mj_m2", out var pSfe)) TxtSfe.Text = pSfe.GetDouble().ToString("F1", CultureInfo.InvariantCulture);
                    if (root.TryGetProperty("radius_avg_pm", out var pRad)) TxtRadius.Text = pRad.GetDouble().ToString("F1", CultureInfo.InvariantCulture);

                    TxtProvenance.Text = $"Imported from {Path.GetFileName(dlg.FileName)}";
                    ChkCustomOverride.IsChecked = true;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Failed to parse DFT JSON file: {ex.Message}", "Import Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnApply_Click(object sender, RoutedEventArgs e)
        {
            double ParseVal(string text, double def) =>
                double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out double val) ? val : def;

            DftInput.Enabled = ChkEnableDft.IsChecked == true;
            DftInput.EnthalpyBccKj = ParseVal(TxtBccH.Text, -8.50);
            DftInput.EnthalpyFccKj = ParseVal(TxtFccH.Text, -8.28);
            DftInput.EnthalpyHcpKj = ParseVal(TxtHcpH.Text, -8.18);
            DftInput.EnthalpySigmaKj = ParseVal(TxtSigmaH.Text, 7.20);
            DftInput.BoAvg = ParseVal(TxtBo.Text, 0.857);
            DftInput.MdAvg = ParseVal(TxtMd.Text, 0.858);
            DftInput.RadiusAvgPm = ParseVal(TxtRadius.Text, 126.0);
            DftInput.SfeMjM2 = ParseVal(TxtSfe.Text, 28.0);
            DftInput.Source = TxtProvenance.Text.Trim();
            DftInput.CustomOverride = ChkCustomOverride.IsChecked == true;

            string selectedGs = (CmbGroundState.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "FCC_A1";
            if (selectedGs.Contains("BCC")) DftInput.GroundState = "BCC_A2";
            else if (selectedGs.Contains("HCP")) DftInput.GroundState = "HCP_A3";
            else if (selectedGs.Contains("Sigma")) DftInput.GroundState = "Sigma";
            else if (selectedGs.Contains("B2")) DftInput.GroundState = "Ordered_B2";
            else DftInput.GroundState = "FCC_A1";

            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
