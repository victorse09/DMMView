"""
DMMView - VICTOR 98A+ Plugin
Full implementation of the DMMVIEW_G communication protocol.
"""

import logging
from typing import Optional, Dict, List
from plugins.base_plugin import BaseDMMPlugin, SerialParams, MeasurementData

logger = logging.getLogger("DMMView.Victor98A")

# ──────────────────────────────────────────────────────────────────────
# Function code mapping  (Appendix 2 & 5)
# Key = 2-byte func code (as tuple), Value = function info
# ──────────────────────────────────────────────────────────────────────
FUNC_MAP = {
    (0x30, 0x30): {'name': 'ACV',     'unit': 'V',   'ac': True},
    (0x30, 0x31): {'name': 'dBm_V',   'unit': 'dBm', 'ac': True},
    (0x30, 0x32): {'name': 'ACmV',    'unit': 'mV',  'ac': True},
    (0x30, 0x33): {'name': 'dBm_mV',  'unit': 'dBm', 'ac': True},
    (0x30, 0x34): {'name': 'DCV',     'unit': 'V',   'ac': False},
    (0x30, 0x35): {'name': 'DCmV',    'unit': 'mV',  'ac': False},
    (0x30, 0x36): {'name': 'TC_K',    'unit': '°C',  'ac': False},
    (0x30, 0x37): {'name': 'CONT',    'unit': 'Ω',   'ac': False},
    (0x30, 0x38): {'name': 'DIODE',   'unit': 'V',   'ac': False},
    (0x30, 0x39): {'name': 'OHM',     'unit': 'Ω',   'ac': False},
    (0x31, 0x30): {'name': 'RTD',     'unit': '°C',  'ac': False},
    (0x31, 0x31): {'name': 'CAP',     'unit': 'F',   'ac': False},
    (0x31, 0x32): {'name': 'FREQ',    'unit': 'Hz',  'ac': False},
    (0x31, 0x33): {'name': 'DCµA',    'unit': 'µA',  'ac': False},
    (0x31, 0x34): {'name': 'DCmA',    'unit': 'mA',  'ac': False},
    (0x31, 0x35): {'name': 'DCA',     'unit': 'A',   'ac': False},
    (0x31, 0x36): {'name': 'ACµA',    'unit': 'µA',  'ac': True},
    (0x31, 0x37): {'name': 'ACmA',    'unit': 'mA',  'ac': True},
    (0x31, 0x38): {'name': 'ACA',     'unit': 'A',   'ac': True},
    (0x31, 0x39): {'name': 'PEAK_DCmV', 'unit': 'mV', 'ac': False},
    (0x32, 0x30): {'name': 'PEAK_DCV',  'unit': 'V',  'ac': False},
    (0x32, 0x31): {'name': 'PEAK_DCµA', 'unit': 'µA', 'ac': False},
    (0x32, 0x32): {'name': 'PEAK_DCmA', 'unit': 'mA', 'ac': False},
    (0x32, 0x33): {'name': 'PEAK_DCA',  'unit': 'A',  'ac': False},
    (0x32, 0x34): {'name': 'ACmV+Hz',   'unit': 'mV', 'ac': True},
    (0x32, 0x35): {'name': 'ACV+Hz',    'unit': 'V',  'ac': True},
    (0x32, 0x36): {'name': 'ACµA+Hz',   'unit': 'µA', 'ac': True},
    (0x32, 0x37): {'name': 'ACmA+Hz',   'unit': 'mA', 'ac': True},
    (0x32, 0x38): {'name': 'ACA+Hz',    'unit': 'A',  'ac': True},
    (0x32, 0x39): {'name': 'ACmV+DCmV', 'unit': 'mV', 'ac': True},
    (0x33, 0x30): {'name': 'ACV+DCV',   'unit': 'V',  'ac': True},
    (0x33, 0x31): {'name': 'ACµA+DCµA', 'unit': 'µA', 'ac': True},
    (0x33, 0x32): {'name': 'ACmA+DCmA', 'unit': 'mA', 'ac': True},
    (0x33, 0x33): {'name': 'ACA+DCA',   'unit': 'A',  'ac': True},
    (0x33, 0x34): {'name': 'ACV~ VFC',  'unit': 'V',  'ac': True},
}

# ──────────────────────────────────────────────────────────────────────
# Range descriptions per function
# ──────────────────────────────────────────────────────────────────────
RANGE_MAP = {
    'ACV':    {0x30: '2V',    0x31: '20V',   0x32: '200V',  0x33: '1000V'},
    'ACV~ VFC': {0x30: '1000V', 0x31: '2V',  0x32: '20V',   0x33: '200V'},
    'dBm_V':  {0x30: '2V',    0x31: '20V',   0x32: '200V',  0x33: '1000V'},
    'ACmV':   {0x30: '200mV'},
    'dBm_mV': {0x30: '200mV'},
    'DCV':    {0x30: '2V',    0x31: '20V',   0x32: '200V',  0x33: '1000V'},
    'DCmV':   {0x30: '200mV'},
    'TC_K':   {0x30: 'K'},
    'CONT':   {0x30: '200Ω'},
    'DIODE':  {0x30: '2V'},
    'OHM':    {0x30: '200Ω',  0x31: '2kΩ',   0x32: '20kΩ',  0x33: '200kΩ',
               0x34: '2MΩ',   0x35: '20MΩ',  0x36: '60MΩ'},
    'RTD':    {0x30: 'PT100'},
    'CAP':    {0x30: '10nF',  0x31: '100nF', 0x32: '1000nF', 0x33: '10µF',
               0x34: '100µF', 0x35: '1000µF', 0x36: '100mF'},
    'FREQ':   {0x30: '10Hz',  0x31: '100Hz', 0x32: '1kHz',  0x33: '10kHz',
               0x34: '100kHz', 0x35: '1MHz', 0x36: '10MHz'},
    'DCµA':   {0x30: '200µA', 0x31: '2000µA'},
    'DCmA':   {0x30: '20mA',  0x31: '200mA'},
    'DCA':    {0x30: '2A',    0x31: '10A'},
    'ACµA':   {0x30: '200µA', 0x31: '2000µA'},
    'ACmA':   {0x30: '20mA',  0x31: '200mA'},
    'ACA':    {0x30: '2A',    0x31: '10A'},
    'PEAK_DCmV': {0x30: '200mV'},
    'PEAK_DCV':  {0x30: '2V', 0x31: '20V', 0x32: '200V', 0x33: '1000V'},
    'PEAK_DCµA': {0x30: '200µA', 0x31: '2000µA'},
    'PEAK_DCmA': {0x30: '20mA',  0x31: '200mA'},
    'PEAK_DCA':  {0x30: '2A',    0x31: '10A'},
    'ACmV+Hz':   {0x30: '10Hz',  0x31: '100Hz', 0x32: '1kHz', 0x33: '10kHz',
                  0x34: '100kHz', 0x35: '1MHz', 0x36: '10MHz'},
    'ACV+Hz':    {0x30: '10Hz',  0x31: '100Hz', 0x32: '1kHz', 0x33: '10kHz',
                  0x34: '100kHz', 0x35: '1MHz', 0x36: '10MHz'},
    'ACµA+Hz':   {0x30: '10Hz',  0x31: '100Hz', 0x32: '1kHz', 0x33: '10kHz',
                  0x34: '100kHz', 0x35: '1MHz', 0x36: '10MHz'},
    'ACmA+Hz':   {0x30: '10Hz',  0x31: '100Hz', 0x32: '1kHz', 0x33: '10kHz',
                  0x34: '100kHz', 0x35: '1MHz', 0x36: '10MHz'},
    'ACA+Hz':    {0x30: '10Hz',  0x31: '100Hz', 0x32: '1kHz', 0x33: '10kHz',
                  0x34: '100kHz', 0x35: '1MHz', 0x36: '10MHz'},
    'ACmV+DCmV': {0x30: '200mV'},
    'ACV+DCV':   {0x30: '2V', 0x31: '20V', 0x32: '200V', 0x33: '1000V'},
    'ACµA+DCµA': {0x30: '200µA', 0x31: '2000µA'},
    'ACmA+DCmA': {0x30: '20mA',  0x31: '200mA'},
    'ACA+DCA':   {0x30: '2A',    0x31: '10A'},
}

# Unit mapping for range display
UNIT_SUFFIX = {
    'V': 'V', 'mV': 'mV', 'Ω': 'Ω', 'kΩ': 'kΩ', 'MΩ': 'MΩ',
    'Hz': 'Hz', 'kHz': 'kHz', 'MHz': 'MHz',
    'µA': 'µA', 'mA': 'mA', 'A': 'A',
    'nF': 'nF', 'µF': 'µF', 'mF': 'mF',
    '°C': '°C', '°F': '°F', 'dBm': 'dBm',
}

# SEL function codes (Appendix 6)
SEL_FUNCTIONS = {
    'ACV':  [('ACV', 0x30), ('dBm', 0x31), ('AC+Hz', 0x32), ('VFC', 0x33)],
    'ACmV': [('ACmV', 0x30), ('dBm', 0x31), ('AC+Hz', 0x32)],
    'DCV':  [('DCV', 0x30), ('AC+DC', 0x31), ('PEAK_DCV', 0x32)],
    'DCmV': [('DCmV', 0x30), ('TC', 0x31), ('AC+DC', 0x32), ('PEAK_DCmV', 0x33)],
    'CONT': [('CONT', 0x30), ('DIODE', 0x31)],
    'OHM':  [('OHM', 0x30), ('RTD', 0x31), ('CAP', 0x32)],
    'FREQ': [],
    'DCuA': [('DCµA', 0x30), ('AC+DC', 0x31), ('PEAK_DCµA', 0x32), ('ACµA', 0x33), ('AC+Hz', 0x34)],
    'DCmA': [('DCmA', 0x30), ('AC+DC', 0x31), ('PEAK_DCmA', 0x32), ('ACmA', 0x33), ('AC+Hz', 0x34)],
    'DCA':  [('DCA', 0x30), ('AC+DC', 0x31), ('PEAK_DCA', 0x32), ('ACA', 0x33), ('AC+Hz', 0x34)],
}


class Victor98APlugin(BaseDMMPlugin):
    """
    Plugin for VICTOR 98A+ Multimeter.
    Implements the DMMVIEW_G communication protocol.
    """

    @property
    def name(self) -> str:
        return "VICTOR 98A+"

    @property
    def manufacturer(self) -> str:
        return "VICTOR"

    @property
    def model(self) -> str:
        return "98A+"

    @property
    def description(self) -> str:
        return "VICTOR 98A+ True RMS Digital Multimeter — DMMVIEW_G Protocol"

    @property
    def serial_params(self) -> SerialParams:
        return SerialParams(
            baudrate=9600,
            databits=8,
            stopbits=1,
            parity='N',
            timeout=1.0,
        )

    # ── Command builders ─────────────────────────────────────────────

    def build_online_command(self) -> bytes:
        """#<ONL><cr>"""
        return b'#ONL\r'

    def build_reset_command(self) -> bytes:
        """#<RST><cr>"""
        return b'#RST\r'

    def build_read_command(self) -> bytes:
        """#<RD?><cr>"""
        return b'#RD?\r'

    def build_select_function_command(self, func_code: int) -> bytes:
        """#<SEL>x<cr> where x is function code byte."""
        return b'#SEL' + bytes([func_code]) + b'\r'

    def build_range_command(self, auto: bool, range_code: int) -> bytes:
        """#<RAN>x1 x2<cr>"""
        auto_byte = 0x31 if auto else 0x30
        return b'#RAN' + bytes([auto_byte, range_code]) + b'\r'

    def build_manual_record_count_command(self) -> bytes:
        """#<SC?><cr>"""
        return b'#SC?\r'

    def build_manual_record_read_command(self, record_num: int) -> bytes:
        """#<SD?>xxxx<cr> where xxxx is 4-byte record number."""
        num_str = f'{record_num:04d}'
        return b'#SD?' + num_str.encode('ascii') + b'\r'

    def build_timed_record_count_command(self) -> bytes:
        """#<TC?><cr>"""
        return b'#TC?\r'

    def build_timed_interval_command(self) -> bytes:
        """#<TI?><cr>"""
        return b'#TI?\r'

    def build_timed_record_read_command(self, record_num: int) -> bytes:
        """#<TD?>xxxx<cr> where xxxx is 4-byte record number."""
        num_str = f'{record_num:04d}'
        return b'#TD?' + num_str.encode('ascii') + b'\r'

    # ── Response parsers ─────────────────────────────────────────────

    def parse_ack_response(self, data: bytes) -> bool:
        """Parse ACK (0x06 0x00) or NAK (0x15 0x00) response."""
        if not data:
            return False
        # Strip STX '#' and EM '\r'
        clean = data.strip(b'#\r\n ')
        if len(clean) >= 2 and clean[0] == 0x06:
            return True   # ACK
        if len(clean) >= 2 and clean[0] == 0x15:
            return False  # NAK
        # Also check ASCII
        if b'ACK' in data:
            return True
        if b'NAK' in data:
            return False
        return False

    def parse_measurement(self, data: bytes) -> Optional[MeasurementData]:
        """
        Parse 26-byte measurement data from RD, SD, or TD response.

        Structure (after #RD header):
          Function (2 bytes) + Range1 (1 byte) + Data1 (7 bytes)
                             + Range2 (1 byte) + Data2 (7 bytes)
                             + Range3 (1 byte) + Data3 (7 bytes)
          = 26 bytes total data
        """
        if not data:
            return None

        # Find the data payload - skip the response header (#RD, #SD, #TD)
        payload = None
        for prefix in [b'#RD', b'#SD', b'#TD']:
            idx = data.find(prefix)
            if idx >= 0:
                payload = data[idx + len(prefix):]
                break

        if payload is None:
            logger.warning(f"Unknown response format: {data.hex()}")
            return None

        # Remove trailing CR/LF
        payload = payload.rstrip(b'\r\n')

        if len(payload) < 26:
            logger.warning(f"Data payload too short: {len(payload)} bytes (need 26)")
            return None

        # Parse the 26 bytes
        func_code = (payload[0], payload[1])
        range1 = payload[2]
        data1 = payload[3:10]
        range2 = payload[10]
        data2 = payload[11:18]
        range3 = payload[18]
        data3 = payload[19:26]

        # Look up function
        func_info = FUNC_MAP.get(func_code)
        if func_info is None:
            logger.warning(f"Unknown function code: {hex(func_code[0])} {hex(func_code[1])}")
            func_info = {'name': f'UNK_{func_code[0]:02X}{func_code[1]:02X}',
                         'unit': '', 'ac': False}

        func_name = func_info['name']

        # Swap secondary and tertiary data for +Hz functions
        # The device sends Duty Cycle in data2 and AC value in data3,
        # but the UI prefers AC value (Voltage/Current) in Secondary (Left) and Duty Cycle (%) in Tertiary (Right).
        if '+Hz' in func_name:
            data2, data3 = data3, data2
            range2, range3 = range3, range2
        base_unit = func_info['unit']

        # Parse range
        range_dict = RANGE_MAP.get(func_name, {})
        range_str = range_dict.get(range1, f'Range_{range1:02X}')

        # Determine actual unit from range
        unit = self._unit_from_range(range_str, base_unit)

        # Parse primary value
        value, value_str, is_overload = self._parse_value(data1)

        # Build result
        result = MeasurementData(
            function=func_name,
            range_str=range_str,
            value=value,
            value_str=value_str,
            unit=unit,
            is_overload=is_overload,
            raw_bytes=data,
        )

        # Parse secondary value if present
        sec_val, sec_str, sec_ol = self._parse_value(data2)
        if sec_str and sec_str != '\x00' * 7:
            result.secondary_value = sec_val
            result.secondary_str = sec_str
            result.secondary_unit = self._get_secondary_unit(func_name, range2)

        # Parse tertiary value if present
        ter_val, ter_str, ter_ol = self._parse_value(data3)
        if ter_str and ter_str != '\x00' * 7:
            result.tertiary_value = ter_val
            result.tertiary_str = ter_str
            result.tertiary_unit = self._get_tertiary_unit(func_name, range3)

        return result

    def parse_record_count(self, data: bytes) -> Optional[int]:
        """Parse SC or TC response to get record count (4-byte data)."""
        if not data:
            return None
        # Find SC or TC header
        for prefix in [b'#SC', b'#TC']:
            idx = data.find(prefix)
            if idx >= 0:
                payload = data[idx + len(prefix):].rstrip(b'\r\n')
                if len(payload) >= 4:
                    try:
                        count = int(payload[:4].decode('ascii'))
                        return count
                    except (ValueError, UnicodeDecodeError):
                        logger.warning(f"Could not parse record count: {payload[:4].hex()}")
                        return None
        return None

    def parse_interval(self, data: bytes) -> Optional[int]:
        """Parse TI response to get interval time (4-byte data)."""
        if not data:
            return None
        idx = data.find(b'#TI')
        if idx >= 0:
            payload = data[idx + 3:].rstrip(b'\r\n')
            if len(payload) >= 4:
                try:
                    interval = int(payload[:4].decode('ascii'))
                    return interval
                except (ValueError, UnicodeDecodeError):
                    logger.warning(f"Could not parse interval: {payload[:4].hex()}")
                    return None
        return None

    # ── Function / Range info ────────────────────────────────────────

    def get_available_functions(self) -> List[Dict]:
        """Get all available measurement functions."""
        functions = []
        seen = set()
        for key, info in FUNC_MAP.items():
            name = info['name']
            if name not in seen and name != 'MEM':
                seen.add(name)
                icon = '⚡' if info['ac'] else '⎓'
                if 'OHM' in name or 'CONT' in name:
                    icon = 'Ω'
                elif 'CAP' in name:
                    icon = '⊥'
                elif 'FREQ' in name or 'Hz' in name:
                    icon = '∿'
                elif 'DIODE' in name:
                    icon = '▷|'
                elif 'TC' in name or 'RTD' in name:
                    icon = '🌡'
                functions.append({
                    'name': name,
                    'code': key,
                    'unit': info['unit'],
                    'icon': icon,
                })
        return functions

    def get_function_ranges(self, func_name: str) -> List[Dict]:
        """Get available ranges for a measurement function."""
        range_dict = RANGE_MAP.get(func_name, {})
        return [
            {'name': name, 'code': code}
            for code, name in sorted(range_dict.items())
        ]

    def get_sel_functions(self) -> Dict:
        """Get SEL command function options (Appendix 6)."""
        return SEL_FUNCTIONS

    # ── Internal helpers ─────────────────────────────────────────────

    def _parse_value(self, data7: bytes):
        """
        Parse a 7-byte value field.
        Format: ±X.XXXX or FFFFFFF (overload)
        Returns: (float_value, string_repr, is_overload)
        """
        try:
            val_str = data7.decode('ascii').strip('\x00').strip()
        except UnicodeDecodeError:
            val_str = ''

        if not val_str:
            return 0.0, '', False

        # Check for overload (FFFFFFF, +FFFFFF, -FFFFFF, OL, etc.)
        clean_val = val_str.replace('+', '').replace('-', '').strip()
        if (clean_val.replace('F', '') == '' and len(clean_val) >= 4) or 'OL' in clean_val or 'O.L' in clean_val:
            return float('inf'), 'OL', True

        try:
            value = float(val_str)
            return value, val_str, False
        except ValueError:
            logger.warning(f"Could not parse value: '{val_str}' ({data7.hex()})")
            return 0.0, val_str, False

    def _unit_from_range(self, range_str: str, base_unit: str) -> str:
        """Determine the actual unit from the range string."""
        if not range_str:
            return base_unit

        # Extract unit suffix from range string
        range_lower = range_str.lower()
        if 'mω' in range_lower or 'mohm' in range_lower or 'mΩ' in range_str:
            return 'MΩ'
        if 'kω' in range_lower or 'kohm' in range_lower or 'kΩ' in range_str:
            return 'kΩ'
        if 'ω' in range_lower or 'Ω' in range_str:
            return 'Ω'
        if 'mhz' in range_lower:
            return 'MHz'
        if 'khz' in range_lower:
            return 'kHz'
        if 'hz' in range_lower:
            return 'Hz'
        if 'mf' in range_lower:
            return 'mF'
        if 'µf' in range_lower or 'uf' in range_lower:
            return 'µF'
        if 'nf' in range_lower:
            return 'nF'
        if 'mv' in range_lower:
            return 'mV'
        if 'µa' in range_lower or 'ua' in range_lower:
            return 'µA'
        if 'ma' in range_lower:
            return 'mA'

        return base_unit

    def _get_secondary_unit(self, func_name: str, range_code: int) -> str:
        """Determine secondary value unit based on function."""
        if 'dBm' in func_name:
            # Secondary is the voltage value
            return 'V' if 'V' in func_name and 'mV' not in func_name else 'mV'
        if 'TC' in func_name:
            return 'mV'  # Cold junction
        if 'RTD' in func_name:
            return 'kΩ'  # Sensor resistance in kΩ
        if '+Hz' in func_name:
            # Secondary is the AC value (swapped)
            if 'mV' in func_name:
                return 'mV'
            elif 'V' in func_name:
                return 'V'
            elif 'µA' in func_name:
                return 'µA'
            elif 'mA' in func_name:
                return 'mA'
            elif 'A' in func_name:
                return 'A'
        if '+DC' in func_name:
            return 'V' if 'V' in func_name else 'A'
        if 'PEAK' in func_name:
            return self._unit_from_range('', FUNC_MAP.get(
                self._func_code_from_name(func_name), {}).get('unit', ''))
        return ''

    def _get_tertiary_unit(self, func_name: str, range_code: int) -> str:
        """Determine tertiary value unit based on function."""
        if 'dBm' in func_name:
            return 'Ω'  # Reference resistance is in ohms
        if 'TC' in func_name:
            return '°C'   # Temperature unit
        if 'RTD' in func_name:
            return '°C'
        if '+Hz' in func_name:
            # Tertiary is the Duty Cycle (swapped)
            return '%'
        if '+DC' in func_name:
            # Tertiary is the DC component
            if 'mV' in func_name:
                return 'mV'
            elif 'V' in func_name:
                return 'V'
            elif 'µA' in func_name:
                return 'µA'
            elif 'mA' in func_name:
                return 'mA'
            elif 'A' in func_name:
                return 'A'
        return ''

    def _func_code_from_name(self, name: str):
        """Reverse lookup function code from name."""
        for code, info in FUNC_MAP.items():
            if info['name'] == name:
                return code
        return None
