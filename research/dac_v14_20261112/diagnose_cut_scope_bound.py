#!/usr/bin/env python3
"""Bound the protected connection with a scope-conditional required entry kept free."""
import array,collections,mmap,struct,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prefixes,prune_sinks,attach
from run_native_frontier_queries import write_cases
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

started=time.monotonic();b=D/'joint_native_cut_scope_bound_01';b.mkdir(exist_ok=False)
order=D/'joint_native_cut_order_dev_01';cut=read(order/'cut_evidence.json');reg=read(order/'registration.json')['roles']['Tf_cut_order']
source=Path(reg['source']);manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
binary=D/'residual_query_offline_01/graph.bin';binding=read(binary.with_name('graph_binding.json'))
assert sha(graph)==binding['source_rrg_sha256'] and sha(binary)==binding['binary_graph_sha256']
switches={}
for section,e in graph_records(graph):
 if section!='switches':break
 t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
caps=array.array('I');caps.frombytes((D/'current_sta_Tf_relaxed_02/capacities.bin').read_bytes())
traces=read_trace(source/'routed.route');original={int(n):from_trace(traces[int(n)]['trace'],switches) for n in reg['removed_pins']}
partial={n:prune_sinks(t,reg['removed_pins'][str(n)]) for n,t in original.items()}
tx=Path(reg['transaction']);first=read(tx/'initial_transaction.json');final=read(tx/'final_transaction_trees.json')
for n,p in reg['targets']:
 path=first['target_reserved_nodes'][str(n)];sw=[final[str(n)]['edges'][str(v)][1] for v in path[1:]]
 partial[n]=attach(partial[n],p,original[n]['sinks'][p],path,sw,[switches[s] for s in sw])
owners=collections.defaultdict(set)
for n,t in traces.items():
 for node in nodes(partial[n]) if n in partial else {r.inode for r in t['trace']}:owners[node].add(n)
assert all(len(ns)<=caps[node] for node,ns in owners.items())
failed=cut['target']['net'];frontier=[r['node'] for r in cut['cut']]
free=[node for node in frontier if len(owners[node]-{failed})<caps[node]]
assert len(free)==1;gate=free[0]
assert all(owners[node] and not owners[node]&set(partial) for node in frontier if node!=gate)
victim=tuple(cut['precedence'][1]);net,pin=victim
assert net!=failed and caps[gate]==1 and not owners[gate]
tree=partial[net];retained=nodes(tree);pref=prefixes(tree);kinds={r.inode:r.kind for r in traces[net]['trace']}
anchors={str(n):pref[n] for n in retained if kinds[n] not in ['IPIN','SINK']}
blocked={n for n,c in enumerate(caps) if len(owners[n]-{net})>=c}
assert not blocked&retained and gate not in retained
driver=D/'current_sta_queries_01/critical_capacity_driver';assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
files=[Path(__file__),order/'registration.json',order/'cut_evidence.json',source/'routed.route',graph,binary,driver]
write(b/'registration.json',dict(status='registered_before_queries',victim=victim,failed_connection=cut['target'],required_gate=gate,
 question='With all other released connections still absent, can the protected connection avoid delay loss while leaving the only access allowed by the unchanged background for the failed sink?',
 scope_certificate='Thirteen other positive-capacity entry nodes are occupied by nets outside the released scope. The remaining capacity-one entry is required by the failed sink for every complete route in this scope.',
 limits=dict(query_seconds=120,memory_bytes=24*1024**3),source_sha256={str(p):sha(p) for p in files}))
results=[]
for name,extra in [('before_restoration',set()),('leave_required_entry',{gate})]:
 q=b/name;q.mkdir();case=dict(net=net,pin=pin,sink=original[net]['sinks'][pin],retained=sorted(retained),anchors=anchors,blocked=sorted(blocked|extra))
 write(q/'case.json',case);write_cases(q/'cases.txt',[case]);t=time.monotonic()
 with (q/'stdout.log').open('w') as out,(q/'stderr.log').open('w') as err:r=subprocess.run(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(q/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=120)
 seconds=time.monotonic()-t;assert r.returncode==0
 lines=(q/'stdout.log').read_text().splitlines();v=lines[0].split();assert int(v[4])==0 and float(v[8])==float(v[9]);cost=float(v[8])
 edges=[(int(v[5]),int(v[6]),float(v[7])) for v in [s.split() for s in lines[1:]]]
 assert edges[0][0]==case['sink'] and edges[-1][1]==len(caps) and all(x[1]==y[0] for x,y in zip(edges,edges[1:]))
 assert edges[-1][0] in retained and edges[-1][2]==anchors[str(edges[-1][0])]
 assert not {u for u,v,w in edges[:-1]}&retained and not {u for u,v,w in edges}&set(case['blocked'])
 assert abs(sum(w for u,v,w in edges)-cost)<1e-23
 wanted={(v,u,w) for u,v,w in edges[:-1]};seen=set()
 with binary.open('rb') as f:
  data=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);n=struct.unpack_from('<I',data,8)[0];m=struct.unpack_from('<Q',data,12)[0];offset=36+20*n
  for i in range(m):
   edge=struct.unpack_from('<IId',data,offset+16*i)
   if edge in wanted:seen.add(edge)
  data.close()
 assert seen==wanted
 result=dict(mode=name,minimum_seconds=cost,original_seconds=prefixes(original[net])[case['sink']],gate_used=gate in {u for u,v,w in edges},process_seconds=seconds,expansions=int(v[5]))
 results.append(result);write(q/'result.json',result)
write(b/'completion.json',dict(passed=True,results=results,required_gate=gate,complete_seconds=time.monotonic()-started,
 qualification='Exact zero-RC physical-connection bounds with all other released connections absent. Gate is necessary only under this fixed released scope/background, not a unique static entry. Not a global CPD/STA bound.',
 source_sha256={str(p):sha(p) for p in [b/'registration.json',*b.glob('*/result.json'),*b.glob('*/stdout.log')]}))
print(dict(results=results,required_gate=gate),flush=True)
