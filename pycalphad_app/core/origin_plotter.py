# -*- coding: utf-8 -*-
"""
origin_plotter.py - OriginLab Publication-Grade Scientific Plotting Utility
Ported from MATLAB OriginPlotter.m
Formats pyqtgraph PlotItem widgets to commercial scientific CAE standards:
  - 4-sided closed rectangular frame
  - Inward tick directions
  - Bold, crisp black/slate borders (1.25 pt)
  - Mirrored top and right ticks
  - High-contrast publication palette
"""

import pyqtgraph as pg
from PyQt6.QtGui import QPen, QColor, QFont


class OriginPlotter:
    """
    Standard OriginLab-style graphics decorator for pyqtgraph PlotItem widgets.
    """
    @staticmethod
    def format_plot(plot_item: pg.PlotItem, title: str = "", x_label: str = "", y_label: str = "",
                    theme: str = "light"):
        """
        Applies OriginLab 4-sided boxed frame styling to a pyqtgraph PlotItem.
        """
        if theme == "dark":
            frame_color = QColor("#555555")
            text_color = QColor("#D4D4D4")
            grid_color = (60, 60, 60, 150)
            bg_color = "#1E1E1E"
        else:
            frame_color = QColor("#333333")
            text_color = QColor("#0F172A")
            grid_color = (220, 220, 220, 200)
            bg_color = "#FFFFFF"

        plot_item.getViewBox().setBackgroundColor(bg_color)

        pen = QPen(frame_color, 1.25)
        font = QFont("Segoe UI", 9)

        # Bottom axis
        ax_bottom = plot_item.getAxis('bottom')
        ax_bottom.setPen(pen)
        ax_bottom.setTextPen(text_color)
        ax_bottom.setTickFont(font)
        if x_label:
            ax_bottom.setLabel(text=x_label)

        # Left axis
        ax_left = plot_item.getAxis('left')
        ax_left.setPen(pen)
        ax_left.setTextPen(text_color)
        ax_left.setTickFont(font)
        if y_label:
            ax_left.setLabel(text=y_label)

        # Show right and top axes to create a closed 4-sided box
        plot_item.showAxis('top')
        plot_item.showAxis('right')

        ax_top = plot_item.getAxis('top')
        ax_top.setPen(pen)
        ax_top.setStyle(showValues=False)

        ax_right = plot_item.getAxis('right')
        ax_right.setPen(pen)
        ax_right.setStyle(showValues=False)

        # Grids
        plot_item.showGrid(x=True, y=True, alpha=0.35)

        if title:
            plot_item.setTitle(title, color=text_color.name(), size="10pt", bold=True)
