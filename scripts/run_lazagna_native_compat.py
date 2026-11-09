#!/usr/bin/env python3
"""Preserve old packed-netlist identity by disabling new constant-net merging."""
import concurrent.futures
import fcntl
import json
import os
import time
from lazagna_common import BASE,utc,write_json
from run_lazagna_routes import run_one


def main():
    lock=(BASE/'native_compat_owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    path=BASE/'native_compat_state.json'
    if path.exists():raise RuntimeError('Compatibility state exists')
    cases=json.loads((BASE/'protocol.json').read_text())['diagnostics']['focus_cases']
    jobs=[dict(name=f'native_ideal_compat_{case}_w{w}_i200',case=case,family='native',width=w,arm='fixed',state='queued') for case in cases for w in [100,300]]
    state=dict(owner_pid=os.getpid(),utc=utc(),stage='routing',jobs=jobs,workers=4)
    write_json(path,state)
    write_json(BASE/'native_compat_protocol.json',dict(utc=utc(),reason='New VPR defaults merge_constant_generators=true, unlike paper-era VPR; it merges $undef into $false before reading the unchanged .net, causing an unknown-net input error.',
        change='Set --merge_constant_generators off in separately named native retry arms only. Preserve BLIF, packed.net, fixed.place, RRG, clock=ideal, all routing options and binary bytes.',
        scope='Compatibility control for the exact old packed netlist; this is not evidence of a routing algorithm failure. Original failed attempts remain retained.'))
    pending={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        while any(j['state']=='queued' for j in jobs) or pending:
            prior=json.loads((BASE/'clock_diagnostic_state.json').read_text());parents={j['name']:j for j in prior['jobs']}
            for j in jobs:
                if len(pending)>=4:break
                if j['state']!='queued':continue
                old=parents[f"native_ideal_{j['case']}_w{j['width']}_i200"]
                if old['state'] in ['queued','running']:continue
                log=BASE/'runs'/old['name']/'stdout.log'
                if not log.exists() or 'unknown net $undef' not in log.read_text(errors='replace'):
                    j.update(state='not_needed_no_constant_merge_failure');write_json(path,state);continue
                primary={'directory':str(BASE/'runs'/f"paper_primary_{j['case']}_w300")}
                j['state']='running';pending[pool.submit(run_one,j,primary,'ideal',True)]=j;write_json(path,state)
            for f in list(pending):
                if not f.done():continue
                j=pending.pop(f)
                try:j.update(f.result())
                except Exception as e:j.update(state='supervisor_error',error=repr(e))
                write_json(path,state);print(json.dumps({k:j.get(k) for k in ['name','state','classification','native_legal','error']}),flush=True)
            time.sleep(2)
    state.update(stage='finished',finished_utc=utc());write_json(path,state)


if __name__=='__main__':main()
