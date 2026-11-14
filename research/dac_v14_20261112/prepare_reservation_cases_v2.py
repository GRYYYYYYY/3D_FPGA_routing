#!/usr/bin/env python3
"""Register same-source reservation off/on controls, preserving all older batches."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
stage=D/'native_reservation_stage_03';assert sha(stage/'bin/vpr')==read(stage/'binding.json')['binary_sha256']
proof=D/'pending_reservation_tiny_regression_02/completion.json';assert read(proof)['passed'];assert all(sha(p)==h for p,h in read(proof)['source_sha256'].items())
baseline=D/'bnn_strong_release_joint_dev_01';reg=read(baseline/'registration.json');progress=read(baseline/'progress.json');b=D/'pending_reservation_dev_02';b.mkdir(exist_ok=False);roles={}
files=[Path(__file__).resolve(),proof,stage/'binding.json',D/'run_reserved_native_transactions_v2.py',D/'run_native_reservation_analysis_v2.py',D/'audit_pending_reservations.py',D/'A0_target_order_causal_summary_01.json',baseline/'registration.json']
for scope in ['target_only','combined']:
 for objective in ['weighted_soft','physical_capacity']:
  original_name='A0_'+scope+'_'+objective;old=reg['roles'][original_name];reference=progress[original_name];assert reference['status']=='legal_evaluated' and read(Path(reference['evaluation'])/'completion.json')['passed']
  targets=b/(original_name+'_targets.txt');targets.write_text(str(len(old['targets']))+'\n'+''.join(f'{n} {p}\n' for n,p in old['targets']))
  assert len({n for n,p in old['targets']})==len(old['targets'])
  for enabled in [False,True]:
   name=original_name+('_reserve_on' if enabled else '_reserve_off');role=copy.deepcopy(old)
   role.update(reservations_enabled=enabled,reserve_targets_file=str(targets),reference_batch=str(baseline),reference_role=original_name,reference_evaluation=reference['evaluation'])
   role['source_sha256'].update({str(p):sha(p) for p in [targets,stage/'binding.json',baseline/(original_name+'_decisions.json')]});roles[name]=role
  files += [targets,baseline/(original_name+'_decisions.json')]
write(b/'registration.json',dict(status='registered_before_native',roles=roles,source_sha256={str(p):sha(p) for p in files},
 question='Does reserving original resources for unprocessed critical targets prevent greedy starvation and improve the final timing/resource tradeoff, with identical source, query order, native cost objective, full-device domain and modifiable tree scope?',
 controls='Off/on within each of target-only and combined scopes, paired for nativeweighted and physicalcapacity objectives. Off must reproduce old candidate body exactly before quality inference. On reserves only explicit current critical target paths, releasing own-net reservations during own searches; donors remain released.',
 gates='Audit native original-state/occupancy restoration, reservation membership/count/capacity/release order/cleanup, native candidate edge/tree/capacity, complete FULLSTA and exact fixed-budget decisions. Old complete FULLSTA reused only for exact candidate body/inputs/config/constraints.',
 limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
 qualification='New independent native version; Tiny actual native off/on bookkeeping regression passed; BNN paired benefit remains unknown. This trace audit explicitly covers one critical target per net. Larger nonconfig closure/other architectures require further evidence. Existing native, selected-group and automatic-trajectory registrations unchanged.'))
print('Registered',len(roles),'reservation controls',flush=True)
