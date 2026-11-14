#!/usr/bin/env python3
"""Summarize completed automatic repair trajectories, including rejected work."""
import argparse, collections, math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from current_sta_selector import select
from endpoint_timing_policy import compare

p=argparse.ArgumentParser();p.add_argument('--batches',nargs='+',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
sources={str(Path(__file__)):sha(Path(__file__))};rows=[]
def bind(path):
    path=Path(path);sources[str(path)]=sha(path);return read(path)
def describe(state,threshold):
    state=Path(state);c=bind(state/'completion.json');assert c['passed'];v=bind(state/'endpoint_vector.json');rd=Path(c['run'])
    audit=bind(rd/'independent_audit.json');assert audit['audit']['passed'];assert bind(rd/'analysis_gate.json')['passed']
    finite=[x for x in v['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x)]
    return dict(state=str(state),cpd_ns=v['cpd_s']*1e9,resources=audit['physical_metrics'],
      near_fixed_initial_components=sum(x<=threshold for x in finite),near_current_components=sum(x<=min(finite)+.2e-9 for x in finite),
      current_selection=select(rd/'native_sta_frontier.jsonl'),constraints_sha256=v['constraints_sha256'])
def category(tag):
    if tag.startswith('queries'):return 'capacity_query_audit' if tag.endswith('_audit') else 'capacity_state_and_query'
    if tag.startswith('joint'):return 'relaxed_audit' if tag.endswith('_audit') else 'joint_search' if tag.endswith('_search') else 'relaxed_query_preparation'
    for suffix in ['scope','native','audit','evaluation']:
        if tag.endswith('_'+suffix):return 'candidate_'+suffix
    raise AssertionError(tag)
for batch in a.batches:
    b=batch.resolve();c=bind(b/'completion.json');assert c['status']=='native_scope_policy_terminal'
    for path,h in c['source_sha256'].items():assert sha(path)==h
    reg=bind(b/'registration.json')
    for path,h in reg['source_sha256'].items():assert sha(path)==h
    initial=Path(reg['initial_state']);v0=read(initial/'endpoint_vector.json');threshold=min(x for x in v0['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x))+.2e-9
    costs=bind(b/'process_costs.json');groups=collections.defaultdict(float)
    for x in costs:groups[category(x['tag'])]+=x['complete_process_seconds']
    assert abs(sum(groups.values())-c['complete_child_process_seconds'])<1e-8
    attempts=bind(b/'attempts.json') if (b/'attempts.json').exists() else [];attemptrows=[]
    for x in attempts:
        work=Path(x['work']);r=bind(work/'registration.json')['roles']['candidate'];item=dict(**x,targets=r['targets'],removed_pins=r['removed_pins'],ordered_queries=r['queries'])
        ap=work/'candidate_audit/analysis.json'
        if ap.exists():
            audit=bind(ap);item['native_queries']=len(audit['queries']);item['native_attempts']=len(audit['attempts']);item['native_core_seconds']=audit.get('native_transaction_seconds');item['connection_delay_changes']=audit.get('changed_delays',[])
        if x.get('evaluated_state'):item['candidate']=describe(x['evaluated_state'],threshold)
        attemptrows.append(item)
    decisions=bind(b/'decisions.json') if (b/'decisions.json').exists() else [];decisionrows=[]
    for x in decisions:
        item={k:v for k,v in x.items() if k!='decision'};q=x.get('decision')
        if q:
            item['decision']={k:v for k,v in q.items() if k!='comparison'};cmp=q['comparison'];item['comparison']={k:v for k,v in cmp.items() if k!='changes'}
            item['largest_setup_losses']=sorted([r for r in cmp.get('changes',[]) if r['kind']=='setup' and r['delta_s']<0],key=lambda r:r['delta_s'])[:5]
        decisionrows.append(item)
    policies={}
    for name,o in c['outcomes'].items():
        state=Path(o['state']);cmp=compare(v0,read(state/'endpoint_vector.json'));cmp.pop('changes',None)
        histories=[]
        for path in sorted(b.glob(name+'_state_*.json')):
            h=bind(path);histories.append(dict(state=h['state'],selection=h['selection']))
        policies[name]=dict(**o,final=describe(state,threshold),comparison_to_initial=cmp,selection_history=histories)
    rows.append(dict(batch=str(b),scope=reg['scope'],objective=reg['objective'],near_ns=reg['near_ns'],initial=describe(initial,threshold),policies=policies,attempts=attemptrows,decisions=decisionrows,
      child_status_counts=dict(collections.Counter(x['status'] for x in costs)),
      costs=dict(complete_orchestrator_seconds=c['complete_orchestrator_seconds'],complete_child_process_seconds=c['complete_child_process_seconds'],
         nonoverlapping_child_categories_seconds=dict(groups),controller_outside_children_seconds=c['complete_orchestrator_seconds']-c['complete_child_process_seconds'],
         native_core_seconds=sum(x.get('native_core_seconds') or 0 for x in attemptrows),qualification='Native core is nested in native child time; do not add it. Shared exact historical work is excluded from measured incremental time. Not cold-start policy timing.'),
      reuse_receipts=bind(b/'reuse_receipts.json') if (b/'reuse_receipts.json').exists() else []))
write(a.output,dict(passed=True,research_complete=False,quality_promoted=False,batches=rows,source_sha256=sources,
 qualification='Development automatic current-STA trajectories, not an all-circuit or formal runtime claim. Local operator exhaustion does not terminate research. Full-precision exact acceptance and immutable rollback. Public snapshot f7167bd; new work local.'))
print([dict(batch=Path(r['batch']).name,policies={k:(v['accepted_steps'],v['final']['cpd_ns']) for k,v in r['policies'].items()},seconds=r['costs']['complete_orchestrator_seconds']) for r in rows])
