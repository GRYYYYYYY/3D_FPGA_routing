#!/usr/bin/env python3
"""Expand repair scope from verified conflicts of the victim's optimistic path."""
import collections,copy,json,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,downstream_pins,nodes
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
old=D/'joint_native_repair_dev_01';reg=copy.deepcopy(read(old/'registration.json')['roles']['Tf_fixed_slack'])
source=Path(reg['source']);bound=D/'joint_victim_bound_01';assert read(bound/'completion.json')['passed']
case=read(bound/'before_any_blocker/case.json');victim=(case['net'],case['pin'])
path=[]
for line in (bound/'only_fixed_targets/stdout.log').read_text().splitlines():
 v=line.split()
 if v[0]=='EDGE':path.append(int(v[5]))
blocked=set(case['blocked']);conflict_nodes=set(path)&blocked
traces=read_trace(source/'routed.route');original_nodes={n:{x.inode for x in t['trace']} for n,t in traces.items()}
partial=collections.defaultdict(set)
for line in (old/'Tf_fixed_slack/runs/state/joint_native.log').read_text().splitlines():
 v=line.split()
 if v[0]=='KEEP':partial[int(v[1])].add(int(v[2]))
first=read(Path(reg['transaction'])/'initial_transaction.json')
for n,p in first['target_reserved_nodes'].items():partial[int(n)].update(p)
owners={node:[n for n,owned in original_nodes.items() if node in partial.get(n,owned) and n!=victim[0]] for node in conflict_nodes}
manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);switches={}
for section,e in graph_records(graph):
 if section!='switches':break
 t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
extra=collections.defaultdict(set)
for node,ns in owners.items():
 assert ns
 for n in ns:extra[n].update(downstream_pins(from_trace(traces[n]['trace'],switches),node))
for n,pins in extra.items():reg['removed_pins'][str(n)]=sorted(set(reg['removed_pins'].get(str(n),[]))|pins)
sta={}
for line in (source/'native_sta_frontier.jsonl').open():
 r=json.loads(line)
 if r['type']=='pin' and not r['driver']:sta[r['net'],r['pin']]=r
allpins={(int(n),int(p)) for n,pins in reg['removed_pins'].items() for p in pins};targets={tuple(t) for t in reg['targets']};querypins=allpins-targets
# This arm isolates victim protection plus conflict-feedback scope; the protected
# output is routed first, followed by current-slack order. It is not evidence
# about scope versus order separately; separate ablation follows if beneficial.
ordered=sorted(querypins,key=lambda k:(k!=victim,sta[k]['setup_slack_s'] if isinstance(sta[k]['setup_slack_s'],(int,float)) else float('inf'),k))
b=D/'joint_native_feedback_dev_01';b.mkdir(exist_ok=False);request=b/'Tf_feedback_scope.txt'
final=read(Path(reg['transaction'])/'final_transaction_trees.json')
with request.open('w') as f:
 f.write(str(len(reg['removed_pins']))+'\n')
 for n,pins in sorted(reg['removed_pins'].items(),key=lambda x:int(x[0])):f.write(' '.join(map(str,[n,len(pins),*pins]))+'\n')
 f.write(str(len(targets))+'\n')
 for n,p in sorted(targets):
  route=first['target_reserved_nodes'][str(n)];f.write(f'{n} {p} {len(route)-1}\n')
  for u,v in zip(route,route[1:]):f.write(f"{u} {v} {final[str(n)]['edges'][str(v)][1]}\n")
 f.write(str(len(ordered))+'\n')
 for n,p in ordered:f.write(f"{n} {p} {sta[n,p]['setup_criticality_raw']:.17g}\n")
reg.update(request=str(request),order='victim_first_then_current_slack',queries=[dict(net=n,pin=p,slack_s=sta[n,p]['setup_slack_s'],raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in ordered])
reg['source_sha256'].update({str(p):sha(p) for p in [Path(__file__),request,bound/'completion.json',bound/'before_any_blocker/case.json',bound/'only_fixed_targets/stdout.log']})
write(b/'registration.json',dict(status='registered_before_native',roles={'Tf_feedback_scope':reg},
 hypothesis='The registered fixed scope imposes a 0.460476ns physical victim loss. Expand only branches owning conflicts on a verified shorter victim path, then protect that victim first.',
 conflict_feedback={str(n):v for n,v in owners.items()},additional_scope={str(n):sorted(p) for n,p in extra.items()},protected_victim=victim,
 qualification='Mechanism development, not a pure order-only ablation. New scope is derived from an actual witness, not a net whitelist. Original fixed scope/order controls preserved; all updated occupancy/FULL/STA gates apply.',
 source_sha256={str(p):sha(p) for p in [Path(__file__),bound/'completion.json',old/'registration.json']}))
print(dict(conflict_nodes=sorted(conflict_nodes),owners=owners,additional_scope={n:sorted(p) for n,p in extra.items()},queries=len(ordered)))
