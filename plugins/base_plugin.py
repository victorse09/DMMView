"""
DMMView - Base Plugin Interface
Abstract base class defining the interface all DMM plugins must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from core.data_logger import MeasurementRecord


@dataclass
class SerialParams:
    """Default serial port parameters for a DMM."""
    baudrate: int = 9600
    databits: int = 8
    stopbits: int = 1
    parity: str = 'N'   # 'N', 'E', 'O'
    timeout: float = 1.0


@dataclass
class MeasurementData:
    """Parsed measurement data from DMM."""
    function: str           # e.g., "DCV", "ACV", "OHM"
    range_str: str          # e.g., "20V", "200mV"
    value: float
    value_str: str
    unit: str
    secondary_value: Optional[float] = None
    secondary_str: Optional[str] = None
    secondary_unit: Optional[str] = None
    tertiary_value: Optional[float] = None
    tertiary_str: Optional[str] = None
    tertiary_unit: Optional[str] = None
    is_overload: bool = False
    raw_bytes: bytes = b''


class BaseDMMPlugin(ABC):
    """
    Abstract base class for DMM instrument plugins.
    All multimeter plugins must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin display name."""
        pass

    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """Manufacturer name."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Model name/number."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""
        pass

    @property
    @abstractmethod
    def serial_params(self) -> SerialParams:
        """Default serial parameters for this DMM."""
        pass

    @abstractmethod
    def build_online_command(self) -> bytes:
        """Build the command to establish online/handshake connection."""
        pass

    @abstractmethod
    def build_reset_command(self) -> bytes:
        """Build the reset command."""
        pass

    @abstractmethod
    def build_read_command(self) -> bytes:
        """Build the real-time read measurement command."""
        pass

    @abstractmethod
    def build_select_function_command(self, func_code: int) -> bytes:
        """Build command to select measurement function."""
        pass

    @abstractmethod
    def build_range_command(self, auto: bool, range_code: int) -> bytes:
        """Build command to set measurement range."""
        pass

    @abstractmethod
    def build_manual_record_count_command(self) -> bytes:
        """Build command to read manual recording count."""
        pass

    @abstractmethod
    def build_manual_record_read_command(self, record_num: int) -> bytes:
        """Build command to read a specific manual record."""
        pass

    @abstractmethod
    def build_timed_record_count_command(self) -> bytes:
        """Build command to read timed recording count."""
        pass

    @abstractmethod
    def build_timed_interval_command(self) -> bytes:
        """Build command to read timed recording interval."""
        pass

    @abstractmethod
    def build_timed_record_read_command(self, record_num: int) -> bytes:
        """Build command to read a specific timed record."""
        pass

    @abstractmethod
    def parse_ack_response(self, data: bytes) -> bool:
        """Parse an ACK/NAK response. Returns True for ACK."""
        pass

    @abstractmethod
    def parse_measurement(self, data: bytes) -> Optional[MeasurementData]:
        """Parse measurement data response."""
        pass

    @abstractmethod
    def parse_record_count(self, data: bytes) -> Optional[int]:
        """Parse record count response."""
        pass

    @abstractmethod
    def parse_interval(self, data: bytes) -> Optional[int]:
        """Parse timed recording interval response."""
        pass

    @abstractmethod
    def get_available_functions(self) -> List[Dict]:
        """
        Get list of available measurement functions.
        Returns list of dicts with 'name', 'code', 'icon' keys.
        """
        pass

    @abstractmethod
    def get_function_ranges(self, func_code: str) -> List[Dict]:
        """
        Get available ranges for a measurement function.
        Returns list of dicts with 'name', 'code' keys.
        """
        pass
