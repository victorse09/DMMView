"""
DMMView - UNI-T UT-61E+ Plugin
Communication via USB HID (Silicon Labs CP2110 bridge).
VID:PID = 10C4:EA80
Binary protocol: AB CD header, 19-byte payload.
Reference: github.com/ljakob/unit_ut61eplus
"""

import logging
from plugins.base_plugin import BaseDMMPlugin, SerialParams, MeasurementData

logger = logging.getLogger("DMMView.UT61E+")

# Mode table (byte 0 of payload)
MODE_TABLE = [
    'ACV', 'ACmV', 'DCV', 'DCmV', 'Hz', '%', 'OHM', 'CONT',
    'DIODE', 'CAP', '\u00B0C', '\u00B0F', 'DC\u00B5A', 'AC\u00B5A',
    'DCmA', 'ACmA', 'DCA', 'ACA', 'HFE', 'Live', 'NCV',
    'LozV', 'ACA', 'DCA', 'LPF', 'AC/DC', 'LPF', 'AC+DC',
    'LPF', 'AC+DC2', 'INRUSH',
]

# Units based on mode and range (from vendor JSON)
UNITS = {
    '%': {'0': '%'},
    'AC+DC': {'1': 'A'}, 'AC+DC2': {'1': 'A'},
    'AC/DC': {'0': 'V', '1': 'V', '2': 'V', '3': 'V'},
    'ACA': {'1': 'A'}, 'ACV': {'0': 'V', '1': 'V', '2': 'V', '3': 'V'},
    'ACmA': {'0': 'mA', '1': 'mA'}, 'ACmV': {'0': 'mV'},
    'AC\u00B5A': {'0': '\u00B5A', '1': '\u00B5A'},
    'CAP': {'0': 'nF', '1': 'nF', '2': '\u00B5F', '3': '\u00B5F',
            '4': '\u00B5F', '5': 'mF', '6': 'mF', '7': 'mF'},
    'CONT': {'0': '\u03A9'}, 'DCA': {'1': 'A'},
    'DCV': {'0': 'V', '1': 'V', '2': 'V', '3': 'V'},
    'DCmA': {'0': 'mA', '1': 'mA'}, 'DCmV': {'0': 'mV'},
    'DC\u00B5A': {'0': '\u00B5A', '1': '\u00B5A'},
    'DIODE': {'0': 'V'},
    'Hz': {'0': 'Hz', '1': 'Hz', '2': 'kHz', '3': 'kHz',
           '4': 'kHz', '5': 'MHz', '6': 'MHz', '7': 'MHz'},
    'LPF': {'0': 'V', '1': 'V', '2': 'V', '3': 'V'},
    'LozV': {'0': 'V', '1': 'V', '2': 'V', '3': 'V'},
    'OHM': {'0': '\u03A9', '1': 'k\u03A9', '2': 'k\u03A9', '3': 'k\u03A9',
            '4': 'M\u03A9', '5': 'M\u03A9', '6': 'M\u03A9'},
    '\u00B0C': {'0': '\u00B0C', '1': '\u00B0C'},
    '\u00B0F': {'0': '\u00B0F', '1': '\u00B0F'},
    'HFE': {'0': 'B'}, 'NCV': {'0': 'NCV'},
    'INRUSH': {'1': 'A'}, 'Live': {'0': ''},
}

OVERLOAD_STRINGS = {'.OL', 'O.L', 'OL.', 'OL', '-.OL', '-O.L', '-OL.', '-OL'}

# Unit exponent multipliers
EXPONENTS = {'M': 1e6, 'k': 1e3, 'm': 1e-3, '\u00B5': 1e-6, 'n': 1e-9}


class UT61EPlusPlugin(BaseDMMPlugin):
    """Plugin for UNI-T UT-61E+ Digital Multimeter (USB HID)."""

    CP2110_VID = 0x10C4
    CP2110_PID = 0xEA80

    HEADER = bytes.fromhex('AB CD')
    CMD_GET_NAME = bytes.fromhex('AB CD 03 5F 01 DA')
    CMD_SEND_DATA = bytes.fromhex('AB CD 03 5E 01 D9')

    def __init__(self):
        super().__init__()
        self._name = "UNI-T UT-61E+"
        self._manufacturer = "UNI-T"
        self._model = "UT-61E+"
        self._serial_params = SerialParams(
            baudrate=9600, databits=8, stopbits=1, parity='N', timeout=2.0
        )
        self._hid_device = None
        self._connection_type = 'hid'

    @property
    def name(self):
        return self._name

    @property
    def manufacturer(self):
        return self._manufacturer

    @property
    def model(self):
        return self._model

    @property
    def description(self):
        return "UNI-T UT-61E+ DMM - USB HID (CP2110), binary protocol"

    @property
    def serial_params(self):
        return self._serial_params

    @property
    def connection_type(self):
        """Returns 'hid' — this device uses USB HID, not serial."""
        return self._connection_type

    # ── HID Connection ───────────────────────────────────────────

    def connect_hid(self):
        """Connect to the UT-61E+ via USB HID."""
        try:
            import hid
        except ImportError:
            raise ImportError(
                "La libreria 'hidapi' es necesaria para el UT-61E+.\n"
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
        logger.info("UT-61E+ connected via USB HID")

    def disconnect_hid(self):
        """Disconnect HID device."""
        if self._hid_device:
            self._hid_device.close()
            self._hid_device = None
            logger.info("UT-61E+ disconnected")

    def is_connected_hid(self):
        return self._hid_device is not None

    def read_measurement_hid(self):
        """Read a measurement directly via HID. Returns MeasurementData."""
        if not self._hid_device:
            return None
        try:
            # Send read command
            cmd = list(self.CMD_SEND_DATA)
            self._hid_device.write([len(cmd)] + cmd)
            # Read response
            payload = self._read_hid_response()
            if payload:
                return self._parse_payload(payload)
        except Exception as e:
            logger.error(f"HID read error: {e}")
        return None

    def _read_hid_response(self):
        """Read and validate a response packet from HID."""
        state = 0  # 0=init, 1=AB, 2=CD, 3=reading
        buf = None
        index = 0
        checksum = 0

        max_iterations = 100
        for _ in range(max_iterations):
            data = self._hid_device.read(64, timeout_ms=2000)
            if not data:
                return None
            for b in data[1:]:  # Skip first byte (HID length)
                if state < 3 or (buf and index + 2 < len(buf)):
                    checksum += b
                if state == 0 and b == 0xAB:
                    state = 1
                elif state == 1 and b == 0xCD:
                    state = 2
                elif state == 2:
                    buf = bytearray(b)
                    index = 0
                    state = 3
                elif state == 3:
                    buf[index] = b
                    index += 1
                    if index == len(buf):
                        recv_sum = (buf[-2] << 8) + buf[-1]
                        if checksum != recv_sum:
                            logger.warning("HID checksum mismatch")
                            return None
                        return bytes(buf[:-2])
                else:
                    state = 0
                    checksum = 0
        return None

    # ── Standard Plugin Interface (for serial fallback) ──────────

    def build_online_command(self):
        return self.CMD_GET_NAME

    def build_read_command(self):
        return self.CMD_SEND_DATA

    def build_reset_command(self):
        return b''

    def build_select_function_command(self):
        return b''

    def build_range_command(self):
        return b''

    def build_manual_record_count_command(self):
        return b''

    def build_manual_record_read_command(self, index):
        return b''

    def build_timed_record_count_command(self):
        return b''

    def build_timed_interval_command(self):
        return b''

    def build_timed_record_read_command(self, index):
        return b''

    def parse_ack_response(self, response):
        if not response:
            return False
        return True

    def parse_measurement(self, response):
        """Parse measurement from raw bytes."""
        if not response or len(response) < 14:
            return None
        return self._parse_payload(response)

    def parse_record_count(self, response):
        return 0  # UT-61E+ has no memory download

    def parse_interval(self, response):
        return None

    # ── Payload Parsing ──────────────────────────────────────────

    def _parse_payload(self, data):
        """
        Parse 14-byte measurement payload.
        Byte 0:    mode index
        Byte 1:    range (ASCII char)
        Bytes 2-8: display digits (7 ASCII chars)
        Bytes 9-10: progress
        Byte 11:   flags1 (Max/Min/Hold/Rel)
        Byte 12:   flags2 (Auto/Battery/HVWarning)
        Byte 13:   flags3 (DC/PeakMax/PeakMin/BarPol)
        """
        if len(data) < 14:
            return None

        try:
            mode_idx = data[0]
            if mode_idx >= len(MODE_TABLE):
                mode = f'Mode_{mode_idx}'
            else:
                mode = MODE_TABLE[mode_idx]

            range_char = chr(data[1]) if 0x20 <= data[1] <= 0x7E else '0'
            display = data[2:9].decode('ascii', errors='replace').replace(' ', '')

            # Check overload
            is_overload = display in OVERLOAD_STRINGS

            # Get unit
            mode_units = UNITS.get(mode, {})
            unit = mode_units.get(range_char, '')

            # Parse value
            if is_overload:
                value = float('inf')
                value_str = 'OL'
            else:
                try:
                    value = float(display)
                    value_str = display
                except ValueError:
                    value = 0.0
                    value_str = display
                    is_overload = True

            # Parse flags
            flags1 = data[11] if len(data) > 11 else 0
            flags2 = data[12] if len(data) > 12 else 0
            flags3 = data[13] if len(data) > 13 else 0

            is_hold = bool(flags1 & 0x02)
            is_rel = bool(flags1 & 0x01)
            is_auto = not bool(flags2 & 0x04)
            is_dc = bool(flags3 & 0x08)

            range_str = f"Range {range_char}" + (" Auto" if is_auto else " Manual")

            # Build secondary info string
            sec_parts = []
            if is_hold:
                sec_parts.append("HOLD")
            if is_rel:
                sec_parts.append("REL")
            if bool(flags1 & 0x08):
                sec_parts.append("MAX")
            if bool(flags1 & 0x04):
                sec_parts.append("MIN")
            secondary_str = ', '.join(sec_parts) if sec_parts else None

            return MeasurementData(
                function=mode,
                range_str=range_str,
                value=value,
                value_str=value_str,
                unit=unit,
                secondary_str=secondary_str,
                secondary_unit=None,
                is_overload=is_overload,
            )

        except Exception as e:
            logger.error(f"UT-61E+ parse error: {e}")
            return None

    # ── Available Functions ──────────────────────────────────────

    def get_available_functions(self):
        return list(set(MODE_TABLE))

    def get_available_ranges(self, function):
        mode_units = UNITS.get(function, {})
        return list(mode_units.keys()) if mode_units else ['Auto']

    def get_function_ranges(self, func_code):
        mode_units = UNITS.get(func_code, {})
        return [{'name': f'Range {k}', 'code': k} for k in mode_units] if mode_units else [{'name': 'Auto', 'code': 0}]

    @staticmethod
    def detect_device():
        """Check if a UT-61E+ is connected via USB."""
        try:
            import hid
            devices = hid.enumerate(UT61EPlusPlugin.CP2110_VID,
                                     UT61EPlusPlugin.CP2110_PID)
            return len(devices) > 0
        except ImportError:
            return False
