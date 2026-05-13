"""
DMMView - Serial Connection Panel
Configuration panel for serial port connection with auto-detection.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QGroupBox, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont
from ui.styles import COLORS, FONTS
from core.serial_manager import SerialManager


class StatusLED(QWidget):
    """Circular LED status indicator."""

    def __init__(self, size=14, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = COLORS['status_disconnected']
        self.setFixedSize(size, size)

    def set_connected(self):
        self._color = COLORS['status_connected']
        self.update()

    def set_disconnected(self):
        self._color = COLORS['status_disconnected']
        self.update()

    def set_logging(self):
        self._color = COLORS['status_logging']
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QRadialGradient
        from PyQt6.QtCore import QPointF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(self._color)
        center = QPointF(self._size / 2, self._size / 2)
        radius = self._size / 2 - 1

        # Glow effect
        glow = QRadialGradient(center, radius * 1.5)
        glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 80))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 1.3, radius * 1.3)

        # Main LED
        gradient = QRadialGradient(center - QPointF(1, 1), radius)
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(130))
        painter.setBrush(gradient)
        painter.setPen(QColor(color.darker(180)))
        painter.drawEllipse(center, radius, radius)

        # Highlight
        highlight = QRadialGradient(center - QPointF(radius * 0.3, radius * 0.3), radius * 0.5)
        highlight.setColorAt(0, QColor(255, 255, 255, 100))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(highlight)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center - QPointF(radius * 0.2, radius * 0.2),
                           radius * 0.5, radius * 0.5)

        painter.end()


class ConnectionPanel(QWidget):
    """Serial port connection configuration panel."""

    connect_requested = pyqtSignal(dict)
    disconnect_requested = pyqtSignal()
    instrument_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._setup_ui()
        self._refresh_ports()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Instrument Selection ──────────────────────────────────
        instrument_group = QGroupBox("\u25B8  Instrumento")
        instrument_layout = QGridLayout(instrument_group)
        instrument_layout.setSpacing(6)

        instrument_layout.addWidget(QLabel("Multímetro:"), 0, 0)
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItem("\u25C6 VICTOR 98A+ (Serial)", "victor98a")
        self.instrument_combo.addItem("\u25C6 Fluke 287/289 (IR Serial)", "fluke287")
        self.instrument_combo.addItem("\u25C6 Brymen BM250s (IR Serial)", "brymen_bm250s")
        self.instrument_combo.addItem("\u25C6 UNI-T UT-61E+ (USB HID)", "unit_ut61eplus")
        self.instrument_combo.addItem("\u25C6 EEVBlog 121GW (BLE)", "eevblog121gw")
        self.instrument_combo.addItem("\u25C6 UNI-T UT-181 (Serial)", "unit_ut181")
        self.instrument_combo.addItem("\u25C6 OWON XDM1041/XDM1241 (Serial)", "owon_xdm1041")
        self.instrument_combo.addItem("\u25C6 OWON XDM3041/XDM3051 (Serial)", "owon_xdm3041")
        self.instrument_combo.currentIndexChanged.connect(self._on_instrument_changed)
        instrument_layout.addWidget(self.instrument_combo, 0, 1)

        # Connection type info label
        self.conn_type_label = QLabel("Tipo: Serial (Puerto COM)")
        self.conn_type_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        instrument_layout.addWidget(self.conn_type_label, 1, 0, 1, 2)

        layout.addWidget(instrument_group)

        # ── Serial Port Configuration ──────────────────────────────
        serial_group = QGroupBox("\u2699  Puerto Serie")
        serial_layout = QGridLayout(serial_group)
        serial_layout.setSpacing(6)

        # Port selection
        serial_layout.addWidget(QLabel("Puerto:"), 0, 0)
        port_row = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(160)
        port_row.addWidget(self.port_combo, 1)
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("Actualizar puertos")
        self.refresh_btn.clicked.connect(self._refresh_ports)
        port_row.addWidget(self.refresh_btn)
        serial_layout.addLayout(port_row, 0, 1)

        # Baudrate
        serial_layout.addWidget(QLabel("Baudrate:"), 1, 0)
        self.baudrate_combo = QComboBox()
        for baud in [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
            self.baudrate_combo.addItem(str(baud), baud)
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)

        # Data bits
        serial_layout.addWidget(QLabel("Data Bits:"), 2, 0)
        self.databits_combo = QComboBox()
        for bits in [5, 6, 7, 8]:
            self.databits_combo.addItem(str(bits), bits)
        self.databits_combo.setCurrentText("8")
        serial_layout.addWidget(self.databits_combo, 2, 1)

        # Stop bits
        serial_layout.addWidget(QLabel("Stop Bits:"), 3, 0)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItem("1", 1)
        self.stopbits_combo.addItem("1.5", 1.5)
        self.stopbits_combo.addItem("2", 2)
        self.stopbits_combo.setCurrentText("1")
        serial_layout.addWidget(self.stopbits_combo, 3, 1)

        # Parity
        serial_layout.addWidget(QLabel("Paridad:"), 4, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItem("Ninguna (N)", 'N')
        self.parity_combo.addItem("Par (E)", 'E')
        self.parity_combo.addItem("Impar (O)", 'O')
        serial_layout.addWidget(self.parity_combo, 4, 1)

        layout.addWidget(serial_group)

        # ── Connection Status ──────────────────────────────────────
        status_group = QGroupBox("\u25C9  Estado")
        status_layout = QVBoxLayout(status_group)

        # Status indicator
        status_row = QHBoxLayout()
        self.status_led = StatusLED(16)
        status_row.addWidget(self.status_led)
        self.status_label = QLabel("Desconectado")
        self.status_label.setStyleSheet(f"color: {COLORS['status_disconnected']}; "
                                        f"font-weight: 600;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_layout.addLayout(status_row)

        # Port info
        self.port_info_label = QLabel("")
        self.port_info_label.setStyleSheet(f"color: {COLORS['text_muted']}; "
                                           f"font-size: 10px;")
        self.port_info_label.setWordWrap(True)
        status_layout.addWidget(self.port_info_label)

        layout.addWidget(status_group)

        # ── Connect / Disconnect buttons ───────────────────────────
        btn_layout = QHBoxLayout()

        self.connect_btn = QPushButton("⚡ Conectar")
        self.connect_btn.setProperty("cssClass", "success")
        self.connect_btn.setMinimumHeight(36)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("✕ Desconectar")
        self.disconnect_btn.setProperty("cssClass", "danger")
        self.disconnect_btn.setMinimumHeight(36)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        btn_layout.addWidget(self.disconnect_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_ports)
        self._refresh_timer.start(5000)  # Refresh every 5 seconds

    def _refresh_ports(self):
        """Refresh available serial ports."""
        current = self.port_combo.currentData()
        self.port_combo.clear()

        ports = SerialManager.list_ports()
        if ports:
            for port in ports:
                label = f"{port['device']}"
                if port['description'] and port['description'] != port['device']:
                    label += f" — {port['description']}"
                self.port_combo.addItem(label, port['device'])
                if current and port['device'] == current:
                    self.port_combo.setCurrentIndex(self.port_combo.count() - 1)
        else:
            self.port_combo.addItem("— No se detectaron puertos —", None)

        # Update port info
        idx = self.port_combo.currentIndex()
        if idx >= 0 and idx < len(ports):
            port = ports[idx]
            info = f"Fabricante: {port['manufacturer'] or 'Desconocido'}"
            if port['vid'] and port['pid']:
                info += f"\nVID:PID  {port['vid']:04X}:{port['pid']:04X}"
            self.port_info_label.setText(info)

    def _on_connect(self):
        """Handle connect button click."""
        port = self.port_combo.currentData()
        if not port:
            return

        params = {
            'port': port,
            'baudrate': self.baudrate_combo.currentData(),
            'databits': self.databits_combo.currentData(),
            'stopbits': self.stopbits_combo.currentData(),
            'parity': self.parity_combo.currentData(),
            'instrument': self.instrument_combo.currentData(),
        }
        self.connect_requested.emit(params)

    def _on_disconnect(self):
        """Handle disconnect button click."""
        self.disconnect_requested.emit()

    def set_connected(self, port_name=""):
        """Update UI to connected state."""
        self._connected = True
        self.status_led.set_connected()
        self.status_label.setText(f"Conectado: {port_name}")
        self.status_label.setStyleSheet(f"color: {COLORS['status_connected']}; "
                                        f"font-weight: 600;")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.port_combo.setEnabled(False)
        self.baudrate_combo.setEnabled(False)
        self.databits_combo.setEnabled(False)
        self.stopbits_combo.setEnabled(False)
        self.parity_combo.setEnabled(False)
        self.instrument_combo.setEnabled(False)

    def set_disconnected(self):
        """Update UI to disconnected state."""
        self._connected = False
        self.status_led.set_disconnected()
        self.status_label.setText("Desconectado")
        self.status_label.setStyleSheet(f"color: {COLORS['status_disconnected']}; "
                                        f"font-weight: 600;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.baudrate_combo.setEnabled(True)
        self.databits_combo.setEnabled(True)
        self.stopbits_combo.setEnabled(True)
        self.parity_combo.setEnabled(True)
        self.instrument_combo.setEnabled(True)

    def apply_plugin_defaults(self, serial_params):
        """Apply default serial parameters from a plugin."""
        self.baudrate_combo.setCurrentText(str(serial_params.baudrate))
        self.databits_combo.setCurrentText(str(serial_params.databits))
        self.stopbits_combo.setCurrentText(str(serial_params.stopbits))
        parity_map = {'N': 0, 'E': 1, 'O': 2}
        self.parity_combo.setCurrentIndex(parity_map.get(serial_params.parity, 0))

    def _on_instrument_changed(self, index):
        """Update UI based on selected instrument's connection type."""
        instrument_id = self.instrument_combo.currentData()

        # Connection type info
        conn_types = {
            'victor98a': ('Serial (Puerto COM)', True),
            'fluke287': ('Serial IR (Cable IR189USB, 115200 baud)', True),
            'brymen_bm250s': ('Serial IR (Cable BRUA-20X, 9600 baud)', True),
            'unit_ut61eplus': ('USB HID (CP2110, sin puerto serie)', False),
            'eevblog121gw': ('Bluetooth LE (requiere adaptador BT)', False),
            'unit_ut181': ('USB HID (CP2110, sin puerto serie)', False),
            'owon_xdm1041': ('Serial SCPI (Puerto COM)', True),
            'owon_xdm3041': ('Serial SCPI (Puerto COM)', True),
        }

        conn_info, uses_serial = conn_types.get(instrument_id, ('Serial', True))
        self.conn_type_label.setText(f"Tipo: {conn_info}")

        # Enable/disable serial port controls
        serial_enabled = uses_serial and not self._connected
        self.port_combo.setEnabled(serial_enabled)
        self.baudrate_combo.setEnabled(serial_enabled)
        self.databits_combo.setEnabled(serial_enabled)
        self.stopbits_combo.setEnabled(serial_enabled)
        self.parity_combo.setEnabled(serial_enabled)

        # Emit instrument changed signal to update plugin in main window
        self.instrument_changed.emit(instrument_id)
