"""Seal the four-prefix readonly stage audit without changing any old actor."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'interrupted_stage_reconciliation_01';assert not (root/'plan.json').exists()
inventory=read(root/'inventory.json');assert inventory['passed'] and len(inventory['rows'])==4
assert all(sha(p)==h for p,h in inventory['source_sha256'].items())
pred=D/'cp1r3_distinct_input_cohort_01/queue';reg=read(pred/'registration.json');live=process_identity(reg['pid'])
assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
reconciliation=read(D/'execution_reconciliation_20261116_01/completion.json')
old={(r['input'],r['arm']):r for r in reconciliation['attempts']}
costs=[]
for row in inventory['rows']:
    original=old[row['pair'],row['arm']]
    assert original['complete_method_verified'] is False and original['quality'] is None
    costs.append({k:original[k] for k in ['input','arm','failed_attempt_seconds','sampled_PSS_kib','missing_memory_observations']})
names=['audit_interrupted_stages_01.py','queue_interrupted_stage_reconciliation_01.py',
    'preregister_interrupted_stage_reconciliation_01.py','recovery_prefix_v1.py',
    'observation_timing_identity_v2.py','run_native_scope_policy_v4.py',
    'endpoint_timing_policy_streaming_v2.py','state_resource_assurance.py',
    'retained_prefix_workflow.py','seed_census_analysis_pool_v2.py']
files=[D/n for n in names]+[root/'inventory.json',D/'execution_reconciliation_20261116_01/completion.json',pred/'registration.json']
for n in names:compile((D/n).read_text(),n,'exec')
write(root/'plan.json',dict(passed=True,status='registered_readonly_reconciliation_pending_serial_slot',
    predecessor=str(pred),predecessor_identity=live,source_sha256={str(p):sha(p) for p in files},
    cases=inventory['rows'],original_failed_attempt_costs=costs,
    purpose='Determine which existing native/source-control/audit stages can be reused. Separate original incomplete resource and timing actors; no blanket fresh-route or native replay.',
    audit='Check original actors/recorded child identities dead, source and runtime hashes, shared/private bytes, unchanged source route/pack/place, command/options/request/domain bindings, actual GNU exit0/native FULL/success/query terminal, exact full-precision CPD/setup/hold/ordered endpoints/constraints and any existing candidate audit.',
    reduction_native_rule='Running manifest without worker completion remains original. Require raw successful command plus exact source/vector/byte evidence; emit a separate readonly audit only. Do not fabricate an old worker completion, candidate quality, endpoint result or whole-flow duration.',
    recovery_rule='No adoption adapter or new experiment launched by this audit. Later explicit development recovery must retain original anchor/limits, accepted prefix, legal rejected archive, fixed original timing portfolio and stage order. Reuse only verified same-actor stages; partial candidate STA requires reconciliation.',
    cost_rule='Old failed-attempt times remain failed costs. This new audit has a separate duration, zero native calls, and no cold full-method cost. Raw GNU elapsed may extend beyond a failed outer supervisor and must not be added as an asserted whole-flow total.',
    new_native_calls=0,new_independent_inputs=0,adoption_implemented=False,full_method_complete=False,
    preserve_public_evidence_base='9734eee',research_complete=False))
print(dict(passed=True,cases=4,new_native_calls=0,adoption_implemented=False))
