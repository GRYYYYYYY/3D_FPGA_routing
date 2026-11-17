"""Run the existing necessary LSTM checks only after the registered CLSTM owner.

Each child owns the shared serial lock itself. Original failures remain intact;
there are no native/STA calls, automatic retries or edits to active batches.
"""
import fcntl
import os
import select
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure

ROOT=D/'LSTM_necessary_readonly_02'


def live(reg):
    p=process_identity(reg['pid'])
    return bool(p and p['state']!='Z' and p['start_ticks']==reg['start_ticks'])


def main():
    queue=ROOT/'queue'
    queue.mkdir(exist_ok=False)
    owner=(queue/'owner.lock').open('w')
    fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    plan=read(ROOT/'execution_plan.json')
    bound={**plan['source_sha256'],str(ROOT/'execution_plan.json'):sha(ROOT/'execution_plan.json')}
    predecessor=Path(plan['predecessor'])
    prior=read(predecessor/'registration.json')
    write(queue/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,
          predecessor=str(predecessor),registered_readonly_stages=3,new_native_or_STA_calls=0))
    started=time.monotonic()
    rows=[]
    try:
        assert all(sha(p)==h for p,h in bound.items())
        write(queue/'status.json',dict(status='waiting_for_registered_CLSTM_recovery_owner_terminal'))
        if live(prior):
            descriptor=os.pidfd_open(prior['pid'])
            assert live(prior)
            event=select.poll();event.register(descriptor,select.POLLIN)
            while not event.poll(45000):pass
            os.close(descriptor)
        assert not live(prior)
        terminal=read(predecessor/'completion.json')
        write(queue/'predecessor_terminal_observed.json',dict(receipt=str(predecessor/'completion.json'),
              sha256=sha(predecessor/'completion.json'),original_owner_exited=True,
              original_passed=terminal['passed'],independent_readonly_checks_not_contingent_on_positive_result=True))
        assert all(sha(p)==h for p,h in bound.items())
        active_started=time.monotonic()
        for stage in plan['stages']:
            if stage.get('requires_native_supplement_passed') and not rows[0]['validation_passed']:
                row=dict(stage=stage['id'],execution_ended=False,validation_passed=False,
                         status='not_executed_native_supplement_prerequisite_failed',
                         complete_command_seconds=None,new_native_or_STA_calls=0)
            else:
                write(queue/'status.json',dict(status='running_registered_readonly_stage',stage=stage['id']))
                measurement=measure(stage['command'],ROOT/(stage['id']+'_measurement'))
                receipt=Path(stage['result'])
                result=read(receipt) if receipt.exists() else {}
                passed=bool(measurement['passed'] and result.get('passed'))
                row=dict(stage=stage['id'],execution_ended=True,validation_passed=passed,
                         status='readonly_validation_passed' if passed else 'readonly_validation_failed_originals_preserved',
                         complete_command_seconds=measurement['complete_command_wall_seconds'],
                         returncode=measurement['returncode'],result=str(receipt),
                         sampled_PSS_kib=measurement['sampled_tree_PSS_peak_kib'],
                         missing_memory_observations=measurement['missing_memory_observations'],
                         new_native_or_STA_calls=0)
            rows.append(row);write(ROOT/'stages.json',rows)
        write(queue/'completion.json',dict(passed=all(r['validation_passed'] for r in rows),
              status='registered_LSTM_readonly_stages_terminal',stages=rows,
              predecessor_wait_seconds=active_started-started,complete_active_queue_seconds=time.monotonic()-active_started,
              original_failures_rewritten=False,new_native_or_STA_calls=0,
              full_native_domain_pair_admitted=False,automatic_retry=False,Goal_complete=False))
        write(queue/'status.json',dict(status='terminal'))
    except BaseException as error:
        write(queue/'completion.json',dict(passed=False,status='readonly_queue_reconciliation_required',
              error=repr(error),stages=rows,original_failures_rewritten=False,new_native_or_STA_calls=0,
              complete_queue_seconds=time.monotonic()-started,automatic_retry=False))
        write(queue/'status.json',dict(status='terminal_reconciliation_required'))
        raise


if __name__=='__main__':
    main()
