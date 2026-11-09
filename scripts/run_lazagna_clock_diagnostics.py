#!/usr/bin/env python3
"""Keep strict reproduction; diagnose known unroutable BRAM clocks separately."""
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import signal
import time
import xml.etree.ElementTree as ET
from lazagna_common import BASE,utc,write_json
from run_lazagna_routes import run_one


def active_bram_clock(packed):
    if not packed.exists():return False
    root=ET.parse(packed).getroot()
    return any((p.text or '').strip() not in ('','open')
               for b in root.findall('block') if b.get('instance','').startswith('spram[')
               for p in b.findall('clocks/port'))


def main():
    lock=(BASE/'clock_diagnostic_owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    path=BASE/'clock_diagnostic_state.json'
    if path.exists():raise RuntimeError('Diagnostic state exists')
    protocol=json.loads((BASE/'protocol.json').read_text())
    jobs=[dict(name=f'{family}_ideal_{case}_w{width}_i200',case=case,family=family,width=width,arm='fixed',state='queued')
          for case in protocol['diagnostics']['focus_cases'] for family in ['paper','native'] for width in [100,300]]
    state=dict(owner_pid=os.getpid(),utc=utc(),stage='waiting_clock_proof',workers=12,jobs=jobs)
    write_json(path,state)
    while not all((BASE/f'clock_{f}_w300.json').exists() for f in ['paper','native']):time.sleep(5)
    for family in ['paper','native']:
        proof=json.loads((BASE/f'clock_{family}_w300.json').read_text())
        assert proof['complete_graph_scan'] and proof['incoming_edges']==0
    write_json(BASE/'clock_diagnostic_protocol.json',dict(utc=utc(),reason='Published architecture has zero-Fc BRAM clock pins while published template sets clock_modeling=route. Complete RRG scans and explicit no-path errors establish structural unreachability.',
        original_reproduction='Finish all 11 strict primary attempts. Retain their exact outputs and failures.',
        fixed_original_clock_policy='For a case with an active BRAM clock, cancel redundant original-clock fixed executions after their immutable manifest is created; retain a per-run preflight record and SIGTERM receipt. A structural cancellation is not a router convergence result.',
        diagnosis='Separate 44 planned arms: only clock_modeling becomes ideal; reuse the exact original primary packed netlist and placement and original RRG; 200 iterations, failure predictor off. Cases lacking a primary placement are explicitly skipped.',
        interpretation='These ideal-clock runs are diagnostic adaptations, not unmodified LaZagna reproduction; original placement may have been degraded by unreachable clocks. No cross-tool algorithm-only or paper CPD reproduction claim.'))
    state['stage']='routing';write_json(path,state);cancelled=set();pending={};primaries={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        while True:
            original=json.loads((BASE/'route_state.json').read_text())
            for j in original['jobs']:
                if j['arm']=='primary' and j['state'] not in ['queued','running']:
                    primaries[j['case']]=j
                if j['arm']!='fixed' or j['state']!='running' or j['name'] in cancelled:continue
                directory=BASE/'runs'/j['name'];receipt=directory/'manifest.json'
                packed=BASE/'runs'/f"paper_primary_{j['case']}_w300"/'packed.net'
                if not receipt.exists() or not active_bram_clock(packed):continue
                m=json.loads(receipt.read_text())
                if m.get('status')!='running' or 'pid' not in m:continue
                write_json(directory/'clock_preflight_cancel.json',dict(utc=utc(),reason='Active BRAM clock has zero incoming physical edges in the published architecture; additional iteration/width runs cannot repair this.',
                            packed_netlist=str(packed),pid=m['pid'],signal='SIGTERM',classification='cancelled_structural_clock_unreachable'))
                try:os.killpg(m['pid'],signal.SIGTERM)
                except ProcessLookupError:pass
                cancelled.add(j['name'])
            for j in jobs:
                if len(pending)>=12:break
                if j['state']!='queued' or j['case'] not in primaries:continue
                primary=primaries[j['case']]
                if not (BASE/'runs'/f"paper_primary_{j['case']}_w300"/'fixed.place').exists():
                    j.update(state='not_run_no_fixed_placement');write_json(path,state);continue
                j['state']='running';pending[pool.submit(run_one,j,primary,'ideal')]=j;write_json(path,state)
            for f in list(pending):
                if not f.done():continue
                j=pending.pop(f)
                try:j.update(f.result())
                except Exception as e:j.update(state='supervisor_error',error=repr(e))
                write_json(path,state);print(json.dumps({k:j.get(k) for k in ['name','state','classification','native_legal','error']}),flush=True)
            if original['stage']=='finished' and not pending and all(j['state']!='queued' for j in jobs):break
            time.sleep(2)
    state.update(stage='finished',finish_utc=utc(),cancelled_original_fixed=sorted(cancelled));write_json(path,state)


if __name__=='__main__':main()
