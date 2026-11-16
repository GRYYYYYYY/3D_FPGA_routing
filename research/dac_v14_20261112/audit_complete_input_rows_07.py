"""Read-only own-root endpoint audit for new complete manuscript rows; no native calls."""
import fcntl
import os
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy_streaming_v2 import compare
from seed_census_analysis_pool_v2 import process_identity

root = D/'complete_input_paper_evidence_07'
root.mkdir(exist_ok=False)
owner = (root/'owner.lock').open('w')
fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
bound = {str(Path(__file__).resolve()): sha(Path(__file__).resolve())}
write(root/'registration.json', dict(**process_identity(os.getpid()), source_sha256=bound,
    native_calls=0, uses_shared_serial_slot=True, purpose='Complete-row own-root endpoint accounting'))
write(root/'status.json', dict(status='waiting_for_shared_serial_slot'))
serial = (D/'critical_scope_runner.lock').open('r')
fcntl.flock(serial, fcntl.LOCK_EX)
assert all(sha(p) == h for p,h in bound.items())
write(root/'status.json', dict(status='auditing_completed_outputs'))
cases = {
    'BNN terminal N': D/'complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire',
    'Robot SDC N': D/'unified_input_integration_01/robot_s23_SDC_native',
    'Robot SDC D': D/'unified_input_integration_01/robot_s23_SDC_domain',
}
rows = []
files = [Path(__file__).resolve()]
for label, case in cases.items():
    cp = case/'completion.json'
    c = read(cp)
    assert c['passed'] and c['complete_configuration_verified']
    iv, fv = [Path(c[k])/'endpoint_vector.json' for k in ['initial_state','final_state']]
    initial, final = read(iv), read(fv)
    delta = compare(initial, final)
    assert delta['compatible']
    out = root/(case.name+'_endpoints.json')
    write(out, delta)
    if label.startswith('Robot'):
        assert all(initial[k] == final[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        assert c['resource_accepted_steps'] == c['timing_accepted_steps'] == c['owner_commits'] == 0
        assert c['explicit_SDC_result']['all_observed_components_finite_and_nonnegative']
    rows.append(dict(label=label, CPD_ns=c['CPD_ns'], resources=c['resources'],
        time_seconds=c['complete_wall_seconds'], PSS_GiB=c['sampled_tree_PSS_peak_kib']/1024**2,
        missing_memory_observations=c['missing_memory_observations'],
        endpoint_summary={k:v for k,v in delta.items() if k != 'changes'},
        receipt=str(cp), endpoint_changes=str(out), cost_scope='complete_configuration'))
    files.extend([cp,iv,fv,out])
pair = D/'unified_input_integration_01/comparison.json'
failure = D/'attention_initial_failure_pair_01/completion.json'
assert read(pair)['passed'] and read(failure)['passed']
for arm in ['native','domain']:
    row = read(pair)['outcomes']['attention_'+arm]
    assert row['status'] == 'initial_route_failed' and row['quality'] is None
    rows.append(dict(label='Attention '+arm[0].upper()+' (initial fail)',
        CPD_ns=None, resources=None, time_seconds=row['complete_seconds'],
        PSS_GiB=None, endpoint_summary=None, receipt=row['measurement'],
        cost_scope='complete_attempt_initial_failure'))
    files.append(Path(row['measurement']))
files += [pair,failure]
write(root/'rows.json', rows)
files.append(root/'rows.json')
write(root/'completion.json', dict(passed=True, native_calls=0, new_table_rows=len(rows),
    legal_rows=3, initial_failure_rows=2, source_sha256={str(p):sha(p) for p in files},
    qualification='Own-root full endpoints, not summed step deltas. BNN baseline-prefix comparison remains a separate audit. Known historical physical inputs and a declared benchmark SDC; not unseen tests or frozen-controller confirmation.'))
write(root/'status.json', dict(status='terminal', passed=True))
print(dict(passed=True, rows=len(rows), native_calls=0), flush=True)
