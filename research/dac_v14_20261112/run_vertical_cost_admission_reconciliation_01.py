"""One read-only audit owner; reuse all original weighted native results."""
import fcntl
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from recovery_prefix_v1 import live_identity


def main():
    root = D/'vertical_cost_admission_reconciliation_01'
    execution = root/'execution'
    assert not execution.exists(), 'Preserve every attempt; no automatic retry'
    execution.mkdir()
    plan = read(root/'execution_plan.json')
    assert all(sha(p)==h for p,h in plan['source_sha256'].items())
    assert read(D/'vertical_cost_baseline_dev_01/queue_priority_05/completion.json')['status']=='registered_baseline_attempt_terminal'
    assert read(D/'CP1r3_raw_admission_01/queue_priority_04/completion.json')['status']=='registered_raw_admission_terminal'
    assert not live_identity(4040853,'1967534397')
    write(execution/'registration.json',dict(**process_identity(os.getpid()),
          source_sha256=plan['source_sha256'],native_or_STA_calls=0))
    write(execution/'status.json',dict(status='waiting_for_existing_serial_slot',
          original_running_and_queued_rules_unchanged=True))
    start_wait=time.monotonic()
    with (D/'critical_scope_runner.lock').open('r') as lock:
        while True:
            try:
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                select.select([],[],[],15)
        waited=time.monotonic()-start_wait
        assert all(sha(p)==h for p,h in plan['source_sha256'].items())
        start=time.monotonic();rows=[]
        for role,weight in [('weight_05',.5),('weight_1',1.),('weight_2',2.)]:
            output=execution/(role+'_admission.json')
            assert not output.exists()
            command=[sys.executable,'-B',str(D/'vertical_cost_evidence_reconcile_v3.py'),
                     '--mode','weighted','--transaction',plan['transaction'],
                     '--role',role,'--weight',str(weight),'--output',str(output),
                     '--serial-lock-fd',str(lock.fileno())]
            write(execution/'status.json',dict(status='readonly_actual_admission',role=role))
            before=time.monotonic()
            with (execution/(role+'.log')).open('x') as log:
                child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                                       pass_fds=(lock.fileno(),))
                write(execution/'active_child.json',dict(**process_identity(child.pid),role=role))
                try:
                    code=child.wait(timeout=600)
                except subprocess.TimeoutExpired:
                    child.kill();code=child.wait()
            proof=read(output) if output.exists() else None
            rows.append(dict(role=role,weight=weight,returncode=code,
                complete_audit_command_seconds=time.monotonic()-before,
                passed=bool(code==0 and proof and proof['passed']),
                receipt=str(output),new_native_or_STA_calls=0))
            write(execution/'process_costs.json',rows)
        assert all(sha(p)==h for p,h in plan['source_sha256'].items())
        write(execution/'completion.json',dict(status='readonly_reconciliation_terminal',
              all_three_roles_passed=all(r['passed'] for r in rows),roles=rows,
              slot_wait_seconds=waited,complete_readonly_scope_seconds=time.monotonic()-start,
              source_sha256=plan['source_sha256'],new_native_or_STA_calls=0,
              original_failure_rewritten=False,whole_method_or_cross_input_claim=False))
        write(execution/'status.json',dict(status='terminal'))


if __name__=='__main__':
    main()
