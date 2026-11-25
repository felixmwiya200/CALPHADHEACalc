using System.IO;
using System.Linq;
using ScottPlot;
using Xunit;

namespace PyCalphadSuite.Tests;

public class ScottPlotLegendTests
{
    [Fact]
    public void TestLegendOutsideOnRightEdge_18Items()
    {
        var plot = new Plot();
        for (int i = 0; i < 18; i++)
        {
            var sig = plot.Add.Signal(Generate.Sin());
            sig.LegendText = $"Phase Line {i + 1} System Curve Tie-Line";
        }

        var panel = plot.ShowLegend(Edge.Right);
        plot.Legend.FontSize = 9.0f;
        Assert.NotNull(panel);

        string testPngPath = Path.Combine(Directory.GetCurrentDirectory(), "test_legend_18_items.png");
        plot.SavePng(testPngPath, 1000, 550);
        Assert.True(File.Exists(testPngPath));
    }

    [Fact]
    public void TestHorizontalBarsRender()
    {
        var plot = new Plot();
        double[] scores = new double[] { 85, 53, 47, 47, 47, 46, 38, 38, 37, 15, 15, 15 };
        int count = scores.Length;
        double[] yPositions = Enumerable.Range(0, count).Select(i => (double)(count - i)).ToArray();
        string[] labels = new string[] {
            "Cryogenic Storage & Valves",
            "Marine Propulsion & Naval Architecture",
            "Solid-State Metal Hydrides",
            "Electrochemical & Fuel Cells",
            "High-Pressure Turbomachinery",
            "Gas Turbine Blades & Discs",
            "Thermal Spray Coatings",
            "Hydro-Turbine Cavitation Runners",
            "Hot Work Tooling & Dies",
            "Generation-IV Nuclear Reactors",
            "Biomedical Orthopaedic Implants",
            "Ultra-High Temperature Aerospace"
        };

        var bars = plot.Add.Bars(yPositions, scores);
        bars.Horizontal = true;
        bars.Color = ScottPlot.Color.FromHex("#1D4ED8");

        plot.Axes.Left.TickGenerator = new ScottPlot.TickGenerators.NumericManual(yPositions, labels);
        plot.Axes.Left.TickLabelStyle.FontSize = 10.0f;
        plot.Axes.Left.TickLabelStyle.Bold = true;
        plot.Axes.Left.MinimumSize = 220f;

        plot.Axes.Bottom.Label.Text = "Suitability Score (%)";
        plot.Axes.Left.Label.Text = "Industrial Application Sector";

        for (int i = 0; i < count; i++)
        {
            var txt = plot.Add.Text($"{scores[i]:F0}%", scores[i] + 1.2, yPositions[i]);
            txt.LabelFontSize = 9.5f;
            txt.LabelBold = true;
            txt.LabelAlignment = Alignment.MiddleLeft;
        }

        var line75 = plot.Add.VerticalLine(75.0);
        line75.LineColor = ScottPlot.Color.FromHex("#64748B");
        line75.LinePattern = LinePattern.Dashed;
        line75.LineWidth = 1.0f;

        plot.Axes.SetLimits(0.0, 112.0, 0.4, count + 0.6);

        string testPngPath = Path.Combine(Directory.GetCurrentDirectory(), "test_horizontal_bar.png");
        plot.SavePng(testPngPath, 900, 500);
        Assert.True(File.Exists(testPngPath));
    }
}
