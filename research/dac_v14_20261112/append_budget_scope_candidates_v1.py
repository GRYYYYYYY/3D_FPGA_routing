"""Retain actual budget64 candidates; no component time is relabeled as full time."""
import copy,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy import compare
from pareto_archive_dimensions import annotate

parent=D/'multiobjective_complete_serial_lazy_01';out=D/'multiobjective_budget_scope_candidates_01'
probe=D/'connection_budget_scope_probe_01';proof=read(probe/'verification.json');assert proof['passed']
assert all(sha(f)==h for f,h in proof['source_sha256'].items())
pc=read(parent/'completion.json');assert pc['passed']
assert all(sha(parent/f)==h for f,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');source=Path(read(probe/'plan.json')['current_state'])
origin=next(p for p in points if p.get('state')==str(source))
files=[Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json',probe/'verification.json',probe/'completion.json'];added=[]
for name,row in proof['roles'].items():
    if row['status']!='legal_evaluated':continue
    state=Path(row['evaluation']);rd=run_dir(state);m=read(rd/'manifest.json');v=read(state/'endpoint_vector.json')
    assert read(state/'completion.json')['passed'] and m['metrics']['native_full_check_passed']
    assert all(sha(rd/n)==m['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
    audit=read(rd/'independent_audit.json');assert audit['audit']['passed'];axes=audit['physical_metrics']
    diff=compare(read(source/'endpoint_vector.json'),v);assert diff['compatible']
    ident=f'connection_budget_scope_probe_01/{name}_legal_candidate';assert all(p['id']!=ident for p in points)
    p={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort']}
    p.update(id=ident,arm='budget64_scope_'+name,batch='connection_budget_scope_probe_01',state=str(state),source_state=str(source),status='legal',
        record_kind='legal_single_scope_candidate_not_committed',actor_final_selected=False,transition_committed=False,
        run_manifest=str(rd/'manifest.json'),binary_sha256=sha(m['command'][0]),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=m['command'],environment=m.get('environment'),
        CPD_ns=v['cpd_s']*1e9,CPD_interval_ns=[v['cpd_s']*1e9]*2,CPD_precision='Full-precision native endpoint vector',
        wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'],SB_net_occupancy=axes['sb_pair_net_occupancy'],CB_net_occupancy=axes['cb_crossing_output_source_net_occupancy'],
        acceptance=dict(resources_under_timing=row['admissible_from_recorded_current_state'],strict_CPD=diff['cpd_strictly_better']),
        endpoint_change={k:diff[k] for k in ['setup_improved','setup_regressed','hold_violation_regressions']},
        convergence='single_scope_development_candidate',initial_routing_convergence=origin.get('initial_routing_convergence',origin['convergence']),
        opportunity='First rank window, budget64 whole cut net4111/54 connections from sealed BNN round6 current state; same seed/objective/original absolute limits. No original actor changed.',
        complete_single_configuration_seconds=None,timing_cohort=None,measurement_proof=str(probe/'verification.json'),
        actual_query_count=row['actual_queries'],actual_query_core_seconds=row['query_core_seconds'],
        shared_component_workflow=dict(receipt=str(probe/'completion.json'),seconds=proof['complete_imported_scope_seconds'],semantics='Shared two-arm imported-scope component execution, not this candidate whole-algorithm time; excludes selection preparation and initial routing.'),
        audit_provenance=str(rd/'independent_audit.json'),source_constraints_sha256=v['constraints_sha256'],
        unknowns=['No complete budget64 trajectory or fresh-route configuration cost; pooled historical query cores are descriptive, not same-backend full timing. Four quality axes omit secondary endpoint gains.'])
    points.append(p);added.append(ident);files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json']
annotate(points);out.mkdir(exist_ok=False);write(out/'points.json',points)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds','timing_cohort']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'scope_summary.json',dict(passed=True,added=added,source_state=str(source),committed_to_original_actor=False,shared_component_seconds=proof['complete_imported_scope_seconds'],roles=proof['roles']))
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls_new=0,source_sha256={str(f):sha(f) for f in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','scope_summary.json']}))
print(dict(passed=True,records=len(points),added=added),flush=True)
