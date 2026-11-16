from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
"""Continue the interrupted robot development input after all registered work."""
import fcntl,os,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure
root=D/'robot_p1_prefix_recovery_01';plan=read(root/'plan.json');q=root/'queue_priority_02';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}
bound.update({str(D/'confirmation_priority_handoff_02/plan.json'):sha(D/'confirmation_priority_handoff_02/plan.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,mode='interrupted_development_recovery',repeat_completed_native=False))
try:
    pred=D/'interrupted_stage_reconciliation_01/queue_priority_02';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        live=process_identity(reg['pid']);assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
        write(q/'status.json',dict(status='waiting_for_priority_readonly_four_arm_audit'));time.sleep(15)
    previous=read(pred/'completion.json');assert previous['status'] in ['registered_readonly_stage_audit_terminal','reconciliation_required']
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot_recovery'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items())
    runtime=Path(plan['release'])/'runtime';assert read(Path(plan['release'])/'release_manifest.json')['release_id']=='current_sta_cp1r3'
    command=[sys.executable,str(runtime/'supervise_method_phase.py'),'--receipt',str(root/'supervision.json'),'--',sys.executable,'-I','-B',str(root/'runtime_extension/run_robot_prefix_recovery_01.py'),'--plan',str(root/'plan.json'),'--output',str(root/'flow')]
    write(q/'status.json',dict(status='running_recovery_suffix',mode='original_prefix_and_root_preserved'))
    measured=measure(command,root/'measurement',interval=.5)
    assert not measured['live_descendants_after_command_exit']
    assert read(root/'supervision.json')['passed'] and not read(root/'supervision.json')['residual_descendants']
    complete=read(root/'flow/completion.json');assert measured['passed'] and complete['passed'] and complete['status']=='recovered_full_method_terminal'
    failed=read(plan['historical_failed_measurement'])
    write(root/'result.json',dict(passed=True,recovered_full_method_complete=True,fresh_complete_cost_available=False,
        quality=dict(CPD_ns=complete['final_CPD_ns'],resources=complete['final_resources']),
        own_root_endpoint_summary=complete['own_root_endpoint_summary'],
        recovery_suffix_seconds=measured['complete_command_wall_seconds'],sampled_PSS_kib=measured['sampled_tree_PSS_peak_kib'],
        missing_memory_observations=measured['missing_memory_observations'],
        historical_failed_attempt_seconds=failed['complete_command_wall_seconds'],
        independent_new_inputs=0,frozen_confirmation=False,
        source_sha256={str(f):sha(f) for f in [root/'plan.json',root/'flow/completion.json',root/'measurement/completion.json',root/'supervision.json']},
        qualification='Original failed prefix cost remains separate. New wall/PSS covers this recovery suffix with exact original roots/budgets/archive and completed native-request reuse. No fresh whole-method cost or matching native/domain speedup ratio.'))
    write(q/'completion.json',dict(passed=True,status='registered_development_recovery_terminal',result=str(root/'result.json'),source_sha256=bound));write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,no_automatic_retry=True));raise
