#!/usr/bin/env python3
"""Isolate extra iterations from post-50 high-effort mode on the two regressions."""
import argparse
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from check_route import sha256
from collect_results import native_counters
from diagnose_failures import BASE, PLAN, ROOT, source_key, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--common-baselines',action='store_true')
    args=parser.parse_args()
    suffix='_baselines' if args.common_baselines else ''
    lock=(BASE/('schedule_controls'+suffix+'.lock')).open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    path=BASE/('schedule_controls'+suffix+'.json')
    if path.exists():raise RuntimeError('Inspect existing schedule-control queue before reusing')
    plan=json.loads(PLAN.read_text())
    if args.common_baselines:
        sources=[s for s in plan['sources'] if s['variant']=='a0' and s['circuit'] not in ['clstm_like.small','robot_rl']]
        sources.sort(key=lambda s:(not s['circuit'].startswith('elliptic'),s['circuit']))
        assert len(sources)==11
    else:
        sources=[s for s in plan['sources'] if s['circuit'] in ['clstm_like.small','robot_rl']]
        assert len(sources)==5
    jobs=[dict(circuit=s['circuit'],variant=s['variant'],source_key=source_key(s),
               original_output=s['original_output'],state='queued',
               output=str(BASE/'runs'/('schedule200__'+source_key(s)))) for s in sources]
    state=dict(owner_pid=os.getpid(),started_epoch=time.time(),protocol_sha256=sha256(PLAN),
               purpose='Counterfactual to off200: keep normal congestion mode through 200 iterations',
               scope='Common-failure A0 baselines' if args.common_baselines else 'Two specific regressions and their controls',
               predictor='off',budget=200,congestion_mode_after_iteration=200,workers=3,jobs=jobs)
    write_json(path,state)
    by_key={source_key(s):s for s in sources}
    def run(job):
        source=by_key[job['source_key']];m=source['manifest']
        command=[sys.executable,str(ROOT/'scripts/run_vpr.py'),'--reuse',m['reuse'],
                 '--binary',m['inputs']['binary']['path'],'--output',job['output'],'--timeout','3600']
        for key,value in m['experimental_environment'].items():command+=['--env',key+'='+value]
        extra=m['command'][m['command'].index('--read_rr_graph')+2:]
        command+=['--extra',*extra,'--routing_failure_predictor','off','--max_router_iterations','200',
                  '--congested_routing_iteration_threshold','1.0']
        with (BASE/('schedule200__'+job['source_key']+'.log')).open('w') as stream:
            subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=False)
        result=json.loads((Path(job['output'])/'manifest.json').read_text())
        counters,history=native_counters((Path(job['output'])/'vpr.log').read_text())
        write_json(Path(job['output'])/'iterations.json',history)
        for role in ['binary','architecture','circuit','packed_netlist','placement','rr_graph']:
            if result['inputs'][role]!=m['inputs'][role]:raise RuntimeError('Fixed input mismatch: '+role)
        if result['experimental_environment']!=m['experimental_environment']:raise RuntimeError('Environment mismatch')
        return dict(state=result['status'],metrics={**result['metrics'],**counters},returncode=result['returncode'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={}
        for job in jobs:
            job['state']='running';futures[pool.submit(run,job)]=job
        write_json(path,state)
        for future in concurrent.futures.as_completed(futures):
            job=futures[future]
            try:job.update(future.result())
            except Exception as error:job.update(state='supervisor_error',error=str(error))
            write_json(path,state);print(json.dumps(job),flush=True)
    if any(j['state']=='supervisor_error' for j in jobs):raise RuntimeError('Schedule control failed')
    state['finished_epoch']=time.time();write_json(path,state)
    with (BASE/('schedule_audit'+suffix+'.log')).open('w') as stream:
        subprocess.run([sys.executable,str(ROOT/'scripts/audit_matrix.py'),'--matrix',str(path),
                        '--output',str(BASE/('audits_schedule'+suffix+'.json')),'--workers','2'],
                        cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    audits={r['output']:r for r in json.loads((BASE/('audits_schedule'+suffix+'.json')).read_text())}
    rows=[]
    for job in jobs:
        reference=BASE/'runs'/('off200__'+job['source_key'])
        a=native_counters((reference/'vpr.log').read_text())[1]
        b=json.loads((Path(job['output'])/'iterations.json').read_text())
        clean=lambda xs:[{k:v for k,v in x.items() if k!='seconds'} for x in xs]
        n=min(50,len(a),len(b));prefix=clean(a[:n])==clean(b[:n])
        if not prefix:raise RuntimeError('Schedule comparison differs before intervention')
        audit=audits.get(job['output']);passed=job['state']=='completed' and bool(audit and audit['passed'])
        if job['state']=='completed' and not passed:raise RuntimeError('Schedule success lacks audit')
        rows.append(dict(**job,common_prefix_iterations=n,common_prefix_passed=prefix,
                         independent_audit_passed=bool(audit and audit['passed']),valid_solution=passed,
                         fixed50_reference=str(reference)))
    write_json(BASE/('schedule_comparison'+suffix+'.json'),dict(complete=True,rows=rows,protocol_sha256=sha256(PLAN),
        scope=state['scope']+'. All runs retain identical fixed inputs, binary and algorithm flags; the sole off200 difference is congestion-mode threshold 1.0 instead of 0.25.'))


if __name__=='__main__':main()
