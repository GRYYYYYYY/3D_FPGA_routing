"""Bind both later local timing terminals and retain every actual candidate."""
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
parent=D/'multiobjective_budget47_intermediates_04';out=D/'multiobjective_budget47_complete_pair_01';pc=read(parent/'completion.json');assert pc['passed'];assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
comparison=D/'budget47_current_timing_composition_01/comparison.json';v=read(comparison);assert v['passed'] and v['whole_local_pair_terminal'];assert all(sha(f)==h for f,h in v['source_sha256'].items())
points=read(parent/'points.json');updates=[]
for arm,c in v['arms'].items():
 p=next(p for p in points if p.get('state')==c['final_state']);old={k:p.get(k) for k in ['record_kind','actor_final_selected','actor_terminal_claim','convergence']}
 p.update(previous_archive_metadata=old,previous_archive=str(parent),record_kind='sealed_final_selected_local_timing_candidate',actor_final_selected=True,actor_terminal_claim=True,actor_terminal_scope='Completed local timing arm from a resource-stage alternative; not an entire fresh-route algorithm.',convergence='complete_own_current_local_timing_menu',paired_local_completion_evidence=str(comparison),paired_local_completion_sha256=sha(comparison),imported_timing_segment_process_seconds=c['complete_timing_segment_process_seconds'],source_reobservation_seconds=c['source_reobservation_seconds'])
 assert p['complete_single_configuration_seconds'] is None
 updates.append(dict(arm=arm,id=p['id'],prior_metadata=old,quality_status=p['quality_status']))
assert next(p for p in points if p['state']==v['arms']['native_full462']['final_state'])['quality_status']=='dominated'
assert next(p for p in points if p['state']==v['arms']['guided_budget54']['final_state'])['quality_status']=='nondominated_in_collected_population'
out.mkdir(exist_ok=False);write(out/'points.json',points);write(out/'complete_pair_summary.json',v);write(out/'phase_terminal_updates.json',dict(passed=True,updates=updates,full_fresh_route_algorithm_cost_known=False,qualification='Both local timing menus terminal; no new observation introduced by reconciling metadata with actual terminal receipts. Old archives/snapshot labels retained.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','record_kind','actor_final_selected','actor_terminal_claim','convergence','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=[],metadata_updates=[x['id'] for x in updates],native_calls=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent/'completion.json',parent/'points.json',comparison]},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','complete_pair_summary.json','phase_terminal_updates.json']}))
print(dict(passed=True,records=len(points),native_final_dominated=True,guided_final_resources=v['arms']['guided_budget54']['resources']),flush=True)
