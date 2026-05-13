"""
DMMView - Fluke 287/289 Plugin
Communication via IR-Serial (IR189USB cable) at 115200/8N1.
ASCII command protocol: QM, QDDA, ID, RI.
Reference: Fluke 287/289 Remote Interface Specification.
"""

import logging
from plugins.base_plugin import BaseDMMPlugin, SerialParams, MeasurementData

logger = logging.getLogger("DMMView.Fluke287")

# Base unit codes from Fluke spec
UNIT_MAP = {
    'VDC': 'V DC', 'VAC': 'V AC', 'VAC+DC': 'V AC+DC',
    'AAC': 'A AC', 'ADC': 'A DC', 'AAC+DC': 'A AC+DC',
    'OHM': '\u03A9', 'SIE': 'S', 'FAR': 'F',
    'HZ': 'Hz', 'PCT': '%', 'CEL': '\u00B0C', 'FAH': '\u00B0F',
    'DBM': 'dBm', 'DBV': 'dBV', 'NONE': '',
}

# Unit multiplier codes
MULTIPLIER_MAP = {
    'NONE': 1, 'NANO': 1e-9, 'MICRO': 1e-6,
    'MILLI': 1e-3, 'KILO': 1e3, 'MEGA': 1e6,
    'GIGA': 1e9,
}

MULTIPLIER_PREFIX = {
    'NONE': '', 'NANO': 'n', 'MICRO': '\u00B5',
    'MILLI': 'm', 'KILO': 'k', 'MEGA': 'M', 'GIGA': 'G',
}

# Reading state codes
READING_STATE = {
    '0': 'Normal', '1': 'Blank', '2': 'Discharge',
    '4': 'OL', '8': 'OL_Minus', '16': 'Open_TC',
    '32': 'Lead_Error', '64': 'dBm_OL',
}


class Fluke287Plugin(BaseDMMPlugin):
    """Plugin for Fluke 287/289 Digital Multimeters."""

    def __init__(self):
        super().__init__()
        self._name = "Fluke 287"
        self._manufacturer = "Fluke"
        self._model = "287/289"
        self._serial_params = SerialParams(
            baudrate=115200, databits=8, stopbits=1, parity='N', timeout=2.0
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
        return "Fluke 287/289 DMM - IR Serial (IR189USB), ASCII protocol, 115200/8N1"

    @property
    def serial_params(self):
        return self._serial_params

    # ── Command Building ─────────────────────────────────────────

    def build_online_command(self):
        """ID command for handshake — returns model and firmware."""
        return b'ID\r'

    def build_read_command(self):
        """QDDA — Query Displayed Data, full measurement info."""
        return b'QDDA\r'

    def build_reset_command(self):
        return b'RI\r'

    def build_select_function_command(self):
        return b''  # Cannot remotely change function on Fluke 287

    def build_range_command(self):
        return b''  # Cannot remotely change range

    def build_manual_record_count_command(self):
        return b'QSLS\r'  # Query Saved Log Sessions

    def build_manual_record_read_command(self, index):
        return f'QSRR {index}\r'.encode()

    def build_timed_record_count_command(self):
        return b'QSLS\r'

    def build_timed_interval_command(self):
        return b'QLSI 0\r'  # Query Log Session Info

    def build_timed_record_read_command(self, index):
        return f'QSRR {index}\r'.encode()

    # ── Response Parsing ─────────────────────────────────────────

    def parse_ack_response(self, response):
        """Parse ID response: returns True if valid."""
        if not response:
            return False
        text = self._decode(response)
        # ID returns something like "0,FLUKE 287,V1.02,..."
        return 'FLUKE' in text.upper() or '287' in text or '289' in text

    def parse_measurement(self, response):
        """Parse QDDA response into MeasurementData."""
        if not response:
            return None
        text = self._decode(response)
        return self._parse_qdda(text)

    def parse_record_count(self, response):
        """Parse QSLS response for record count."""
        if not response:
            return None
        text = self._decode(response)
        try:
            # QSLS returns: 0,<numberOfSessions>
            parts = text.strip().split(',')
            if len(parts) >= 2:
                return int(parts[1].strip())
        except (ValueError, IndexError):
            pass
        return 0

    def parse_interval(self, response):
        """Parse QLSI response for log interval."""
        if not response:
            return None
        text = self._decode(response)
        try:
            parts = text.strip().split(',')
            # Look for sample interval field
            for i, p in enumerate(parts):
                if p.strip().isdigit() and i > 2:
                    return int(p.strip())
        except (ValueError, IndexError):
            pass
        return None

    # ── Available Functions ──────────────────────────────────────

    def get_available_functions(self):
        return [
            'V DC', 'V AC', 'V AC+DC', 'mV DC', 'mV AC', 'mV AC+DC',
            '\u03A9', 'nS', 'Continuity', 'Diode',
            'Capacitance', 'Temperature \u00B0C', 'Temperature \u00B0F',
            '\u00B5A DC', '\u00B5A AC', 'mA DC', 'mA AC',
            'A DC', 'A AC', 'A AC+DC',
            'Hz', 'Duty Cycle %', 'Pulse Width',
            'dBm', 'dBV',
            'Peak Min', 'Peak Max',
        ]

    def get_available_ranges(self, function):
        return ['Auto']  # Fluke 287 is mainly auto-ranging

    def get_function_ranges(self, func_code):
        return [{'name': 'Auto', 'code': 0}]

    # ── Internal Helpers ─────────────────────────────────────────

    def _decode(self, response):
        """Decode response bytes to string."""
        if isinstance(response, bytes):
            return response.decode('ascii', errors='replace').strip()
        return str(response).strip()

    def _parse_qdda(self, text):
        """
        Parse QDDA response.
        Format: primaryFunction, secondaryFunction, autoRangeState, baseUnit,
                rangeNumber, unitMultiplier, lightningBolt, minMaxStartTime,
                numberOfModes, [modes...], numberOfReadings, [readings...]
        Reading: readingID, readingValue, baseUnit, unitMultiplier,
                 decimalPlaces, displayDigits, readingState, readingAttribute
        """
        try:
            parts = [p.strip() for p in text.split(',')]
            if len(parts) < 10:
                logger.warning(f"QDDA response too short: {len(parts)} fields")
                return None

            # Primary function description
            primary_func = parts[0] if parts[0] else 'Unknown'
            secondary_func = parts[1] if len(parts) > 1 else ''

            # Range data
            auto_range = parts[2] if len(parts) > 2 else '1'
            base_unit_code = parts[3] if len(parts) > 3 else 'NONE'

            # Find numberOfModes and readings
            # The format is variable-length, so we parse dynamically
            idx = 6  # After lightningBolt
            if idx >= len(parts):
                return None

            # Skip to numberOfReadings
            # Standard order: ..., minMaxStartTime, numberOfModes, [modes],
            #                 numberOfReadings, [readingData x8 per reading]
            n_modes_idx = 8
            if n_modes_idx >= len(parts):
                return None

            try:
                n_modes = int(parts[n_modes_idx])
            except (ValueError, IndexError):
                n_modes = 0

            readings_start = n_modes_idx + 1 + n_modes
            if readings_start >= len(parts):
                # Try simple QM-style parsing
                return self._parse_qm_fallback(text)

            try:
                n_readings = int(parts[readings_start])
            except (ValueError, IndexError):
                return self._parse_qm_fallback(text)

            # Parse first reading (primary)
            r_idx = readings_start + 1
            if r_idx + 7 >= len(parts):
                return self._parse_qm_fallback(text)

            reading_value = float(parts[r_idx + 1])
            r_base_unit = parts[r_idx + 2]
            r_multiplier = parts[r_idx + 3]
            r_decimal_places = int(parts[r_idx + 4]) if parts[r_idx + 4].isdigit() else 4
            r_display_digits = int(parts[r_idx + 5]) if parts[r_idx + 5].isdigit() else 5
            r_state = parts[r_idx + 6]

            # Determine if overload
            is_overload = r_state in ('4', '8', '16', '32', '64')

            # Build display value
            multiplier = MULTIPLIER_MAP.get(r_multiplier, 1)
            prefix = MULTIPLIER_PREFIX.get(r_multiplier, '')
            unit_base = UNIT_MAP.get(r_base_unit, r_base_unit)
            display_unit = f"{prefix}{unit_base}"

            # The reading value is in base units — apply multiplier for display
            display_value = reading_value / multiplier if multiplier != 0 else reading_value
            value_str = f"{display_value:.{r_decimal_places}f}" if not is_overload else "OL"

            # Parse secondary reading if available
            sec_value = None
            sec_str = None
            sec_unit = None
            if n_readings >= 2:
                s_idx = r_idx + 8
                if s_idx + 7 < len(parts):
                    try:
                        sec_raw = float(parts[s_idx + 1])
                        sec_mult = MULTIPLIER_MAP.get(parts[s_idx + 3], 1)
                        sec_prefix = MULTIPLIER_PREFIX.get(parts[s_idx + 3], '')
                        sec_base = UNIT_MAP.get(parts[s_idx + 2], parts[s_idx + 2])
                        sec_value = sec_raw
                        sec_str = f"{sec_raw / sec_mult if sec_mult else sec_raw:.4f}"
                        sec_unit = f"{sec_prefix}{sec_base}"
                    except (ValueError, IndexError):
                        pass

            # Build function name
            func_name = primary_func
            range_str = 'Auto' if auto_range == '1' else f'Range {auto_range}'

            return MeasurementData(
                function=func_name,
                range_str=range_str,
                value=reading_value,
                value_str=value_str,
                unit=display_unit,
                secondary_value=sec_value,
                secondary_str=sec_str,
                secondary_unit=sec_unit,
                is_overload=is_overload,
            )

        except Exception as e:
            logger.error(f"QDDA parse error: {e}")
            return self._parse_qm_fallback(text)

    def _parse_qm_fallback(self, text):
        """Fallback parser using simple QM-like response."""
        try:
            parts = [p.strip() for p in text.split(',')]
            if len(parts) >= 3:
                value_str = parts[0]
                unit = parts[1] if len(parts) > 1 else ''
                try:
                    value = float(value_str)
                    is_ol = False
                except ValueError:
                    value = float('inf')
                    is_ol = True

                return MeasurementData(
                    function='Measurement',
                    range_str='Auto',
                    value=value,
                    value_str=value_str,
                    unit=unit,
                    is_overload=is_ol,
                )
        except Exception:
            pass
        return None
