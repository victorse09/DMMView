"""
DMMView - Data Logger
Records measurements with timestamps for logging and analysis.
"""

import time
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("DMMView.Logger")


@dataclass
class MeasurementRecord:
    """Single measurement record."""
    timestamp: datetime
    function: str           # e.g., "DCV", "ACV", "OHM"
    range_str: str          # e.g., "20V", "200mV"
    value: float
    value_str: str          # Raw string representation
    unit: str               # e.g., "V", "mV", "Ω"
    secondary_value: Optional[float] = None
    secondary_str: Optional[str] = None
    secondary_unit: Optional[str] = None
    tertiary_value: Optional[float] = None
    tertiary_str: Optional[str] = None
    tertiary_unit: Optional[str] = None
    is_overload: bool = False
    source: str = "live"     # "live", "manual_memory", "timed_memory"
    record_number: int = 0   # For memory records


class DataLogger:
    """
    Records and manages measurement data.
    Supports circular buffer for live data and separate storage for memory downloads.
    """

    def __init__(self, max_records=100000):
        self._max_records = max_records
        self._live_records: deque[MeasurementRecord] = deque(maxlen=max_records)
        self._manual_memory_records: list[MeasurementRecord] = []
        self._timed_memory_records: list[MeasurementRecord] = []
        self._is_logging = False
        self._start_time: Optional[datetime] = None
        self._sample_count = 0

    def start_logging(self):
        """Start recording measurements."""
        self._is_logging = True
        self._start_time = datetime.now()
        self._sample_count = 0
        logger.info("Logging started")

    def stop_logging(self):
        """Stop recording measurements."""
        self._is_logging = False
        logger.info(f"Logging stopped. {self._sample_count} samples recorded")

    def is_logging(self):
        return self._is_logging

    def add_record(self, record: MeasurementRecord):
        """Add a measurement record to the appropriate storage."""
        if record.source == "live":
            if self._is_logging:
                self._live_records.append(record)
                self._sample_count += 1
        elif record.source == "manual_memory":
            self._manual_memory_records.append(record)
        elif record.source == "timed_memory":
            self._timed_memory_records.append(record)

    def get_live_records(self):
        """Get all live recorded measurements."""
        return list(self._live_records)

    def get_manual_memory_records(self):
        """Get downloaded manual memory records."""
        return list(self._manual_memory_records)

    def get_timed_memory_records(self):
        """Get downloaded timed memory records."""
        return list(self._timed_memory_records)

    def get_all_records(self):
        """Get all records from all sources."""
        all_records = []
        all_records.extend(self._live_records)
        all_records.extend(self._manual_memory_records)
        all_records.extend(self._timed_memory_records)
        return sorted(all_records, key=lambda r: r.timestamp)

    def clear_live(self):
        """Clear live recording data."""
        self._live_records.clear()
        self._sample_count = 0

    def clear_manual_memory(self):
        """Clear downloaded manual memory records."""
        self._manual_memory_records.clear()

    def clear_timed_memory(self):
        """Clear downloaded timed memory records."""
        self._timed_memory_records.clear()

    def clear_all(self):
        """Clear all data."""
        self.clear_live()
        self.clear_manual_memory()
        self.clear_timed_memory()

    @property
    def sample_count(self):
        return self._sample_count

    @property
    def live_count(self):
        return len(self._live_records)

    @property
    def manual_memory_count(self):
        return len(self._manual_memory_records)

    @property
    def timed_memory_count(self):
        return len(self._timed_memory_records)

    @property
    def start_time(self):
        return self._start_time

    def get_statistics(self, records=None):
        """Calculate statistics for a set of records."""
        if records is None:
            records = self.get_live_records()

        values = [r.value for r in records if not r.is_overload and r.value is not None]
        if not values:
            return {
                'count': 0, 'min': 0, 'max': 0,
                'avg': 0, 'range': 0,
            }

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'range': max(values) - min(values),
        }
