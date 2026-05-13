"""
DMMView - Live Measurement Display
Digital LCD-style display showing real-time measurements with bargraph.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QPen, QBrush,
    QRadialGradient, QPainterPath,
)
from ui.styles import COLORS, FONTS
from plugins.base_plugin import MeasurementData


class AnalogBarGraph(QWidget):
    """Animated analog-style bargraph for measurement display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(32)
        self.setMaximumHeight(40)
        self._value = 0.0
        self._max_value = 100.0
        self._segments = 50
        self._target_value = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.setInterval(16)  # ~60 fps

    def set_value(self, value, max_value=None):
        """Set the current value (animated)."""
        if max_value is not None:
            self._max_value = max(abs(max_value), 0.001)
        self._target_value = min(abs(value) / self._max_value, 1.0)
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def _animate(self):
        diff = self._target_value - self._value
        if abs(diff) < 0.005:
            self._value = self._target_value
            self._anim_timer.stop()
        else:
            self._value += diff * 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 4
        seg_w = (w - 2 * margin) / self._segments
        seg_h = h - 2 * margin
        gap = 2
        filled = int(self._value * self._segments)

        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor(COLORS['bg_dark'])
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, w, h, 6, 6)

        for i in range(self._segments):
            x = margin + i * seg_w + gap / 2
            rect = QRectF(x, margin, seg_w - gap, seg_h)

            if i < filled:
                # Color gradient: green -> yellow -> orange -> red
                ratio = i / self._segments
                if ratio < 0.6:
                    color = QColor(COLORS['accent_green'])
                elif ratio < 0.8:
                    color = QColor(COLORS['accent_orange'])
                else:
                    color = QColor(COLORS['accent_red'])
                # Glow effect on tip segment
                if i == filled - 1:
                    color = color.lighter(140)
            else:
                color = QColor(COLORS['lcd_segment_off'])

            painter.setBrush(color)
            painter.drawRoundedRect(rect, 1.5, 1.5)

        painter.end()


class LiveDisplay(QWidget):
    """
    Main LCD-style measurement display.
    Shows primary value, function, range, unit, and secondary readings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── LCD Screen Container ─────────────────────────────────
        self.lcd_frame = QFrame()
        self.lcd_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #080c18, stop:0.05 #0a0f1a,
                    stop:0.95 #0a0f1a, stop:1 #0e1425);
                border: 2px solid {COLORS['border_dark']};
                border-radius: 12px;
            }}
        """)
        lcd_layout = QVBoxLayout(self.lcd_frame)
        lcd_layout.setContentsMargins(20, 16, 20, 16)
        lcd_layout.setSpacing(6)

        # ── Top info bar (function + range) ──────────────────────
        top_bar = QHBoxLayout()

        # Function indicator with colored badge
        self.func_badge = QLabel("DCV")
        self.func_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_bright']};
                border-radius: 6px;
                padding: 1px 6px;
                font-size: 9px;
                font-weight: 700;
                font-family: {FONTS['family_sans']};
            }}
        """)
        top_bar.addWidget(self.func_badge)

        # AC/DC indicator
        self.acdc_label = QLabel("DC")
        self.acdc_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 11px;
                font-weight: 600;
                padding: 0 4px;
            }}
        """)
        top_bar.addWidget(self.acdc_label)

        top_bar.addStretch()

        # Range indicator
        self.range_label = QLabel("AUTO")
        self.range_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_orange']};
                font-size: 11px;
                font-weight: 600;
                font-family: {FONTS['family_mono']};
                padding: 1px 6px;
                border: 1px solid {COLORS['accent_orange']};
                border-radius: 4px;
            }}
        """)
        top_bar.addWidget(self.range_label)

        lcd_layout.addLayout(top_bar)

        # ── Primary value display ────────────────────────────────
        value_row = QHBoxLayout()
        value_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.value_label = QLabel("----.---")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['lcd_segment_on']};
                font-family: {FONTS['family_mono']};
                font-size: 100px;
                font-weight: 700;
                letter-spacing: 2px;
                padding: 0 8px;
            }}
        """)
        value_row.addWidget(self.value_label, 1)

        # Unit label
        self.unit_label = QLabel("V")
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.unit_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-family: {FONTS['family_sans']};
                font-size: 42px;
                font-weight: 600;
                padding-bottom: 16px;
            }}
        """)
        value_row.addWidget(self.unit_label)

        lcd_layout.addLayout(value_row)

        # ── Bargraph ─────────────────────────────────────────────
        self.bargraph = AnalogBarGraph()
        lcd_layout.addWidget(self.bargraph)

        # ── Secondary readings ────────────────────────────────────
        secondary_frame = QFrame()
        secondary_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 40, 60, 0.5);
                border-radius: 6px;
                border: 1px solid {COLORS['border_dark']};
            }}
        """)
        sec_layout = QGridLayout(secondary_frame)
        sec_layout.setContentsMargins(12, 6, 12, 6)
        sec_layout.setSpacing(8)

        # Secondary value
        self.sec_title = QLabel("Secundario")
        self.sec_title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        sec_layout.addWidget(self.sec_title, 0, 0)

        self.sec_value = QLabel("----.---")
        self.sec_value.setStyleSheet(f"""
            color: {COLORS['accent_cyan']};
            font-family: {FONTS['family_mono']};
            font-size: 20px;
            font-weight: 600;
        """)
        sec_layout.addWidget(self.sec_value, 1, 0)

        self.sec_unit = QLabel("")
        self.sec_unit.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        sec_layout.addWidget(self.sec_unit, 1, 1)

        # Separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {COLORS['border_dark']};")
        sec_layout.addWidget(sep, 0, 2, 2, 1)

        # Tertiary value
        self.ter_title = QLabel("Terciario")
        self.ter_title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        sec_layout.addWidget(self.ter_title, 0, 3)

        self.ter_value = QLabel("----.---")
        self.ter_value.setStyleSheet(f"""
            color: {COLORS['accent_purple']};
            font-family: {FONTS['family_mono']};
            font-size: 20px;
            font-weight: 600;
        """)
        sec_layout.addWidget(self.ter_value, 1, 3)

        self.ter_unit = QLabel("")
        self.ter_unit.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        sec_layout.addWidget(self.ter_unit, 1, 4)

        lcd_layout.addWidget(secondary_frame)

        # ── Statistics bar ────────────────────────────────────────
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 40, 60, 0.3);
                border-radius: 6px;
                border: 1px solid {COLORS['border_dark']};
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 6, 12, 6)

        self.stat_labels = {}
        for name, color in [('MIN', COLORS['accent_cyan']),
                            ('MAX', COLORS['accent_red']),
                            ('AVG', COLORS['accent_orange']),
                            ('Δ', COLORS['accent_purple'])]:
            stat_box = QVBoxLayout()
            title = QLabel(name)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; "
                               f"font-weight: 600;")
            stat_box.addWidget(title)

            val = QLabel("----")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setStyleSheet(f"color: {color}; font-family: {FONTS['family_mono']}; "
                             f"font-size: 12px; font-weight: 600;")
            stat_box.addWidget(val)
            self.stat_labels[name] = val
            stats_layout.addLayout(stat_box)

        lcd_layout.addWidget(stats_frame)

        layout.addWidget(self.lcd_frame)

    def update_measurement(self, data: MeasurementData):
        """Update display with new measurement data."""
        self._current_data = data

        # Function badge
        func = data.function
        self.func_badge.setText(func)

        # Set badge color based on function type
        if 'AC' in func and 'DC' not in func:
            badge_color = COLORS['lcd_value_ac']
            self.acdc_label.setText("AC ∿")
        elif 'DC' in func:
            badge_color = COLORS['lcd_value_dc']
            self.acdc_label.setText("DC ⎓")
        elif 'OHM' in func or 'CONT' in func:
            badge_color = COLORS['accent_green']
            self.acdc_label.setText("Ω")
        elif 'CAP' in func:
            badge_color = COLORS['accent_purple']
            self.acdc_label.setText("⊥")
        elif 'FREQ' in func or 'Hz' in func:
            badge_color = COLORS['accent_cyan']
            self.acdc_label.setText("∿")
        elif 'DIODE' in func:
            badge_color = COLORS['accent_orange']
            self.acdc_label.setText("▷|")
        elif 'TC' in func or 'RTD' in func:
            badge_color = COLORS['accent_red']
            self.acdc_label.setText("🌡")
        elif 'PEAK' in func:
            badge_color = '#ff6b9d'
            self.acdc_label.setText("⚡")
        else:
            badge_color = COLORS['accent_blue']
            self.acdc_label.setText("")

        self.func_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_color};
                color: {COLORS['bg_darkest']};
                border-radius: 6px;
                padding: 1px 6px;
                font-size: 11px;
                font-weight: 700;
                font-family: {FONTS['family_sans']};
            }}
        """)

        # Range
        self.range_label.setText(data.range_str or "AUTO")

        # Primary value
        if data.is_overload:
            self.value_label.setText("O.L")
            self.value_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['lcd_overload']};
                    font-family: {FONTS['family_mono']};
                    font-size: 100px;
                    font-weight: 700;
                    letter-spacing: 2px;
                    padding: 0 8px;
                }}
            """)
        else:
            display_val = self._format_value(data.value, data.value_str)
            self.value_label.setText(display_val)
            value_color = badge_color if 'AC' in func else COLORS['lcd_segment_on']
            self.value_label.setStyleSheet(f"""
                QLabel {{
                    color: {value_color};
                    font-family: {FONTS['family_mono']};
                    font-size: 100px;
                    font-weight: 700;
                    letter-spacing: 2px;
                    padding: 0 8px;
                }}
            """)

        # Unit
        self.unit_label.setText(data.unit)

        # Bargraph
        range_max = self._get_range_max(data.range_str)
        self.bargraph.set_value(data.value, range_max)

        # Secondary
        if data.secondary_str:
            self.sec_value.setText(data.secondary_str)
            self.sec_unit.setText(data.secondary_unit or '')
        else:
            self.sec_value.setText("----.---")
            self.sec_unit.setText("")

        # Tertiary
        if data.tertiary_str:
            self.ter_value.setText(data.tertiary_str)
            self.ter_unit.setText(data.tertiary_unit or '')
        else:
            self.ter_value.setText("----.---")
            self.ter_unit.setText("")

    def update_statistics(self, stats: dict):
        """Update statistics display."""
        if stats['count'] > 0:
            self.stat_labels['MIN'].setText(f"{stats['min']:.4g}")
            self.stat_labels['MAX'].setText(f"{stats['max']:.4g}")
            self.stat_labels['AVG'].setText(f"{stats['avg']:.4g}")
            self.stat_labels['Δ'].setText(f"{stats['range']:.4g}")
        else:
            for label in self.stat_labels.values():
                label.setText("----")

    def set_idle(self):
        """Set display to idle state."""
        self.value_label.setText("----.---")
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['lcd_segment_off']};
                font-family: {FONTS['family_mono']};
                font-size: 100px;
                font-weight: 700;
                letter-spacing: 2px;
                padding: 0 8px;
            }}
        """)
        self.func_badge.setText("---")
        self.range_label.setText("---")
        self.unit_label.setText("")
        self.acdc_label.setText("")
        self.sec_value.setText("----.---")
        self.ter_value.setText("----.---")
        self.bargraph.set_value(0, 100)
        for label in self.stat_labels.values():
            label.setText("----")

    def _format_value(self, value, raw_str=""):
        """Format value for display with appropriate precision."""
        if raw_str and raw_str not in ('OL', 'O.L'):
            return raw_str

        abs_val = abs(value)
        if abs_val >= 1000:
            return f"{value:.1f}"
        elif abs_val >= 100:
            return f"{value:.2f}"
        elif abs_val >= 10:
            return f"{value:.3f}"
        elif abs_val >= 1:
            return f"{value:.4f}"
        else:
            return f"{value:.4f}"

    def _get_range_max(self, range_str):
        """Extract maximum value from range string for bargraph."""
        if not range_str:
            return 100
        import re
        match = re.search(r'([\d.]+)', range_str)
        if match:
            return float(match.group(1))
        return 100
