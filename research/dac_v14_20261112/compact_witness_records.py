"""Preserve all scored/path records, exclude only cache-size telemetry and elapsed."""
from candidate_path_cached_records import records as old_records

def records(lines,allowed_prefixes=None):
    return [line for line in old_records(lines,allowed_prefixes) if not line.startswith('H3D_CANDIDATE_PATH_COMPACT ')]
