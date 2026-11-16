"""Seal interrupted attempts without inventing lost supervisor receipts or retrying."""
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out = D/'execution_reconciliation_20261116_01'
out.mkdir(exist_ok=False)
home = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
workspace = home/'confirmation_workspaces'
serial = (D/'critical_scope_runner.lock').open('r')
fcntl.flock(serial, fcntl.LOCK_EX | fcntl.LOCK_NB)

def actual(pid, ticks):
    try:
        v = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
    except (FileNotFoundError, ProcessLookupError):
        return None
    return dict(pid=int(pid),state=v[0],start_ticks=v[19]) if v[19]==str(ticks) and v[0]!='Z' else None

queues = ['portable_reduction_pair_01','clstm_input_contract_pair_02',
          'robot_p1_input_contract_pair_02','cp1_cross_circuit_cohort_01',
          'robot_union_mechanism_01','BNN_interleaved_timing_01']
files = [Path(__file__).resolve()]
owners = []
for name in queues:
    q = D/name/'queue'; reg = read(q/'registration.json')
    assert actual(reg['pid'],reg['start_ticks']) is None, name
    done = read(q/'completion.json')
    owners.append(dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],
                       original_terminal_status=done['status'],live=False))
    files += [q/'registration.json',q/'completion.json']

specs = [
 ('reduction_pair_01','native','flow/fresh_route_and_complete_resource.log'),
 ('reduction_pair_01','domain','flow/resource_flow/repair/round_004/candidate_00/reuse_on_FULL_STA.log'),
 ('clstm_input_contract_pair_02','native','flow/complete_current_STA_timing.log'),
 ('clstm_input_contract_pair_02','domain','flow/resource_flow/resource_repair.log'),
 ('robot_p1_input_contract_pair_02','native','measurement/stdout.log')]
attempts = []
for name,arm,trace in specs:
    case = workspace/name/arm
    m = read(case/'measurement/completion.json')
    assert m['returncode']==1 and not m['live_descendants_after_command_exit']
    surviving = [actual(pid,tick) for pid,tick in m['process_identities'].items()]
    assert not any(surviving), (name,arm)
    assert 'ProcessLookupError: [Errno 3] No such process' in (case/trace).read_text()
    initial = case/'flow/resource_flow/initial/completion.json'
    ini = read(initial) if initial.exists() else None
    steps = case/'flow/resource_flow/repair/steps.json'
    last = read(steps) if steps.exists() else []
    preserved = None
    if last:
        a = last[-1];r = a['roles'][a['accepted_role']]
        preserved = dict(accepted_steps=len(last),resources=r['resources'],CPD_ns=r['cpd_s']*1e9)
    row = dict(input=name,arm=arm,status='supervision_proc_race_interrupted',
        complete_method_verified=False,quality=None,
        failed_attempt_seconds=m['complete_command_wall_seconds'],
        sampled_PSS_kib=m['sampled_tree_PSS_peak_kib'],
        missing_memory_observations=m['missing_memory_observations'],
        actual_initial_legal=bool(ini and ini['passed']),
        preserved_partial_resource_trajectory=preserved,
        original_outer_supervision_present=(case/'supervision.json').exists(),
        identities_rechecked=len(m['process_identities']),live_identity_count=0,
        failure_trace=str(case/trace),measurement=str(case/'measurement/completion.json'))
    attempts.append(row)
    files += [case/trace,case/'measurement/completion.json']
    if initial.exists(): files.append(initial)
    if steps.exists(): files.append(steps)

unexecuted = [workspace/'robot_p1_input_contract_pair_02/domain']
cp = read(D/'cp1_cross_circuit_cohort_01/plan.json')
for item in cp['inputs']:
    assert not (Path(item['workspace'])/'provisioning.json').exists()
    unexecuted += [Path(item['workspace'])/arm for arm in ['native','domain']]
unexecuted += [D/'robot_union_mechanism_01/transaction']
unexecuted += [D/'BNN_interleaved_timing_01'/role for role in ['native_0','domain_0','domain_1','native_1']]
assert all(not p.exists() for p in unexecuted)
write(out/'completion.json',dict(passed=True,observed_at=datetime.now(timezone.utc).isoformat(),
    status='actual_processes_reconciled_original_failures_preserved',
    owners=owners,attempts=attempts,unexecuted_paths=list(map(str,unexecuted)),
    native_calls_new=0,original_receipts_rewritten=False,
    source_sha256={str(p):sha(p) for p in files},
    qualification='Five attempted arms ended through vanished-/proc supervision errors, not scientific negatives. Initial legal states and partial commits do not constitute complete method outputs. Missing supervisor receipts remain missing. Observer times are failed-attempt costs only. Original robot domain and downstream roles were never executed; changes require separately sealed versions/registrations.'))
print(dict(passed=True,attempts=attempts,unexecuted=len(unexecuted)))
