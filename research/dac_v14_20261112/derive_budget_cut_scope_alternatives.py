#!/usr/bin/env python3
"""Locate retained branch releases suggested by audited paths avoiding the certified cut."""
import argparse,array,collections,json,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,downstream_pins
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--certificate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
ref=a.reference.resolve();cert=a.certificate.resolve();proof=read(cert/'completion.json');assert proof['passed'] and proof['conditional_cut_certified'];assert all(sha(p)==h for p,h in proof['source_sha256'].items())
reg=read(ref/'registration.json');source=Path(reg['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cases={c['net']:c for c in read(ref/'original_cases.json')};fixed={n:set(c['retained']) for n,c in cases.items()};owners=collections.defaultdict(set)
for n,nodes in fixed.items():
 for node in nodes:owners[node].add(n)
switches={};caps=array.array('I')
for section,e in graph_records(graph):
 if section=='switches':t=e.find('timing');switches[int(e.attrib['id'])]=0 if t is None else f32(t.attrib.get('Tdel',0))
 elif section=='rr_nodes':assert len(caps)==int(e.attrib['id']);caps.append(int(e.attrib['capacity']))
 else:break
traces=read_trace(source/'routed.route');trees={n:from_trace(traces[n]['trace'],switches) for n in cases};sta={}
for line in (source/'native_sta_frontier.jsonl').open():
 r=json.loads(line)
 if r['type']=='pin' and not r['driver']:sta[r['net'],r['pin']]=r
offset={int(n):v for n,v in read(ref/'matching.json')['offsets_s'].items()};scope={}
for o in read(ref/'options.json'):
 net=o['net']
 if net not in proof['agents'] or proof['cut_node'] in o['forward'] or o['cost_s']+offset[net]>=0:continue
 affected=collections.defaultdict(set)
 for node in set(o['forward'])-fixed[net]:
  other=owners[node]-{net}
  if len(other)+1>caps[node]:
   for owner in other:affected[owner].add(node)
 extra={owner:sorted({p for node in nodes for p in downstream_pins(trees[owner],node)}-{cases[owner]['pin']}) for owner,nodes in affected.items()}
 assert extra and all(extra.values());key=tuple((n,tuple(pins)) for n,pins in sorted(extra.items()))
 if key not in scope:scope[key]=dict(extra_prune_by_net=extra,required_extra_pins=sum(map(len,extra.values())),enabling_options=[],affected_fixed_resources={})
 row=scope[key];row['enabling_options'].append(dict(net=net,pin=o['pin'],ipin=o['ipin'],cost_s=o['cost_s'],physical_nodes=o['forward']))
 for owner,nodes in affected.items():row['affected_fixed_resources'][owner]=sorted(set(row['affected_fixed_resources'].get(owner,[]))|nodes)
rows=[]
for key,row in scope.items():
 pins={(n,p) for n,ps in key for p in ps}
 if any({(n,p) for n,ps in other for p in ps}<pins for other in scope):continue
 row['extra_pin_current_STA']=[dict(net=n,pin=p,slack_s=sta[n,p]['setup_slack_s'],headroom_vs_current_worst_s=sta[n,p]['setup_slack_s']-reg['selection']['worst_slack_s'],physical_delay_s=sta[n,p]['native_net_delay_s']) for n,p in sorted(pins)];rows.append(row)
rows.sort(key=lambda r:(r['required_extra_pins'],sorted(r['extra_prune_by_net'])))
files=[Path(__file__),ref/'completion.json',ref/'options.json',ref/'original_cases.json',cert/'completion.json',source/'routed.route',source/'native_sta_frontier.jsonl',graph]
write(a.output,dict(passed=True,status='retained_scope_alternatives_derived_not_routed',input_run=str(source),cut_node=proof['cut_node'],alternatives=rows,native_calls=0,new_distance_queries=0,source_sha256={str(p):sha(p) for p in files},
 qualification='Minimal additional-pin sets only among the observed audited cut-avoiding paths. Recomputing target queries after pruning, mutual capacity, all collateral sink restoration, and nativeFULL/STA are still required. No global minimal-scope or quality claim.'))
print([dict(extra=r['extra_prune_by_net'],pins=r['required_extra_pins'],headrooms_ps=[p['headroom_vs_current_worst_s']*1e12 for p in r['extra_pin_current_STA']]) for r in rows],flush=True)
