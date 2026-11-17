"""One owner, three fixed read-only gates; no original rerun or auto-retry."""
import fcntl
import os
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure

ROOT=D/'LSTM_domain_whole_admission_03'


def main():
    queue=ROOT/'queue';queue.mkdir(exist_ok=False)
    owner=(queue/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    plan=read(ROOT/'execution_plan.json');bound={**plan['source_sha256'],str(ROOT/'execution_plan.json'):sha(ROOT/'execution_plan.json')}
    write(queue/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,
          registered_readonly_stages=3,new_native_or_STA_calls=0))
    started=time.monotonic();rows=[]
    try:
        assert all(sha(p)==h for p,h in bound.items())
        for predecessor in plan['terminated_predecessors']:
            path=Path(predecessor);terminal=read(path/'completion.json')
            reg=read(path/'registration.json');actual=process_identity(reg['pid'])
            assert not actual or actual['state']=='Z' or actual['start_ticks']!=reg['start_ticks']
            assert terminal['passed'],'Known predecessor terminal proof missing'
        for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
        for stage in plan['stages']:
            if rows and not rows[-1]['validation_passed']:
                row=dict(stage=stage['id'],execution_ended=False,validation_passed=False,
                         status='not_executed_required_prior_validation_failed',complete_command_seconds=None,new_native_or_STA_calls=0)
            else:
                write(queue/'status.json',dict(status='running_registered_full_domain_readonly_gate',stage=stage['id']))
                print(dict(started_stage=stage['id']),flush=True)
                command=['/usr/bin/prlimit','--as=68719476736','--',*stage['command']]
                measurement=measure(command,ROOT/(stage['id']+'_measurement'))
                path=Path(stage['result']);result=read(path) if path.exists() else {}
                valid=bool(measurement['passed'] and result.get('passed'))
                row=dict(stage=stage['id'],execution_ended=True,validation_passed=valid,
                         status='readonly_gate_passed' if valid else 'readonly_gate_failed_original_history_preserved',
                         complete_command_seconds=measurement['complete_command_wall_seconds'],
                         returncode=measurement['returncode'],result=str(path),
                         sampled_PSS_kib=measurement['sampled_tree_PSS_peak_kib'],
                         missing_memory_observations=measurement['missing_memory_observations'],new_native_or_STA_calls=0)
                print(dict(ended_stage=stage['id'],passed=valid,complete_seconds=row['complete_command_seconds']),flush=True)
            rows.append(row);write(ROOT/'stages.json',rows)
        pair_path=ROOT/'pair/completion.json';pair=read(pair_path) if pair_path.exists() else {}
        write(queue/'completion.json',dict(passed=all(r['validation_passed'] for r in rows),
              status='registered_full_domain_readonly_gates_terminal',stages=rows,
              complete_active_queue_seconds=time.monotonic()-started,
              actual_matched_complete_quality_pair=pair.get('matched_complete_quality_pair',False),
              formal_complete_time_ratio=None,new_native_or_STA_calls=0,
              historical_failures_rewritten=False,automatic_retry=False,Goal_complete=False))
        write(queue/'status.json',dict(status='terminal'))
    except BaseException as error:
        write(queue/'completion.json',dict(passed=False,status='whole_domain_readonly_reconciliation_required',
              error=repr(error),stages=rows,complete_queue_seconds=time.monotonic()-started,
              original_history_rewritten=False,new_native_or_STA_calls=0,automatic_retry=False))
        write(queue/'status.json',dict(status='terminal_reconciliation_required'))
        raise


if __name__=='__main__':
    main()
