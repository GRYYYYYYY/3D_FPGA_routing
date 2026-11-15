"""Rebuild the four closed budget menus' legal event set and compare their actual endpoints."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from pareto_archive_dimensions import annotate
import copy

out=D/'multiobjective_connection_budget_closed_01';c=read(out/'completion.json');assert c['passed']
assert all(sha(out/f)==h for f,h in c['artifact_sha256'].items())
parent=Path(c['parent']);old=read(parent/'points.json');points=read(out/'points.json')
rows={r['id']:r for r in points};assert len(rows)==len(points)
oldids={r['id'] for r in old};expected=set();failed=[];summaries=[]
sources=[Path(__file__).resolve(),out/'completion.json',parent/'points.json']
for name in ['eltwise_A0_native','eltwise_A0_paired','bnn_A0_native','bnn_A0_paired']:
    actor=D/'connection_budget_resource_dev_02'/name
    terminal=read(actor/'completion.json');reg=read(actor/'registration.json')
    assert terminal['passed'] and reg['connection_budget']==64
    assert all(sha(f)==h for f,h in terminal['source_sha256'].items())
    attempts=read(actor/'attempts.json');steps=read(actor/'steps.json')
    selected={x['committed_evaluation'] for x in steps};counts=dict(legal=0,rejected=0)
    for attempt in attempts:
        for role,result in attempt['pair'].items():
            if result['status']!='legal_evaluated':
                failed.append(dict(actor=str(actor),round=attempt['round'],rank=attempt['candidate_rank'],role=role,outcome=result));continue
            state=Path(result['evaluation']);rid=str(run_dir(state).relative_to(D));expected.add(rid);r=rows[rid]
            assert rid not in oldids
            proof=require_publication_proof(state);v=read(state/'endpoint_vector.json')
            assert {k:r[k] for k in ['wirelength','SB_pairs','CB_sources']}==proof['resource_axes']==result['resources']
            assert r['CPD_ns']==v['cpd_s']*1e9
            assert r['policy_accepted']==result['accepted']
            assert r['transition_committed']==(str(state) in selected)
            final=str(state)==terminal['final_state'];assert r['actor_final_selected']==final
            assert r['complete_single_configuration_seconds'] is None and r['timing_cohort'] is None
            assert r['complete_imported_workflow_seconds']==(terminal['complete_imported_algorithm_workflow_seconds'] if final else None)
            counts['legal']+=1;counts['rejected']+=int(not result['accepted'])
    final=next(r for r in points if r.get('state')==terminal['final_state'])
    assert final['actor_final_selected'] and final['transition_committed']
    # Original K8 actors are closed controls, not imported cold-cost surrogates.
    control=D/'stable_seed_transfer_dev_01'/name
    oldreg=read(control/'registration.json');oldterminal=read(control/'completion.json')
    assert oldterminal['passed']
    for key in ['initial_state','anchor','domain_mode','seed_order','resource_objectives']:
        assert reg[key]==oldreg[key],key
    assert reg['local_probe']==oldreg['local_probe'] and reg['bundle_size']==oldreg['bundle_size']==8
    baseline=next(r for r in points if r.get('state')==oldterminal['final_state'])
    summaries.append(dict(actor=name,legal_observations=counts['legal'],rejected_legal_observations=counts['rejected'],
        old_final=oldterminal['final_state'],new_final=terminal['final_state'],
        new_minus_old_resources={k:terminal['final_resources'][k]-oldterminal['final_resources'][k] for k in ['wirelength','SB_pairs','CB_sources']},
        new_minus_old_CPD_ns=(terminal['final_CPD_s']-oldterminal['final_CPD_s'])*1e9,
        old_imported_seconds=oldterminal['complete_imported_algorithm_workflow_seconds'],new_imported_seconds=terminal['complete_imported_algorithm_workflow_seconds'],
        new_final_quality_status=final['quality_status'],baseline_id=baseline['id']))
    sources += [actor/'completion.json',actor/'registration.json',actor/'attempts.json',actor/'steps.json',control/'completion.json',control/'registration.json']
assert set(rows)-oldids==expected==set(c['added'])
assert failed==read(out/'nonlegal_outcomes.json')
derived={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
assert all({k:v for k,v in x.items() if k not in derived}=={k:v for k,v in rows[x['id']].items() if k not in derived} for x in old)
recalculated=copy.deepcopy(points);annotate(recalculated);assert recalculated==points
negative=next(x for x in summaries if x['actor']=='bnn_A0_paired')
assert negative['new_minus_old_resources']==dict(wirelength=46,SB_pairs=0,CB_sources=0) and negative['new_minus_old_CPD_ns']==0
assert c['complete_measured_configurations_total']==read(parent/'completion.json')['complete_measured_configurations_total']==26
write(out/'verification.json',dict(passed=True,records=len(points),added=len(expected),registered_roles=4,
    parent_non_derived_fields_exact=True,all_actual_legal_candidates_including_rejects_preserved=True,
    actual_native_FULL_STA_and_independent_audit=True,original_root_anchor_seed_scope_rules_matched=True,
    decisions_recomputed_by_archiver=True,whole_configuration_cost_not_invented=True,
    pareto_annotation_recomputed=True,complete_measured_configurations_total=26,
    comparisons=summaries,nonlegal_outcomes=len(failed),native_calls_new=0,
    qualification='Four closed development budget64 menus compared with original K8 own-current controls. Equal roots/anchors/seed/rank windows, different grouping and resulting trajectories. Costs are complete imported repair workflows, not cold runs or statistical speedups. All rejected legal alternatives retained; no independent-sample count increase inferred.',
    source_sha256={str(f):sha(f) for f in sources}))
print(dict(passed=True,records=len(points),added=len(expected),comparisons=summaries),flush=True)
