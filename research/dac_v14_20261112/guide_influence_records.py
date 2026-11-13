"""Remove only new read-only influence records and known elapsed fields."""
from compact_witness_records import records as previous_records

def records(lines,allowed_prefixes=None):
    return [line for line in previous_records(lines,allowed_prefixes) if not line.startswith('H3D_GUIDE_INFLUENCE_')]
