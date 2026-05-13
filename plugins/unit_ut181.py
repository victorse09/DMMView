"""
DMMView Plugin - UNI-T UT-181A
Communication via USB HID (Silicon Labs CP2110 bridge).
"""

import logging
from typing import Optional, List, Dict
from plugins.base_plugin import BaseDMMPlugin, SerialParams, MeasurementData

logger = logging.getLogger("DMMView.UT181A")

class UnitUT181Plugin(BaseDMMPlugin):
    """Plugin for UNI-T UT-181A Digital Multimeter (USB HID)."""

    CP2110_VID = 0x10C4
    CP2110_PID = 0xEA80

    def __init__(self):
        super().__init__()
        self._name = "UNI-T UT-181A"
        self._manufacturer = "UNI-T"
        self._model = "UT-181A"
        self._serial_params = SerialParams(
            baudrate=9600, databits=8, stopbits=1, parity='N', timeout=2.0
        )
        self._hid_device = None
        self._connection_type = 'hid'

    @property
    def name(self) -> str:
        return self._name

    @property
    def manufacturer(self) -> str:
        return self._manufacturer

    @property
    def model(self) -> str:
        return self._model

    @property
    def description(self) -> str:
        return "UNI-T UT-181A DMM - USB HID (CP2110)"

    @property
    def serial_params(self) -> SerialParams:
        return self._serial_params

    @property
    def connection_type(self) -> str:
        return self._connection_type

    # ── HID Connection ───────────────────────────────────────────

    def connect_hid(self):
        """Connect to the UT-181A via USB HID."""
        try:
            import hid
        except ImportError:
            raise ImportError(
                "La libreria 'hidapi' es necesaria para el UT-181A.\n"
                "Instalar con: pip install hidapi"
            )
        self._hid_device = hid.device()
        self._hid_device.open(self.CP2110_VID, self.CP2110_PID)
        # Initialize CP2110 UART bridge
        self._hid_device.send_feature_report([0x41, 0x01])  # Enable UART
        self._hid_device.send_feature_report([  # 9600 8N1
            0x50, 0x00, 0x00, 0x25, 0x80, 0x00, 0x00, 0x03, 0x00, 0x00
        ])
        self._hid_device.send_feature_report([0x43, 0x02])  # Purge FIFOs
        logger.info("UT-181A connected via USB HID")

    def disconnect_hid(self):
        """Disconnect HID device."""
        if self._hid_device:
            self._hid_device.close()
            self._hid_device = None
            logger.info("UT-181A disconnected")

    def is_connected_hid(self):
        return self._hid_device is not None

    def read_measurement_hid(self):
        """Read a measurement directly via HID."""
        if not self._hid_device:
            return None
        try:
            # TODO: Add specific command to request data for UT-181A
            # This is a placeholder for the actual request command if needed
            # self._hid_device.write([len(cmd)] + cmd)
            
            data = self._hid_device.read(64, timeout_ms=2000)
            if data:
                return self.parse_measurement(bytes(data))
        except Exception as e:
            logger.error(f"HID read error: {e}")
        return None

    # ── Standard Plugin Interface (for serial fallback) ──────────

    def build_online_command(self) -> bytes:
        return b''

    def build_reset_command(self) -> bytes:
        return b''

    def build_read_command(self) -> bytes:
        return b''

    def build_select_function_command(self, func_code: int) -> bytes:
        return b''

    def build_range_command(self, auto: bool, range_code: int) -> bytes:
        return b''

    def build_manual_record_count_command(self) -> bytes:
        return b''

    def build_manual_record_read_command(self, record_num: int) -> bytes:
        return b''

    def build_timed_record_count_command(self) -> bytes:
        return b''

    def build_timed_interval_command(self) -> bytes:
        return b''

    def build_timed_record_read_command(self, record_num: int) -> bytes:
        return b''

    def parse_ack_response(self, data: bytes) -> bool:
        return True

    def parse_measurement(self, data: bytes) -> Optional[MeasurementData]:
        # Placeholder for actual payload parsing
        if not data or len(data) < 5:
            return None
        return MeasurementData(
            function="HID",
            range_str="Auto",
            value=0.0,
            value_str="0.0",
            unit="",
            raw_bytes=data
        )

    def parse_record_count(self, data: bytes) -> Optional[int]:
        return None

    def parse_interval(self, data: bytes) -> Optional[int]:
        return None

    def get_available_functions(self) -> List[Dict]:
        return []

    def get_function_ranges(self, func_code: str) -> List[Dict]:
        return []
