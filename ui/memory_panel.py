"""
DMMView - Memory Panel
Panel for downloading and viewing stored records from the DMM memory.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QGroupBox, QFrame, QTabWidget, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from ui.styles import COLORS, FONTS
from core.data_logger import MeasurementRecord


class MemoryPanel(QWidget):
    """Panel for downloading and displaying DMM memory records."""

    download_manual_requested = pyqtSignal()
    download_timed_requested = pyqtSignal()
    export_manual_requested = pyqtSignal()
    export_timed_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Download Controls ─────────────────────────────────────
        controls = QFrame()
        controls.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_dark']};
                border-radius: 8px;
            }}
        """)
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(12, 10, 12, 10)

        # Manual records download
        self.dl_manual_btn = QPushButton("\u2B07 Descargar Registros Manuales")
        self.dl_manual_btn.setProperty("cssClass", "primary")
        self.dl_manual_btn.setMinimumHeight(36)
        self.dl_manual_btn.clicked.connect(self.download_manual_requested.emit)
        ctrl_layout.addWidget(self.dl_manual_btn)

        # Timed records download
        self.dl_timed_btn = QPushButton("⏱ Descargar Registros Temporizados")
        self.dl_timed_btn.setProperty("cssClass", "primary")
        self.dl_timed_btn.setMinimumHeight(36)
        self.dl_timed_btn.clicked.connect(self.download_timed_requested.emit)
        ctrl_layout.addWidget(self.dl_timed_btn)

        ctrl_layout.addStretch()

        # Record count display
        count_box = QVBoxLayout()
        count_lbl = QLabel("Registros")
        count_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_box.addWidget(count_lbl)

        self.record_count_label = QLabel("0")
        self.record_count_label.setStyleSheet(f"""
            color: {COLORS['accent_blue']};
            font-family: {FONTS['family_mono']};
            font-size: 18px;
            font-weight: 700;
        """)
        self.record_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_box.addWidget(self.record_count_label)
        ctrl_layout.addLayout(count_box)

        # Interval display (for timed records)
        interval_box = QVBoxLayout()
        interval_lbl = QLabel("Intervalo")
        interval_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        interval_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        interval_box.addWidget(interval_lbl)

        self.interval_label = QLabel("---")
        self.interval_label.setStyleSheet(f"""
            color: {COLORS['accent_orange']};
            font-family: {FONTS['family_mono']};
            font-size: 14px;
            font-weight: 600;
        """)
        self.interval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        interval_box.addWidget(self.interval_label)
        ctrl_layout.addLayout(interval_box)

        layout.addWidget(controls)

        # ── Progress Bar ─────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Descargando registro %v de %m...")
        layout.addWidget(self.progress_bar)

        # ── Tabs for Manual / Timed records ──────────────────────
        self.tabs = QTabWidget()

        # Manual records tab
        manual_widget = QWidget()
        manual_layout = QVBoxLayout(manual_widget)
        manual_layout.setContentsMargins(0, 4, 0, 0)

        # Export button
        manual_btn_row = QHBoxLayout()
        manual_btn_row.addStretch()
        self.export_manual_btn = QPushButton("\u2913 Exportar Manuales a CSV")
        self.export_manual_btn.clicked.connect(self.export_manual_requested.emit)
        manual_btn_row.addWidget(self.export_manual_btn)
        manual_layout.addLayout(manual_btn_row)

        self.manual_table = self._create_table()
        manual_layout.addWidget(self.manual_table, 1)
        self.tabs.addTab(manual_widget, "\u2261 Registros Manuales")

        # Timed records tab
        timed_widget = QWidget()
        timed_layout = QVBoxLayout(timed_widget)
        timed_layout.setContentsMargins(0, 4, 0, 0)

        # Export button
        timed_btn_row = QHBoxLayout()
        timed_btn_row.addStretch()
        self.export_timed_btn = QPushButton("\u2913 Exportar Temporizados a CSV")
        self.export_timed_btn.clicked.connect(self.export_timed_requested.emit)
        timed_btn_row.addWidget(self.export_timed_btn)
        timed_layout.addLayout(timed_btn_row)

        self.timed_table = self._create_table()
        timed_layout.addWidget(self.timed_table, 1)
        self.tabs.addTab(timed_widget, "⏱ Registros Temporizados")

        layout.addWidget(self.tabs, 1)

    def _create_table(self):
        """Create a styled table widget for memory records."""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "#", "Función", "Rango", "Valor Principal",
            "Unidad", "Secundario", "Terciario", "OL"
        ])
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        table.verticalHeader().setDefaultSectionSize(28)
        return table

    def show_progress(self, total):
        """Show progress bar for download."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.dl_manual_btn.setEnabled(False)
        self.dl_timed_btn.setEnabled(False)

    def update_progress(self, current):
        """Update progress bar."""
        self.progress_bar.setValue(current)

    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
        self.dl_manual_btn.setEnabled(True)
        self.dl_timed_btn.setEnabled(True)

    def set_record_count(self, count):
        """Update record count display."""
        self.record_count_label.setText(str(count))

    def set_interval(self, interval_seconds):
        """Update interval display."""
        if interval_seconds:
            self.interval_label.setText(f"{interval_seconds}s")
        else:
            self.interval_label.setText("---")

    def add_manual_record(self, record: MeasurementRecord):
        """Add a record to the manual records table."""
        self._add_to_table(self.manual_table, record)

    def add_timed_record(self, record: MeasurementRecord):
        """Add a record to the timed records table."""
        self._add_to_table(self.timed_table, record)

    def _add_to_table(self, table: QTableWidget, record: MeasurementRecord):
        """Add a record row to a table."""
        row = table.rowCount()
        table.insertRow(row)

        # Record number
        num_item = QTableWidgetItem(str(record.record_number))
        num_item.setForeground(QColor(COLORS['text_muted']))
        table.setItem(row, 0, num_item)

        # Function
        func_item = QTableWidgetItem(record.function)
        func_item.setForeground(QColor(COLORS['accent_blue']))
        table.setItem(row, 1, func_item)

        # Range
        table.setItem(row, 2, QTableWidgetItem(record.range_str))

        # Value
        val_item = QTableWidgetItem(record.value_str)
        val_item.setFont(QFont(FONTS['family_mono'].split(',')[0], 11))
        if record.is_overload:
            val_item.setForeground(QColor(COLORS['accent_red']))
        else:
            val_item.setForeground(QColor(COLORS['accent_green']))
        table.setItem(row, 3, val_item)

        # Unit
        table.setItem(row, 4, QTableWidgetItem(record.unit))

        # Secondary
        sec = record.secondary_str or ""
        if record.secondary_unit:
            sec += f" {record.secondary_unit}"
        table.setItem(row, 5, QTableWidgetItem(sec))

        # Tertiary
        ter = record.tertiary_str or ""
        if record.tertiary_unit:
            ter += f" {record.tertiary_unit}"
        table.setItem(row, 6, QTableWidgetItem(ter))

        # Overload
        ol_item = QTableWidgetItem("⚠ OL" if record.is_overload else "")
        if record.is_overload:
            ol_item.setForeground(QColor(COLORS['accent_red']))
        table.setItem(row, 7, ol_item)

    def clear_manual_records(self):
        """Clear manual records table."""
        self.manual_table.setRowCount(0)

    def clear_timed_records(self):
        """Clear timed records table."""
        self.timed_table.setRowCount(0)
