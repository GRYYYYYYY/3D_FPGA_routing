"""Check actual domain events, original records and unspliced whole cost."""
import argparse
from pathlib import Path
from retained_prefix_workflow import read, write, sha
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy import compare

p=argparse.ArgumentParser()
for n in ['archive','case','cost','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();archive,case,cost,out=[getattr(a,n).resolve() for n in ['archive','case','cost','output']]
assert not out.exists()
receipt=read(archive/'completion.json');proof=read(case/'completion.json')
assert receipt['passed'] and proof['passed'] and proof['complete_configuration_verified']
checked={}
def digest(path):
    path=str(Path(path).resolve())
    if path not in checked:checked[path]=sha(path)
    return checked[path]
assert all(digest(archive/n)==h for n,h in receipt['artifact_sha256'].items())
assert all(digest(f)==h for f,h in receipt['source_sha256'].items())
points=read(archive/'points.json');parent=Path(receipt['parent'])
original=read(parent/'points.json');parent_receipt=read(parent/'completion.json')
assert len(points)==receipt['records']==len(original)+len(receipt['added'])
by_id={row['id']:row for row in points};assert len(by_id)==len(points)
derived={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by',
         'quality_projection_retained','quality_status','candidate_retention','archive_retained',
         'record_preserved','five_dimensional_comparison_count','retention_qualification'}
for row in original:
    assert row['id'] in by_id
    assert {k:v for k,v in row.items() if k not in derived}=={k:v for k,v in by_id[row['id']].items() if k not in derived}
added=[by_id[ident] for ident in receipt['added']]
assert len(added)==len({row['state'] for row in added})
assert all(Path(row['state']).resolve().is_relative_to(case/'flow') for row in added)
events=read(archive/'events.json')
assert {e['state'] for e in events}=={row['state'] for row in added}
assert len(events)==receipt['actual_observation_events']
assert sum(e['phase']=='fresh_initial' for e in events)==1
assert sum(e['phase']=='handoff_LOAD' for e in events)==1
assert sum(e['phase']=='resource' and e['committed'] for e in events)==proof['resource_accepted_steps']
assert sum(e['phase']=='timing' and e['committed'] for e in events)==proof['timing_accepted_steps']
expected={proof['initial_state']}
flow=case/'flow';done=read(flow/'completion.json')
expected.add(done['timing_initial_state'])
for attempt in read(flow/'resource_flow/repair/attempts.json'):
    for row in read(Path(attempt['transaction'])/'progress.json').values():
        if row['status']=='legal_evaluated':expected.add(row['evaluation'])
for attempt in read(flow/'timing/attempts.json'):
    if attempt.get('evaluation'):expected.add(attempt['evaluation'])
assert expected=={row['state'] for row in added},'Missing or invented actual observation'
initial=read(Path(proof['initial_state'])/'endpoint_vector.json')
for point in added:
    state=Path(point['state']);run=run_dir(state)
    assert read(state/'completion.json')['passed'] and require_publication_proof(state)['passed']
    assert digest(run/'routed.route')==point['route_sha256']
    vector=read(state/'endpoint_vector.json');assert compare(initial,vector)['compatible']
    assert point['CPD_ns']==vector['cpd_s']*1e9
    metrics=read(run/'independent_audit.json')['physical_metrics']
    assert point['wirelength']==metrics['planar_wirelength_excluding_sb_half_nodes']
    assert point['SB_pairs']==metrics['sb_pairs_used'] and point['CB_sources']==metrics['cb_crossing_output_sources_used']
    if not point['actor_final_selected']:
        assert point['complete_single_configuration_seconds'] is None and point['memory_observation'] is None
        assert point['timing_cohort'] is None
finals=[row for row in added if row['actor_final_selected']];assert len(finals)==1
final=finals[0]
assert final['state']==proof['final_state']
assert final['complete_single_configuration_seconds']==proof['complete_wall_seconds']
assert final['memory_observation']['sampled_tree_PSS_peak_kib']==proof['sampled_tree_PSS_peak_kib']
assert {k:final[k] for k in ['wirelength','SB_pairs','CB_sources']}==proof['resources']
assert final['whole_case_actual_work']=={k:proof[k] for k in final['whole_case_actual_work']}
cost_proof=read(cost/'completion.json');summary=read(cost/'summary.json')
assert cost_proof['passed'] and summary['passed']
assert all(digest(cost/n)==h for n,h in cost_proof['artifact_sha256'].items())
assert all(digest(f)==h for f,h in summary['source_sha256'].items())
assert summary['complete_wall_seconds']==proof['complete_wall_seconds']
assert abs(sum(summary['disjoint_category_seconds'].values())-proof['complete_wall_seconds'])<1e-8
assert all(r['byte_exact_same_command_payloads'] for r in summary['metadata_runtime_aliases'])
assert receipt['complete_measured_configurations_total']==parent_receipt['complete_measured_configurations_total']+1
write(out,dict(passed=True,native_calls_new=0,records=receipt['records'],new_actual_states=len(added),
    actual_events=len(events),parent_records_preserved=True,only_actual_final_has_whole_cost=True,
    complete_measured_configurations_total=receipt['complete_measured_configurations_total'],
    actual_final_resources=proof['resources'],actual_final_CPD_ns=proof['CPD_ns'],
    actual_final_whole_seconds=proof['complete_wall_seconds'],
    source_sha256={str(f):digest(f) for f in [Path(__file__).resolve(),archive/'completion.json',case/'completion.json',cost/'completion.json']},
    qualification='Independent read-only reconstruction of expected actual state/event set and unchanged parent observations. Dominance-only derived metadata may update; original quality/cost/provenance stays exact. Every new point has actual native FULL/STA and independent physical proof; only actual final receives measured own whole time/memory. Pending structural candidates remain excluded. No native rerun.'))
print(dict(passed=True,records=receipt['records'],new_actual_states=len(added),whole_seconds=proof['complete_wall_seconds']),flush=True)
