"""
DMMView - Main Window
Central application window with menus, toolbar, and tabbed panels.
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont

from ui.styles import COLORS, FONTS
from ui.resources import svg_to_icon
from ui.connection_panel import ConnectionPanel
from ui.live_display import LiveDisplay
from ui.logger_panel import LoggerPanel
from ui.chart_panel import ChartPanel
from ui.memory_panel import MemoryPanel
from core.serial_manager import SerialManager
from core.data_logger import DataLogger, MeasurementRecord
from core.csv_export import export_to_csv, import_from_csv
from core.version import VERSION
from plugins.base_plugin import BaseDMMPlugin, MeasurementData
from plugins.victor98a import Victor98APlugin
from plugins.eevblog121gw import EEVBlog121GWPlugin
from plugins.fluke287 import Fluke287Plugin
from plugins.unit_ut61eplus import UT61EPlusPlugin
from plugins.brymen_bm250s import BrymenBM250sPlugin
from plugins.unit_ut181 import UnitUT181Plugin
from plugins.owon_xdm1041 import OwonXDM1041Plugin
from plugins.owon_xdm3041 import OwonXDM3041Plugin

logger = logging.getLogger("DMMView.MainWindow")


class MeasurementWorker(QTimer):
    """Timer-based worker for periodic measurement reading (Serial)."""
    measurement_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_mgr, plugin, parent=None):
        super().__init__(parent)
        self._serial = serial_mgr
        self._plugin = plugin
        self.timeout.connect(self._read)

    def _read(self):
        try:
            cmd = self._plugin.build_read_command()
            resp = self._serial.send_and_receive(cmd, timeout=1.5)
            if resp:
                data = self._plugin.parse_measurement(resp)
                if data:
                    self.measurement_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))


class BLEMeasurementWorker(QTimer):
    """Timer-based worker for BLE devices (polls latest notification data)."""
    measurement_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self._plugin = plugin
        self.timeout.connect(self._read)

    def _read(self):
        try:
            data = self._plugin.get_latest_measurement()
            if data:
                self.measurement_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))


class HIDMeasurementWorker(QTimer):
    """Timer-based worker for USB HID devices."""
    measurement_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self._plugin = plugin
        self.timeout.connect(self._read)

    def _read(self):
        try:
            data = self._plugin.read_measurement_hid()
            if data:
                self.measurement_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))



class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMMView — Digital Multimeter Viewer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # Set window icon
        from PyQt6.QtGui import QIcon
        import os
        import sys
        
        if hasattr(sys, '_MEIPASS'):
            # Path when bundled by PyInstaller
            icon_path = os.path.join(sys._MEIPASS, "ui", "icon.png")
        else:
            # Path when running from source
            icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Core components
        self.serial_mgr = SerialManager()
        self.data_logger = DataLogger()
        self.plugin: BaseDMMPlugin | None = None
        self.worker: MeasurementWorker | None = None

        # Available plugins
        self.plugins = {
            'victor98a': Victor98APlugin(),
            'fluke287': Fluke287Plugin(),
            'brymen_bm250s': BrymenBM250sPlugin(),
            'unit_ut61eplus': UT61EPlusPlugin(),
            'eevblog121gw': EEVBlog121GWPlugin(),
            'unit_ut181': UnitUT181Plugin(),
            'owon_xdm1041': OwonXDM1041Plugin(),
            'owon_xdm3041': OwonXDM3041Plugin(),
        }

        self._chart_refresh_counter = 0
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Left: Connection Panel
        self.connection_panel = ConnectionPanel()
        self.connection_panel.setFixedWidth(280)

        # Right: Tabbed content
        self.tabs = QTabWidget()
        self.live_display = LiveDisplay()
        self.logger_panel = LoggerPanel()
        self.chart_panel = ChartPanel()
        self.memory_panel = MemoryPanel()

        self.tabs.addTab(self.live_display, "\u25C9  Medición en Vivo")
        self.tabs.addTab(self.logger_panel, "\u2261  Registro de Datos")
        self.tabs.addTab(self.chart_panel, "\u223F  Gráficos")
        self.tabs.addTab(self.memory_panel, "\u2B07  Memoria del DMM")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.connection_panel)
        splitter.addWidget(self.tabs)
        splitter.setSizes([280, 900])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

    def _setup_menus(self):
        menubar = self.menuBar()

        # ── Archivo ──
        file_menu = menubar.addMenu("&Archivo")
        import_csv_action = QAction("Abrir CSV de registros...", self)
        import_csv_action.setShortcut("Ctrl+O")
        import_csv_action.triggered.connect(self._import_csv)
        file_menu.addAction(import_csv_action)
        file_menu.addSeparator()
        self.export_action = QAction("Exportar Logging a CSV...", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self._export_logging_csv)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── Conexión ──
        conn_menu = menubar.addMenu("&Conexión")
        self.connect_action = QAction("Conectar", self)
        self.connect_action.triggered.connect(lambda: self.connection_panel._on_connect())
        conn_menu.addAction(self.connect_action)
        self.disconnect_action = QAction("Desconectar", self)
        self.disconnect_action.setEnabled(False)
        self.disconnect_action.triggered.connect(lambda: self.connection_panel._on_disconnect())
        conn_menu.addAction(self.disconnect_action)

        # ── Datos ──
        data_menu = menubar.addMenu("&Datos")
        self.start_log_action = QAction("▶ Iniciar Logging", self)
        self.start_log_action.setShortcut("F5")
        self.start_log_action.triggered.connect(self._start_logging)
        data_menu.addAction(self.start_log_action)
        self.stop_log_action = QAction("⏹ Detener Logging", self)
        self.stop_log_action.setShortcut("F6")
        self.stop_log_action.setEnabled(False)
        self.stop_log_action.triggered.connect(self._stop_logging)
        data_menu.addAction(self.stop_log_action)
        data_menu.addSeparator()
        dl_manual = QAction("\u2B07 Descargar Registros Manuales", self)
        dl_manual.triggered.connect(self._download_manual_records)
        data_menu.addAction(dl_manual)
        dl_timed = QAction("⏱ Descargar Registros Temporizados", self)
        dl_timed.triggered.connect(self._download_timed_records)
        data_menu.addAction(dl_timed)

        # ── Gráficos ──
        chart_menu = menubar.addMenu("&Gráficos")
        refresh_chart = QAction("Actualizar Gráficos", self)
        refresh_chart.setShortcut("F7")
        refresh_chart.triggered.connect(lambda: self.chart_panel._refresh_all())
        chart_menu.addAction(refresh_chart)
        clear_chart = QAction("Limpiar Gráficos", self)
        clear_chart.triggered.connect(lambda: self.chart_panel._clear_all())
        chart_menu.addAction(clear_chart)
        chart_menu.addSeparator()
        export_png = QAction("Exportar gráfico como PNG...", self)
        export_png.triggered.connect(lambda: self.chart_panel.export_current_chart('png'))
        chart_menu.addAction(export_png)
        export_jpg = QAction("Exportar gráfico como JPG...", self)
        export_jpg.triggered.connect(lambda: self.chart_panel.export_current_chart('jpg'))
        chart_menu.addAction(export_jpg)
        export_pdf = QAction("Exportar gráfico como PDF...", self)
        export_pdf.triggered.connect(lambda: self.chart_panel.export_current_chart('pdf'))
        chart_menu.addAction(export_pdf)

        # ── Ayuda ──
        help_menu = menubar.addMenu("A&yuda")
        instructions_action = QAction("Instrucciones...", self)
        instructions_action.triggered.connect(self._show_instructions)
        help_menu.addAction(instructions_action)
        changelog_action = QAction("Cambios de versión...", self)
        changelog_action.triggered.connect(self._show_changelog)
        help_menu.addAction(changelog_action)
        help_menu.addSeparator()
        about_action = QAction("Acerca de DMMView...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Herramientas")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.tb_connect = toolbar.addAction("⚡ Conectar")
        self.tb_connect.triggered.connect(lambda: self.connection_panel._on_connect())
        self.tb_disconnect = toolbar.addAction("✕ Desconectar")
        self.tb_disconnect.setEnabled(False)
        self.tb_disconnect.triggered.connect(lambda: self.connection_panel._on_disconnect())
        toolbar.addSeparator()
        self.tb_start_log = toolbar.addAction("▶ Logging")
        self.tb_start_log.triggered.connect(self._start_logging)
        self.tb_stop_log = toolbar.addAction("⏹ Parar")
        self.tb_stop_log.setEnabled(False)
        self.tb_stop_log.triggered.connect(self._stop_logging)
        toolbar.addSeparator()
        self.tb_download = toolbar.addAction("\u2B07 Memoria")
        self.tb_download.triggered.connect(self._download_manual_records)
        self.tb_export = toolbar.addAction("\u2913 CSV")
        self.tb_export.triggered.connect(self._export_logging_csv)
        self.tb_import_csv = toolbar.addAction("\u2912 Abrir CSV")
        self.tb_import_csv.triggered.connect(self._import_csv)
        toolbar.addSeparator()
        self.tb_refresh_chart = toolbar.addAction("\u223F Gráfico")
        self.tb_refresh_chart.triggered.connect(lambda: self.chart_panel._refresh_all())

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_conn = QLabel("⚫ Desconectado")
        self.status_conn.setStyleSheet(f"color: {COLORS['status_disconnected']}; padding: 0 12px;")
        self.statusbar.addWidget(self.status_conn)

        self.status_func = QLabel("")
        self.status_func.setStyleSheet(f"color: {COLORS['accent_blue']}; padding: 0 12px;")
        self.statusbar.addWidget(self.status_func)

        self.status_samples = QLabel("Muestras: 0")
        self.status_samples.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 0 12px;")
        self.statusbar.addPermanentWidget(self.status_samples)

        self.status_plugin = QLabel("")
        self.status_plugin.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 0 12px;")
        self.statusbar.addPermanentWidget(self.status_plugin)

    def _connect_signals(self):
        self.connection_panel.connect_requested.connect(self._handle_connect)
        self.connection_panel.disconnect_requested.connect(self._handle_disconnect)
        self.logger_panel.logging_started.connect(self._start_logging)
        self.logger_panel.logging_stopped.connect(self._stop_logging)
        self.logger_panel.clear_requested.connect(self._clear_logging)
        self.logger_panel.export_requested.connect(self._export_logging_csv)
        self.memory_panel.download_manual_requested.connect(self._download_manual_records)
        self.memory_panel.download_timed_requested.connect(self._download_timed_records)
        self.memory_panel.export_manual_requested.connect(self._export_manual_csv)
        self.memory_panel.export_timed_requested.connect(self._export_timed_csv)

    # ── Connection Handling ──────────────────────────────────────

    def _handle_connect(self, params):
        plugin_key = params.pop('instrument', 'victor98a')
        self.plugin = self.plugins.get(plugin_key)
        if not self.plugin:
            QMessageBox.warning(self, "Error", "Plugin no disponible")
            return

        conn_type = getattr(self.plugin, 'connection_type', 'serial')

        if conn_type == 'ble':
            self._connect_ble()
        elif conn_type == 'hid':
            self._connect_hid()
        else:
            self._connect_serial(params)

    def _connect_serial(self, params):
        """Connect via standard serial port."""
        try:
            self.serial_mgr.connect(**params)
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexi\u00F3n", f"No se pudo conectar:\n{e}")
            return

        # Send ONL handshake
        try:
            resp = self.serial_mgr.send_and_receive(self.plugin.build_online_command())
            if not self.plugin.parse_ack_response(resp):
                logger.warning("ONL handshake returned NAK \u2014 continuing anyway")
        except Exception as e:
            logger.warning(f"Handshake error (continuing): {e}")

        port_name = params.get('port', '')
        self._set_connected_ui(f"Serial: {port_name}")

        # Start serial measurement worker
        self.worker = MeasurementWorker(self.serial_mgr, self.plugin, self)
        self.worker.measurement_ready.connect(self._on_measurement)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start(self.logger_panel.get_interval_ms())
        self.statusbar.showMessage("Conexi\u00F3n serial establecida \u2014 leyendo mediciones", 3000)

    def _connect_ble(self):
        """Connect to EEVBlog 121GW via Bluetooth LE."""
        import asyncio
        import subprocess
        import threading

        self.statusbar.showMessage("Preparando Bluetooth LE...", 10000)
        QApplication.processEvents()

        # Disconnect any existing BlueZ connection first
        # (bleak can't see devices already connected by BlueZ)
        try:
            subprocess.run(
                ['bluetoothctl', 'disconnect'],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

        import time
        time.sleep(1)
        self.statusbar.showMessage("Buscando 121GW via Bluetooth LE...", 10000)
        QApplication.processEvents()

        # Create a dedicated event loop for BLE in a background thread
        self._ble_loop = asyncio.new_event_loop()

        # Connect synchronously using the new loop
        try:
            self._ble_loop.run_until_complete(self.plugin.connect_ble())
        except ImportError as e:
            QMessageBox.critical(self, "Dependencia Faltante",
                f"No se puede conectar al 121GW:\n\n{e}")
            return
        except ConnectionError as e:
            QMessageBox.critical(self, "Error BLE",
                f"No se encontr\u00F3 el 121GW:\n\n{e}\n\n"
                "Aseg\u00FArate de que:\n"
                "1. El 121GW est\u00E1 encendido con Bluetooth activo\n"
                "2. El adaptador BT del PC est\u00E1 habilitado\n"
                "3. No est\u00E1 emparejado con otro dispositivo")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error BLE",
                f"Error conectando via Bluetooth:\n{e}")
            return

        # Now run the event loop in a background thread so BLE
        # notifications keep being processed by bleak/D-Bus
        def _run_ble_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._ble_thread = threading.Thread(
            target=_run_ble_loop,
            args=(self._ble_loop,),
            daemon=True
        )
        self._ble_thread.start()

        self._set_connected_ui("BLE: 121GW")

        # Start BLE polling worker — polls the plugin's notification buffer
        self.worker = BLEMeasurementWorker(self.plugin, self)
        self.worker.measurement_ready.connect(self._on_measurement)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start(500)  # Poll at 2Hz
        self.statusbar.showMessage("121GW conectado via Bluetooth LE \u2014 leyendo mediciones", 5000)

    def _connect_hid(self):
        """Connect via USB HID."""
        try:
            self.plugin.connect_hid()
        except ImportError as e:
            QMessageBox.critical(self, "Dependencia Faltante",
                f"No se puede conectar al {self.plugin.name}:\n\n{e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error USB HID",
                f"No se pudo conectar al {self.plugin.name}:\n{e}\n\n"
                "Aseg\u00FArate de que:\n"
                "1. El cable USB est\u00E1 conectado\n"
                "2. Tienes permisos: sudo chmod 666 /dev/hidraw*\n"
                "3. No hay otro programa usando el dispositivo")
            return

        self._set_connected_ui(f"USB HID: {self.plugin.name}")

        # Start HID measurement worker
        self.worker = HIDMeasurementWorker(self.plugin, self)
        self.worker.measurement_ready.connect(self._on_measurement)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start(self.logger_panel.get_interval_ms())
        self.statusbar.showMessage(f"{self.plugin.name} conectado via USB HID \u2014 leyendo mediciones", 5000)

    def _set_connected_ui(self, conn_info):
        """Update all UI elements to connected state."""
        self.connection_panel.set_connected(conn_info)
        self.status_conn.setText(f"\u25CF Conectado: {conn_info}")
        self.status_conn.setStyleSheet(f"color: {COLORS['status_connected']}; padding: 0 12px;")
        self.status_plugin.setText(f"\u25A0 {self.plugin.name}")
        self.connect_action.setEnabled(False)
        self.disconnect_action.setEnabled(True)
        self.tb_connect.setEnabled(False)
        self.tb_disconnect.setEnabled(True)

    def _handle_disconnect(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

        # Disconnect based on connection type
        conn_type = getattr(self.plugin, 'connection_type', 'serial') if self.plugin else 'serial'

        if conn_type == 'ble':
            try:
                import asyncio
                if hasattr(self, '_ble_loop') and self._ble_loop.is_running():
                    # Run disconnect in the BLE thread
                    future = asyncio.run_coroutine_threadsafe(self.plugin.disconnect_ble(), self._ble_loop)
                    try:
                        future.result(timeout=5)
                    except Exception as e:
                        logger.warning(f"Timeout disconnecting BLE: {e}")
                    
                    # Stop the loop and wait for thread
                    self._ble_loop.call_soon_threadsafe(self._ble_loop.stop)
                    if hasattr(self, '_ble_thread'):
                        self._ble_thread.join(timeout=2)
            except Exception as e:
                logger.warning(f"BLE disconnect error: {e}")
        elif conn_type == 'hid':
            try:
                self.plugin.disconnect_hid()
            except Exception as e:
                logger.warning(f"HID disconnect error: {e}")
        else:
            self.serial_mgr.disconnect()

        self.connection_panel.set_disconnected()
        self.live_display.set_idle()
        self.status_conn.setText("\u26AB Desconectado")
        self.status_conn.setStyleSheet(f"color: {COLORS['status_disconnected']}; padding: 0 12px;")
        self.status_func.setText("")
        self.status_plugin.setText("")
        self.connect_action.setEnabled(True)
        self.disconnect_action.setEnabled(False)
        self.tb_connect.setEnabled(True)
        self.tb_disconnect.setEnabled(False)
        self.statusbar.showMessage("Desconectado", 3000)

    # ── Measurement Handling ─────────────────────────────────────

    def _on_measurement(self, data: MeasurementData):
        self.live_display.update_measurement(data)
        self.status_func.setText(f"⚡ {data.function} | {data.range_str}")

        now = datetime.now()
        record = MeasurementRecord(
            timestamp=now, function=data.function, range_str=data.range_str,
            value=data.value, value_str=data.value_str, unit=data.unit,
            secondary_value=data.secondary_value, secondary_str=data.secondary_str,
            secondary_unit=data.secondary_unit, tertiary_value=data.tertiary_value,
            tertiary_str=data.tertiary_str, tertiary_unit=data.tertiary_unit,
            is_overload=data.is_overload, source="live",
        )

        if self.data_logger.is_logging():
            self.data_logger.add_record(record)
            self.logger_panel.add_record(record)
            self.status_samples.setText(f"Muestras: {self.data_logger.sample_count}")
            if not data.is_overload:
                self.chart_panel.add_data_point(now, data.value)
            self._chart_refresh_counter += 1
            if self._chart_refresh_counter % 10 == 0:
                self.chart_panel.refresh_time_chart()

        stats = self.data_logger.get_statistics()
        self.live_display.update_statistics(stats)

    def _on_worker_error(self, error_msg):
        logger.error(f"Worker error: {error_msg}")
        self.statusbar.showMessage(f"⚠ Error: {error_msg}", 5000)

    # ── Logging Control ──────────────────────────────────────────

    def _start_logging(self):
        self.data_logger.start_logging()
        self.start_log_action.setEnabled(False)
        self.stop_log_action.setEnabled(True)
        self.tb_start_log.setEnabled(False)
        self.tb_stop_log.setEnabled(True)
        if self.worker:
            self.worker.setInterval(self.logger_panel.get_interval_ms())
        self.statusbar.showMessage("\u25CF Registrando mediciones...", 3000)

    def _stop_logging(self):
        self.data_logger.stop_logging()
        self.start_log_action.setEnabled(True)
        self.stop_log_action.setEnabled(False)
        self.tb_start_log.setEnabled(True)
        self.tb_stop_log.setEnabled(False)
        self.chart_panel.refresh_time_chart()
        self.chart_panel.refresh_histogram()
        self.statusbar.showMessage("Registro detenido", 3000)

    def _clear_logging(self):
        self.data_logger.clear_live()
        self.logger_panel.clear_table()
        self.chart_panel._clear_all()
        self.status_samples.setText("Muestras: 0")

    # ── Memory Download ──────────────────────────────────────────

    def _download_manual_records(self):
        if not self.serial_mgr.is_connected() or not self.plugin:
            QMessageBox.warning(self, "Error", "No hay conexión activa con el multímetro")
            return
        try:
            resp = self.serial_mgr.send_and_receive(self.plugin.build_manual_record_count_command())
            count = self.plugin.parse_record_count(resp)
            if count is None or count == 0:
                QMessageBox.information(self, "Memoria", "No hay registros manuales o el multímetro no está en modo lectura de registros")
                return
            self.memory_panel.set_record_count(count)
            self.memory_panel.clear_manual_records()
            self.memory_panel.show_progress(count)
            self.data_logger.clear_manual_memory()

            for i in range(1, count + 1):
                resp = self.serial_mgr.send_and_receive(
                    self.plugin.build_manual_record_read_command(i))
                data = self.plugin.parse_measurement(resp)
                if data:
                    record = MeasurementRecord(
                        timestamp=datetime.now(), function=data.function,
                        range_str=data.range_str, value=data.value,
                        value_str=data.value_str, unit=data.unit,
                        secondary_value=data.secondary_value,
                        secondary_str=data.secondary_str,
                        secondary_unit=data.secondary_unit,
                        tertiary_value=data.tertiary_value,
                        tertiary_str=data.tertiary_str,
                        tertiary_unit=data.tertiary_unit,
                        is_overload=data.is_overload,
                        source="manual_memory", record_number=i,
                    )
                    self.data_logger.add_record(record)
                    self.memory_panel.add_manual_record(record)
                self.memory_panel.update_progress(i)
                QApplication.processEvents()

            self.memory_panel.hide_progress()
            self.statusbar.showMessage(f"✅ {count} registros manuales descargados", 5000)
        except Exception as e:
            self.memory_panel.hide_progress()
            QMessageBox.critical(self, "Error", f"Error descargando registros:\n{e}")

    def _download_timed_records(self):
        if not self.serial_mgr.is_connected() or not self.plugin:
            QMessageBox.warning(self, "Error", "No hay conexión activa con el multímetro")
            return
        try:
            resp = self.serial_mgr.send_and_receive(self.plugin.build_timed_record_count_command())
            count = self.plugin.parse_record_count(resp)
            if count is None or count == 0:
                QMessageBox.information(self, "Memoria", "No hay registros temporizados o el multímetro no está en modo lectura")
                return

            resp2 = self.serial_mgr.send_and_receive(self.plugin.build_timed_interval_command())
            interval = self.plugin.parse_interval(resp2)
            self.memory_panel.set_record_count(count)
            self.memory_panel.set_interval(interval)
            self.memory_panel.clear_timed_records()
            self.memory_panel.show_progress(count)
            self.data_logger.clear_timed_memory()

            for i in range(1, count + 1):
                resp = self.serial_mgr.send_and_receive(
                    self.plugin.build_timed_record_read_command(i))
                data = self.plugin.parse_measurement(resp)
                if data:
                    record = MeasurementRecord(
                        timestamp=datetime.now(), function=data.function,
                        range_str=data.range_str, value=data.value,
                        value_str=data.value_str, unit=data.unit,
                        secondary_value=data.secondary_value,
                        secondary_str=data.secondary_str,
                        secondary_unit=data.secondary_unit,
                        tertiary_value=data.tertiary_value,
                        tertiary_str=data.tertiary_str,
                        tertiary_unit=data.tertiary_unit,
                        is_overload=data.is_overload,
                        source="timed_memory", record_number=i,
                    )
                    self.data_logger.add_record(record)
                    self.memory_panel.add_timed_record(record)
                self.memory_panel.update_progress(i)
                QApplication.processEvents()

            self.memory_panel.hide_progress()
            self.statusbar.showMessage(f"✅ {count} registros temporizados descargados", 5000)
        except Exception as e:
            self.memory_panel.hide_progress()
            QMessageBox.critical(self, "Error", f"Error descargando registros:\n{e}")

    # ── CSV Export ───────────────────────────────────────────────

    def _export_logging_csv(self):
        records = self.data_logger.get_live_records()
        if not records:
            QMessageBox.information(self, "Exportar", "No hay datos de logging para exportar")
            return
        self._do_export(records, "logging")

    def _export_manual_csv(self):
        records = self.data_logger.get_manual_memory_records()
        if not records:
            QMessageBox.information(self, "Exportar", "No hay registros manuales para exportar")
            return
        self._do_export(records, "memoria_manual")

    def _export_timed_csv(self):
        records = self.data_logger.get_timed_memory_records()
        if not records:
            QMessageBox.information(self, "Exportar", "No hay registros temporizados para exportar")
            return
        self._do_export(records, "memoria_temporizada")

    def _do_export(self, records, prefix):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"dmmview_{prefix}_{timestamp}.csv"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar a CSV", default_name,
            "CSV Files (*.csv);;All Files (*)")
        if filepath:
            try:
                export_to_csv(filepath, records)
                self.statusbar.showMessage(f"✅ Exportado: {filepath}", 5000)
                QMessageBox.information(self, "Exportar",
                    f"Datos exportados exitosamente:\n{filepath}\n{len(records)} registros")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exportando CSV:\n{e}")

    # ── CSV Import (Offline Viewing) ─────────────────────────────

    def _import_csv(self):
        """Import a CSV file to view and chart previous measurement sessions."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo CSV de registros", "",
            "CSV Files (*.csv);;Todos los archivos (*)")
        if not filepath:
            return

        try:
            records = import_from_csv(filepath)
            if not records:
                QMessageBox.information(self, "Importar CSV",
                    "No se encontraron registros v\u00e1lidos en el archivo.")
                return

            # Clear existing data
            self.data_logger.clear_live()
            self.logger_panel.clear_table()
            self.chart_panel._clear_all()

            # Load records into logger and charts
            valid_count = 0
            for record in records:
                record.source = "live"  # Treat as live for logger display
                self.data_logger.add_record(record)
                self.logger_panel.add_record(record)
                if not record.is_overload and record.value is not None:
                    self.chart_panel.add_data_point(record.timestamp, record.value)
                    valid_count += 1

            # Start logger so records get counted
            if not self.data_logger.is_logging():
                self.data_logger.start_logging()
                # Re-add records since logger was just started
                self.data_logger.stop_logging()

            # Refresh charts
            self.chart_panel.refresh_time_chart()
            values = [r.value for r in records
                      if not r.is_overload and r.value is not None]
            self.chart_panel.refresh_histogram(values)

            # Update statistics display
            stats = self.data_logger.get_statistics(records)
            self.live_display.update_statistics(stats)

            # Update status
            self.status_samples.setText(f"Muestras: {len(records)}")
            import os
            filename = os.path.basename(filepath)
            self.statusbar.showMessage(
                f"\u2713 Importado: {filename} \u2014 {len(records)} registros, "
                f"{valid_count} con valores v\u00e1lidos", 8000)

            # Show the last measurement on the live display if available
            valid_records = [r for r in records if not r.is_overload]
            if valid_records:
                last = valid_records[-1]
                from plugins.base_plugin import MeasurementData
                last_data = MeasurementData(
                    function=last.function, range_str=last.range_str,
                    value=last.value, value_str=last.value_str,
                    unit=last.unit,
                    secondary_value=last.secondary_value,
                    secondary_str=last.secondary_str,
                    secondary_unit=last.secondary_unit,
                    tertiary_value=last.tertiary_value,
                    tertiary_str=last.tertiary_str,
                    tertiary_unit=last.tertiary_unit,
                    is_overload=last.is_overload,
                )
                self.live_display.update_measurement(last_data)

            # Switch to Logger tab to show the imported data
            self.tabs.setCurrentIndex(1)

            QMessageBox.information(self, "Importar CSV",
                f"Archivo importado exitosamente:\n{filepath}\n\n"
                f"Registros: {len(records)}\n"
                f"Valores v\u00e1lidos: {valid_count}\n\n"
                f"Los datos est\u00e1n disponibles en las pesta\u00f1as de\n"
                f"Registro de Datos y Gr\u00e1ficos.")

        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Error importando CSV:\n{e}")

    # ── About Dialog ─────────────────────────────────────────────

    def _show_instructions(self):
        QMessageBox.about(self, "Instrucciones de Uso",
            "<h2>Instrucciones de DMMView</h2>"
            "<p><b>Conexión:</b> Seleccione su multímetro, configure el puerto (si aplica) y presione Conectar.</p>"
            "<p><b>Medición en Vivo:</b> Muestra el último valor leído de forma destacada, incluyendo estadísticas básicas (mín, máx, promedio).</p>"
            "<p><b>Registro de Datos (Logging):</b> Permite grabar las lecturas en tiempo real y exportarlas a un archivo CSV para análisis posterior. Utilice los botones de Inicio/Parada.</p>"
            "<p><b>Gráficos:</b> Visualice la tendencia temporal de las mediciones y la distribución en un histograma. Haga uso de las herramientas de Zoom para enfocar un área, y pase el cursor (hover) para ver el valor exacto en un punto dado.</p>"
            "<p><b>Memoria del DMM:</b> Permite descargar los registros guardados internamente en los multímetros que soportan esta función (como registros manuales o temporizados).</p>")

    def _show_changelog(self):
        QMessageBox.about(self, "Cambios de Versión",
            f"<h2>Novedades en DMMView v{VERSION}</h2>"
            "<ul>"
            "<li>Se añadió soporte oficial para <b>Windows 10/11</b> con fuentes optimizadas (Segoe UI).</li>"
            "<li>Se incorporó un nuevo <b>icono profesional</b> para la aplicación y el ejecutable.</li>"
            "<li>Se corrigieron fallos de estabilidad al cambiar entre diferentes instrumentos.</li>"
            "<li>Se tradujeron las configuraciones de los gráficos al español.</li>"
            "<li>Se optimizó el tamaño de los controles en el panel de gráficos.</li>"
            "<li>Se añadieron implementaciones para los multímetros <b>UNI-T UT-181</b>, <b>OWON XDM1041</b> y <b>OWON XDM3041</b>.</li>"
            "</ul>")

    def _show_about(self):
        QMessageBox.about(self, "Acerca de DMMView",
            f"<h2>DMMView v{VERSION}</h2>"
            "<p>Dedicado al Gran Yaki.</p>"
            "<p>Desarrollo por Tio Vito.</p>"
            "<p>Aplicación de visualización para multímetros digitales.</p>"
            "<p><b>Instrumentos soportados:</b></p>"
            "<ul>"
            "<li>VICTOR 98A+ (Serial, DMMVIEW_G Protocol)</li>"
            "<li>Fluke 287/289 (IR Serial, ASCII Commands)</li>"
            "<li>UNI-T UT-61E+ (USB HID, CP2110)</li>"
            "<li>Brymen BM250s (IR Serial, LCD Segments)</li>"
            "<li>EEVBlog 121GW (BLE, 19-byte Packets)</li>"
            "<li>UNI-T UT-181 (Serial)</li>"
            "<li>OWON XDM1041/XDM1241 (SCPI Serial)</li>"
            "<li>OWON XDM3041/XDM3051 (SCPI Serial)</li>"
            "</ul>"
            "<p><b>Funcionalidades:</b></p>"
            "<ul>"
            "<li>Medición en tiempo real</li>"
            "<li>Registro de datos (logging) con exportación CSV</li>"
            "<li>Importación de CSV para análisis offline</li>"
            "<li>Gráficos temporales interactivos (Zoom/Hover) e histogramas</li>"
            "<li>Exportación de gráficos (PNG, JPG, PDF)</li>"
            "<li>Descarga de memoria del instrumento</li>"
            "</ul>"
            "<p>Desarrollado para Linux Mint 22.3</p>"
            "<p>Python + PyQt6 + Matplotlib</p>")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        self.serial_mgr.disconnect()
        event.accept()
