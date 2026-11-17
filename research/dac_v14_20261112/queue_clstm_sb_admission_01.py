"""Single readonly successor; wait for the existing confirmation owner to exit."""
import fcntl
import os
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from recovery_prefix_v1 import live_identity
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure

ROOT=D/'CLSTM_SB_complete_admission_01'
COHORT=D/'cp1r5_clstm_sb_pair_01'


def main():
    queue=ROOT/'queue';queue.mkdir(exist_ok=False)
    owner=(queue/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    plan=read(ROOT/'plan.json');bound={**plan['source_sha256'],str(ROOT/'plan.json'):sha(ROOT/'plan.json')}
    write(queue/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,
          predecessor=str(COHORT/'queue'),registered_readonly_stages=['native','domain','pair'],new_native_or_STA_calls=0))
    started=time.monotonic();rows=[]
    try:
        predecessor=read(COHORT/'queue/registration.json')
        write(queue/'status.json',dict(status='waiting_for_original_CLSTM_SB_pair_terminal'))
        while not (COHORT/'queue/completion.json').exists():
            assert live_identity(predecessor['pid'],predecessor['start_ticks']),'Original owner missing without terminal receipt'
            time.sleep(15)
        while live_identity(predecessor['pid'],predecessor['start_ticks']):time.sleep(2)
        waited=time.monotonic()-started
        assert all(sha(p)==h for p,h in bound.items())
        for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
        # Reserve the next shared slot, then let each existing audit acquire it.
        with (D/'critical_scope_runner.lock').open() as lock:fcntl.flock(lock,fcntl.LOCK_EX)
        for arm in ['native','domain','pair']:
            write(queue/'status.json',dict(status='running_registered_readonly_admission',stage=arm))
            command=['/usr/bin/prlimit','--as=68719476736','--',sys.executable,'-B',
                     str(D/'admit_cp1r5_clstm_sb_pair_01.py'),'--role',arm]
            measured=measure(command,ROOT/(arm+'_measurement'))
            output=ROOT/arm/'completion.json';result=read(output) if output.exists() else {}
            rows.append(dict(stage=arm,execution_ended=True,command_returncode=measured['returncode'],
                complete_command_seconds=measured['complete_command_wall_seconds'],
                validation_passed=bool(measured['passed'] and result.get('passed')),
                quality_admitted=result.get('quality_admitted',result.get('matched_complete_quality_pair',False)),
                result=str(output),status=result.get('status','missing_readonly_completion'),
                sampled_PSS_kib=measured['sampled_tree_PSS_peak_kib'],
                missing_memory_observations=measured['missing_memory_observations']))
            write(ROOT/'stages.json',rows)
            assert not measured['live_descendants_after_command_exit'],'Readonly process tree not closed'
        pair=read(ROOT/'pair/completion.json') if (ROOT/'pair/completion.json').exists() else {}
        write(queue/'completion.json',dict(passed=all(r['command_returncode']==0 for r in rows),
            status='all_registered_readonly_stages_accounted',stages=rows,wait_for_predecessor_seconds=waited,
            complete_queue_seconds=time.monotonic()-started,
            matched_complete_quality_pair=pair.get('matched_complete_quality_pair',False),
            new_native_or_STA_calls=0,automatic_retry=False,Goal_complete=False))
        write(queue/'status.json',dict(status='terminal'))
    except BaseException as error:
        write(queue/'completion.json',dict(passed=False,status='readonly_successor_requires_reconciliation',
            error=repr(error),stages=rows,complete_queue_seconds=time.monotonic()-started,
            new_native_or_STA_calls=0,automatic_retry=False))
        write(queue/'status.json',dict(status='terminal_reconciliation_required'));raise


if __name__=='__main__':main()
