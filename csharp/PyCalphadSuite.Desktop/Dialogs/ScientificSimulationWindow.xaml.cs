// <copyright file="ScientificSimulationWindow.xaml.cs" company="PyCALPHAD Materials CAE">
// Interactive C# WPF physical metallurgy analyzer dialog supporting all simulation and utility modules.
// </copyright>

using System;
using System.Collections.Generic;
using System.Data;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using PyCalphadSuite.Core.Models;
using PyCalphadSuite.Core.Services;
using ScottPlot;

namespace PyCalphadSuite.Desktop.Dialogs
{
    public partial class ScientificSimulationWindow : Window
    {
        private readonly CaeDaemonProcessClient? _client;
        private readonly string _module;
        private readonly string _dbName;
        private readonly Dictionary<string, double> _composition;

        public string? LoadedAlloyFormula { get; private set; }

        public ScientificSimulationWindow(
            CaeDaemonProcessClient? client,
            string module,
            string title,
            string dbName,
            Dictionary<string, double> composition,
            Window owner)
        {
            InitializeComponent();
            Owner = owner;
            _client = client;
            _module = module;
            _dbName = dbName;
            _composition = new Dictionary<string, double>(composition);

            TxtDialogTitle.Text = title;
            TxtDialogSubtitle.Text = $"Active Materials System: {dbName}";

            ConfigureUiForModule();
            Loaded += async (_, _) => await RunModuleAsync();
        }

        private void ConfigureUiForModule()
        {
            if (_module == "conversions")
            {
                ParamPanelBorder.Visibility = Visibility.Collapsed;
                SimPlotHost.Visibility = Visibility.Collapsed;
                ConverterPanel.Visibility = Visibility.Visible;
                BtnRunModule.Visibility = Visibility.Collapsed;
                UpdateConverterOutputs();
                return;
            }

            if (_module is "oxide_db" or "imc_laves_db" or "literature_heas")
            {
                ParamPanelBorder.Visibility = Visibility.Collapsed;
                SimPlotHost.Visibility = Visibility.Collapsed;
                SimDataGrid.Visibility = Visibility.Visible;
                if (_module == "literature_heas")
                {
                    BtnLoadSelectedAlloy.Visibility = Visibility.Visible;
                }
                return;
            }

            switch (_module)
            {
                case "ttt_cct":
                    LblParam1.Text = "Nose Temp (°C):";
                    TxtParam1.Text = "620";
                    LblParam2.Text = "Grain Size (μm):";
                    TxtParam2.Text = "25";
                    break;
                case "creep":
                    LblParam1.Text = "Test Temp (K):";
                    TxtParam1.Text = "973.15";
                    LblParam2.Text = "Larson-Miller C:";
                    TxtParam2.Text = "20";
                    break;
                case "fatigue":
                    LblParam1.Text = "Est. UTS (MPa):";
                    TxtParam1.Text = "780";
                    LblParam2.Text = "Stress Ratio R:";
                    TxtParam2.Text = "-1";
                    break;
                case "concentration_step":
                    LblParam1.Text = "Sweep Element:";
                    TxtParam1.Text = _composition.Keys.FirstOrDefault() ?? "Al";
                    LblParam2.Text = "Step Increment (%):";
                    TxtParam2.Text = "1.0";
                    break;
                case "single_step":
                    LblParam1.Text = "Target Temp (K):";
                    TxtParam1.Text = "1273.15";
                    LblParam2.Text = "Grain Size (μm):";
                    TxtParam2.Text = "25";
                    break;
                default:
                    LblParam1.Text = "Ref Temp (K):";
                    TxtParam1.Text = "298.15";
                    LblParam2.Text = "Grain Size (μm):";
                    TxtParam2.Text = "25";
                    break;
            }
        }

        private async void BtnRunModule_Click(object sender, RoutedEventArgs e)
        {
            await RunModuleAsync();
        }

        private async Task RunModuleAsync()
        {
            if (_module == "conversions") return;
            if (_client == null)
            {
                TxtSimResultSummary.Text = "Python IPC daemon offline.";
                return;
            }

            try
            {
                BtnRunModule.IsEnabled = false;
                TxtSimResultSummary.Text = "Evaluating physical metallurgy equations...";

                if (_module == "single_step")
                {
                    double.TryParse(TxtParam1.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var tK);
                    tK = tK > 0 ? tK : 1273.15;
                    var step = await _client.CalculateSingleStepAsync(_dbName, _composition, tK);
                    SimPlotHost.ApplyOtisLiuStyle($"Single-Point Equilibrium at T = {tK:F1} K", "Constituent Phase Index", "Phase Mole Fraction");
                    var names = step.Phases.Keys.ToList();
                    var vals = step.Phases.Values.ToList();
                    if (vals.Count > 0)
                    {
                        var xs = Enumerable.Range(1, vals.Count).Select(i => (double)i).ToArray();
                        var bars = SimPlotHost.Plot.Add.Bars(xs, vals.ToArray());
                        bars.Color = ScottPlot.Color.FromHex("#2563EB");
                        SimPlotHost.AddExportSeries("PhaseFraction", xs, vals.ToArray());
                        SimPlotHost.SetLimitsAndRemember(0, vals.Count + 1, 0, 1.05);
                    }
                    SimPlotHost.HeaderTitle = $"Single Point Equilibrium (T = {tK:F1} K)";
                    SimPlotHost.HeaderSummary = $"Dominant: {step.DominantPhase} | G = {step.GibbsEnergyJMol:F0} J/mol | σy = {step.YieldStrengthMpa:F0} MPa";
                    SimPlotHost.Refresh();
                    TxtSimResultSummary.Text = SimPlotHost.HeaderSummary;
                    return;
                }

                var modParams = new Dictionary<string, object>();
                if (_module == "ttt_cct" && double.TryParse(TxtParam1.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var nose))
                    modParams["nose_temp_c"] = nose;
                if (_module == "creep" && double.TryParse(TxtParam1.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var tk))
                    modParams["temp_k"] = tk;
                if (_module == "fatigue" && double.TryParse(TxtParam1.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var uts))
                    modParams["uts_mpa"] = uts;
                if (_module == "concentration_step")
                    modParams["element"] = TxtParam1.Text.Trim();

                var res = await _client.RunSimulationModuleAsync(_module, _dbName, _composition, modParams);

                if (res.Oxides != null)
                {
                    PopulateDataTableFromJson(res.Oxides);
                    return;
                }
                if (res.Imcs != null)
                {
                    PopulateDataTableFromJson(res.Imcs);
                    return;
                }
                if (res.Alloys != null)
                {
                    PopulateDataTableFromJson(res.Alloys);
                    return;
                }

                SimPlotHost.ApplyOtisLiuStyle(res.Title, res.XLabel, res.YLabel);
                SimPlotHost.HeaderTitle = res.Title;
                SimPlotHost.HeaderSummary = res.Summary;
                TxtSimResultSummary.Text = res.Summary;

                double minX = double.MaxValue, maxX = double.MinValue;
                double minY = double.MaxValue, maxY = double.MinValue;

                foreach (var curve in res.Curves)
                {
                    if (curve.X.Count == 0 || curve.Y.Count == 0) continue;
                    var xs = curve.X.ToArray();
                    var ys = curve.Y.ToArray();

                    var sc = SimPlotHost.Plot.Add.ScatterLine(xs, ys, ScottPlot.Color.FromHex(curve.Color));
                    sc.LineWidth = 2.4f;
                    sc.LegendText = curve.Name;

                    SimPlotHost.AddExportSeries(curve.Name, xs, ys);
                    minX = Math.Min(minX, xs.Min());
                    maxX = Math.Max(maxX, xs.Max());
                    minY = Math.Min(minY, ys.Min());
                    maxY = Math.Max(maxY, ys.Max());
                }

                if (minX < maxX && minY < maxY)
                {
                    double padX = (maxX - minX) * 0.05;
                    double padY = (maxY - minY) * 0.08;
                    SimPlotHost.SetLimitsAndRemember(minX - padX, maxX + padX, minY - padY, maxY + padY);
                }
                SimPlotHost.Refresh();
            }
            catch (Exception ex)
            {
                TxtSimResultSummary.Text = $"Error: {ex.Message}";
            }
            finally
            {
                BtnRunModule.IsEnabled = true;
            }
        }

        private void PopulateDataTableFromJson(List<Dictionary<string, System.Text.Json.JsonElement>> rows)
        {
            var dt = new DataTable();
            if (rows.Count > 0)
            {
                foreach (var key in rows[0].Keys)
                {
                    dt.Columns.Add(key);
                }
                foreach (var r in rows)
                {
                    var dr = dt.NewRow();
                    foreach (var key in rows[0].Keys)
                    {
                        dr[key] = r.TryGetValue(key, out var val) ? val.ToString() : "";
                    }
                    dt.Rows.Add(dr);
                }
            }
            SimDataGrid.ItemsSource = dt.DefaultView;
            TxtSimResultSummary.Text = $"Loaded {rows.Count} peer-reviewed records.";
        }

        private void BtnLoadSelectedAlloy_Click(object sender, RoutedEventArgs e)
        {
            if (SimDataGrid.SelectedItem is DataRowView drv)
            {
                if (drv.Row.Table.Columns.Contains("Formula"))
                {
                    LoadedAlloyFormula = drv["Formula"]?.ToString();
                    DialogResult = true;
                    Close();
                }
            }
            else
            {
                MessageBox.Show("Select an alloy row from the repository first.", "Select Row", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void TxtConv_TextChanged(object sender, TextChangedEventArgs e)
        {
            UpdateConverterOutputs();
        }

        private void UpdateConverterOutputs()
        {
            if (LblConvTempOut == null || LblConvStressOut == null || LblConvEnergyOut == null) return;
            if (double.TryParse(TxtConvTempC.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var tc))
            {
                LblConvTempOut.Text = $"= {tc + 273.15:F2} K  |  {tc * 9.0 / 5.0 + 32.0:F1} °F";
            }
            if (double.TryParse(TxtConvStress.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var mpa))
            {
                LblConvStressOut.Text = $"= {mpa / 1000.0:F3} GPa  |  {mpa * 0.145038:F2} ksi";
            }
            if (double.TryParse(TxtConvEnergy.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out var kj))
            {
                LblConvEnergyOut.Text = $"= {kj / 96.485:F4} eV/atom";
            }
        }
    }
}
