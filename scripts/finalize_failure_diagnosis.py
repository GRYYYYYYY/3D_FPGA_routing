#!/usr/bin/env python3
"""Wait for the one diagnostic owner, then audit and bind the completed evidence."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from check_route import sha256
from diagnose_failures import BASE, PLAN, ROOT, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-primary',action='store_true')
    args=parser.parse_args()
    suffix='_native' if args.native_primary else ''
    protocol=ROOT/'configs/failure_diagnosis_native.json' if args.native_primary else PLAN
    lock=(BASE/('finalizer'+suffix+'.lock')).open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    path=BASE/('validation'+suffix+'.json')
    state=dict(owner_pid=os.getpid(),started_epoch=time.time(),stage='waiting_for_routing',steps=[])
    write_json(path,state)
    while True:
        queue=json.loads((BASE/('native_state.json' if args.native_primary else 'state.json')).read_text())
        if 'finished_epoch' in queue:break
        owner=queue['owner_pid']
        try:
            cmd=(Path('/proc')/str(owner)/'cmdline').read_bytes()
        except FileNotFoundError:
            raise RuntimeError('Routing owner exited before queue completion; inspect existing jobs')
        if b'diagnose_failures.py' not in cmd:
            raise RuntimeError('Routing owner identity mismatch')
        state.update(last_observed_epoch=time.time(),routing_stage=queue['active_stage'])
        write_json(path,state)
        time.sleep(15)
    # Incremental width checks use the same unchanged per-route audit cache.
    # Wait for their owner before the ordinary final audit can read/write it.
    width_audit_lock=(BASE/'width_audit.lock').open('a')
    state['stage']='waiting_for_incremental_width_audit';write_json(path,state)
    while True:
        try:
            fcntl.flock(width_audit_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            break
        except BlockingIOError:time.sleep(5)
    commands=[
        ('collect_before_audit',[sys.executable,str(ROOT/'scripts/collect_failure_diagnosis.py')]),
        ('make_audit_matrix',[sys.executable,str(ROOT/'scripts/collect_failure_diagnosis.py'),'--audit-matrix']),
        ('independent_audit',[sys.executable,str(ROOT/'scripts/audit_matrix.py'),'--matrix',str(BASE/('audit_matrix'+suffix+'.json')),
                              '--output',str(BASE/('audits'+suffix+'.json')),'--workers','4']),
        ('final_collection',[sys.executable,str(ROOT/'scripts/collect_failure_diagnosis.py'),'--final']),
    ]
    if args.native_primary:
        for label,command in commands:
            if label!='independent_audit':command.append('--native-primary')
    for label,command in commands:
        state['stage']=label;write_json(path,state)
        with (BASE/(label+suffix+'.log')).open('w') as stream:
            code=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT).returncode
        state['steps'].append(dict(stage=label,returncode=code,finished_epoch=time.time()))
        write_json(path,state)
        if code:raise RuntimeError('Validation failed: '+label)
    state['stage']='final_frozen_input_verification';write_json(path,state)
    plan=json.loads(protocol.read_text());checked={}
    for source in plan['sources']:
        manifest_path=Path(source['original_output'])/'manifest.json'
        if sha256(manifest_path)!=source['manifest_sha256']:
            raise RuntimeError('Original manifest changed: '+str(manifest_path))
        for inp in source['manifest']['inputs'].values():
            if inp['path'] not in checked:checked[inp['path']]=sha256(inp['path'])
            if checked[inp['path']]!=inp['sha256']:
                raise RuntimeError('Frozen input changed during diagnosis: '+inp['path'])
    if sha256(ROOT/'results/analysis.json')!=plan['original_analysis_sha256']:
        raise RuntimeError('Original analysis was overwritten')
    state.update(stage='validated',finished_epoch=time.time(),frozen_files_reverified=len(checked),
                 original_analysis_preserved=True)
    write_json(path,state)
    print(json.dumps(state,indent=2))


if __name__=='__main__':main()
