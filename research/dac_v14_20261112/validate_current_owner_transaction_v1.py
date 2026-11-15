"""Actual positive/zero/foreign/stale selector adapter checks; no native execution."""
from pathlib import Path
import copy
from retained_prefix_workflow import D,read,write,sha
from current_owner_transaction_v1 import prepare
r=D/'current_owner_transaction_validation_01';r.mkdir(exist_ok=False)
cache=D/'full_route_graph_cache_bnn_01';selection=D/'current_escape_owner_selector_validation_01/R1'
state=Path(read(selection/'completion.json')['state']);root=Path(read(D/'stable_seed_transfer_recovery_01/bnn_R1_paired/registration.json')['initial_state'])
result=prepare(state,root,selection,cache,r/'positive',domain_mode='matched_target_CB')
assert result['transaction_registered']
a=read(r/'positive/registration.json');b=read(D/'R1_owner_release_joint_probe_01/prepared_transaction_registration.json')
keys=['state','source','queries','removed_pins','objective','fixed_target_paths','crossing_reuse_enabled','domain_failure_release','seed_order','original_budget','fixed_resource_limits','allowed_resource_kind']
for name in b['roles']:
 x,y=a['roles'][name],b['roles'][name]
 assert all(x[k]==y[k] for k in keys)
 assert Path(x['request']).read_bytes()==Path(y['request']).read_bytes()
 assert Path(x['crossing_domain']).read_bytes()==Path(y['crossing_domain']).read_bytes()
 if x['explicit_crossings']:assert Path(x['explicit_crossings']).read_bytes()==Path(y['explicit_crossings']).read_bytes()
assert a['resource_conditions']==b['resource_conditions']
negative=[]
def reject(label,**changes):
 params=dict(state=state,root_state=root,selection=selection,full_graph_cache=cache,output=r/label)
 params.update(changes)
 try:prepare(**params)
 except AssertionError as e:
  assert not params['output'].exists();negative.append(dict(case=label,rejected=True,reason=str(e)));return
 raise AssertionError('Unexpected acceptance: '+label)
other=Path(read(D/'current_escape_owner_selector_validation_01/A0/completion.json')['state'])
reject('foreign_selection',state=other)
reject('foreign_physical_root',root_state=D/'native_endpoint_vector_dev_01/A0')
for label in ['A0','complete43']:
 sel=D/'current_escape_owner_selector_validation_01'/label;s=Path(read(sel/'completion.json')['state'])
 n=prepare(s,s,sel,cache,r/('no_group_'+label))
 assert not n['transaction_registered'] and not (r/('no_group_'+label)/'registration.json').exists()
# A corrupted artifact keeps the original completion digest, and must fail closed.
bad=r/'corrupted_selection';bad.mkdir()
for name in ['completion.json','groups.json','certificates.json','screens.json','classifications.json','cache_identity.json','selected_request.txt']:
 if (selection/name).exists():(bad/name).write_bytes((selection/name).read_bytes())
(bad/'groups.json').write_text('[]')
reject('changed_artifact',selection=bad)
write(r/'completion.json',dict(passed=True,actual_positive_controls_exact=True,matched_roles=2,comparison_keys=keys,no_group_states=2,negative_checks=negative,native_calls_new=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),D/'current_owner_transaction_v1.py',selection/'completion.json',D/'R1_owner_release_joint_probe_01/prepared_transaction_registration.json',r/'positive/registration.json',r/'positive/preparation.json']},qualification='Actual already sealed R1 group reproduces all native-affecting fields, requests, budgets and explicit crossings without using old registration as constructor input. A0/complete43 have no group. Foreign selection, different input root and changed artifacts rejected before output registration. No repeated native batch and no new quality/whole cost claim.'))
print(dict(passed=True,positive_roles=2,no_group_states=2,negative_checks=negative,native_calls_new=0))
