"""Only remove diagnostic application/cumulative records, preserve stored policy."""
from guide_influence_records import records as old_records

def records(lines,allowed_prefixes=None):
    return [l for l in old_records(lines,allowed_prefixes) if not l.startswith(('H3D_BOUNDED_CRITICAL_APPLY ','H3D_BOUNDED_CRITICAL_SUMMARY '))]
