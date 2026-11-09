#!/usr/bin/env python3
"""Audit each shared width graph once its registered routing trials are terminal.

This only schedules the unchanged independent auditor. Identical graph SHA256s
may share one scan even when preparation exported separate copies. Final audit
still rechecks every successful route and graph hash using the ordinary cache.
"""
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import time

from audit_matrix import check_group
from diagnose_failures import BASE,write_json


def main():
    lock=(BASE/'width_audit.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    state_path=BASE/'width_incremental_audit_state.json'
    if state_path.exists():raise RuntimeError('Existing audit owner requires inspection')
    queue=json.loads((BASE/'width_parallel_state.json').read_text())
    jobs=[j for j in queue['jobs'] if not j['stage'].startswith('prepare_')]
    assert len(jobs)==114
    groups={}
    for j in jobs:
        prep=Path(j['graph_preparation']);m=json.loads((prep/'manifest.json').read_text())
        digest=m['outputs']['rr_graph.xml']['sha256']
        group=groups.setdefault(digest,dict(graph=str(prep/'rr_graph.xml'),ids=[]))
        group['ids'].append(j['id'])
    state=dict(owner_pid=os.getpid(),started_epoch=time.time(),stage='auditing_terminal_groups',
               total_graph_groups=len(groups),completed=[],pending=[])
    write_json(state_path,state);rows=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        futures={}
        waiting=dict(groups)
        while waiting or futures:
            queue=json.loads((BASE/'width_parallel_state.json').read_text())
            current={j['id']:j for j in queue['jobs']}
            for digest,group in list(waiting.items()):
                if len(futures)>=2:break
                selected=[current[i] for i in group['ids']]
                if any(j['state'] in ['queued','running'] for j in selected):continue
                if any(j['state'] not in ['completed','failed','timeout'] for j in selected):
                    raise RuntimeError('Width group has a non-routing error')
                successes=[j for j in selected if j['state']=='completed']
                del waiting[digest]
                if successes:futures[pool.submit(check_group,(group['graph'],successes))]=digest
                else:state['completed'].append(dict(rr_graph_sha256=digest,successful_routes=0))
            state['pending']=list(futures.values());write_json(state_path,state)
            if not futures:
                if waiting:time.sleep(5)
                continue
            done,_=concurrent.futures.wait(futures,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                digest=futures.pop(future);checked=future.result()
                if not all(r['passed'] for r in checked):raise RuntimeError('A successful width route failed independent audit')
                rows.extend(checked);write_json(BASE/'audits_width_incremental.json',rows)
                state['completed'].append(dict(rr_graph_sha256=digest,successful_routes=len(checked)))
                write_json(state_path,state)
                print(json.dumps(dict(graph_groups=len(state['completed']),audited_routes=len(rows))),flush=True)
    state.update(stage='complete',finished_epoch=time.time(),pending=[],audited_routes=len(rows))
    write_json(state_path,state)


if __name__=='__main__':main()
