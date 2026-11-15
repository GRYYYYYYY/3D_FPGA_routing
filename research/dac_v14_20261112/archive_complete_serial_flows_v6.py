"""Preserve complete measured serial flows and every legal attempted candidate."""
import argparse,copy,csv,hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from pareto_archive_dimensions import annotate

p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--flow',type=Path,action='append',required=True);p.add_argument('--cohort',type=Path,required=True);args=p.parse_args()
parent=args.parent.resolve();out=args.output.resolve();pc=read(parent/'completion.json')
assert pc['passed'] and all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',D/'pareto_archive_dimensions.py'];added=[];summaries=[]
cohort=args.cohort.resolve();comparison=read(cohort/'comparison.json');assert comparison['passed']
assert comparison['registered_roles']==len(comparison['results'])
assert all(sha(f)==h for f,h in comparison['source_sha256'].items())
assert {Path(root).resolve() for root in args.flow}=={cohort/name for name,r in comparison['results'].items() if r['status']=='complete_legal_configuration'}
files += [cohort/'comparison.json',cohort/'queue/completion.json',cohort/'queue/results.json',cohort/'plan.json']
failures=[]
for name,r in comparison['results'].items():
    if r['status']=='complete_legal_configuration':continue
    root=cohort/name;measurement=read(root/'measurement/completion.json');m=read(root/'flow/initial/runs/state/manifest.json')
    assert not measurement['passed'] and m['status']=='failed' and not m['metrics']['native_full_check_passed']
    assert r['quality'] is None and r['actual_failed_seconds']==measurement['complete_command_wall_seconds']
    failures.append(dict(role=name,status='initial_routing_failed_before_resource_repair',quality=None,complete_failed_command_seconds=measurement['complete_command_wall_seconds'],measurement=measurement,native_manifest=str(root/'flow/initial/runs/state/manifest.json'),native_returncode=m['returncode'],wrapper_returncode=r['failed_returncode'],qualification='Failure within registered200route iterations; not mathematical unroutability or a legal CPD/resource point. Initial graph-index construction and failed routing remain in measured command cost.'))
    files += [root/'measurement/completion.json',root/'measurement/stdout.log',root/'flow/initial/runs/state/manifest.json',root/'flow/initial/runs/state/stdout.log',root/'config.json']
original_circuits={row['circuit'] for row in points}

for root in map(Path.resolve,args.flow):
    proof_path=root/('explicit_policy_verification.json' if (root/'explicit_policy_verification.json').exists() else 'completion.json');proof=read(proof_path);assert proof['passed'] and proof['complete_configuration_verified']
    assert all(sha(f)==h for f,h in proof['source_sha256'].items())
    initial=Path(proof['initial_state']);identity=problem_identity(run_dir(initial))
    initial_manifest=read(run_dir(initial)/'manifest.json');cmd=initial_manifest['command']
    def option(name,default=None):return cmd[cmd.index(name)+1] if name in cmd else default
    sdc=option('--sdc_file');assert sdc is None,'Explicit SDC needs an explicitly bound cohort identity'
    physical_identity=dict(architecture=identity['architecture'],graph=identity['graph'],netlist=identity['circuit'],packed=identity['packed'],placed=identity['placed'],clock_modeling=option('--clock_modeling'),sdc='native_generated_default_from_bound_netlist',seed=option('--seed'))
    cohort=hashlib.sha256(json.dumps(physical_identity,sort_keys=True).encode()).hexdigest()
    origin=dict(circuit=Path(cmd[2]).stem,physical_identity=physical_identity,quality_cohort=cohort)
    matching=[p for p in points if p['quality_cohort']==cohort]
    assert all(p['physical_identity']==physical_identity for p in matching)
    initial_convergence=option('--router_max_convergence_count','native_default')
    config=read(root/'config.json');actor=root/'flow/repair';terminal=read(actor/'completion.json')
    files += [proof_path,root/'config.json',root/'measurement/completion.json',actor/'completion.json',actor/'attempts.json']
    observations=[dict(state=initial,source=initial,role='initial',tx=None,committed=False,final=proof['initial_state']==proof['final_state'])]
    for attempt in read(actor/'attempts.json'):
        tx=Path(attempt['transaction'])
        for role,result in read(tx/'progress.json').items():
            if result['status']!='legal_evaluated':continue
            state=Path(result['evaluation']);committed=attempt.get('committed_evaluation')==str(state) and attempt.get('accepted_role')==role
            observations.append(dict(state=state,source=Path(attempt['current_state']),role=role,tx=tx,committed=committed,final=committed and str(state)==proof['final_state']))
    for observation in observations:
        state=observation['state'];rd=run_dir(state);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed']
        assert all(sha(rd/n)==m['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
        audit=read(rd/'independent_audit.json');assert audit['audit']['passed'];axes=audit['physical_metrics'];v=read(state/'endpoint_vector.json')
        ident=str((observation['tx']/f"{observation['role']}_measured_candidate_observation" if observation['tx'] else root/'fresh_route_observation').relative_to(D))
        assert all(p['id']!=ident for p in points)
        row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort']}
        row['initial_routing_convergence']=initial_convergence
        row.update(id=ident,arm='complete_serial_'+config['domain_mode']+'_'+observation['role'],batch=root.name,batch_full_path=str(root),state=str(state),source_state=str(observation['source']),status='legal',
            record_kind='complete_measured_algorithm_final' if observation['final'] else 'complete_flow_initial_or_intermediate_observation',actor_final_selected=observation['final'],transition_committed=observation['committed'],
            run_manifest=str(rd/'manifest.json'),binary_sha256=sha(config['route_command'][0]),final_STA_binary_sha256=sha(m['command'][0]),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=m['command'],environment=m.get('environment'),
            CPD_ns=v['cpd_s']*1e9,CPD_interval_ns=[v['cpd_s']*1e9]*2,CPD_precision='Full-precision native endpoint vector',
            wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'],SB_net_occupancy=axes['sb_pair_net_occupancy'],CB_net_occupancy=axes['cb_crossing_output_source_net_occupancy'],
            convergence='complete_current_resource_menu' if observation['final'] else 'initial_or_intermediate_in_completed_flow',
            opportunity='Fresh initial route followed by serial K8/rank3 own-current '+config['domain_mode']+' refinement; seed='+config.get('seed_order','native')+', domain failure release='+str(config.get('domain_feedback',False))+'. No external result reuse or history-best selection.',
            complete_single_configuration_seconds=proof['complete_wall_seconds'] if observation['final'] else None,
            timing_cohort=None,complete_timing_comparison_status='Single shared-host development observation retained; matched repeated confirmation not yet available',
            measured_memory={k:proof[k] for k in ['waited_process_RSS_high_water_kib','sampled_tree_RSS_peak_kib','sampled_tree_PSS_peak_kib','missing_memory_observations']} if observation['final'] else None,
            audit_provenance=str(rd/'independent_audit.json'),source_constraints_sha256=v['constraints_sha256'],
            accepted_steps=proof['accepted_steps'],attempted_scopes=proof['attempted_scopes'],actual_native_work=proof.get('actual_native_work'),execution_policy=config.get('execution_policy','evaluate_both_native_and_domain'),measurement_proof=str(proof_path),unknowns=['Single shared-host observation, uncontrolled OS cache; no statistical speedup or transfer of time to other implementations, pooled executions or other outputs.'])
        if observation['tx']:
            decision=read(observation['tx']/(observation['role']+'_decisions.json'))['resources_under_timing'];row['acceptance']=decision;files.append(observation['tx']/(observation['role']+'_decisions.json'))
        points.append(row);added.append(ident);files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json']
    assert sum(x['final'] for x in observations)==1,'Exactly one actual selected final state carries complete cost'
    summaries.append(dict(root=str(root),final_state=proof['final_state'],mode=config['domain_mode'],quality={k:proof[k] for k in ['CPD_ns','resources']},complete_wall_seconds=proof['complete_wall_seconds'],cache_mode=config['cache_mode'],memory={k:proof[k] for k in ['waited_process_RSS_high_water_kib','sampled_tree_RSS_peak_kib','sampled_tree_PSS_peak_kib','missing_memory_observations']},observations=len(observations)))
annotate(points);out.mkdir(exist_ok=False);write(out/'points.json',points)
write(out/'failed_role_observations.json',failures)
write(out/'complete_flow_summaries.json',dict(passed=True,flows=summaries,registered_new_roles=comparison['registered_roles'],successful_new_legal_roles=comparison['successful_legal_roles'],failed_new_roles=len(failures),qualification='Every legal initial/candidate observation retained. Zero-commit initial states remain actual final outputs. Only selected final outputs carry their own actual complete configuration time and memory; no intermediate-state or other-version time borrowed. Same-state local FULLSTA reuse is within the measured execution. Development timing comparisons, not independent circuit samples or statistical speedups.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds','timing_cohort']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls=0,complete_measured_configurations_total=pc['complete_measured_configurations_total']+len(summaries),complete_known_circuits=pc['complete_known_circuits']+len({row['circuit'] for row in points}-original_circuits),complete_vertical_families=pc['complete_vertical_families'],registered_new_roles=comparison['registered_roles'],successful_new_legal_roles=len(summaries),failed_new_roles=len(failures),source_sha256={str(f):sha(f) for f in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','complete_flow_summaries.json','failed_role_observations.json']}))
print(dict(records=len(points),added=len(added),flows=summaries),flush=True)
