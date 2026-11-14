#!/usr/bin/env python3
"""Counterfactual native-first control flow on complete sealed paired observations."""
import collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
b=D/'native_first_resource_replay_01';b.mkdir(exist_ok=False);files=[Path(__file__).resolve()];results={}
for name in ['R1_fast','A0_native8']:
 actor=D/'pooled_resource_repair_dev_01'/name;c=read(actor/'completion.json');assert c['passed'] and read(actor/'evaluation_context/input_seal.json')['passed'];attempts=read(actor/'attempts.json');steps=[];skippable=[];current=Path(c['initial_state']);roles_skipped=[]
 for row in attempts:
  current_vector=read(current/'endpoint_vector.json');before=Path(row['current_state']);assert sha(run_dir(current)/'routed.route')==sha(run_dir(before)/'routed.route');assert all(read(before/'endpoint_vector.json')[k]==current_vector[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']);pair=row['pair'];chosen='reuse_off' if pair.get('reuse_off',{}).get('accepted') else 'reuse_on' if pair.get('reuse_on',{}).get('accepted') else None
  if pair.get('reuse_off',{}).get('accepted') and 'reuse_on' in pair:
   skipped='reuse_on';roles_skipped.append(dict(round=row['round'],candidate_rank=row['candidate_rank'],role=skipped));prefix=f"{row['round']:03d}_{row['candidate_rank']:02d}_{skipped}_";skippable += [x for x in read(actor/'process_costs.json') if x['tag'].startswith(prefix)]
  if chosen is None:continue
  target=Path(pair[chosen]['evaluation']);actual=Path(row['committed_evaluation']);assert sha(run_dir(target)/'routed.route')==sha(run_dir(actual)/'routed.route');assert all(read(target/'endpoint_vector.json')[k]==read(actual/'endpoint_vector.json')[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']);steps.append(dict(round=row['round'],candidate_rank=row['candidate_rank'],selected=chosen,recorded_selected='reuse_on' if actual==Path(pair['reuse_on']['evaluation']) else 'reuse_off',actual_route_exact=True,setup_hold_constraints_exact=True));current=target
 assert sha(run_dir(current)/'routed.route')==sha(run_dir(Path(c['final_state']))/'routed.route');results[name]=dict(steps=steps,skipped_ON_roles=roles_skipped,observed_omittable_sequential_work_seconds=sum(x['complete_process_seconds'] for x in skippable),observed_omittable_cost_records=skippable,actual_new_runtime_seconds=None,final_route_and_native_vector_match=True,final_resources=c['final_resources']);files += [actor/'completion.json',actor/'attempts.json',actor/'process_costs.json',actor/'evaluation_context/input_seal.json']
write(b/'completion.json',dict(passed=True,rows=results,native_calls=0,route_calls=0,source_sha256={str(p):sha(p) for p in files},qualification='Recorded-trajectory control-flow replay only. Same initial route and exact selected intermediate routes/vectors prove the native-first choice matches these two logged paired trajectories. It does not prove global policy equivalence, a complete-runtime speedup or behavior on new bundles/circuits. Omitted-stage measured wall sums are diagnostic work that would be absent, not a measured new algorithm time; full prospective validation remains necessary.'))
print({k:dict(skipped=len(v['skipped_ON_roles']),recorded_stage_seconds=v['observed_omittable_sequential_work_seconds']) for k,v in results.items()},flush=True)
