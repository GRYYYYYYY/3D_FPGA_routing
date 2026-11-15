"""Archive sealed transactions independently of a still-running parent actor."""
import argparse, collections, copy, csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from endpoint_timing_policy_streaming_v2 import compare
from current_rejection_feedback_v1 import selected_actions
from pareto_archive_dimensions import annotate

p=argparse.ArgumentParser()
for name in ['parent','output']: p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--transaction',type=Path,action='append',required=True)
p.add_argument('--attempts',type=Path,required=True)
a=p.parse_args();parent=a.parent.resolve();out=a.output.resolve()
pc=read(parent/'completion.json');assert pc['passed']
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');added=[];summaries=[]
attempts=read(a.attempts)
files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',D/'pareto_archive_dimensions.py',D/'endpoint_timing_policy_streaming_v2.py',D/'current_rejection_feedback_v1.py',a.attempts.resolve()]
for tx in map(Path.resolve,a.transaction):
    c=read(tx/'completion.json');assert c['passed']
    assert all(sha(f)==h for f,h in c['source_sha256'].items())
    reg=read(tx/'registration.json');source=Path(reg['roles']['current_group']['state'])
    result=c['roles']['current_group'];assert result['status']=='legal_evaluated'
    state=Path(result['evaluation']);attempt=next(r for r in attempts if r.get('evaluation')==str(state))
    assert Path(attempt['before_state'])==source and not attempt['accepted'] and not attempt['policy_accepted']
    rd=run_dir(state);m=read(rd/'manifest.json')
    assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
    assert all(sha(f)==v['sha256'] for f,v in read(state/'input_seal.json')['inputs'].items())
    assert m['metrics']['native_full_check_passed']
    for n in ['packed.net','placed.place','routed.route']:assert sha(rd/n)==m['outputs'][n]['sha256']
    assert problem_identity(rd)==problem_identity(run_dir(source))==reg['problem_identity']
    physical=read(rd/'independent_audit.json');assert physical['audit']['passed']
    axes=physical['physical_metrics'];resources=dict(wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'])
    vector=read(state/'endpoint_vector.json');before=read(source/'endpoint_vector.json');delta=compare(before,vector)
    assert resources==result['resources'] and vector['cpd_s']==result['cpd_s'] and delta['compatible']
    decisions=read(tx/'current_group_decisions.json')
    for k in ['setup_improved','setup_regressed','hold_violation_regressions','cpd_after_s']:assert delta[k]==decisions['strict']['comparison'][k]
    origin=next(x for x in points if x.get('state')==str(source))
    ident=str(rd.relative_to(D));assert all(x['id']!=ident for x in points)
    row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
    row.update(id=ident,arm='sealed_timing_'+tx.parent.name,batch=tx.parents[3].name,batch_full_path=str(tx.parents[3]),
        state=str(state),source_state=str(source),status='legal',record_kind='sealed_candidate_in_live_actor',
        actor_final_selected=False,actor_terminal_claim=False,transition_committed=False,
        policy_accepted=False,actual_transition_policy='endpoint_under_resources',acceptance=decisions,
        run_manifest=str(rd/'manifest.json'),binary_sha256=sha(m['command'][0]),final_STA_binary_sha256=sha(m['command'][0]),
        route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=m['command'],environment=m.get('environment'),
        convergence='sealed_transaction_only',opportunity='Current-state action proposal in registered v5 endpoint branch; alternate-policy evaluation is descriptive, not a committed strict trajectory.',
        CPD_ns=vector['cpd_s']*1e9,CPD_interval_ns=[vector['cpd_s']*1e9]*2,CPD_precision='Full-precision native endpoint vector',**resources,
        SB_net_occupancy=axes['sb_pair_net_occupancy'],CB_net_occupancy=axes['cb_crossing_output_source_net_occupancy'],
        complete_single_configuration_seconds=None,timing_cohort=None,
        sealed_transaction_orchestrator_seconds=c['complete_orchestrator_seconds'],
        transaction_cost_scope='Excludes actor proposal preparation, selection, earlier rejections, initial routing and graph construction; not full algorithm time.',
        audit_provenance=str(rd/'independent_audit.json'),input_seal=str(state/'input_seal.json'),source_constraints_sha256=vector['constraints_sha256'])
    audit=read(tx/'current_group_audit/analysis.json');assert audit['passed']
    assert sha(audit['candidate_route'])==audit['candidate_sha256']
    assert all(sha(f)==h for f,h in audit['source_sha256'].items())
    regressions=[v for v in delta['changes'] if v['kind']=='setup' and v['delta_s']<0]
    summary=dict(transaction=str(tx),state=str(state),CPD_ns=row['CPD_ns'],resources=resources,
        CPD_gain_ps=(before['cpd_s']-vector['cpd_s'])*1e12,
        setup_improved=delta['setup_improved'],setup_regressed=delta['setup_regressed'],hold_violation_regressions=delta['hold_violation_regressions'],
        minimum_regressed_setup_distance_above_new_worst_ns=min((v['after_s']+vector['cpd_s'])*1e9 for v in regressions) if regressions else None,
        native_strict_accepts=decisions['strict']['accepted'],endpoint_vector_accepts=decisions['endpoint_vector']['accepted'])
    plan=tx.parents[1]/'feedback/proposal/plan.json'
    summary['actual_proposal']=attempt['proposal']
    summary['actual_rejection_reason']=attempt['reason']
    if plan.exists() and attempt['proposal'] in ['primary','all_positive_combined']:
        chosen,bad=selected_actions(read(plan)['actions'],audit['changed_delays'])
        summary.update(aggregate_feedback_surviving_actions=chosen,delay_increasing_connections=sorted(bad));files.append(plan)
    summaries.append(summary);points.append(row);added.append(ident)
    files += [tx/'completion.json',tx/'registration.json',tx/'current_group_decisions.json',tx/'current_group_audit/analysis.json',state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',source/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json']
annotate(points)
for s in summaries:s['quality_status']=next(x['quality_status'] for x in points if x.get('state')==s['state'])
out.mkdir(exist_ok=False);(out/'observed_attempts.json').write_bytes(a.attempts.read_bytes());write(out/'points.json',points)
write(out/'transaction_summaries.json',dict(passed=True,transactions=summaries,qualification='Sealed actual candidates; actor still running, no trajectory completion or independent circuit/sample claim. Exact policy rejection is preserved.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','record_kind','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:x.get(k) for k in fields} for x in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls=0,source_sha256={str(f):sha(f) for f in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','transaction_summaries.json']}))
print(dict(records=len(points),transactions=summaries),flush=True)
