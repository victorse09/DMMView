"""
DMMView - CSV Export
Exports measurement data to CSV files.
"""

import csv
import logging
from datetime import datetime
from typing import List
from core.data_logger import MeasurementRecord

logger = logging.getLogger("DMMView.CSV")


def export_to_csv(filepath: str, records: List[MeasurementRecord],
                  include_secondary=True):
    """
    Export measurement records to a CSV file.

    Args:
        filepath: Path to save the CSV file.
        records: List of MeasurementRecord objects.
        include_secondary: Include secondary/tertiary values if available.
    """
    if not records:
        logger.warning("No records to export")
        return False

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Determine if secondary/tertiary columns are needed
            has_secondary = include_secondary and any(
                r.secondary_value is not None for r in records
            )
            has_tertiary = include_secondary and any(
                r.tertiary_value is not None for r in records
            )

            # Build header
            headers = [
                'Timestamp',
                'Source',
                'Record #',
                'Function',
                'Range',
                'Value',
                'Unit',
                'Overload',
            ]
            if has_secondary:
                headers.extend(['Secondary Value', 'Secondary Unit'])
            if has_tertiary:
                headers.extend(['Tertiary Value', 'Tertiary Unit'])

            writer = csv.writer(csvfile)

            # Write metadata header
            writer.writerow(['# DMMView - Measurement Data Export'])
            writer.writerow([f'# Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([f'# Total Records: {len(records)}'])
            writer.writerow([])

            # Write column headers
            writer.writerow(headers)

            # Write data rows
            for record in records:
                row = [
                    record.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    record.source,
                    record.record_number,
                    record.function,
                    record.range_str,
                    record.value_str if record.is_overload else f'{record.value:.6g}',
                    record.unit,
                    'OL' if record.is_overload else '',
                ]
                if has_secondary:
                    row.extend([
                        f'{record.secondary_value:.6g}' if record.secondary_value is not None else '',
                        record.secondary_unit or '',
                    ])
                if has_tertiary:
                    row.extend([
                        f'{record.tertiary_value:.6g}' if record.tertiary_value is not None else '',
                        record.tertiary_unit or '',
                    ])
                writer.writerow(row)

        logger.info(f"Exported {len(records)} records to {filepath}")
        return True

    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise


def import_from_csv(filepath: str) -> List[MeasurementRecord]:
    """
    Import measurement records from a DMMView CSV file or a generic CSV.

    Supports:
      - DMMView exported CSVs (with # comment header)
      - Generic CSVs with columns: Timestamp, Function, Range, Value, Unit

    Returns:
        List of MeasurementRecord objects.
    """
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            # Skip comment lines starting with '#' or empty lines
            lines = []
            for line in csvfile:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    lines.append(stripped)

            if not lines:
                logger.warning(f"CSV file is empty: {filepath}")
                return records

            reader = csv.DictReader(lines)
            fieldnames = reader.fieldnames or []

            # Normalize field names (strip whitespace, lowercase for matching)
            field_map = {f.strip().lower(): f for f in fieldnames}

            for row_num, row in enumerate(reader, 1):
                try:
                    # Parse timestamp
                    ts_key = _find_field(field_map, ['timestamp', 'time', 'fecha'])
                    ts_str = row.get(field_map.get(ts_key, ''), '').strip()
                    timestamp = _parse_timestamp(ts_str) if ts_str else datetime.now()

                    # Parse function
                    func_key = _find_field(field_map, ['function', 'función', 'func', 'mode'])
                    function = row.get(field_map.get(func_key, ''), 'Unknown').strip()

                    # Parse range
                    range_key = _find_field(field_map, ['range', 'rango'])
                    range_str = row.get(field_map.get(range_key, ''), '').strip()

                    # Parse value
                    val_key = _find_field(field_map, ['value', 'valor', 'reading'])
                    val_str = row.get(field_map.get(val_key, ''), '0').strip()
                    is_overload = val_str.upper() in ('OL', 'O.L', 'O.L.', 'FFFFFFF', 'INF')
                    try:
                        value = float(val_str) if not is_overload else float('inf')
                    except ValueError:
                        value = 0.0
                        is_overload = True

                    # Parse unit
                    unit_key = _find_field(field_map, ['unit', 'unidad', 'units'])
                    unit = row.get(field_map.get(unit_key, ''), '').strip()

                    # Parse source
                    src_key = _find_field(field_map, ['source', 'fuente', 'origen'])
                    source = row.get(field_map.get(src_key, ''), 'csv_import').strip()
                    if not source:
                        source = 'csv_import'

                    # Parse record number
                    num_key = _find_field(field_map, ['record #', 'record', '#', 'numero'])
                    rec_num_str = row.get(field_map.get(num_key, ''), '0').strip()
                    try:
                        rec_num = int(rec_num_str)
                    except ValueError:
                        rec_num = row_num

                    # Parse overload flag
                    ol_key = _find_field(field_map, ['overload', 'ol'])
                    ol_str = row.get(field_map.get(ol_key, ''), '').strip()
                    if ol_str.upper() in ('OL', 'YES', 'TRUE', '1'):
                        is_overload = True

                    # Parse secondary value
                    sec_val = None
                    sec_str = None
                    sec_unit = None
                    sec_key = _find_field(field_map, ['secondary value', 'secundario'])
                    if sec_key:
                        sec_raw = row.get(field_map.get(sec_key, ''), '').strip()
                        if sec_raw:
                            try:
                                sec_val = float(sec_raw)
                                sec_str = sec_raw
                            except ValueError:
                                sec_str = sec_raw
                    sec_u_key = _find_field(field_map, ['secondary unit'])
                    if sec_u_key:
                        sec_unit = row.get(field_map.get(sec_u_key, ''), '').strip() or None

                    # Parse tertiary value
                    ter_val = None
                    ter_str = None
                    ter_unit = None
                    ter_key = _find_field(field_map, ['tertiary value', 'terciario'])
                    if ter_key:
                        ter_raw = row.get(field_map.get(ter_key, ''), '').strip()
                        if ter_raw:
                            try:
                                ter_val = float(ter_raw)
                                ter_str = ter_raw
                            except ValueError:
                                ter_str = ter_raw
                    ter_u_key = _find_field(field_map, ['tertiary unit'])
                    if ter_u_key:
                        ter_unit = row.get(field_map.get(ter_u_key, ''), '').strip() or None

                    record = MeasurementRecord(
                        timestamp=timestamp,
                        function=function,
                        range_str=range_str,
                        value=value,
                        value_str=val_str,
                        unit=unit,
                        secondary_value=sec_val,
                        secondary_str=sec_str,
                        secondary_unit=sec_unit,
                        tertiary_value=ter_val,
                        tertiary_str=ter_str,
                        tertiary_unit=ter_unit,
                        is_overload=is_overload,
                        source=source,
                        record_number=rec_num,
                    )
                    records.append(record)

                except Exception as e:
                    logger.warning(f"Skipping row {row_num}: {e}")
                    continue

        logger.info(f"Imported {len(records)} records from {filepath}")
        return records

    except Exception as e:
        logger.error(f"CSV import failed: {e}")
        raise


def _find_field(field_map: dict, candidates: list) -> str | None:
    """Find first matching field name from candidates."""
    for c in candidates:
        if c in field_map:
            return c
    return None


def _parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp string in various formats."""
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%H:%M:%S.%f',
        '%H:%M:%S',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    # Last resort: return current time
    logger.warning(f"Could not parse timestamp: '{ts_str}'")
    return datetime.now()
