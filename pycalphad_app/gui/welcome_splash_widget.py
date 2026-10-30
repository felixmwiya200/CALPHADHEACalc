# -*- coding: utf-8 -*-
"""
welcome_splash_widget.py - Authentic JMatPro-Style Scientific Desktop Startup View
Provides the signature JMatPro welcome splash canvas with dynamic thermodynamic
curves, industry vertical ribbon, material selection trigger, and quick-start alloy presets.

Lead Materials Suite Developers: Felix Mwiya and Prof. (Dr.) Sheela Singh, SRM University-AP.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, QFont,
    QPen, QBrush, QPolygonF
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal


class JMatProSplashBanner(QWidget):
    """
    Renders the signature JMatPro splash banner card with:
    - Left: Soft blue gradient canvas with intersecting CALPHAD curves,
      bold 'PyCALPHAD' typography, 'PRACTICAL SOFTWARE FOR MATERIALS PROPERTIES',
      versioning, and academic attribution.
    - Right: Deep navy ribbon with scientific engineering domain iconography.
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(700, 400)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        r_width = 120  # Right ribbon width
        l_width = w - r_width

        # -------------------------------------------------------------------
        # 1. Outer Border & Card Clipping
        # -------------------------------------------------------------------
        card_path = QPainterPath()
        card_path.addRoundedRect(QRectF(0, 0, w, h), 8, 8)
        painter.setClipPath(card_path)

        # -------------------------------------------------------------------
        # 2. Left Background: Soft Gradient Sky Blue
        # -------------------------------------------------------------------
        left_grad = QLinearGradient(0, 0, l_width, h)
        left_grad.setColorAt(0.0, QColor("#C7DCF1"))
        left_grad.setColorAt(0.35, QColor("#DDEBFA"))
        left_grad.setColorAt(0.70, QColor("#EDF4FC"))
        left_grad.setColorAt(1.0, QColor("#FFFFFF"))
        painter.fillRect(QRectF(0, 0, l_width, h), left_grad)

        # Subtle Dot Matrix Texture in lower half
        painter.setPen(QColor(180, 205, 230, 90))
        for x in range(30, l_width - 20, 16):
            for y in range(int(h * 0.45), h - 30, 16):
                painter.drawPoint(x, y)

        # -------------------------------------------------------------------
        # 3. Flowing Thermodynamic & Phase Equilibrium Wave Curves
        # -------------------------------------------------------------------
        # Curve 1: Deep Navy Blue CALPHAD Isotherm
        path1 = QPainterPath()
        path1.moveTo(0, h * 0.78)
        path1.cubicTo(l_width * 0.25, h * 0.88, l_width * 0.45, h * 0.35, l_width * 0.70, h * 0.55)
        path1.cubicTo(l_width * 0.82, h * 0.65, l_width * 0.92, h * 0.50, l_width, h * 0.45)
        painter.setPen(QPen(QColor("#0F2B5C"), 3.2))
        painter.drawPath(path1)

        # Curve 2: Cyan / Teal Solidus-Liquidus Envelope
        path2 = QPainterPath()
        path2.moveTo(0, h * 0.85)
        path2.cubicTo(l_width * 0.30, h * 0.40, l_width * 0.60, h * 0.90, l_width * 0.85, h * 0.42)
        path2.lineTo(l_width, h * 0.38)
        painter.setPen(QPen(QColor("#0284C7"), 2.2))
        painter.drawPath(path2)

        # Curve 3: Soft White Transition Wave
        path3 = QPainterPath()
        path3.moveTo(0, h * 0.60)
        path3.cubicTo(l_width * 0.35, h * 0.82, l_width * 0.55, h * 0.22, l_width, h * 0.62)
        painter.setPen(QPen(QColor(255, 255, 255, 220), 2.8))
        painter.drawPath(path3)

        # Curve 4: Slate Blue Free-Energy Tangent
        path4 = QPainterPath()
        path4.moveTo(0, h * 0.70)
        path4.cubicTo(l_width * 0.40, h * 0.95, l_width * 0.65, h * 0.50, l_width, h * 0.75)
        painter.setPen(QPen(QColor("#64748B"), 1.8))
        painter.drawPath(path4)

        # Draw Marker Nodes on Curves (matching JMatPro diamond/circle/triangle markers)
        painter.setBrush(QColor("#D97706"))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.2))
        painter.drawEllipse(QPointF(l_width * 0.68, h * 0.67), 5.0, 5.0)

        painter.setBrush(QColor("#1D4ED8"))
        painter.drawRect(QRectF(l_width * 0.45 - 4, h * 0.44 - 4, 8, 8))

        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPointF(l_width * 0.75, h * 0.58), 4.0, 4.0)

        # -------------------------------------------------------------------
        # 4. Typography & Branding
        # -------------------------------------------------------------------
        # Main Title: PyCALPHAD
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        painter.setFont(title_font)
        painter.setPen(QColor("#1E3A8A"))  # Deep Corporate Blue
        painter.drawText(36, 85, "PyCALPHAD")

        # Subtitle: PRACTICAL SOFTWARE FOR MATERIALS PROPERTIES
        sub_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(sub_font)
        painter.setPen(QColor("#475569"))
        painter.drawText(38, 110, "PRACTICAL SOFTWARE FOR MATERIALS PROPERTIES")

        # Version & Suite Specifications
        ver_font = QFont("Segoe UI", 16, QFont.Weight.Normal)
        painter.setFont(ver_font)
        painter.setPen(QColor("#1E3A8A"))
        painter.drawText(38, h - 55, "Version 2026.3")

        # Academic Attribution
        credit_font = QFont("Segoe UI", 8, QFont.Weight.Normal)
        painter.setFont(credit_font)
        painter.setPen(QColor("#64748B"))
        painter.drawText(38, h - 35, "SRM University-AP | Felix Mwiya & Prof. (Dr.) Sheela Singh")
        painter.drawText(38, h - 20, "Thermodynamic & Mechanical Property Simulation Suite")

        # -------------------------------------------------------------------
        # 5. Right Section: Deep Navy Ribbon with Industry Icons
        # -------------------------------------------------------------------
        ribbon_rect = QRectF(l_width, 0, r_width, h)
        ribbon_grad = QLinearGradient(l_width, 0, w, h)
        ribbon_grad.setColorAt(0.0, QColor("#14214D"))
        ribbon_grad.setColorAt(1.0, QColor("#0B1330"))
        painter.fillRect(ribbon_rect, ribbon_grad)

        # Vertical hairline divider
        painter.setPen(QPen(QColor("#1E3A8A"), 1.0))
        painter.drawLine(int(l_width), 0, int(l_width), h)

        # Render 9 Industry & Metallurgy Emblems
        emblems = [
            ("MECHANICAL", "[Gears]"),
            ("ELECTRONICS", "[Microchip]"),
            ("ENERGY", "[Plant]"),
            ("AUTOMOTIVE", "[Vehicle]"),
            ("AEROSPACE", "[Aircraft]"),
            ("ROCKETRY", "[Propulsion]"),
            ("RESEARCH", "[Academia]"),
            ("FORGING", "[Anvil]"),
            ("FOUNDRY", "[Crucible]")
        ]

        # Draw stylized vector symbols
        icon_font = QFont("Segoe UI", 8, QFont.Weight.DemiBold)
        painter.setFont(icon_font)

        total_icons = len(emblems)
        spacing = (h - 40) / total_icons

        for idx, (label, symbol) in enumerate(emblems):
            cy = 30 + idx * spacing
            cx = l_width + r_width / 2.0

            # Subtle emblem glow
            painter.setPen(QColor(147, 197, 253, 160))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Draw representative scientific geometry
            if idx == 0:  # Gears
                painter.drawEllipse(QPointF(cx, cy), 9.0, 9.0)
                painter.drawEllipse(QPointF(cx, cy), 4.0, 4.0)
            elif idx == 1:  # Microchip
                painter.drawRect(QRectF(cx - 8, cy - 8, 16, 16))
                painter.drawRect(QRectF(cx - 4, cy - 4, 8, 8))
            elif idx == 2:  # Plant / Factory
                p = QPainterPath()
                p.moveTo(cx - 9, cy + 8)
                p.lineTo(cx - 9, cy - 2)
                p.lineTo(cx - 4, cy + 2)
                p.lineTo(cx - 4, cy - 6)
                p.lineTo(cx + 1, cy - 2)
                p.lineTo(cx + 1, cy - 8)
                p.lineTo(cx + 9, cy - 8)
                p.lineTo(cx + 9, cy + 8)
                painter.drawPath(p)
            elif idx == 3:  # Automotive
                painter.drawRoundedRect(QRectF(cx - 10, cy - 5, 20, 10), 3, 3)
                painter.drawEllipse(QPointF(cx - 5, cy + 5), 2.5, 2.5)
                painter.drawEllipse(QPointF(cx + 5, cy + 5), 2.5, 2.5)
            elif idx == 4:  # Aerospace / Aircraft
                p = QPainterPath()
                p.moveTo(cx, cy - 9)
                p.lineTo(cx + 2, cy - 1)
                p.lineTo(cx + 11, cy + 3)
                p.lineTo(cx + 2, cy + 4)
                p.lineTo(cx + 3, cy + 9)
                p.lineTo(cx, cy + 7)
                p.lineTo(cx - 3, cy + 9)
                p.lineTo(cx - 2, cy + 4)
                p.lineTo(cx - 11, cy + 3)
                p.lineTo(cx - 2, cy - 1)
                p.closeSubpath()
                painter.drawPath(p)
            elif idx == 5:  # Rocket / Space
                p = QPainterPath()
                p.moveTo(cx, cy - 10)
                p.lineTo(cx + 4, cy - 2)
                p.lineTo(cx + 4, cy + 6)
                p.lineTo(cx + 8, cy + 9)
                p.lineTo(cx - 8, cy + 9)
                p.lineTo(cx - 4, cy + 6)
                p.lineTo(cx - 4, cy - 2)
                p.closeSubpath()
                painter.drawPath(p)
            elif idx == 6:  # Mortarboard Academia
                p = QPainterPath()
                p.moveTo(cx, cy - 6)
                p.lineTo(cx + 10, cy)
                p.lineTo(cx, cy + 6)
                p.lineTo(cx - 10, cy)
                p.closeSubpath()
                painter.drawPath(p)
                painter.drawLine(int(cx - 6), int(cy + 3), int(cx - 6), int(cy + 8))
            elif idx == 7:  # Anvil / Metallurgy
                p = QPainterPath()
                p.moveTo(cx - 9, cy - 4)
                p.lineTo(cx + 9, cy - 4)
                p.lineTo(cx + 6, cy + 1)
                p.lineTo(cx + 4, cy + 5)
                p.lineTo(cx + 7, cy + 7)
                p.lineTo(cx - 7, cy + 7)
                p.lineTo(cx - 4, cy + 5)
                p.lineTo(cx - 6, cy + 1)
                p.closeSubpath()
                painter.drawPath(p)
            else:  # Crucible / Solidification
                p = QPainterPath()
                p.moveTo(cx - 8, cy - 7)
                p.lineTo(cx + 8, cy - 7)
                p.lineTo(cx + 6, cy + 7)
                p.lineTo(cx - 6, cy + 7)
                p.closeSubpath()
                painter.drawPath(p)
                painter.drawLine(int(cx - 5), int(cy - 2), int(cx + 5), int(cy - 2))

        # -------------------------------------------------------------------
        # 6. Outer Border
        # -------------------------------------------------------------------
        painter.setPen(QPen(QColor("#94A3B8"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 8, 8)


class WelcomeSplashWidget(QWidget):
    """
    Standard JMatPro Startup View.
    Centers the splash banner with quick-access controls and instruction hints,
    providing the authentic experience of commercial CALPHAD software.
    """
    material_type_requested = pyqtSignal()
    database_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Centered container
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(20, 20, 20, 20)
        center_layout.setSpacing(16)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Signature JMatPro Banner Card
        self.banner = JMatProSplashBanner(self)
        self.banner.clicked.connect(self.material_type_requested.emit)

        # Soft drop shadow for elevation
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(15, 23, 42, 45))
        shadow.setOffset(0, 8)
        self.banner.setGraphicsEffect(shadow)

        center_layout.addWidget(self.banner)

        # 2. Primary Action Bar
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_open_selector = QPushButton("Select Material Type / Database...")
        self.btn_open_selector.setObjectName("primaryBtn")
        self.btn_open_selector.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_open_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_selector.setStyleSheet(
            "QPushButton {"
            "  background-color: #1D4ED8;"
            "  color: #FFFFFF;"
            "  border: 1px solid #1E40AF;"
            "  border-radius: 4px;"
            "  padding: 8px 24px;"
            "  font-weight: bold;"
            "  font-size: 10pt;"
            "}"
            "QPushButton:hover { background-color: #2563EB; }"
            "QPushButton:pressed { background-color: #1E40AF; }"
        )
        self.btn_open_selector.clicked.connect(self.material_type_requested.emit)
        action_row.addWidget(self.btn_open_selector)
        center_layout.addLayout(action_row)

        # 3. Quick-Start Alloy System Chips
        quick_lbl = QLabel("Quick-Start Active Alloy System:")
        quick_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        quick_lbl.setStyleSheet("color: #64748B;")
        quick_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(quick_lbl)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        quick_systems = [
            ("Thermal Spray Coatings", "#1D4ED8"),
            ("High Entropy Alloys", "#0284C7"),
            ("General Steel", "#475569"),
            ("Stainless Steel", "#059669"),
            ("Nickel Based Superalloy", "#7C3AED"),
            ("Aluminium Alloy", "#D97706"),
            ("Titanium Alloy", "#DC2626")
        ]

        for sys_name, color in quick_systems:
            btn = QPushButton(sys_name)
            btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: #FFFFFF;"
                f"  color: #1E293B;"
                f"  border: 1px solid #CBD5E1;"
                f"  border-radius: 12px;"
                f"  padding: 4px 12px;"
                f"  font-size: 8.5pt;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: #F1F5F9;"
                f"  border-color: {color};"
                f"  color: {color};"
                f"  font-weight: bold;"
                f"}}"
            )
            btn.clicked.connect(lambda checked, name=sys_name: self.database_selected.emit(name))
            chips_row.addWidget(btn)

        center_layout.addLayout(chips_row)

        root_layout.addWidget(center_container)
