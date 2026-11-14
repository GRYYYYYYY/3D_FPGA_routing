#!/usr/bin/env python3
"""Bind an actually committed standalone repair, not its still-running trajectory."""
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha as raw_sha
from endpoint_timing_policy_streaming_v2 import compare
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity

out=D/'low_resource_timing_accept_02.json';assert not out.exists()
actor=D/'low_resource_dual_timing_02/strict';step=dict(read(actor/'steps.json')[1]);assert step['accepted']
before,after=Path(step['before_state']),Path(step['evaluation']);tx=after.parent
paths=[Path(__file__).resolve(),D/'low_resource_dual_timing_02/absolute_limits.json',
    tx/'registration.json',tx/'completion.json',tx/'current_group_decisions.json',
    tx/'current_group_audit/analysis.json',tx/'current_group_successor_cone.json',
    after.parent.parent/'policy_decisions.json']
memo={}
def sha(path):
    path=Path(path).resolve();s=path.stat();key=(str(path),s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in memo:memo[key]=raw_sha(path)
    return memo[key]
for state in [before,after]:
    c=read(state/'completion.json');assert c['passed'] and read(state/'input_seal.json')['passed']
    rd=run_dir(state);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed']
    assert read(rd/'independent_audit.json')['audit']['passed']
    for name in ['packed.net','placed.place','routed.route']:assert sha(rd/name)==m['outputs'][name]['sha256']
    for path,row in read(state/'input_seal.json')['inputs'].items():assert row['passed'] and sha(path)==row['sha256']
    paths.extend([state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',
        rd/'manifest.json',rd/'independent_audit.json',rd/'routed.route'])
assert problem_identity(run_dir(before))==problem_identity(run_dir(after))
av,bv=read(before/'endpoint_vector.json'),read(after/'endpoint_vector.json');change=compare(av,bv)
assert change['compatible'] and change['cpd_strictly_better'] and not change['hold_violation_regressions']
assert av['cpd_s']==step['before_CPD_s'] and bv['cpd_s']==step['after_CPD_s']
caps=read(D/'low_resource_dual_timing_02/absolute_limits.json');assert all(step['after_resources'][k]<=v for k,v in caps.items())
policies=read(after.parent.parent/'policy_decisions.json')
assert policies['timing_under_resources']['accepted'] and not policies['endpoint_under_resources']['accepted']
source_cone=next(path for path in before.parent.glob('*_successor_cone.json') if Path(read(path)['source_state'])==before)
paths.append(source_cone)
original=read(source_cone);current=read(tx/'current_group_successor_cone.json')
assert Path(current['source_state'])==after
identity=lambda cone:[r['identity'] for r in cone['selected_endpoints']]
connections=lambda cone:{(r['net'],r['pin']) for r in cone['routed_connections']}
finite={k:v for k,v in av['setup'].items() if isinstance(v,(int,float)) and math.isfinite(v)}
worst=min(finite.values());near={k for k,v in finite.items() if v<=worst+0.05*av['cpd_s']}
costs=[r for r in read(actor/'process_costs.json') if r['tag'].startswith('001_')]
audit=read(tx/'current_group_audit/analysis.json');assert audit['passed']
write(out,dict(passed=True,immutable_accepted_step=step,trajectory_complete=False,
    CPD_before_ns=av['cpd_s']*1e9,CPD_after_ns=bv['cpd_s']*1e9,
    resources_before=step['before_resources'],resources_after=step['after_resources'],fixed_absolute_limits=caps,
    whole_endpoint_comparison=change,strict_accepted_secondary_rejected=True,
    selected_endpoints_before=identity(original),selected_endpoints_after=identity(current),
    critical_connections_before=sorted(connections(original)),critical_connections_after=sorted(connections(current)),
    critical_connections_added=sorted(connections(current)-connections(original)),
    critical_connections_removed=sorted(connections(original)-connections(current)),
    fixed_source_near_band=dict(rule='Source slack <= source worst +0.05*sourceCPD, diagnostic only',
        components=len(near),improved=sum(bv['setup'][k]>av['setup'][k] for k in near),
        regressed=sum(bv['setup'][k]<av['setup'][k] for k in near)),
    native_changed_connection_switch_delays=audit['changed_delays'],native_transaction_seconds=audit['native_transaction_seconds'],
    complete_candidate_analysis_workflow_seconds=read(after/'completion.json')['timing']['complete_evaluation_seconds'],
    completed_first_round_children=costs,completed_first_round_children_seconds=sum(r['complete_process_seconds'] for r in costs),
    complete_single_configuration_algorithm_seconds=None,native_calls_in_this_binding=0,
    source_sha256={str(path):sha(path) for path in paths},
    qualification='Actual legal standalone input-sealed current-STA accept from registered45SB prefix; full resource/timing branches remain active. Complete endpoint/domain and native numbers, no tolerance. Nested core/analysis/child timings are separate; no cold single-configuration time or final automatic resource-phase endpoint claimed.'))
print(dict(passed=True,CPD_ns=bv['cpd_s']*1e9,resources=step['after_resources'],
    setup_improved=change['setup_improved'],setup_regressed=change['setup_regressed'],
    endpoint_migrated=identity(original)!=identity(current),near_components=len(near)),flush=True)
