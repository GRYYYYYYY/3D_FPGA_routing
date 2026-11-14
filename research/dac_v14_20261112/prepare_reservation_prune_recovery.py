#!/usr/bin/env python3
"""Register one informative large-circuit off/on pair for the prune-index fix."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
proof=D/'reservation_multisink_regression_01/completion.json';assert read(proof)['passed'];assert all(sha(p)==h for p,h in read(proof)['source_sha256'].items());stage=D/'native_reservation_stage_04';assert sha(stage/'bin/vpr')==read(stage/'binding.json')['binary_sha256']
b=D/'reservation_prune_recovery_dev_01';b.mkdir(exist_ok=False);old=D/'bnn_strong_release_joint_dev_01';name='A0_target_only_physical_capacity';role=read(old/'registration.json')['roles'][name];reference=read(old/'completion.json')['roles'][name];assert reference['status']=='legal_evaluated'
targets=b/'targets.txt';targets.write_text(str(len(role['targets']))+'\n'+''.join(f'{n} {p}\n' for n,p in role['targets']));roles={}
files=[Path(__file__).resolve(),proof,stage/'binding.json',D/'reservation_prune_index_recovery_01.json',D/'run_native_reservation_analysis_v3.py',D/'run_reserved_native_transactions_v3.py',D/'audit_pending_reservations.py',old/'registration.json',old/'completion.json',old/(name+'_decisions.json'),targets]
for enabled in [False,True]:
 r=copy.deepcopy(role);r.update(reservations_enabled=enabled,reserve_targets_file=str(targets),reference_batch=str(old),reference_role=name,reference_evaluation=reference['evaluation']);r['source_sha256'].update({str(p):sha(p) for p in files});roles['physical_capacity_reserve_'+('on' if enabled else 'off')]=r
write(b/'registration.json',dict(status='registered_before_native',roles=roles,source_sha256={str(p):sha(p) for p in files},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),question='After fixing stale pruned-sink membership, can reservations avoid the observed A0 target-only physical starvation regression while preserving native search, physical delays and full legality?',
 controls='One independent representative off/on pair from the same pristine A0, exact targets/order/domain/tree scope/budgets. Off must match the old complete candidate body. Old FULLSTA reused only for exact matching candidate/input/config/constraints. Additional objectives/scopes depend on actual evidence, not an obligatory rerun of the old eight arms.',
 qualification='Old stage03 batch continues unchanged; failed on roles are implementation failures, not QoR observations. This new stage04 batch follows all already registered native owners and does not restart completed work. Multi-sink regression reproduces old failure and validates corrected bitset membership; BNN outcome unknown.'))
print('Registered representative two-arm native recovery')
