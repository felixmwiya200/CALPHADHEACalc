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
}
