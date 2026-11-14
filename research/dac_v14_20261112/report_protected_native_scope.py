#!/usr/bin/env python3
"""Record the failed protected transaction and the stronger conditional capacity reference."""
import collections,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_sta_selector import select
from endpoint_timing_policy import compare
from verify_path_witnesses_v2 import graph_records

sources={str(Path(__file__)):sha(Path(__file__))}
def bind(path):
 path=Path(path);sources[str(path)]=sha(path);return read(path)
refs=[]
for name in ['protected_critical_prefix_dev_01','protected_critical_prefix_dev_02']:
 c=bind(D/name/'completion.json');assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items())
 refs.append(dict(batch=name,protected_pins=c['protected_pins'],complete_process_seconds=c['complete_process_seconds'],results=[{k:v for k,v in r.items() if k!='edges'} for r in c['results']]))
native=D/'protected_native_scope_dev_01';nc=bind(native/'completion.json');assert nc['passed'];decision=bind(native/'decisions.json');audit=bind(native/'transaction/candidate_audit/analysis.json');scope=bind(native/'transaction/registration.json')
candidate=Path(nc['evaluated_state']);before=Path(scope['roles']['candidate']['state']);v0=bind(before/'endpoint_vector.json');v1=bind(candidate/'endpoint_vector.json');cmp=compare(v0,v1);cmp.pop('changes')
rd=Path(bind(candidate/'completion.json')['run']);physical=bind(rd/'independent_audit.json');assert physical['audit']['passed'];assert bind(rd/'analysis_gate.json')['passed']
assert not any(x['net']==6589 and x['pin']==4 for x in audit['changed_delays'])
assert any(x['net']==6592 and x['pin']==4 and x['after_s']>x['before_s'] for x in audit['changed_delays'])
search=D/'protected_joint_scope_search_02';s=bind(search/'completion.json');assert s['status']=='no_compatible_joint_positive_gain';assert all(sha(p)==h for p,h in s['source_sha256'].items())
assert s['search']['status']=='compatible';events=s['search']['events'];assert len(events)==1 and events[0]['node']==82116 and events[0]['owners']==[5490,6591] and events[0]['capacity']==1
queryrows=[]
for p in sorted((search/'current').glob('query_*/result.json')):
 r=bind(p);assert r['stop']==0 and r['cost']==r['lower']==8.569782938838699e-10 and r['forbidden']==[82116]
 for f in p.parent.iterdir():
  if f.is_file():sources[str(f)]=sha(f)
 queryrows.append(r)
assert len(queryrows)==2
manifest=read(Path(read(before/'completion.json')['run'])/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);resource=None
for section,e in graph_records(graph):
 if section=='rr_nodes' and int(e.attrib['id'])==82116:resource=dict(attributes=dict(e.attrib),location=dict(e.find('loc').attrib));break
assert resource['attributes']['type']=='IPIN' and resource['attributes']['capacity']=='1';sources[str(graph)]=sha(graph)
for name in ['protected_joint_scope_search_01','protected_joint_scope_search_02']:
 for p in (D/name).rglob('*'):
  if p.is_file():sources[str(p)]=sha(p)
for name in ['registration.json','process_costs.json','protected_scope_check.json','strict_current.json','endpoint_vector_current.json']:bind(native/name)
write(D/'protected_native_scope_summary_01.json',dict(passed=True,research_complete=False,quality_promoted=False,references=refs,
 native_control=dict(comparison=cmp,accepted={p:q['accepted'] for p,q in decision.items()},resources=physical['physical_metrics'],current_selection=select(rd/'native_sta_frontier.jsonl'),
  native_queries=len(audit['queries']),native_attempts=len(audit['attempts']),native_core_seconds=audit['native_transaction_seconds'],complete_orchestrator_seconds=nc['complete_orchestrator_seconds'],costs=read(native/'process_costs.json'),
  connection_delay_changes=audit['changed_delays'],protected_previous_victim=[6589,4],new_worst_victim=[6592,4]),
 conditional_joint_reference=dict(protected_pins=refs[1]['protected_pins'],capacity_resource=resource,node=82116,exhaustive_local_forbidden_queries=queryrows,objective=s['search']['objective'],
  conclusion='Each target can gain 7.639ps individually, but with these eight current non-target prefixes fixed, every strictly improving path for either target must use the same capacity-one IPIN82116. Banning it restores each exact lower distance to its original delay. Both target gains cannot coexist in this residual fixed-tree model.',
  limitation='No global routing or endpoint lower bound. Current prefix protection is stronger than a timing budget; equal-delay alternative victim paths and changes to retained tree scope remain possible research directions.'),
 source_sha256=sources,new_work_pushed=False))
print(dict(native_cpd_ns=v1['cpd_s']*1e9,protected_connections=len(refs[1]['protected_pins']),resource=resource,conditional_joint_gain=False),flush=True)
