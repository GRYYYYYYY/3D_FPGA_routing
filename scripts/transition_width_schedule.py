#!/usr/bin/env python3
"""Preserve finished 500-iteration trials before resuming parallel width scheduling.

Only graph-export setup may be interrupted. No routing trial, input, or solver
parameter changes. The receipt requires main-agent inspection before restart.
"""
import fcntl
import json
import os
from pathlib import Path
import signal
import time

from diagnose_failures import BASE, write_json


def main():
    lock=(BASE/'width_transition.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    receipt=dict(owner_pid=os.getpid(),started_epoch=time.time(),
                 state='waiting_for_post500_checkpoint',cancelled=[])
    receipt_path=BASE/'width_schedule_transition.json';write_json(receipt_path,receipt)
    while True:
        state=json.loads((BASE/'native_state.json').read_text())
        owner=state['owner_pid'];proc=Path('/proc')/str(owner)
        if not proc.exists():raise RuntimeError('Native owner exited; inspect existing state')
        if state['active_stage']=='prepare_w120_native':break
        if state['active_stage']!='normal500_after_capacity_check':
            raise RuntimeError('Unexpected stage; no processes will be signaled')
        time.sleep(1)
    trials=[j for j in state['jobs'] if j['stage']=='normal500_after_capacity_check']
    assert len(trials)==73 and all(j['state'] in ['completed','failed','timeout'] for j in trials)
    assert 'normal500_after_capacity_check' in state['stages_done']
    assert b'scripts/diagnose_failures.py' in (proc/'cmdline').read_bytes()
    validation=json.loads((BASE/'validation_native.json').read_text())
    validator=Path('/proc')/str(validation['owner_pid'])
    if validator.exists():
        assert b'finalize_failure_diagnosis.py' in (validator/'cmdline').read_bytes()
        os.kill(validation['owner_pid'],signal.SIGTERM)
    os.kill(owner,signal.SIGINT);time.sleep(1)
    state=json.loads((BASE/'native_state.json').read_text())
    setups=[j for j in state['jobs'] if j['stage']=='prepare_w120_native']
    assert not any(j['stage'].startswith('w120_') for j in state['jobs'])
    for job in setups:
        path=Path(job['output'])/'manifest.json'
        if not path.exists():continue
        manifest=json.loads(path.read_text())
        if manifest['status']!='running':continue
        pgid=manifest['process_group_id'];child=Path('/proc')/str(pgid)
        try:
            assert manifest['supervisor_pid']==owner
            assert b'/usr/bin/time' in (child/'cmdline').read_bytes()
            assert (child/'cwd').resolve()==Path(job['output'])
            os.killpg(pgid,signal.SIGTERM)
            receipt['cancelled'].append(dict(output=job['output'],process_group_id=pgid))
        except (FileNotFoundError,ProcessLookupError):pass
    for _ in range(60):
        if not proc.exists():break
        time.sleep(1)
    if proc.exists():raise RuntimeError('Owner did not exit; preserve evidence for inspection')
    for job in setups:
        path=Path(job['output'])/'manifest.json'
        if not path.exists():job['state']='not_run_at_width_checkpoint';continue
        m=json.loads(path.read_text());assert m['status']!='running'
        if m['returncode'] not in [0,2]:
            m.update(status='cancelled_graph_preparation_at_width_checkpoint',
                     cancellation_reason='Resume independent widths together under the same resource and solver limits')
            write_json(path,m)
        job.update(state=m['status'],returncode=m['returncode'],metrics=m['metrics'],
                   process_wall_seconds=m['process_wall_seconds'])
    write_json(BASE/'width_checkpoint_preparations.json',dict(jobs=setups,
               scope='Graph-export setup attempts, not formal routing trials'))
    write_json(BASE/'native_state_before_parallel_widths.json',state)
    state['jobs']=[j for j in state['jobs'] if j['stage']!='prepare_w120_native']
    state['stages_done']=[s for s in state['stages_done'] if s!='prepare_w120_native']
    state.update(active_stage='ready_for_parallel_width_resume',width_checkpoint_epoch=time.time())
    write_json(BASE/'native_state.json',state)
    validation.update(stage='width_schedule_checkpoint',checkpoint_epoch=time.time())
    write_json(BASE/'validation_native.json',validation)
    receipt.update(state='ready_for_main_model_inspection',original_owner=owner,
                   finished_epoch=time.time(),preserved_500_trials=len(trials))
    write_json(receipt_path,receipt);print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
