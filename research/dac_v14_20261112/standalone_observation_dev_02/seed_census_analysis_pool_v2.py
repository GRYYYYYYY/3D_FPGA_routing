"""Exact process identity helper; this module does not implement the native pool."""
from pathlib import Path

def process_identity(pid):
    try:
        fields=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1].split()
        return dict(pid=pid,state=fields[0],start_ticks=fields[19])
    except FileNotFoundError:return None
