#!/usr/bin/env python3
"""Prove identical complete physical trees before reusing a prior FULL/STA.

This is not a route-quality approximation. Any tree mismatch prevents reuse.
"""
import argparse,collections,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,prune_sinks,nodes
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--role',required=True);a=p.parse_args();started=time.monotonic()
b=a.batch.resolve();r=read(b/'registration.json')['roles'][a.role];source=Path(r['source']);reference=Path(r['capacity_reference'])
refdone=read(reference/'completion.json');assert refdone['passed'];ref=Path(refdone['run'])
native=read(b/a.role/'completion.json');assert native['passed'];run=Path(native['run']);lines=(run/'joint_native.log').read_text().splitlines()
assert lines[-1].split()[0]=='COMPLETE' and lines[-1].endswith('occupancy_restored')
out=b/(a.role+'_reference_equivalence.json')
if lines[-1].split()[1]!='1':
 write(out,dict(passed=True,identical=False,reason='Native transaction incomplete'));sys.exit(0)
source_manifest=read(source/'manifest.json');ref_manifest=read(ref/'manifest.json')
graph=Path(source_manifest['command'][source_manifest['command'].index('--read_rr_graph')+1]);refgraph=Path(ref_manifest['command'][ref_manifest['command'].index('--read_rr_graph')+1])
assert sha(graph)==sha(refgraph)==source_manifest['shared_inputs'][str(graph)]['sha256']
assert all(sha(source/n)==sha(ref/n)==sha(run/n) for n in ['packed.net','placed.place'])
assert sha(source/'routed.route')==sha(run/'routed.route')
assert read(Path(r['state'])/'endpoint_vector.json')['constraints_sha256']==read(reference/'endpoint_vector.json')['constraints_sha256']
assert read(ref/'analysis_gate.json')['passed'] and read(ref/'independent_audit.json')['audit']['passed']
switches={}
for section,e in graph_records(graph):
 if section!='switches':break
 t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
raw=collections.defaultdict(list);kept=collections.defaultdict(set);queries=[];attempts=[]
for line in lines:
 v=line.split()
 if v[0]=='NODE':raw[int(v[1])].append((int(v[2]),int(v[3]),int(v[4]),int(v[5]),float(v[6])))
 elif v[0]=='KEEP':kept[int(v[1])].add(int(v[2]))
 elif v[0]=='QUERY':queries.append(dict(net=int(v[1]),pin=int(v[2]),feasible=bool(int(v[3])),seconds=float(v[7])))
 elif v[0]=='ATTEMPT':attempts.append(dict(net=int(v[1]),pin=int(v[2]),pressure=float(v[3]),found=bool(int(v[4])),feasible=bool(int(v[5]))))
assert set(raw)==set(map(int,r['removed_pins'])) and all(q['feasible'] for q in queries)
before=read_trace(source/'routed.route');after=read_trace(ref/'routed.route');assert before.keys()==after.keys()
assert all(before[n]==after[n] for n in before if n not in raw),'Reference changes extra nets; cannot reuse'
checks=[]
for net,rows in raw.items():
 original=from_trace(before[net]['trace'],switches);pruned=prune_sinks(original,r['removed_pins'][str(net)])
 roots=[node for node,parent,sw,pin,d in rows if parent<0];assert roots==[original['root']]
 tree=dict(root=roots[0],edges={v:(u,sw,switches[sw]) for v,u,sw,p,d in rows if u>=0},sinks={p:v for v,u,sw,p,d in rows if p>0})
 assert kept[net]==nodes(pruned) and tree['sinks']==original['sinks']
 assert all(tree['edges'].get(v)==edge for v,edge in pruned['edges'].items())
 native_delay={v:d for v,u,sw,p,d in rows};assert native_delay[tree['root']]==0.
 assert all(native_delay[v]==f32(native_delay[u]+w) for v,(u,sw,w) in tree['edges'].items())
 ref_tree=from_trace(after[net]['trace'],switches)
 checks.append(dict(net=net,exact_tree_same=tree==ref_tree,retained_scope_matches=True,native_float_delay_recurrence=True))
identical=all(x['exact_tree_same'] for x in checks)
files=[Path(__file__),b/'registration.json',b/a.role/'completion.json',run/'joint_native.log',source/'routed.route',ref/'routed.route',ref/'packed.net',ref/'placed.place',reference/'completion.json',reference/'endpoint_vector.json',ref/'analysis_gate.json',ref/'independent_audit.json',graph]
write(out,dict(passed=True,identical=identical,checks=checks,queries=queries,attempts=attempts,native_transaction_seconds=float(lines[-1].split()[4]),
 complete_comparison_seconds=time.monotonic()-started,reused_state=str(reference) if identical else None,
 qualification='All replaced physical trees including parent/edge switch/terminal identity exactly equal the already FULL/STA-certified reference; all other nets and packed/place/graph/constraints equal. Reuse is explicit, not a new candidate STA execution or a zero-cost formal algorithm claim.',
 source_sha256={str(p):sha(p) for p in files}))
print(dict(identical=identical,checks=checks),flush=True)
