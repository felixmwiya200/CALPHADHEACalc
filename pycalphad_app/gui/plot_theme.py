# -*- coding: utf-8 -*-
"""
plot_theme.py - Scientific Academic Publication Plot Theme for PyQtGraph
Enforces OriginLab / Nature / Science journal standards:
- Crisp pure white background (#FFFFFF)
- Dark charcoal axes (#1E293B) with high legibility
- Subtle, unobtrusive secondary gridlines (#E2E8F0)
- High-contrast color palettes for calculated curves vs experimental data points
- Clean academic legend with subtle border
"""

from typing import Optional, Tuple, List
import pyqtgraph as pg
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt


# ---------------------------------------------------------------------------
# High-Contrast Academic Color Palette (ColorBrewer & Tol Qualitative)
# ---------------------------------------------------------------------------
CALCULATED_COLORS = [
    "#1D4ED8",  # Royal Blue
    "#D97706",  # Amber Orange
    "#16A34A",  # Forest Green
    "#7C3AED",  # Purple
    "#0891B2",  # Teal Cyan
    "#C026D3",  # Fuchsia
    "#475569",  # Slate Gray
    "#B45309",  # Brown
]

EXPERIMENTAL_COLOR = "#DC2626"       # Crimson Red for experimental literature points
EXPERIMENTAL_EDGE_COLOR = "#7F1D1D"  # Dark Crimson for marker edge
EXPERIMENTAL_FILL_SECONDARY = "#0284C7"  # Deep Sky Blue for secondary experimental set

SCIENTIFIC_LIGHT_THEME = {
    "canvas_background": "#FFFFFF",
    "axis_spine": "#334155",
    "text_pen": "#1E293B",
    "grid_line": "#E2E8F0",
    "grid_alpha": 0.35,
    "calculated_colors": CALCULATED_COLORS,
    "experimental_color": EXPERIMENTAL_COLOR
}


def apply_scientific_light_theme(
    plot_widget: pg.PlotWidget,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    x_units: Optional[str] = None,
    y_units: Optional[str] = None
) -> None:
    """
    Applies an OriginLab-grade scientific light theme to any pyqtgraph PlotWidget.
    """
    plot_widget.setBackground("#FFFFFF")
    plot_widget.showGrid(x=True, y=True, alpha=0.35)

    # Style axes
    axis_pen = pg.mkPen(color="#334155", width=1.3)
    text_font = QFont("Segoe UI", 9)
    label_style = {
        "color": "#0F172A",
        "font-size": "9.5pt",
        "font-family": "Segoe UI",
        "font-weight": "bold"
    }

    for axis_name in ("left", "bottom", "right", "top"):
        ax = plot_widget.getAxis(axis_name)
        if ax is not None:
            ax.setPen(axis_pen)
            ax.setTextPen(pg.mkPen(color="#1E293B"))
            ax.setTickFont(text_font)

    if title:
        plot_widget.setTitle(title, color="#0F172A", size="11pt", bold=True)
    if x_label:
        plot_widget.setLabel("bottom", x_label, units=x_units or "", **label_style)
    if y_label:
        plot_widget.setLabel("left", y_label, units=y_units or "", **label_style)

    # Configure plot item view box
    plot_item = plot_widget.getPlotItem()
    plot_item.getViewBox().setBorder(pg.mkPen(color="#94A3B8", width=1.0))

    # Configure legend if present
    if plot_item.legend is not None:
        style_scientific_legend(plot_item.legend)


def style_scientific_legend(legend: pg.LegendItem) -> None:
    """Styles a PyQtGraph legend to match academic journal specifications."""
    legend.setBrush(pg.mkBrush(255, 255, 255, 230))
    legend.setPen(pg.mkPen(color="#CBD5E1", width=1.0))
    legend.setLabelTextColor("#0F172A")


def get_calculated_pen(index: int = 0, width: float = 2.2, style=Qt.PenStyle.SolidLine) -> pg.mkPen:
    """Returns a high-visibility pen for theoretical or calculated curves."""
    color = CALCULATED_COLORS[index % len(CALCULATED_COLORS)]
    return pg.mkPen(color=color, width=width, style=style)


def plot_experimental_scatter(
    plot_widget: pg.PlotWidget,
    x_data,
    y_data,
    name: str = "Exp. Benchmark",
    symbol: str = "s",
    size: int = 8,
    color: str = EXPERIMENTAL_COLOR
) -> pg.PlotDataItem:
    """
    Plots peer-reviewed experimental benchmark data points alongside calculated curves.
    """
    symbol_map = {
        "diamond": "d",
        "square": "s",
        "circle": "o",
        "triangle": "t",
        "star": "star",
        "cross": "x",
        "plus": "+"
    }
    clean_symbol = symbol_map.get(str(symbol).lower(), symbol)
    edge_pen = pg.mkPen(color="#1E293B", width=1.0)
    brush = pg.mkBrush(color)
    return plot_widget.plot(
        x_data,
        y_data,
        pen=None,
        symbol=clean_symbol,
        symbolSize=size,
        symbolBrush=brush,
        symbolPen=edge_pen,
        name=name
    )
