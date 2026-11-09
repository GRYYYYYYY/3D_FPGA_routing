#!/usr/bin/env python3
"""Drain admitted W=100 trials while using idle slots for independent widths.

SIGINT stops only the Python owner's admission loop. Its executor waits for all
already admitted VPR processes, which have separate process groups and retain
their original supervision, timeout, manifests and complete search trajectories.
The width owner shares the global worker/memory limits, then reconciles terminal
receipts under the original owner lock and starts the independent finalizer.
"""
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from check_route import sha256
from diagnose_failures import BASE,ROOT,make_job,run_one,source_key,write_json


def main():
    lock=(BASE/'width_overlap.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    protocol=ROOT/'configs/failure_diagnosis_native.json'
    plan=json.loads(protocol.read_text());plan['protocol_path']=str(protocol)
    sources={source_key(s):s for s in plan['sources']}
    path=BASE/'width_parallel_state.json'
    if path.exists():raise RuntimeError('Existing overlap requires inspection before recovery')
    state=dict(owner_pid=os.getpid(),started_epoch=time.time(),protocol_sha256=sha256(protocol),
               active_stage='waiting_for_all_500_trials_admitted',jobs=[],stages_done=[])
    write_json(path,state)
    while True:
        native=json.loads((BASE/'native_state.json').read_text())
        assert native['active_stage']=='normal500_after_capacity_check'
        owner=native['owner_pid'];proc=Path('/proc')/str(owner)
        assert b'scripts/diagnose_failures.py' in (proc/'cmdline').read_bytes()
        extended=[j for j in native['jobs'] if j['stage']=='normal500_after_capacity_check']
        assert len(extended)==73
        if not any(j['state']=='queued' for j in extended):
            if all((Path(j['output'])/'manifest.json').exists() for j in extended):break
        time.sleep(2)
    # The earlier, unused post-500 transition watcher must not signal this owner.
    old_transition=BASE/'width_schedule_transition.json'
    if old_transition.exists():
        prior=json.loads(old_transition.read_text());old_proc=Path('/proc')/str(prior['owner_pid'])
        if old_proc.exists():
            assert b'transition_width_schedule.py' in (old_proc/'cmdline').read_bytes()
            os.kill(prior['owner_pid'],signal.SIGTERM)
        prior.update(state='superseded_before_transition_by_overlap',superseded_epoch=time.time())
        write_json(old_transition,prior)
    validation=json.loads((BASE/'validation_native.json').read_text())
    validator=Path('/proc')/str(validation['owner_pid'])
    if validator.exists():
        assert b'finalize_failure_diagnosis.py' in (validator/'cmdline').read_bytes()
        os.kill(validation['owner_pid'],signal.SIGTERM)
    write_json(BASE/'native_state_before_width_overlap.json',native)
    os.kill(owner,signal.SIGINT)
    state.update(draining_owner_pid=owner,drain_started_epoch=time.time(),
                 active_stage='draining_fixed_width_trials')
    write_json(path,state)
    validation.update(stage='waiting_for_overlap_reconciliation',overlap_owner_pid=os.getpid())
    write_json(BASE/'validation_native.json',validation)

    def foreign_running():
        jobs=[]
        for j in extended:
            m=json.loads((Path(j['output'])/'manifest.json').read_text())
            if m['status']=='running':
                if not proc.exists():raise RuntimeError('Draining supervisor exited before terminal manifests')
                jobs.append(j)
        return jobs

    def memory_need(j):
        m=sources[j['source_key']]['manifest']
        return max(1.0,(m.get('peak_rss_kib') or 1048576)/1024**2*1.35*j['width']/100)

    def stage(name,jobs):
        state['jobs'].extend(jobs);state['active_stage']=name;write_json(path,state)
        work=sorted(jobs,key=lambda j:sources[j['source_key']]['manifest']['process_wall_seconds'],reverse=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=plan['workers']) as pool:
            pending={}
            while work or pending:
                foreign=foreign_running()
                used=sum(memory_need(j) for j in foreign)+sum(v[1] for v in pending.values())
                while work and len(pending)+len(foreign)<plan['workers']:
                    index=next((i for i,j in enumerate(work) if used+memory_need(j)<=plan['estimated_memory_limit_gib']),None)
                    if index is None:break
                    job=work.pop(index);need=memory_need(job)
                    job.update(state='running',started_epoch=time.time())
                    pending[pool.submit(run_one,job,sources[job['source_key']],plan)]=(job,need)
                    used+=need;write_json(path,state)
                if not pending:
                    if not foreign and work:raise RuntimeError('No width job fits resource limits')
                    time.sleep(2);continue
                done,_=concurrent.futures.wait(pending,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    job,_=pending.pop(future)
                    try:
                        m=future.result()
                        job.update(state=m['status'],metrics=m['metrics'],returncode=m['returncode'],
                                   process_wall_seconds=m['process_wall_seconds'])
                    except Exception as error:job.update(state='supervisor_error',error=str(error))
                    job['finished_epoch']=time.time();write_json(path,state)
                    print(json.dumps({k:job[k] for k in ['id','state']}),flush=True)
        bad=[j for j in jobs if j['state']=='supervisor_error' or
             (j['state']!='timeout' and j.get('returncode') not in [0,2])]
        if bad:raise RuntimeError('Width stage needs inspection: '+str([j['id'] for j in bad]))
        state['stages_done'].append(name);write_json(path,state)

    a0s=[s for s in sources.values() if s['variant']=='a0']
    prep=[make_job(s,f'prepare_w{w}_native_parallel',1,w) for w in plan['widths'] for s in a0s]
    assert len(prep)==39
    stage('prepare_widths_native_parallel',prep)
    lookup={(j['circuit'],j['width']):j['output'] for j in prep}
    chosen=[s for s in sources.values() if s['variant'] in plan['width_exceptions'].get(s['circuit'],plan['width_variants'])]
    jobs=[make_job(s,f'w{w}_normal200',200,w,lookup[s['circuit'],w]) for w in plan['widths'] for s in chosen]
    assert len(jobs)==114 and len({j['id'] for j in prep+jobs})==153
    for job in jobs:job['congestion_mode_after_iteration']=200
    stage('width_scan_normal200_parallel',jobs)
    state['active_stage']='waiting_for_drained_owner';write_json(path,state)
    while foreign_running() or proc.exists():time.sleep(2)
    original_lock=(BASE/'native_owner.lock').open('w')
    fcntl.flock(original_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    original_lock.write(str(os.getpid()));original_lock.flush()
    native=json.loads((BASE/'native_state.json').read_text())
    assert native['owner_pid']==owner and native['protocol_sha256']==sha256(protocol)
    assert not any(j['stage'].startswith(('prepare_','w120_','w140_','w160_')) for j in native['jobs'])
    for job in native['jobs']:
        if job['stage']!='normal500_after_capacity_check':continue
        m=json.loads((Path(job['output'])/'manifest.json').read_text())
        assert m['status'] in ['completed','failed','timeout']
        assert m['status']=='timeout' or m['returncode'] in [0,2]
        job.update(state=m['status'],metrics=m['metrics'],returncode=m['returncode'],
                   process_wall_seconds=m['process_wall_seconds'],
                   finished_epoch=job.get('started_epoch',state['drain_started_epoch'])+m['process_wall_seconds'])
    native['jobs'].extend(state['jobs'])
    native['stages_done']=list(dict.fromkeys(native['stages_done']+
        ['normal500_after_capacity_check']+state['stages_done']))
    native.update(owner_pid=os.getpid(),drained_owner_pid=owner,finished_epoch=time.time(),
                  active_stage='routing_finished',width_execution_schedule='Independent widths overlapped with draining W100 trials under shared worker/memory limits')
    assert len(native['jobs'])==361
    write_json(BASE/'native_state.json',native)
    state.update(active_stage='reconciled',finished_epoch=time.time());write_json(path,state)
    with (ROOT/'logs/failure_diagnosis_native_validation_overlap.log').open('w') as stream:
        child=subprocess.Popen([sys.executable,str(ROOT/'scripts/finalize_failure_diagnosis.py'),'--native-primary'],
                               cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    state['finalizer_pid']=child.pid;write_json(path,state)
    print(json.dumps(dict(reconciled=True,finalizer_pid=child.pid)),flush=True)


if __name__=='__main__':main()
