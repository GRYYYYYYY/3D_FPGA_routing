from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
"""Continue four audited old actors once; no fresh initial routing or retries."""
import fcntl,os,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure
from admit_interrupted_flow_recovery_01 import ROOT,admit

protocol=read(ROOT/'protocol.json');q=ROOT/'queue_priority_03';q.mkdir(exist_ok=False)
owner=(q/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(ROOT/'protocol.json'):sha(ROOT/'protocol.json'),**protocol['source_sha256']}
bound.update({str(D/'confirmation_priority_handoff_02/plan.json'):sha(D/'confirmation_priority_handoff_02/plan.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
bound.update({str(D/'confirmation_priority_handoff_03/plan.json'):sha(D/'confirmation_priority_handoff_03/plan.json')})
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,mode='same_actor_development_suffix_recovery',registered_arms=4,completed_native_replay=False))
try:
    pred=D/'robot_p1_prefix_recovery_01/queue_priority_03';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        live=process_identity(reg['pid']);assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
        write(q/'status.json',dict(status='waiting_for_registered_four_arm_stage_audit'));time.sleep(15)
    live=process_identity(reg['pid'])
    while live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']:
        time.sleep(2);live=process_identity(reg['pid'])
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot_recovery'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(p)==h for p,h in bound.items())
    assert (D/'interrupted_stage_reconciliation_01/completion.json').exists(),'No actual stage audit result'
    results=[]
    for spec in protocol['arms']:
        case_id=spec['pair']+'_'+spec['arm'];case_root=ROOT/'arms'/case_id;assert not case_root.exists(),'Never restart an existing case'
        before=time.monotonic()
        try:case=admit(spec)
        except Exception as error:
            case_root.mkdir(exist_ok=True)
            result=dict(pair=spec['pair'],arm=spec['arm'],passed=False,status='unexecuted_recovery_admission_failure',error=repr(error),
                quality=None,recovery_suffix_seconds=None,admission_seconds=time.monotonic()-before,new_native_calls=0,
                historical_failed_measurement=spec['historical_failed_measurement'],fresh_complete_algorithm_seconds=None,new_independent_inputs=0)
            write(case_root/'result.json',result);results.append(result);continue
        write(case/'admission.json',dict(passed=True,complete_seconds=time.monotonic()-before,plan_sha256=sha(case/'plan.json'),native_calls_new=0,scope='External plan admission; algorithm prefix/byte verification remains inside suffix command'))
        plan=read(case/'plan.json');runtime=Path(plan['release'])/'runtime'
        command=[sys.executable,str(runtime/'supervise_method_phase.py'),'--receipt',str(case/'supervision.json'),'--',sys.executable,'-I','-B',
            str(ROOT/'runtime_extension/run_interrupted_full_flow_recovery_v1.py'),'--plan',str(case/'plan.json'),'--output',str(case/'flow')]
        write(q/'status.json',dict(status='running_recovery_suffix',case=case_id))
        measured=measure(command,case/'measurement',interval=.5)
        # A residual child blocks subsequent execution until reconciliation.
        assert not measured['live_descendants_after_command_exit'],'Live residual child; preserve prefix and stop dispatch'
        supervision=read(case/'supervision.json') if (case/'supervision.json').exists() else {}
        assert not supervision.get('residual_descendants',[]),'Residual descendants require reconciliation'
        complete=read(case/'flow/completion.json') if (case/'flow/completion.json').exists() else {}
        passed=measured['passed'] and supervision.get('passed',False) and complete.get('passed',False) and complete.get('status')=='recovered_full_method_terminal'
        failed=read(plan['historical_failed_measurement'])
        result=dict(pair=spec['pair'],arm=spec['arm'],passed=passed,status='recovered_development_full_method_terminal' if passed else 'recovery_execution_incomplete',
            quality=(dict(CPD_ns=complete['final_CPD_ns'],resources=complete['final_resources']) if passed else None),
            own_root_endpoint_summary=complete.get('own_root_endpoint_summary') if passed else None,
            recovery_suffix_seconds=measured['complete_command_wall_seconds'],sampled_PSS_kib=measured['sampled_tree_PSS_peak_kib'],
            missing_memory_observations=measured['missing_memory_observations'],historical_failed_attempt_seconds=failed['complete_command_wall_seconds'],
            fresh_complete_algorithm_seconds=None,new_independent_inputs=0,frozen_confirmation=False,automatic_retry=False,
            source_sha256={str(p):sha(p) for p in [case/'plan.json',case/'measurement/completion.json',case/'supervision.json'] if p.exists()})
        write(case/'result.json',result);results.append(result);write(ROOT/'results.json',results)
    write(ROOT/'results.json',results)
    write(q/'completion.json',dict(passed=all(x['passed'] for x in results),status='registered_four_arm_recovery_terminal',
        terminal_arms=len(results),results=str(ROOT/'results.json'),source_sha256=bound,research_complete=False,
        qualification='Ordinary no-gain closure is a valid recovery result. Admission/infrastructure failures remain explicit and unretired. Complete cost and independent-input claims are not created from recovered suffixes.'))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,no_automatic_retry=True));raise
