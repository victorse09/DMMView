"""
DMMView - Brymen BM250s Plugin
Communication via IR optical serial (BRUA-20X cable) at 9600/8N1.
Binary protocol: 15-byte LCD segment frames.
Activation: Hold HOLD button while powering on the meter.
Reference: BM250-BM250s-6000-count-digital-multimeters-r1.pdf, sigrok brymen-bm25x driver.
"""

import logging
from plugins.base_plugin import BaseDMMPlugin, SerialParams, MeasurementData

logger = logging.getLogger("DMMView.BM250s")

# LCD 7-segment digit decoding (segment bits → digit)
# Standard 7-segment: a=bit0, b=bit1, c=bit2, d=bit3, e=bit4, f=bit5, g=bit6
SEGMENT_DIGITS = {
    0x7D: '0', 0x05: '1', 0x5B: '2', 0x1F: '3',
    0x27: '4', 0x3E: '5', 0x7E: '6', 0x15: '7',
    0x7F: '8', 0x3F: '9',
    # Alternate segment mappings (varies by manufacturer)
    0x00: ' ', 0x68: 'L',
    # Common overload patterns
    0x5C: '0', 0x44: '1', 0x6A: '2', 0x4E: '3',
    0x46: '4', 0x0E: '5', 0x2E: '6', 0x45: '7',
    0x6E: '8', 0x4F: '9',
}

# Function/mode byte mapping
MODE_MAP = {
    0x00: 'DCV', 0x01: 'ACV', 0x02: 'DCA', 0x03: 'ACA',
    0x04: 'OHM', 0x05: 'CAP', 0x06: 'Hz', 0x07: 'DUTY',
    0x08: '\u00B0C', 0x09: '\u00B0F', 0x0A: 'DIODE', 0x0B: 'CONT',
    0x0C: 'HFE', 0x0D: 'LOGIC', 0x0E: 'DBM', 0x0F: 'BEEP',
}

# Unit mapping based on range
UNIT_MAP = {
    'DCV': {0: 'mV', 1: 'V', 2: 'V', 3: 'V', 4: 'V'},
    'ACV': {0: 'mV', 1: 'V', 2: 'V', 3: 'V', 4: 'V'},
    'DCA': {0: '\u00B5A', 1: '\u00B5A', 2: 'mA', 3: 'mA', 4: 'A', 5: 'A'},
    'ACA': {0: '\u00B5A', 1: '\u00B5A', 2: 'mA', 3: 'mA', 4: 'A', 5: 'A'},
    'OHM': {0: '\u03A9', 1: 'k\u03A9', 2: 'k\u03A9', 3: 'k\u03A9', 4: 'M\u03A9', 5: 'M\u03A9'},
    'CAP': {0: 'nF', 1: 'nF', 2: '\u00B5F', 3: '\u00B5F', 4: '\u00B5F', 5: 'mF'},
    'Hz': {0: 'Hz', 1: 'Hz', 2: 'kHz', 3: 'kHz', 4: 'MHz'},
    'DUTY': {0: '%'},
    '\u00B0C': {0: '\u00B0C'}, '\u00B0F': {0: '\u00B0F'},
    'DIODE': {0: 'V'}, 'CONT': {0: '\u03A9'},
    'HFE': {0: ''}, 'DBM': {0: 'dBm'},
}

# Decimal point positions per range (digits from left, 0=none)
DP_POSITIONS = {
    'DCV':  {0: 1, 1: 1, 2: 2, 3: 3, 4: 0},
    'ACV':  {0: 1, 1: 1, 2: 2, 3: 3, 4: 0},
    'DCA':  {0: 2, 1: 0, 2: 1, 3: 2, 4: 2, 5: 0},
    'ACA':  {0: 2, 1: 0, 2: 1, 3: 2, 4: 2, 5: 0},
    'OHM':  {0: 1, 1: 1, 2: 2, 3: 3, 4: 1, 5: 2},
    'CAP':  {0: 2, 1: 0, 2: 1, 3: 2, 4: 0, 5: 1},
    'Hz':   {0: 1, 1: 2, 2: 1, 3: 2, 4: 1},
}


class BrymenBM250sPlugin(BaseDMMPlugin):
    """Plugin for Brymen BM250s Digital Multimeter."""

    FRAME_LENGTH = 15
    FRAME_START = 0x02

    def __init__(self):
        super().__init__()
        self._name = "Brymen BM250s"
        self._manufacturer = "Brymen"
        self._model = "BM250s"
        self._serial_params = SerialParams(
            baudrate=9600, databits=8, stopbits=1, parity='N', timeout=1.0
        )

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
        return "Brymen BM250s DMM - IR Serial (BRUA-20X), 15-byte LCD segments, 9600/8N1"

    @property
    def serial_params(self):
        return self._serial_params

    # ── Command Building ─────────────────────────────────────────
    # BM250s is passive — it streams data, no commands needed

    def build_online_command(self):
        return b''  # No handshake — meter streams when enabled

    def build_read_command(self):
        return b''  # Passive — just read from the stream

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

    # ── Response Parsing ─────────────────────────────────────────

    def parse_ack_response(self, response):
        """BM250s has no handshake — return True if data is flowing."""
        return response is not None and len(response) > 0

    def parse_measurement(self, response):
        """Parse a 15-byte binary frame from the BM250s."""
        if not response:
            return None

        # Find frame start byte (0x02)
        frame = self._find_frame(response)
        if not frame:
            return None

        return self._parse_frame(frame)

    def parse_record_count(self, response):
        return 0  # No memory download support

    def parse_interval(self, response):
        return None

    # ── Frame Detection ──────────────────────────────────────────

    def _find_frame(self, data):
        """Find a complete 15-byte frame starting with 0x02."""
        if isinstance(data, (bytes, bytearray)):
            for i in range(len(data) - self.FRAME_LENGTH + 1):
                if data[i] == self.FRAME_START:
                    frame = data[i:i + self.FRAME_LENGTH]
                    if self._validate_frame(frame):
                        return frame
        return None

    def _validate_frame(self, frame):
        """Validate frame length and basic structure."""
        if len(frame) != self.FRAME_LENGTH:
            return False
        if frame[0] != self.FRAME_START:
            return False
        return True

    def read_frame_from_serial(self, serial_mgr):
        """Read a complete frame from the serial stream."""
        if not serial_mgr or not serial_mgr.is_connected():
            return None
        try:
            # Read until we get a frame start byte
            buf = bytearray()
            for _ in range(100):  # Max attempts
                byte = serial_mgr._serial.read(1)
                if not byte:
                    continue
                if byte[0] == self.FRAME_START:
                    buf = bytearray([self.FRAME_START])
                    remaining = serial_mgr._serial.read(self.FRAME_LENGTH - 1)
                    if remaining and len(remaining) == self.FRAME_LENGTH - 1:
                        buf.extend(remaining)
                        return bytes(buf)
        except Exception as e:
            logger.error(f"BM250s frame read error: {e}")
        return None

    # ── Frame Parsing ────────────────────────────────────────────

    def _parse_frame(self, frame):
        """
        Parse 15-byte LCD segment frame.
        Byte 0:    Start (0x02)
        Bytes 1-2: Status/mode flags
        Bytes 3-10: LCD digit segments (4 digits x 2 bytes each)
        Bytes 11-12: Additional flags (bargraph, etc.)
        Bytes 13-14: Status/checksum
        """
        try:
            # Mode and status flags
            status1 = frame[1]
            status2 = frame[2]

            # Determine function from status flags
            is_ac = bool(status1 & 0x08)
            is_dc = bool(status1 & 0x04)
            is_auto = bool(status1 & 0x02)

            # Determine measurement function
            func_byte = (status2 >> 4) & 0x0F
            func_name = MODE_MAP.get(func_byte, f'Mode_{func_byte:02X}')

            # Range
            range_byte = status2 & 0x0F

            # Parse 4 display digits from bytes 3-10
            sign_negative = bool(frame[3] & 0x08)
            digits = []
            dp_position = -1

            for i in range(4):
                byte_hi = frame[3 + i * 2]
                byte_lo = frame[4 + i * 2]

                # Combine segment bits
                seg = ((byte_hi & 0x07) << 4) | (byte_lo & 0x0F)

                # Check decimal point
                if byte_lo & 0x80:
                    dp_position = i

                # Decode digit
                digit = SEGMENT_DIGITS.get(seg, '?')
                digits.append(digit)

            # Build display string
            display = ''.join(digits).strip()

            # Insert decimal point
            if dp_position >= 0 and dp_position < len(digits):
                display_chars = list(digits)
                display_chars.insert(dp_position + 1, '.')
                display = ''.join(display_chars).strip()

            # Alternately, use the range-based decimal position
            if dp_position < 0 and func_name in DP_POSITIONS:
                dp_pos = DP_POSITIONS[func_name].get(range_byte, 0)
                if dp_pos > 0 and dp_pos < len(digits):
                    display_chars = list(digits)
                    display_chars.insert(dp_pos, '.')
                    display = ''.join(display_chars).strip()

            if sign_negative:
                display = '-' + display

            # Check overload
            is_overload = 'OL' in display.upper() or '?' in display

            # Get unit
            unit = ''
            if func_name in UNIT_MAP:
                unit = UNIT_MAP[func_name].get(range_byte, '')

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

            # Build range string
            range_str = f"Range {range_byte}" + (" Auto" if is_auto else "")

            # AC/DC indicator
            if is_ac and 'AC' not in func_name:
                func_name += ' AC'
            elif is_dc and 'DC' not in func_name:
                func_name += ' DC'

            return MeasurementData(
                function=func_name,
                range_str=range_str,
                value=value,
                value_str=value_str,
                unit=unit,
                is_overload=is_overload,
            )

        except Exception as e:
            logger.error(f"BM250s parse error: {e}")
            return None

    # ── Available Functions ──────────────────────────────────────

    def get_available_functions(self):
        return [
            'DCV', 'ACV', 'DCA', 'ACA',
            '\u03A9 (Resistance)', 'Capacitance', 'Hz', 'Duty Cycle',
            '\u00B0C', '\u00B0F', 'Diode', 'Continuity',
            'HFE', 'dBm',
        ]

    def get_available_ranges(self, function):
        return ['Auto']  # BM250s auto-ranges primarily

    def get_function_ranges(self, func_code):
        return [{'name': 'Auto', 'code': 0}]
