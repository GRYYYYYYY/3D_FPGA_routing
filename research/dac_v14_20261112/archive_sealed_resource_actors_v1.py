"""Append every legal candidate of sealed resource actors, not just winners."""
import argparse
import collections
import copy
import csv
from pathlib import Path
from retained_prefix_workflow import read,write,sha,route_body,D
from run_native_scope_policy_v4 import run_dir,native_config
from native_problem_identity import problem_identity
from pareto_archive_dimensions import annotate

p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--actor',type=Path,action='append',required=True);a=p.parse_args()
parent=a.parent.resolve();out=a.output.resolve();pc=read(parent/'completion.json');assert pc['passed']
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');files=[Path(__file__).resolve(),parent/'points.json',parent/'completion.json',D/'pareto_archive_dimensions.py']
summaries=[];added=[];failures=[]
for actor in map(Path.resolve,a.actor):
    terminal=read(actor/'completion.json');assert terminal['passed']
    assert all(sha(p)==h for p,h in terminal['source_sha256'].items())
    reg=read(actor/'registration.json');root=Path(reg['initial_state']);origin=next(x for x in points if x.get('state')==str(root))
    identity=problem_identity(run_dir(root));constraints=read(root/'endpoint_vector.json')['constraints_sha256']
    seal=actor/'evaluation_context/input_seal.json';assert read(seal)['passed']
    attempts=read(actor/'attempts.json');steps=read(actor/'steps.json')
    assert len(steps)==terminal['accepted_steps']
    chosen={s['committed_evaluation'] for s in steps}
    assert terminal['final_state']==steps[-1]['committed_evaluation']
    local_ids=[]
    for attempt in attempts:
        for name,decision in attempt['pair'].items():
            if decision['status']!='legal_evaluated':
                failures.append(dict(actor=str(actor),round=attempt['round'],rank=attempt['candidate_rank'],role=name,outcome=decision));continue
            state=Path(decision['evaluation']);c=read(state/'completion.json');rd=run_dir(state);m=read(rd/'manifest.json')
            assert c['passed'] and Path(c['requires_final_input_seal'])==seal
            assert m['metrics']['native_full_check_passed'] and native_config(rd)==identity['effective_options']
            for n in ['packed.net','placed.place','routed.route']:
                assert sha(rd/n)==m['outputs'][n]['sha256']
            assert m['outputs']['packed.net']['sha256']==identity['packed'] and m['outputs']['placed.place']['sha256']==identity['placed']
            for key,path in [('architecture',m['command'][1]),('circuit',m['command'][2]),('graph',m['command'][m['command'].index('--read_rr_graph')+1])]:
                assert m['shared_inputs'][path]['sha256']==identity[key]
            audit=read(rd/'independent_audit.json');assert audit['audit']['passed'];metrics=audit['physical_metrics']
            axes=dict(wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'])
            v=read(state/'endpoint_vector.json');assert v['constraints_sha256']==constraints
            assert axes==decision['resources'] and v['cpd_s']==decision['CPD_s']
            assert decision['accepted']==decision['decision']['accepted']
            ident=str(rd.relative_to(D));assert not any(x['id']==ident for x in points)
            final=str(state)==terminal['final_state']
            row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
            row.update(id=ident,arm=actor.name+'_'+name,batch=actor.parent.name,batch_full_path=str(actor.parent),
                state=str(state),source_state=attempt['current_state'],status='legal',run_manifest=str(rd/'manifest.json'),
                record_kind='sealed_resource_final_selected' if final else 'sealed_resource_intermediate_candidate',
                actor_final_selected=final,transition_committed=str(state) in chosen,policy_accepted=decision['accepted'],
                binary_sha256=c['observer_binary_sha256'],final_STA_binary_sha256=c['observer_binary_sha256'],
                route_sha256=m['outputs']['routed.route']['sha256'],route_body_sha256=route_body(rd/'routed.route'),
                command=m['command'],environment=m.get('environment'),
                CPD_ns=v['cpd_s']*1e9,CPD_interval_ns=[v['cpd_s']*1e9]*2,CPD_precision='Full-precision native endpoint vector',**axes,
                SB_net_occupancy=metrics['sb_pair_net_occupancy'],CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],
                convergence=terminal['operator_stop'] if final else 'intermediate_in_completed_resource_menu',
                opportunity='Fixed current-state K8/rank3/delay_rr_id policy, paired unrestricted and retained-domain/failure-release candidates; domain-first commit order. Native-only matched trajectory is a separate actor and may still be pending.',
                iterations=None,initial_router_iterations=origin.get('iterations'),complete_single_configuration_seconds=None,timing_cohort=None,
                complete_imported_workflow_seconds=terminal['complete_imported_algorithm_workflow_seconds'] if final else None,
                observation_workflow=c['timing'],acceptance=decision['decision'],root_anchor=reg['anchor'],
                audit_provenance=str(rd/'independent_audit.json'),input_seal=str(seal),source_constraints_sha256=constraints,
                unknowns=['Complete cold single-configuration cost for this exact output; independently completed matched native-only trajectory.'])
            points.append(row);added.append(ident);local_ids.append(ident)
            files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json']
    files += [actor/'completion.json',actor/'registration.json',actor/'steps.json',actor/'attempts.json',seal]
    summaries.append(dict(actor=str(actor),initial_state=str(root),final_state=terminal['final_state'],
        initial_CPD_s=terminal['initial_CPD_s'],final_CPD_s=terminal['final_CPD_s'],final_resources=terminal['final_resources'],
        initial_resources={k:origin[k] for k in ['wirelength','SB_pairs','CB_sources']},
        root_to_final_resource_delta={k:terminal['final_resources'][k]-origin[k] for k in ['wirelength','SB_pairs','CB_sources']},
        accepted_steps=terminal['accepted_steps'],attempted_scopes=terminal['attempted_scopes'],legal_candidates=len(local_ids),
        candidate_records=local_ids,complete_imported_workflow_seconds=terminal['complete_imported_algorithm_workflow_seconds'],
        native_analysis_children=terminal['native_analysis_children'],matched_native_only_trajectory_complete=False))
annotate(points)
for summary in summaries:
    final=next(x for x in points if x.get('state')==summary['final_state'])
    summary['final_quality_status']=final['quality_status']
out.mkdir(exist_ok=False);write(out/'points.json',points);write(out/'nonlegal_outcomes.json',failures)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','record_kind','actor_final_selected','transition_committed','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:x.get(k) for k in fields} for x in points)
write(out/'actor_summaries.json',dict(passed=True,actors=summaries,nonlegal_outcomes=len(failures),
    qualification='All legal candidates, including rejected/degraded/nonselected alternatives, retained separately from committed/final states. Not independent samples or a matched-native superiority claim. Imported workflow time belongs only to its own final output; complete cold time stays unknown.'))
artifacts=['points.json','points.csv','nonlegal_outcomes.json','actor_summaries.json']
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls=0,
    quality_counts=dict(collections.Counter(x['quality_status'] for x in points)),
    source_sha256={str(p):sha(p) for p in files},artifact_sha256={n:sha(out/n) for n in artifacts}))
print(dict(records=len(points),added=len(added),actors=summaries),flush=True)
