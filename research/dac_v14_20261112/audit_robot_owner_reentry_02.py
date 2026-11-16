"""Audit completed owner reentry and existing reload trace; never launches VPR."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import load
from observation_timing_identity_v2 import check

root=D/'robot_owner_reentry_audit_02'
actor=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/robot_p1_input_contract_pair_02/native/flow/resource_flow/repair')
steps=read(actor/'steps.json');registration=read(actor/'registration.json')
assert len(steps)==7
owners=[];files=[Path(__file__).resolve(),D/'observation_timing_identity_v2.py',actor/'registration.json',actor/'steps.json']
for i,s in enumerate(steps):
    if s.get('mechanism')!='capacity_certified_owner_coordination':continue
    tx=Path(s['transaction']);state=Path(s['committed_evaluation'])
    t=read(tx/'registration.json');role=t['roles']['joint_native']
    assert role['original_budget']==registration['anchor'] and role['fixed_resource_limits']==registration['resource_limits']
    assert not role.get('crossing_reuse_enabled') and not role.get('domain_failure_release')
    decision=read(tx/'joint_native_decisions.json')['resources_under_timing']
    assert decision['accepted'] and read(state/'completion.json')['passed']
    r=s['roles'][s['accepted_role']]['resources'];before=steps[i-1]['roles'][steps[i-1]['accepted_role']]['resources']
    assert r['CB_sources']==before['CB_sources']-1 and r['SB_pairs']==before['SB_pairs']
    if i+1<len(steps):assert steps[i+1]['current_state']==str(state)
    else:
        next_tx=actor/'round_007/candidate_00/registration.json'
        assert read(next_tx)['roles']['reuse_off']['state']==str(state)
        files.append(next_tx)
    owners.append(dict(round=s['round'],resources=r,delta={k:r[k]-before[k] for k in r},
        CPD_s=s['roles'][s['accepted_role']]['cpd_s'],
        endpoint_summary={k:v for k,v in decision['endpoint_comparison'].items() if k!='changes'},
        fixed_root_acceptance=True,current_state_reentry=True,domain_or_release=False))
    files += [tx/'registration.json',tx/'joint_native_decisions.json',state/'completion.json']
assert len(owners)==4
tx=actor/'round_007/candidate_00';worker=tx/'reuse_off';source=Path(read(tx/'registration.json')['roles']['reuse_off']['source'])
run=worker/'runs/state';completion=read(worker/'completion.json');manifest=read(run/'manifest.json');source_manifest=read(source/'manifest.json')
assert manifest['status']=='completed' and manifest['returncode']==0
assert not completion['passed'] and not completion['checks']['CPD_matches_original']
assert all(v for k,v in completion['checks'].items() if k!='CPD_matches_original')
for name in ['routed.route','packed.net','placed.place']:
    assert sha(run/name)==sha(source/name)
    files += [run/name,source/name]
source_vector=read(source.parent.parent/'endpoint_vector.json')
observed=load(run/'native_sta_frontier.jsonl')
identity=check(manifest['metrics']['critical_path_ns'],source_manifest['metrics']['critical_path_ns'],source_vector,observed)
assert identity['passed'],identity
# Regression guards: invisible-at-display CPD drift and endpoint/constraint changes must fail.
negative=[]
for name,change in [('sub_display_CPD',lambda v:v.update(cpd_s=v['cpd_s']+1e-19)),
                    ('constraints',lambda v:v.update(constraints_sha256='changed')),
                    ('endpoint_identity',lambda v:v.update(endpoint_ids=[]))]:
    v=copy.deepcopy(observed);change(v)
    result=check(manifest['metrics']['critical_path_ns'],source_manifest['metrics']['critical_path_ns'],source_vector,v)
    assert not result['passed'];negative.append(name)
assert check(manifest['metrics']['critical_path_ns'],manifest['metrics']['critical_path_ns'],source_vector,observed)['passed']
files += [worker/'completion.json',run/'manifest.json',source/'manifest.json',run/'native_sta_frontier.jsonl',source.parent.parent/'endpoint_vector.json']
write(root/'completion.json',dict(passed=True,owners=owners,
    existing_reload_exact_identity=identity,negative_guards=negative,
    completed_native_reused=True,new_native_calls=0,
    original_receipts_changed=False,full_method_complete=False,
    evidence_scope='Development robot-p1/native: four positive automatic owner commits and current-state reentries, but no complete terminal/timing result. Not CP1 confirmation or domain/release attribution.',
    diagnosis='Owner candidate manifest records full-precision CPD in nanoseconds; inherited reload compared it directly with rounded VPR display. Exact existing fresh-STA vector matches source. Outer vanished-proc supervisor failure is a separate recorded defect.',
    source_sha256={str(p):sha(p) for p in files}))
print(dict(passed=True,owner_commits=4,existing_reload_exact=True,new_native_calls=0))
