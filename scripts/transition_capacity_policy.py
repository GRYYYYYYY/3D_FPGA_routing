#!/usr/bin/env python3
"""Stop the diagnostic owner at the post-200 checkpoint for a proved-capacity policy.

Only this experiment's exact owner/finalizer and recorded process groups can be
signaled. Any just-started 500-stage runs are retained as cancelled setup/search
attempts. Native 200 results are preserved; the main agent inspects the receipt
before resuming the revised finite queue.
"""
import fcntl
import json
import os
from pathlib import Path
import signal
import time

from check_route import sha256
from diagnose_failures import BASE,write_json


def main():
    lock=(BASE/'capacity_transition.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    policy_path=BASE/'certified_infeasibility_policy.json';policy=json.loads(policy_path.read_text())
    for proof in policy['cases'].values():
        assert sha256(proof['evidence'])==proof['evidence_sha256']
        assert sha256(proof['verification'])==proof['verification_sha256']
        assert json.loads(Path(proof['verification']).read_text())['passed']
    receipt=dict(owner_pid=os.getpid(),started_epoch=time.time(),state='waiting_for_post200_checkpoint',
                 policy_sha256=sha256(policy_path),cancelled=[])
    receipt_path=BASE/'capacity_policy_transition.json';write_json(receipt_path,receipt)
    while True:
        state=json.loads((BASE/'native_state.json').read_text())
        owner=state['owner_pid'];proc=Path('/proc')/str(owner)
        if not proc.exists():raise RuntimeError('Original native owner exited; inspect before recovery')
        if state['active_stage']=='normal500':break
        if state['active_stage']!='normal200':raise RuntimeError('Unexpected stage at transition')
        time.sleep(5)
    assert 'normal200' in state['stages_done']
    assert b'scripts/diagnose_failures.py' in (proc/'cmdline').read_bytes()
    validation=json.loads((BASE/'validation_native.json').read_text())
    validator=Path('/proc')/str(validation['owner_pid'])
    if validator.exists():
        assert b'finalize_failure_diagnosis.py' in (validator/'cmdline').read_bytes()
        os.kill(validation['owner_pid'],signal.SIGTERM)
    os.kill(owner,signal.SIGINT);time.sleep(1)
    state=json.loads((BASE/'native_state.json').read_text())
    setup_jobs=[j for j in state['jobs'] if j['stage']=='normal500']
    for job in setup_jobs:
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
    if proc.exists():raise RuntimeError('Original owner did not exit; preserve state for inspection')
    for job in setup_jobs:
        path=Path(job['output'])/'manifest.json'
        if not path.exists():job['state']='not_run_at_capacity_checkpoint';continue
        m=json.loads(path.read_text());assert m['status']!='running'
        if m['returncode'] not in [0,2]:
            m.update(status='cancelled_at_capacity_checkpoint',capacity_policy_sha256=sha256(policy_path),
                     cancellation_reason='Transition to independently verified infeasibility policy before further iteration-500 trials')
            write_json(path,m)
        job.update(state=m['status'],returncode=m['returncode'],metrics=m['metrics'],process_wall_seconds=m['process_wall_seconds'])
    write_json(BASE/'native_500_checkpoint_attempts.json',dict(jobs=setup_jobs,policy_sha256=sha256(policy_path),
                                                             scope='Preserved scheduling-transition attempts; not algorithmic failures'))
    write_json(BASE/'native_state_before_capacity_policy.json',state)
    state['jobs']=[j for j in state['jobs'] if j['stage']!='normal500']
    state.update(active_stage='ready_for_capacity_policy_resume',capacity_policy_sha256=sha256(policy_path),
                 capacity_checkpoint_epoch=time.time())
    write_json(BASE/'native_state.json',state)
    validation.update(stage='capacity_policy_checkpoint',checkpoint_epoch=time.time())
    write_json(BASE/'validation_native.json',validation)
    receipt.update(state='ready_for_main_model_inspection',original_owner=owner,finished_epoch=time.time(),
                   setup_attempts=len([j for j in setup_jobs if (Path(j['output'])/'manifest.json').exists()]))
    write_json(receipt_path,receipt);print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
