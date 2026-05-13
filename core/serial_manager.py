"""
DMMView - Serial Communication Manager
Handles serial port communication with thread-safe operations.
"""

import serial
import serial.tools.list_ports
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

logger = logging.getLogger("DMMView.Serial")


class SerialReaderThread(QThread):
    """Background thread for continuously reading serial data."""
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, serial_port, interval_ms=200):
        super().__init__()
        self._serial = serial_port
        self._interval = interval_ms / 1000.0
        self._running = False
        self._mutex = QMutex()

    def run(self):
        self._running = True
        while self._running:
            try:
                if self._serial and self._serial.is_open:
                    if self._serial.in_waiting > 0:
                        data = self._serial.read(self._serial.in_waiting)
                        if data:
                            self.data_received.emit(data)
                    time.sleep(self._interval)
                else:
                    self.connection_lost.emit()
                    break
            except serial.SerialException as e:
                logger.error(f"Serial read error: {e}")
                self.error_occurred.emit(str(e))
                self.connection_lost.emit()
                break
            except Exception as e:
                logger.error(f"Unexpected read error: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(0.5)

    def stop(self):
        self._running = False
        self.wait(2000)


class SerialManager:
    """Manages serial port connections and communication."""

    def __init__(self):
        self._serial: serial.Serial | None = None
        self._reader_thread: SerialReaderThread | None = None
        self._mutex = QMutex()
        self._connected = False

    @staticmethod
    def list_ports():
        """List available serial ports with descriptions."""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer or '',
                'vid': port.vid,
                'pid': port.pid,
            })
        return ports

    def connect(self, port, baudrate=9600, databits=8, stopbits=1,
                parity='N', timeout=1.0):
        """Open serial connection with specified parameters."""
        locker = QMutexLocker(self._mutex)
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()

            parity_map = {
                'N': serial.PARITY_NONE,
                'E': serial.PARITY_EVEN,
                'O': serial.PARITY_ODD,
            }
            stopbits_map = {
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO,
            }

            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=databits,
                stopbits=stopbits_map.get(stopbits, serial.STOPBITS_ONE),
                parity=parity_map.get(parity, serial.PARITY_NONE),
                timeout=timeout,
                write_timeout=timeout,
            )
            self._connected = True
            logger.info(f"Connected to {port} @ {baudrate} bps")
            return True
        except serial.SerialException as e:
            logger.error(f"Connection failed: {e}")
            self._connected = False
            raise

    def disconnect(self):
        """Close serial connection."""
        locker = QMutexLocker(self._mutex)
        if self._reader_thread:
            self._reader_thread.stop()
            self._reader_thread = None
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Serial port disconnected")
        self._connected = False

    def is_connected(self):
        """Check if serial port is connected and open."""
        return self._connected and self._serial is not None and self._serial.is_open

    def send_command(self, command_bytes):
        """Send raw bytes to serial port. Returns True on success."""
        locker = QMutexLocker(self._mutex)
        if not self.is_connected():
            raise ConnectionError("Serial port not connected")
        try:
            self._serial.write(command_bytes)
            self._serial.flush()
            return True
        except serial.SerialException as e:
            logger.error(f"Send error: {e}")
            raise

    def read_response(self, timeout=2.0):
        """Read response from serial port until CR received."""
        if not self.is_connected():
            raise ConnectionError("Serial port not connected")
        try:
            self._serial.timeout = timeout
            response = b''
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._serial.in_waiting > 0:
                    byte = self._serial.read(1)
                    response += byte
                    # CR (0x0D) signals end of response
                    if byte == b'\r':
                        break
                else:
                    time.sleep(0.01)
            return response
        except serial.SerialException as e:
            logger.error(f"Read error: {e}")
            raise

    def send_and_receive(self, command_bytes, timeout=2.0):
        """Send command and wait for response."""
        self.send_command(command_bytes)
        time.sleep(0.05)  # Small delay before reading
        return self.read_response(timeout)

    def start_continuous_read(self, interval_ms=200):
        """Start background reading thread."""
        if self._reader_thread and self._reader_thread.isRunning():
            self._reader_thread.stop()
        self._reader_thread = SerialReaderThread(self._serial, interval_ms)
        return self._reader_thread

    def stop_continuous_read(self):
        """Stop background reading thread."""
        if self._reader_thread:
            self._reader_thread.stop()
            self._reader_thread = None

    @property
    def serial_port(self):
        return self._serial
