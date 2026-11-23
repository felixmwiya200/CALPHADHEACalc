// <copyright file="CalculationMatrixControl.xaml.cs" company="PyCALPHAD Materials CAE">
// 1:1 port of JMatPro / Pandat Calculation Matrix launchpad in C# WPF.
// </copyright>

using System;
using System.Windows;
using System.Windows.Controls;

namespace PyCalphadSuite.Desktop.Controls
{
    public partial class CalculationMatrixControl : UserControl
    {
        public event Action<string>? ActionTriggered;

        public CalculationMatrixControl()
        {
            InitializeComponent();
        }

        public void AdaptToAlloy(string alloyName)
        {
            TxtAlloyTitle.Text = alloyName;
            var lower = (alloyName ?? string.Empty).ToLowerInvariant();

            bool isSuperalloy = lower.Contains("nickel") || lower.Contains("nife") || lower.Contains("cobalt") || lower.Contains("single crystal");
            BtnGammaMismatch.IsEnabled = isSuperalloy;
            BtnGammaMismatch.ToolTip = isSuperalloy
                ? "Coherent γ/γ' lattice mismatch parameter δ = 2(a_γ' - a_γ) / (a_γ' + a_γ)"
                : "γ/γ' mismatch applies specifically to Ni- and Co-based superalloys with L1₂ precipitates.";

            if (lower.Contains("steel") || lower.Contains("iron"))
            {
                BtnHeatTreatment.ToolTip = "Quench & Temper / Austenitization & Jominy End-Quench Simulation";
            }
            else if (lower.Contains("aluminium") || lower.Contains("aluminum"))
            {
                BtnHeatTreatment.ToolTip = "Solution Heat Treatment & T6/T7 Precipitation Aging in Aluminium Alloys";
            }
            else
            {
                BtnHeatTreatment.ToolTip = "Solution Heat Treatment & Multiphase Precipitation Aging";
            }
        }

        private void MatrixBtn_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string tag)
            {
                ActionTriggered?.Invoke(tag);
            }
        }
    }
}
