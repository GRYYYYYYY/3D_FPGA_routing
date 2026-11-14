#!/usr/bin/env python3
"""Conditional potential with current near-critical victim prefixes preserved.

This is a relaxed fixed-tree reference, not an endpoint or circuit lower bound.
No native route or accepted state is modified.
"""
import argparse,array,collections,json,resource,shutil,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

p=argparse.ArgumentParser();p.add_argument('--attempt',type=Path,required=True);p.add_argument('--queries',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
b=a.batch.resolve();b.mkdir(exist_ok=False);attempt=a.attempt.resolve();q=a.queries.resolve();reg=read(attempt/'registration.json');role=reg['roles']['candidate'];source=Path(role['source']);analysis=read(q/'analysis.json')
assert analysis['passed'] and all(sha(p)==h for p,h in analysis['source_sha256'].items())
assert all(sha(p)==h for p,h in role['source_sha256'].items())
targets={tuple(x) for x in role['targets']};target_nets={x[0] for x in targets};rows={(x['net'],x['pin']):x for x in analysis['results']};cases={(x['net'],x['pin']):x for x in read(q/'cases.json')}
max_gain=max(rows[x]['improvement_ns']*1e-9 for x in targets);assert max_gain>0
worst=reg['selection']['worst_slack_s']
protected=[x for x in role['queries'] if x['net'] not in target_nets and isinstance(x['slack_s'],(int,float)) and x['slack_s']<=worst+max_gain]
assert protected, 'No near-critical released victim selected by the registered rule'
manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']
binary=D/'residual_query_offline_01/graph.bin';driver=D/'current_sta_queries_01/critical_capacity_driver';assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
assert sha(driver)==read(D/'current_sta_queries_01/execution.json')['output_sha256']['critical_capacity_driver']
bindings={str(p):sha(p) for p in [Path(__file__),attempt/'registration.json',q/'analysis.json',q/'cases.json',q/'capacities.bin',source/'routed.route',source/'native_sta_frontier.jsonl',binary,driver,graph]}
write(b/'registration.json',dict(status='registered_before_queries',question='Does a positive target delay gain remain when current near-critical victim prefixes are preserved, while all other background routing is relaxed?',
 selection_rule='Released non-target pins with current slack no greater than worst target slack plus maximum audited relaxed target gain; exact numerical comparison, not acceptance tolerance.',
 protected_pins=protected,max_target_relaxed_gain_s=max_gain,source_sha256=bindings,
 limits=dict(per_query_seconds=120,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),native_calls=0))
switches={}
for section,e in graph_records(graph):
 if section!='switches':break
 t=e.find('timing');switches[int(e.attrib['id'])]=0 if t is None else f32(t.attrib.get('Tdel',0))
traces=read_trace(source/'routed.route');preserved=collections.defaultdict(set)
for x in protected:
 n=x['net'];tree=from_trace(traces[n]['trace'],switches);node=tree['sinks'][x['pin']]
 while True:
  preserved[n].add(node)
  if node==tree['root']:break
  node=tree['edges'][node][0]
owners=collections.Counter(node for nodes in preserved.values() for node in nodes)
caps=array.array('I');caps.frombytes((q/'capacities.bin').read_bytes());blocked={i for i,c in enumerate(caps) if owners[i]>=c}
write(b/'protected_nodes.json',dict(by_net={str(n):sorted(v) for n,v in preserved.items()},blocked=sorted(blocked),rule='Count each protected net once per RR node. Ban a node only when protected occupancy exhausts its actual capacity; high-capacity terminals remain available.'))
bindings[str(b/'protected_nodes.json')]=sha(b/'protected_nodes.json')
results=[]
for n,pin in sorted(targets):
 c=cases[n,pin];retained=set(c['retained']);assert not retained & blocked
 d=b/f'net{n}_pin{pin}';d.mkdir();case=d/'case.txt'
 with case.open('w') as f:
  f.write('1\n'+' '.join(map(str,[n,pin,c['sink'],len(retained),len(c['anchors']),len(blocked)]))+'\n')
  f.write(' '.join(map(str,sorted(retained)))+'\n')
  for node,value in sorted(c['anchors'].items(),key=lambda r:int(r[0])):f.write(f'{node} {value:.17g}\n')
  f.write(' '.join(map(str,sorted(blocked)))+'\n')
 t=time.monotonic()
 with (d/'stdout.log').open('w') as out,(d/'stderr.log').open('w') as err:
  proc=subprocess.run([str(driver),str(binary),str(case),'capacity'],stdout=out,stderr=err,timeout=120)
 elapsed=time.monotonic()-t;assert proc.returncode==0
 record=None;edges=[]
 for line in (d/'stdout.log').read_text().splitlines():
  v=line.split();assert tuple(map(int,v[1:4]))==(n,pin,1)
  if v[0]=='RESULT':record=dict(net=n,pin=pin,stop=int(v[4]),expansions=int(v[5]),cost_s=float(v[8]),lower_s=float(v[9]),query_core_seconds=float(v[10]),edge_count=int(v[11]),complete_query_process_seconds=elapsed)
  else:assert v[0]=='EDGE' and int(v[4])==len(edges);edges.append((int(v[5]),int(v[6]),float(v[7])))
 assert record['stop']==0 and record['cost_s']==record['lower_s']
 assert edges[0][0]==c['sink'] and edges[-1][1]==len(caps) and len(edges)==record['edge_count']
 assert all(x[1]==y[0] for x,y in zip(edges,edges[1:]))
 assert not {x[0] for x in edges}&blocked
 assert abs(sum(x[2] for x in edges)-record['cost_s'])<1e-23
 assert abs(float(c['anchors'][str(edges[-1][0])])-edges[-1][2])<1e-23
 record.update(original_s=c['current_physical_seconds'],relaxed_gain_ns=rows[n,pin]['improvement_ns'],protected_gain_ns=(c['current_physical_seconds']-record['cost_s'])*1e9,edges=edges)
 results.append(record);bindings[str(case)]=sha(case);bindings[str(d/'stdout.log')]=sha(d/'stdout.log')
# Independent XML membership check of the returned paths, preserving model units.
wanted={(v,u,w) for r in results for u,v,w in r['edges'] if v!=len(caps)};seen=set();checked_caps=0
for section,e in graph_records(graph):
 if section=='rr_nodes':assert caps[int(e.attrib['id'])]==int(e.attrib['capacity']);checked_caps+=1
 elif section=='rr_edges':
  edge=(int(e.attrib['src_node']),int(e.attrib['sink_node']),switches[int(e.attrib['switch_id'])])
  if edge in wanted:seen.add(edge)
assert wanted==seen and checked_caps==len(caps)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,status='conditional_protected_prefix_reference',results=results,protected_pins=protected,complete_process_seconds=time.monotonic()-started,native_calls=0,
 source_sha256=bindings,qualification='Exact zero-RC source-to-sink distance for each fixed retained target tree with selected existing victim prefixes reserved; all other background nets relaxed and targets queried separately. No global FPGA/endpoint optimum, no joint feasibility or final STA assertion. If gain vanishes, improvement requires changing a protected prefix or another part of the target tree/scope.'))
print([(r['net'],r['pin'],r['relaxed_gain_ns'],r['protected_gain_ns']) for r in results],flush=True)
