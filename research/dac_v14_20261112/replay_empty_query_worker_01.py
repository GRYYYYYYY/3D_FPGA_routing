"""Run staged worker on completed inputs; forbid graph maps and subprocess calls."""
import argparse
import json
import runpy
import subprocess
import sys
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True)
p.add_argument('--script',type=Path,required=True);p.add_argument('--mode',choices=['empty','nonempty'],required=True)
p.add_argument('--result',type=Path,required=True);p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
sys.path.insert(0,str(a.runtime))
import immutable_rr_audit_cache

class OriginalNonemptyPathReached(Exception):pass
def no_mapping(*args,**kwargs):
    if a.mode=='nonempty':raise OriginalNonemptyPathReached()
    raise AssertionError('Empty target set attempted graph mapping')
def no_process(*args,**kwargs):raise AssertionError('Replay attempted a new query/native process')
immutable_rr_audit_cache.GraphAuditCache=no_mapping
subprocess.run=no_process
sys.argv=[str(a.script),*(a.args[1:] if a.args[:1]==['--'] else a.args)]
try:
    runpy.run_path(str(a.script),run_name='__main__')
except OriginalNonemptyPathReached:
    assert a.mode=='nonempty'
    result=dict(passed=True,mode=a.mode,original_nonempty_graph_path_reached=True,
                new_query_processes=0,new_native_routes=0)
except SystemExit as e:
    assert a.mode=='empty' and e.code in [None,0],e.code
    result=dict(passed=True,mode=a.mode,empty_branch_completed=True,
                new_query_processes=0,new_native_routes=0,graph_maps=0)
else:
    raise AssertionError('Expected explicit empty exit or nonempty dispatch boundary')
with a.result.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
