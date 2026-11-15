"""Recover only actual original GNU-time fields, never an absent observer receipt."""
import math,re
from pathlib import Path
from retained_prefix_workflow import D,read,sha
from seed_census_analysis_pool_v2 import process_identity

def parse_gnu_time(text):
    def one(pattern):
        rows=re.findall(pattern,text,re.M);assert len(rows)==1,(pattern,len(rows));return rows[0]
    clock=one(r'^\s*Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\d+(?::\d+){1,2}(?:\.\d+)?)\s*$')
    fields=list(map(float,clock.split(':')));assert all(0<=x<60 for x in fields[1:])
    seconds=0.
    for value in fields:seconds=seconds*60+value
    assert math.isfinite(seconds) and seconds>=0
    resolution=10.**(-len(clock.split('.')[-1])) if '.' in clock else 1.
    return dict(elapsed_seconds=seconds,elapsed_text=clock,display_resolution_seconds=resolution,
        exit_status=int(one(r'^\s*Exit status:\s*(\d+)\s*$')),
        waited_process_RSS_high_water_kib=int(one(r'^\s*Maximum resident set size \(kbytes\):\s*(\d+)\s*$')),
        command_text=one(r'^\s*Command being timed: "(.*)"\s*$'))

def recover_original_time(root):
    root=Path(root).resolve();recovery=D/'supervision_recovery_20261115_01'
    terminal=recovery/'completion.json'
    assert terminal.exists(),'Original recovery owner has not reported terminal state'
    r=read(terminal);assert r['passed'] and r['status']=='original_measured_process_terminal_observed'
    intervention=read(recovery/'intervention.json');registered=read(root/'measurement/registration.json')
    assert Path(intervention['original_measurement_registration']).resolve()==root/'measurement/registration.json'
    assert registered['measured_pid']==intervention['original_measured_process']['pid']
    assert registered['measured_start_ticks']==intervention['original_measured_process']['start_ticks']
    for pid,ticks in [(registered['measured_pid'],registered['measured_start_ticks']),(registered['owner_pid'],registered['owner_start_ticks'])]:
        p=process_identity(pid);assert not p or p['state']=='Z' or p['start_ticks']!=ticks,'Original process still live'
    assert not (root/'measurement/completion.json').exists(),'Use ordinary verifier for an actual complete observer receipt'
    command=registered['command'];assert Path(command[command.index('--output')+1]).resolve()==root/'flow'
    assert sha(command[command.index('--config')+1])==sha(root/'config.json')
    raw=root/'measurement/gnu_time.txt';parsed=parse_gnu_time(raw.read_text())
    assert parsed['command_text']==' '.join(command)
    launch=registered['launch_command'];assert launch[:3]==['/usr/bin/time','-v','-o'] and Path(launch[3]).resolve()==raw
    assert launch[4:]==['--',*command]
    parsed.update(original_observer_receipt_available=False,full_tree_PSS_available=False,undisturbed_timing=False,
        observer_CPU_seconds=None,complete_observer_wall_seconds=None,sampled_tree_PSS_peak_kib=None,
        source_sha256={str(f):sha(f) for f in [raw,root/'measurement/registration.json',recovery/'intervention.json',terminal]},
        qualification='Original GNU-time invocation only. Observer disappeared and a successor briefly overlapped; no complete tree-memory sample or observer-wall/CPU receipt reconstructed. GNU elapsed and process RSS are distinct from sampled whole-tree PSS.')
    return parsed
