"""Re-register only proven unexecuted successors; preserve original registries."""
import copy
import subprocess
import sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from BNN_interleaved_timing_v1 import validate_configs

reconciliation=D/'execution_reconciliation_20261116_01/completion.json'
assert read(reconciliation)['passed']
prior=D/'cp1r1_cross_circuit_cohort_01/queue'
reg=read(prior/'registration.json');live=process_identity(reg['pid'])
assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']

old=D/'robot_union_mechanism_01';root=D/'robot_union_mechanism_02'
assert not (old/'transaction').exists() and not root.exists();root.mkdir()
for name in ['union_request.txt','shared_only_domain.txt']:
    (root/name).write_bytes((old/name).read_bytes())
def relocate(v):
    if isinstance(v,str):return v.replace(str(old),str(root))
    if isinstance(v,list):return [relocate(x) for x in v]
    if isinstance(v,dict):return {relocate(k):relocate(x) for k,x in v.items()}
    return v
registration=relocate(read(old/'prepared_transaction_registration.json'))
paths=[Path(__file__).resolve(),D/'queue_robot_union_mechanism_02.py',
       D/'verify_robot_union_mechanism_02.py',D/'supervise_method_phase_v2.py',
       D/'method_phase_proc_race_validation_02/completion.json',reconciliation]
extra={str(p):sha(p) for p in paths}
registration['source_sha256'].update(extra)
for row in registration['roles'].values():row['source_sha256'].update(extra)
write(root/'prepared_transaction_registration.json',registration)
plan=relocate(read(old/'plan.json'))
plan.update(predecessor=str(prior),supervisor=str(D/'supervise_method_phase_v2.py'),
    original_unexecuted_plan=str(old/'plan.json'),original_unexecuted_plan_sha256=sha(old/'plan.json'),
    resubmission_reason='Original roles never executed. New owner/output identity after reconciled predecessor failure; only external process supervision changes. Same25queries, domains, owner scope, budgets, native backend and three treatments.')
plan['source_sha256'].update(extra)
plan['source_sha256'][str(root/'prepared_transaction_registration.json')]=sha(root/'prepared_transaction_registration.json')
plan['source_sha256'][str(old/'plan.json')]=sha(old/'plan.json')
write(root/'plan.json',plan)
subprocess.run([sys.executable,str(D/'verify_robot_union_mechanism_02.py'),'--preflight'],check=True)

old=D/'BNN_interleaved_timing_01';root=D/'BNN_interleaved_timing_02'
for role in ['native_0','domain_0','domain_1','native_1']:assert not (old/role).exists()
assert not root.exists();root.mkdir();(root/'configs').mkdir()
for arm in ['native','domain']:
    (root/'configs'/f'{arm}.json').write_bytes((old/'configs'/f'{arm}.json').read_bytes())
validate_configs(read(root/'configs/native.json'),read(root/'configs/domain.json'))
plan=copy.deepcopy(read(old/'plan.json'))
plan.update(predecessor=str(D/'robot_union_mechanism_02/queue'),
    original_unexecuted_plan=str(old/'plan.json'),original_unexecuted_plan_sha256=sha(old/'plan.json'),
    resubmission_reason='Original four timing roles never executed. Byte-exact original paired configs and unchanged algorithm/observer; only queue dependency/output identity changes.')
for p in [Path(__file__).resolve(),D/'queue_BNN_interleaved_timing_02.py',
          root/'configs/native.json',root/'configs/domain.json',old/'plan.json',reconciliation]:
    plan['source_sha256'][str(p)]=sha(p)
write(root/'plan.json',plan)
write(root/'preflight.json',dict(passed=True,native_calls=0,
    original_configs_byte_identical=True,new_independent_inputs=0,
    unchanged_gating_validation=str(D/'BNN_interleaved_timing_01/validation.json'),
    actual_repeated_timing_complete=False,large_input_validation_deferred_to_serial_slot=True,
    source_sha256={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}))
print(dict(passed=True,new_native_calls=0,successors=['robot_union_mechanism_02','BNN_interleaved_timing_02']))
