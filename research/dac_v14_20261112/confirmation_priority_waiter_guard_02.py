"""Validate an unexecuted queue lease before a scheduling-only replacement."""
from pathlib import Path
from retained_prefix_workflow import read,sha
from seed_census_analysis_pool_v2 import process_identity

def check(node,require_running=True):
    q=Path(node['old_queue']);reg=read(q/'registration.json')
    assert sha(q/'registration.json')==node['old_registration_sha256']
    assert reg['pid']==node['pid'] and reg['start_ticks']==node['start_ticks']
    assert not (q/'completion.json').exists() and not Path(node['new_queue']).exists()
    status=read(q/'status.json');assert status['status'].startswith('waiting'),'Queue no longer waiting'
    assert not any(Path(p).exists() for p in node['forbidden_paths']),'Actual execution output already exists'
    if node['batch']=='interrupted_flow_recovery_01':assert not any((q.parent/'arms').iterdir())
    p=process_identity(reg['pid']);assert p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
    if require_running:assert p['state'] not in ['T','t'],'Unexpected already-stopped owner'
    command=Path('/proc',str(reg['pid']),'cmdline').read_bytes().split(b'\0')
    assert str(Path(node['old_script']).resolve()).encode() in command,'Process command differs from old queue script'
    children=[]
    for task in Path('/proc',str(reg['pid']),'task').iterdir():
        path=task/'children'
        try:children += path.read_text().split()
        except (FileNotFoundError,ProcessLookupError):continue
    assert not children,'Queue has actual child processes'
    return p
