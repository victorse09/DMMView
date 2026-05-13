"""
DMMView - EEVBlog 121GW Plugin
Communication via Bluetooth Low Energy (BLE).
19-byte binary packets via BLE notifications.
Tested with BLE112 module, firmware 1.0.3.
Requires: bleak library for BLE on Linux.

Packet structure (19 bytes, reverse-engineered from real device):
  MAIN DISPLAY:
    B0:    Status flags (bit1=Auto, etc.)
    B1:    [7:4]=Mode [3:0]=Range
    B2-B4: 20-bit value (B2 bit7=sign, remaining=magnitude)
    B5:    Decimal point position (number of decimal places)
    B6:    Additional flags

  SUB DISPLAY:
    B7-B8: 16-bit raw value (big-endian)
    B9:    Sub mode (function)
    B10-B12: Sub DP, flags, status

  BAR/STATUS:
    B13-B14: Bar graph
    B15-B17: Status flags
    B18:     CRC/Sync
"""

import logging
from plugins.base_plugin import BaseDMMPlugin, SerialParams, MeasurementData

logger = logging.getLogger("DMMView.121GW")

PACKET_SIZE = 19

# Real UUIDs from BLE112 module
SERVICE_UUID = "0bd51666-e7cb-469b-8e4d-2742f1ba77cc"
CHAR_UUID = "e7add780-b042-4876-aae1-112855353cc1"

# Mode table (4-bit, from byte 1 high nibble)
MODE_NAMES = {
    0: 'Low Z V', 1: 'DCV', 2: 'ACV', 3: 'DCmV', 4: 'ACmV',
    5: 'Temp', 6: 'Hz', 7: 'Duty%', 8: 'mA DC', 9: 'mA AC',
    10: '\u00B5A DC', 11: '\u00B5A AC', 12: 'A DC', 13: 'A AC',
    14: 'Diode', 15: 'Continuity',
}

# Extended modes (if mode > 15, use byte 6 or special logic)
EXT_MODES = {
    16: '\u03A9', 17: 'Cap', 18: 'Live', 19: 'dBm', 20: 'dBV',
}

# Unit per mode
MODE_UNITS = {
    'Low Z V': 'V', 'DCV': 'V', 'ACV': 'V', 'DCmV': 'mV', 'ACmV': 'mV',
    'Temp': '\u00B0C', 'Hz': 'Hz', 'Duty%': '%',
    'mA DC': 'mA', 'mA AC': 'mA',
    '\u00B5A DC': '\u00B5A', '\u00B5A AC': '\u00B5A',
    'A DC': 'A', 'A AC': 'A',
    'Diode': 'V', 'Continuity': '\u03A9', '\u03A9': '\u03A9',
    'Cap': 'F', 'Live': '', 'dBm': 'dBm', 'dBV': 'dBV',
}


class EEVBlog121GWPlugin(BaseDMMPlugin):
    """Plugin for EEVBlog 121GW Digital Multimeter (BLE)."""

    def __init__(self):
        super().__init__()
        self._name = "EEVBlog 121GW"
        self._manufacturer = "EEVBlog"
        self._model = "121GW"
        self._serial_params = SerialParams(
            baudrate=115200, databits=8, stopbits=1, parity='N', timeout=2.0
        )
        self._connection_type = 'ble'
        self._ble_client = None
        self._latest_data = None
        self._ble_address = None
        self._connected = False
        self._device_info = {}

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
        return "EEVBlog 121GW DMM - Bluetooth LE, 19-byte binary packets"

    @property
    def serial_params(self):
        return self._serial_params

    @property
    def connection_type(self):
        return self._connection_type

    # ── BLE Connection ───────────────────────────────────────────

    async def scan_for_device(self, timeout=10.0):
        """Scan for a 121GW device via BLE."""
        try:
            from bleak import BleakScanner
        except ImportError:
            raise ImportError(
                "La librer\u00EDa 'bleak' es necesaria para el EEVBlog 121GW.\n"
                "Instalar con: pip install bleak"
            )
        logger.info("Scanning for 121GW BLE devices...")
        devices = await BleakScanner.discover(timeout=timeout)
        for d in devices:
            name = (d.name or '').upper()
            if '121GW' in name or '121' in name:
                logger.info(f"Found 121GW: {d.name} [{d.address}]")
                return d.address
        logger.warning("No 121GW device found via BLE scan")
        return None

    async def connect_ble(self, address=None):
        """Connect to the 121GW via BLE."""
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError:
            raise ImportError(
                "La librer\u00EDa 'bleak' es necesaria para el EEVBlog 121GW.\n"
                "Instalar con: pip install bleak"
            )

        if not address:
            address = await self.scan_for_device()
        if not address:
            raise ConnectionError(
                "No se encontr\u00F3 dispositivo 121GW via Bluetooth.\n\n"
                "Si estaba conectado previamente, ejecute en terminal:\n"
                "  bluetoothctl disconnect " + (self._ble_address or "<address>") + "\n"
                "y luego reconecte desde DMMView."
            )

        self._ble_address = address

        # Scan to register device in bleak's D-Bus cache
        devices = await BleakScanner.discover(timeout=5)
        target = None
        for d in devices:
            if d.address.upper() == address.upper():
                target = d
                break

        if target:
            self._ble_client = BleakClient(target)
        else:
            self._ble_client = BleakClient(address)

        await self._ble_client.connect(timeout=15)

        if not self._ble_client.is_connected:
            raise ConnectionError(f"No se pudo conectar BLE a {address}")

        # Read device info
        try:
            model_bytes = await self._ble_client.read_gatt_char(
                "00002a24-0000-1000-8000-00805f9b34fb")
            fw_bytes = await self._ble_client.read_gatt_char(
                "00002a26-0000-1000-8000-00805f9b34fb")
            self._device_info = {
                'model': model_bytes.decode('ascii', errors='replace').strip('\x00'),
                'firmware': fw_bytes.decode('ascii', errors='replace').strip('\x00'),
            }
            logger.info(f"121GW: {self._device_info['model']}, "
                        f"FW {self._device_info['firmware']}")
        except Exception as e:
            logger.warning(f"Could not read device info: {e}")

        # Subscribe to measurement notifications
        await self._ble_client.start_notify(CHAR_UUID, self._notification_handler)
        self._connected = True
        logger.info(f"121GW connected via BLE: {address}")

    async def disconnect_ble(self):
        """Disconnect from 121GW BLE."""
        if self._ble_client:
            try:
                await self._ble_client.stop_notify(CHAR_UUID)
            except Exception:
                pass
            try:
                await self._ble_client.disconnect()
            except Exception:
                pass
            self._ble_client = None
            self._connected = False
            self._latest_data = None
            logger.info("121GW disconnected")

    def is_connected_ble(self):
        return self._connected and self._ble_client is not None

    def _notification_handler(self, sender, data):
        """Handle incoming BLE notifications (19-byte packets)."""
        if data and len(data) >= PACKET_SIZE:
            self._latest_data = bytes(data[:PACKET_SIZE])

    def get_latest_measurement(self):
        """Get the latest measurement from BLE notifications."""
        if self._latest_data:
            return self._parse_packet(self._latest_data)
        return None

    # ── Standard Plugin Interface ────────────────────────────────

    def build_online_command(self):
        return b''

    def build_read_command(self):
        return b''

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
        return response is not None and len(response) > 0

    def parse_measurement(self, response):
        if not response or len(response) < PACKET_SIZE:
            return None
        return self._parse_packet(response)

    def parse_record_count(self, response):
        return 0

    def parse_interval(self, response):
        return None

    # ── Packet Parsing ───────────────────────────────────────────

    def _parse_packet(self, data):
        """
        Parse 19-byte packet from 121GW.

        Format (from real device captures):
          B0:    Status flags (bit1=Auto, bit4-7=various)
          B1:    [7:4]=Mode(4bit) [3:0]=Range(4bit)
          B2-B4: Main 20-bit value (B2[7]=sign, B2[6:0]+B3+B4=value)
          B5:    Main decimal places count
          B6:    Main extra flags
          B7-B8: Sub 16-bit raw value (big-endian)
          B9:    Sub mode (function index)
          B10:   Sub info
          B11:   Sub decimal/flags
          B12:   Sub status
          B13-B14: Bar graph
          B15-B17: Status
          B18:   CRC
        """
        if len(data) < PACKET_SIZE:
            return None

        # DEBUG: Dump raw packet to file
        try:
            with open("packet_debug.log", "a") as f:
                hex_str = " ".join(f"{b:02x}" for b in data)
                f.write(f"Raw: {hex_str}\n")
        except:
            pass

        try:
            # ── Main Display ─────────────────────────────────────
            flags0 = data[0]
            is_auto = bool(flags0 & 0x02)

            main_mode_code = (data[1] >> 4) & 0x0F
            main_range = data[1] & 0x0F
            main_mode = MODE_NAMES.get(main_mode_code, f'Mode_{main_mode_code}')

            # 20-bit signed value
            main_sign = bool(data[2] & 0x80)
            main_raw = ((data[2] & 0x7F) << 16) | (data[3] << 8) | data[4]

            # Decimal places
            main_dp = data[5]
            if main_dp > 5:
                main_dp = 0

            # Check overload
            is_overload = (main_raw >= 0x7FFFF)

            if is_overload:
                main_value = float('inf')
                main_str = 'OL'
            else:
                if main_dp > 0:
                    main_value = main_raw / (10 ** main_dp)
                else:
                    main_value = float(main_raw)

                if main_sign and main_value != 0:
                    main_value = -main_value

                if main_dp > 0:
                    main_str = f"{main_value:.{main_dp}f}"
                else:
                    main_str = str(int(main_value))

            main_unit = MODE_UNITS.get(main_mode, '')

            # ── Sub Display ──────────────────────────────────────
            sub_value = None
            sub_str = None
            sub_unit = None

            sub_raw = (data[7] << 8) | data[8]
            sub_mode_code = data[9] & 0x0F
            sub_mode = MODE_NAMES.get(sub_mode_code, '')

            # Sub decimal: estimate from context
            # For Hz readings, DP is typically 2 (49.48 Hz)
            # For voltage, depends on range
            sub_dp = 2  # default
            if sub_mode in ('DCV', 'ACV', 'DCmV', 'ACmV', 'Low Z V'):
                sub_dp = 3
            elif sub_mode in ('Hz',):
                sub_dp = 2
            elif sub_mode in ('Temp',):
                sub_dp = 1
            elif sub_mode in ('Duty%',):
                sub_dp = 1
            elif sub_mode in ('\u03A9', 'Cap'):
                sub_dp = 3

            if sub_raw > 0:
                if sub_dp > 0:
                    sub_value = sub_raw / (10 ** sub_dp)
                    sub_str = f"{sub_value:.{sub_dp}f}"
                else:
                    sub_value = float(sub_raw)
                    sub_str = str(sub_raw)
                sub_unit = MODE_UNITS.get(sub_mode, '')

            range_str = f"Range {main_range}" + (" Auto" if is_auto else "")

            # Swap only the values (not the units/functions) as requested by user
            primary_val = sub_value if sub_value is not None else main_value
            primary_str = sub_str if sub_str is not None else main_str
            
            sec_val = main_value if sub_value is not None else None
            sec_str = main_str if sub_value is not None else None

            return MeasurementData(
                function=main_mode,
                range_str=range_str,
                value=primary_val,
                value_str=primary_str,
                unit=main_unit,
                secondary_value=sec_val,
                secondary_str=sec_str,
                secondary_unit=sub_unit,
                is_overload=is_overload,
            )

        except Exception as e:
            logger.error(f"121GW parse error: {e}")
            return None

    # ── Available Functions ──────────────────────────────────────

    def get_available_functions(self):
        return list(MODE_NAMES.values())

    def get_available_ranges(self, function):
        return ['Auto']

    def get_function_ranges(self, func_code):
        return [{'name': 'Auto', 'code': 0}]
