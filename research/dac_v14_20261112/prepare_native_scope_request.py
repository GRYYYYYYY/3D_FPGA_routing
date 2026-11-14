#!/usr/bin/env python3
"""Generate a native free-path transaction from current STA and witness conflicts."""
import argparse,collections,json,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from coordinated_repair_tree import from_trace,downstream_pins
from verify_path_witnesses_v2 import graph_records,f32
from current_sta_selector import select
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--batch',type=Path,required=True)
p.add_argument('--opportunity',type=Path);p.add_argument('--single',nargs=2,type=int);p.add_argument('--scope',choices=['target_only','conflict'],default='conflict')
p.add_argument('--objective',choices=['weighted_soft','physical_capacity'],default='weighted_soft');p.add_argument('--near-ns',type=float,default=0.)
a=p.parse_args();assert bool(a.opportunity)!=bool(a.single);started=time.monotonic();state=a.state.resolve();source=Path(read(state/'completion.json')['run']);b=a.batch.resolve();b.mkdir(exist_ok=False)
assert read(state/'completion.json')['passed'];selection=select(source/'native_sta_frontier.jsonl',a.near_ns);rank={(r['net'],r['pin']):i for i,r in enumerate(selection['targets'])}
files=[Path(__file__),state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'native_sta_frontier.jsonl',D/'native_objective_stage_01/binding.json']
affected=collections.defaultdict(set)
if a.single:targets=[tuple(a.single)]
else:
 op=read(a.opportunity);assert op['status']=='compatible';seal=read(a.opportunity.parent/'candidate_binding.json');assert seal['passed'] and all(sha(p)==h for p,h in seal['source_sha256'].items())
 assert route_body(Path(op['input_run'])/'routed.route')==route_body(source/'routed.route')
 targets=[(r['net'],r['pin']) for r in op['targets']]
 if a.scope=='conflict':
  for node,c in op['current_other_net_conflicts'].items():
   for net in c['other_nets']:affected[net].add(int(node))
 files += [a.opportunity,a.opportunity.parent/'candidate_binding.json']
assert targets and set(targets)<=rank.keys()
sta={}
for line in (source/'native_sta_frontier.jsonl').open():
 r=json.loads(line)
 if r['type']=='pin' and not r['driver']:sta[r['net'],r['pin']]=r
removed=collections.defaultdict(set)
for net,pin in targets:removed[net].add(pin)
if affected:
 manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256'];files.append(graph)
 switches={}
 for section,e in graph_records(graph):
  if section!='switches':break
  t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
 traces=read_trace(source/'routed.route')
 for net,resources in affected.items():
  tree=from_trace(traces[net]['trace'],switches)
  for node in resources:removed[net].update(downstream_pins(tree,node))
  assert removed[net]
for net,pins in removed.items():
 for pin in pins:assert (net,pin) in sta and not sta[net,pin]['global'] and not sta[net,pin]['ignored']
ordered=sorted(targets,key=rank.get)+[(n,p) for n in sorted(removed) for p in sorted(removed[n]) if (n,p) not in targets]
request=b/'candidate.txt'
with request.open('w') as f:
 f.write(str(len(removed))+'\n')
 for n in sorted(removed):f.write(' '.join(map(str,[n,len(removed[n]),*sorted(removed[n])]))+'\n')
 f.write('0\n'+str(len(ordered))+'\n')
 for n,p in ordered:f.write(f"{n} {p} {sta[n,p]['setup_criticality_raw']:.17g}\n")
files.append(request)
role=dict(state=str(state),source=str(source),request=str(request),objective=a.objective,fixed_target_paths=False,targets=targets,removed_pins={str(n):sorted(p) for n,p in removed.items()},
 order='currentSTA_targets_then_ID_blockers',queries=[dict(net=n,pin=p,slack_s=sta[n,p]['setup_slack_s'],raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in ordered],source_sha256={str(p):sha(p) for p in files})
write(b/'registration.json',dict(status='registered_before_native',roles={'candidate':role},scope=a.scope,selection=selection,conflicting_resources={str(n):sorted(v) for n,v in affected.items()},preparation_seconds=time.monotonic()-started,
 qualification='Targets and released blocker branches derived automatically from the current state and audited witness conflicts. Native chooses every path; no preset target paths or pre-restored external blocker trees.'))
print(dict(targets=targets,affected_nets=len(removed),queries=len(ordered),scope=a.scope),flush=True)
