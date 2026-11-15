"""Add later local-phase completion facts without rewriting historical snapshots."""
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
parent=D/'multiobjective_budget47_intermediates_03';out=D/'multiobjective_budget47_composition_01'
pc=read(parent/'completion.json');assert pc['passed'];assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
terminal=D/'budget47_native_timing_terminal_validation_01/completion.json';closed=read(terminal);assert closed['passed'] and closed['local_native_timing_arm_terminal'] and not closed['paired_comparison_terminal']
assert all(sha(f)==h for f,h in closed['source_sha256'].items())
transfer=D/'budget47_first_timing_transfer_validation_01/completion.json';proof=read(transfer);assert proof['passed'];assert all(sha(f)==h for f,h in proof['source_sha256'].items())
points=read(parent/'points.json');point=next(p for p in points if p.get('state')==closed['final_state'])
assert point['CPD_ns']==closed['final_CPD_ns'] and all(point[k]==v for k,v in closed['final_resources'].items())
old={k:point.get(k) for k in ['record_kind','actor_final_selected','actor_terminal_claim','convergence']}
point.update(observed_snapshot_metadata=old,observed_snapshot_parent=str(parent),record_kind='sealed_candidate_selected_by_completed_local_timing_actor',actor_final_selected=True,actor_terminal_claim=True,actor_terminal_scope='Local native_full462 timing operator only; resource-prefix creation and whole paired workflow remain separate.',convergence='complete_local_timing_menu_from_a_guided_resource_candidate',phase_terminal_evidence=str(terminal),phase_terminal_evidence_sha256=sha(terminal),imported_timing_segment_process_seconds=closed['complete_timing_segment_process_seconds'],source_reobservation_seconds=closed['source_reobservation_seconds'])
assert point['complete_single_configuration_seconds'] is None and point['timing_cohort'] is None
out.mkdir(exist_ok=False);write(out/'points.json',points);write(out/'sealed_timing_summaries.json',read(parent/'sealed_timing_summaries.json'))
write(out/'phase_terminal_updates.json',dict(passed=True,updates=[dict(id=point['id'],old_snapshot=old,local_timing_phase_terminal=True,complete_algorithm_cost_known=False,terminal_evidence=str(terminal))],first_timing_composition_evidence=str(transfer),qualification='Only metadata is reconciled with a later actual local-phase terminal receipt. Older immutable archives retain their original intermediate observation labels. No duplicated observation or invented whole-configuration cost.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','record_kind','actor_final_selected','actor_terminal_claim','convergence','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=[],metadata_updates=[point['id']],native_calls=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent/'completion.json',parent/'points.json',parent/'sealed_timing_summaries.json',terminal,transfer]},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','sealed_timing_summaries.json','phase_terminal_updates.json']}))
print(dict(passed=True,records=len(points),local_native_phase_terminal=True,whole_pair_complete=False),flush=True)
