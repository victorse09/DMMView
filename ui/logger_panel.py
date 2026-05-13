"""
DMMView - Logger Panel
Data logging table with controls for recording measurements.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from ui.styles import COLORS, FONTS
from core.data_logger import MeasurementRecord
from datetime import datetime


class LoggerPanel(QWidget):
    """Panel for logging and displaying measurement records."""

    logging_started = pyqtSignal()
    logging_stopped = pyqtSignal()
    clear_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Controls Bar ─────────────────────────────────────────
        controls = QFrame()
        controls.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_dark']};
                border-radius: 8px;
            }}
        """)
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(12, 8, 12, 8)

        # Start/Stop button
        self.start_btn = QPushButton("▶  Iniciar Registro")
        self.start_btn.setProperty("cssClass", "success")
        self.start_btn.setMinimumWidth(160)
        self.start_btn.clicked.connect(self._toggle_logging)
        ctrl_layout.addWidget(self.start_btn)

        # Interval
        ctrl_layout.addWidget(QLabel("Intervalo:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 60000)
        self.interval_spin.setValue(500)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.setSingleStep(100)
        ctrl_layout.addWidget(self.interval_spin)

        ctrl_layout.addStretch()

        # Sample counter
        counter_box = QVBoxLayout()
        counter_lbl = QLabel("Muestras")
        counter_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        counter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counter_box.addWidget(counter_lbl)

        self.sample_count = QLabel("0")
        self.sample_count.setStyleSheet(f"""
            color: {COLORS['accent_blue']};
            font-family: {FONTS['family_mono']};
            font-size: 18px;
            font-weight: 700;
        """)
        self.sample_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counter_box.addWidget(self.sample_count)
        ctrl_layout.addLayout(counter_box)

        # Elapsed time
        time_box = QVBoxLayout()
        time_lbl = QLabel("Tiempo")
        time_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_box.addWidget(time_lbl)

        self.elapsed_label = QLabel("00:00:00")
        self.elapsed_label.setStyleSheet(f"""
            color: {COLORS['accent_orange']};
            font-family: {FONTS['family_mono']};
            font-size: 14px;
            font-weight: 600;
        """)
        self.elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_box.addWidget(self.elapsed_label)
        ctrl_layout.addLayout(time_box)

        ctrl_layout.addStretch()

        # Clear and Export buttons
        self.clear_btn = QPushButton("\u2716 Limpiar")
        self.clear_btn.setProperty("cssClass", "danger")
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        ctrl_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("\u2913 Exportar CSV")
        self.export_btn.clicked.connect(self.export_requested.emit)
        ctrl_layout.addWidget(self.export_btn)

        layout.addWidget(controls)

        # ── Data Table ───────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Función", "Rango", "Valor",
            "Unidad", "Secundario", "Terciario", "OL"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setDefaultSectionSize(28)

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table, 1)

        # State
        self._is_logging = False
        self._start_time = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)
        self._count = 0

    def _toggle_logging(self):
        """Toggle logging on/off."""
        if self._is_logging:
            self._stop_logging()
        else:
            self._start_logging()

    def _start_logging(self):
        self._is_logging = True
        self._start_time = datetime.now()
        self._count = 0
        self.start_btn.setText("⏹  Detener Registro")
        self.start_btn.setProperty("cssClass", "danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.interval_spin.setEnabled(False)
        self._timer.start(1000)
        self.logging_started.emit()

    def _stop_logging(self):
        self._is_logging = False
        self.start_btn.setText("▶  Iniciar Registro")
        self.start_btn.setProperty("cssClass", "success")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.interval_spin.setEnabled(True)
        self._timer.stop()
        self.logging_stopped.emit()

    def _update_elapsed(self):
        """Update elapsed time display."""
        if self._start_time:
            elapsed = datetime.now() - self._start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.elapsed_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def add_record(self, record: MeasurementRecord):
        """Add a new record to the table."""
        self._count += 1
        self.sample_count.setText(str(self._count))

        row = self.table.rowCount()
        self.table.insertRow(row)

        # Timestamp
        ts_item = QTableWidgetItem(
            record.timestamp.strftime('%H:%M:%S.%f')[:-3]
        )
        ts_item.setForeground(QColor(COLORS['text_muted']))
        self.table.setItem(row, 0, ts_item)

        # Function
        func_item = QTableWidgetItem(record.function)
        func_item.setForeground(QColor(COLORS['accent_blue']))
        self.table.setItem(row, 1, func_item)

        # Range
        self.table.setItem(row, 2, QTableWidgetItem(record.range_str))

        # Value
        val_item = QTableWidgetItem(record.value_str)
        val_item.setFont(QFont(FONTS['family_mono'].split(',')[0], 11))
        if record.is_overload:
            val_item.setForeground(QColor(COLORS['accent_red']))
        else:
            val_item.setForeground(QColor(COLORS['accent_green']))
        self.table.setItem(row, 3, val_item)

        # Unit
        self.table.setItem(row, 4, QTableWidgetItem(record.unit))

        # Secondary
        sec_text = record.secondary_str or ""
        if record.secondary_unit:
            sec_text += f" {record.secondary_unit}"
        self.table.setItem(row, 5, QTableWidgetItem(sec_text))

        # Tertiary
        ter_text = record.tertiary_str or ""
        if record.tertiary_unit:
            ter_text += f" {record.tertiary_unit}"
        self.table.setItem(row, 6, QTableWidgetItem(ter_text))

        # Overload
        ol_item = QTableWidgetItem("⚠ OL" if record.is_overload else "")
        if record.is_overload:
            ol_item.setForeground(QColor(COLORS['accent_red']))
        self.table.setItem(row, 7, ol_item)

        # Auto-scroll to bottom
        self.table.scrollToBottom()

    def clear_table(self):
        """Clear all records from the table."""
        self.table.setRowCount(0)
        self._count = 0
        self.sample_count.setText("0")
        self.elapsed_label.setText("00:00:00")
        self._start_time = None

    def get_interval_ms(self):
        """Get the configured logging interval in milliseconds."""
        return self.interval_spin.value()

    @property
    def is_logging(self):
        return self._is_logging
