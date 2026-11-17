"""Continue only the independently audited CLSTM stage after the completed LSTM readonly owner."""
import fcntl
import os
import select
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure

ROOT = D/'CLSTM_domain_recovery_03'


def live(registration):
    actual = process_identity(registration['pid'])
    return bool(actual and actual['state']!='Z' and actual['start_ticks']==registration['start_ticks'])


def main():
    queue = ROOT/'queue'
    queue.mkdir(exist_ok=False)
    execution = read(ROOT/'execution_plan.json')
    bound = {**execution['source_sha256'],str(ROOT/'execution_plan.json'):sha(ROOT/'execution_plan.json')}
    predecessor = Path(execution['predecessor'])
    previous = read(predecessor/'registration.json')
    write(queue/'registration.json', dict(**process_identity(os.getpid()), source_sha256=bound,
          predecessor=str(predecessor), original_native_queries_to_reuse=23,
          original_registered_recovery_failed_admission_preserved=True))
    started = time.monotonic()
    slot_started = None
    try:
        assert all(sha(p)==h for p,h in bound.items())
        write(queue/'status.json',dict(status='waiting_for_registered_LSTM_readonly_owner_terminal'))
        if live(previous):
            descriptor = os.pidfd_open(previous['pid'])
            assert live(previous)
            event = select.poll()
            event.register(descriptor, select.POLLIN)
            while not event.poll(45000):
                pass
            os.close(descriptor)
        assert not live(previous)
        terminal = read(predecessor/'completion.json')
        assert terminal['passed'] and terminal['status']=='registered_LSTM_readonly_stages_terminal', 'LSTM readonly predecessor failure requires reconciliation'
        write(queue/'predecessor_terminal_observed.json',dict(passed=True,
              receipt=str(predecessor/'completion.json'),sha256=sha(predecessor/'completion.json'),
              original_owner_exited=True,scientific_negative_does_not_stop_research=True))
        with (D/'critical_scope_runner.lock').open('r') as lock:
            write(queue/'status.json',dict(status='waiting_for_shared_serial_slot'))
            fcntl.flock(lock,fcntl.LOCK_EX)
            slot_started = time.monotonic()
            assert all(sha(p)==h for p,h in bound.items())
            plan = read(ROOT/'arm/plan.json')
            audit = read(plan['stage_audit'])
            assert audit['passed'] and not audit['complete_candidate_admitted']
            write(queue/'status.json',dict(status='serial_native_stage_byte_revalidation'))
            # Actual source freshness is checked here, never during the
            # predecessor's graph/route work or from metadata guards alone.
            sys.path[:0] = [str(Path(plan['release'])/'runtime'),str(ROOT/'runtime_extension')]
            from recovery_prefix_v1 import Evidence
            proof = Evidence()
            tick = time.monotonic()
            proof.verify(audit['source_sha256'])
            proof.unchanged()
            write(ROOT/'byte_revalidation.json',dict(passed=True,
                  complete_readonly_seconds=time.monotonic()-tick,source_sha256=proof.bound,
                  new_native_or_STA_calls=0,candidate_or_full_method_admitted=False,
                  qualification='Existing actual stage-audit closure revalidated byte-exact under the serial lock; candidate physical/domain/STA and final acceptance remain new stages.'))
            case = ROOT/'arm'
            runtime = Path(plan['release'])/'runtime'
            command = [sys.executable,'-B',str(runtime/'supervise_method_phase.py'),
                       '--receipt',str(case/'supervision.json'),'--',sys.executable,'-B',
                       str(ROOT/'runtime_extension/run_interrupted_full_flow_recovery_v1.py'),
                       '--plan',str(case/'plan.json'),'--output',str(case/'flow')]
            write(queue/'status.json',dict(status='running_original_CLSTM_domain_suffix',case=str(case)))
            measurement = measure(command,case/'measurement')
            supervision = read(case/'supervision.json') if (case/'supervision.json').exists() else {}
            flow = read(case/'flow/completion.json') if (case/'flow/completion.json').exists() else {}
            passed = measurement['passed'] and supervision.get('passed') and flow.get('passed')
            historical = read(plan['historical_failed_measurement'])
            native_reuse_receipts=[]
            for receipt in (case/'flow').glob('**/*_stage_reuse.json'):
                value=read(receipt)
                if value.get('passed') and value.get('stage')=='native_source_control':
                    seal=receipt.parent/'stage_reuse_seal.json'
                    native_reuse_receipts.append(dict(receipt=str(receipt),receipt_sha256=sha(receipt),
                        final_stage_reuse_seal_passed=seal.exists() and read(seal).get('passed',False)))
            source_consumed=bool(native_reuse_receipts and all(r['final_stage_reuse_seal_passed'] for r in native_reuse_receipts))
            result = dict(passed=bool(passed),status='recovered_development_full_method_terminal' if passed else 'new_recovery_suffix_failed_original_preserved',
                  pair=plan['pair'],arm=plan['arm'],recovery_suffix_seconds=measurement['complete_command_wall_seconds'],
                  historical_failed_attempt_seconds=historical['complete_command_wall_seconds'],
                  fresh_complete_algorithm_seconds=None,new_independent_inputs=0,frozen_confirmation=False,
                  quality=dict(CPD_ns=flow['final_CPD_ns'],resources=flow['final_resources']) if passed else None,
                  own_root_endpoint_summary=flow.get('own_root_endpoint_summary') if passed else None,
                  source_native_stage_reused_without_historical_receipt_rewrite=source_consumed,
                  native_source_stage_reuse_receipts=native_reuse_receipts,
                  sampled_PSS_kib=measurement['sampled_tree_PSS_peak_kib'],
                  missing_memory_observations=measurement['missing_memory_observations'],
                  qualification='Historical development suffix, original roots/rules/archive retained. Actual stage-reuse seal determines old23-query consumption; no fresh complete-time ratio, independent confirmation or automatic retry.')
            write(ROOT/'result.json',result)
            write(queue/'completion.json',dict(passed=bool(passed),status='registered_CLSTM_domain_recovery_terminal',
                  result=str(ROOT/'result.json'),serial_wait_seconds=slot_started-started,
                  complete_active_queue_seconds=time.monotonic()-slot_started,
                  original_failed_admission_rewritten=False,automatic_retry=False))
            write(queue/'status.json',dict(status='terminal'))
    except BaseException as error:
        write(queue/'completion.json',dict(passed=False,status='new_recovery_reconciliation_required',
              error=repr(error),complete_queue_seconds=time.monotonic()-started,
              serial_wait_seconds=None if slot_started is None else slot_started-started,
              original_failures_preserved=True,automatic_retry=False))
        write(queue/'status.json',dict(status='terminal_reconciliation_required'))
        raise


if __name__=='__main__':
    main()
