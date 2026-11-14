#!/usr/bin/env python3
"""Verify diagnostic neutrality and query the exact failed native partial state."""
import array,collections,json,mmap,struct,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import nodes,prefixes
from run_native_frontier_queries import write_cases
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
b=D/'joint_native_failure_state_01';state=b/'diagnostic';assert read(state/'completion.json')['passed'];rd=Path(read(state/'completion.json')['run'])
q=b/'exact_query';q.mkdir(exist_ok=False);started=time.monotonic()
lines=(rd/'joint_native.log').read_text().splitlines();assert lines[-1].startswith('COMPLETE 0 4 16 ') and lines[-1].endswith('occupancy_restored')
old=D/'joint_native_feedback_dev_01';old_audit=read(old/'Tf_feedback_scope_audit/analysis.json');queries=[];attempts=[];raw=collections.defaultdict(list);occ={};rejected=[];target=None
for line in lines:
 v=line.split()
 if v[0]=='QUERY':queries.append(dict(net=int(v[1]),pin=int(v[2]),feasible=bool(int(v[3])),criticality=float(v[4]),pushes=int(v[5]),pops=int(v[6])))
 elif v[0]=='ATTEMPT':attempts.append(dict(net=int(v[1]),pin=int(v[2]),pressure=float(v[3]),found=bool(int(v[4])),feasible=bool(int(v[5]))))
 elif v[0]=='NODE':raw[int(v[1])].append(dict(node=int(v[2]),parent=int(v[3]),switch=int(v[4]),pin=int(v[5]),native_delay=float(v[6]),expand=bool(int(v[7]))))
 elif v[0]=='OCC':occ[int(v[1])]=int(v[2])
 elif v[0]=='FAIL_TARGET':target=dict(net=int(v[1]),pin=int(v[2]),sink=int(v[3]),pressure=float(v[4]))
 elif v[0]=='FAIL_EDGE':rejected.append(dict(parent=int(v[1]),node=int(v[2]),switch=int(v[3]),occ=int(v[4]),capacity=int(v[5]),base_cost=float(v[6]),acc_cost=float(v[7]),congestion_cost=float(v[8])))
assert queries==[{k:v for k,v in r.items() if k!='seconds'} for r in old_audit['queries']]
assert attempts==old_audit['attempts'] and target['net']==queries[-1]['net'] and target['pin']==queries[-1]['pin']
source=Path(read(b/'registration.json')['source']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);binary=D/'residual_query_offline_01/graph.bin';bind=read(binary.with_name('graph_binding.json'))
assert sha(graph)==bind['source_rrg_sha256'] and sha(binary)==bind['binary_graph_sha256']
switches={}
for section,e in graph_records(graph):
 if section!='switches':break
 t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
trees={};float_checks=0
for net,rows in raw.items():
 roots=[r['node'] for r in rows if r['parent']<0];assert len(roots)==1
 tree=dict(root=roots[0],edges={r['node']:(r['parent'],r['switch'],switches[r['switch']]) for r in rows if r['parent']>=0},sinks={r['pin']:r['node'] for r in rows if r['pin']>0})
 pref=prefixes(tree);native={r['node']:r['native_delay'] for r in rows}
 assert native[tree['root']]==0.
 for node,(parent,sw,w) in tree['edges'].items():assert native[node]==f32(native[parent]+w);float_checks+=1
 trees[net]=tree
caps=array.array('I');caps.frombytes((D/'current_sta_Tf_relaxed_02/capacities.bin').read_bytes());assert len(caps)==bind['nodes']
assert all(value<=caps[node] for node,value in occ.items())
traces=read_trace(source/'routed.route');recount=collections.Counter()
for net,t in traces.items():recount.update(nodes(trees[net]) if net in trees else {r.inode for r in t['trace']})
assert all(occ.get(node,0)>=count for node,count in recount.items())
extra_native_reservations={str(node):count-recount.get(node,0) for node,count in occ.items() if count>recount.get(node,0)}
net,pin=target['net'],target['pin'];tree=trees[net];pref=prefixes(tree);retained=nodes(tree)
anchors={str(r['node']):pref[r['node']] for r in raw[net] if r['expand']}
assert target['sink'] not in retained
blocked={node for node,capacity in enumerate(caps) if occ.get(node,0)-int(node in retained)>=capacity}
assert not retained&blocked
case=dict(net=net,pin=pin,sink=target['sink'],retained=sorted(retained),anchors=anchors,blocked=sorted(blocked))
write(q/'case.json',case);write_cases(q/'cases.txt',[case]);write(q/'partial_trees.json',{str(n):t for n,t in trees.items()})
write(q/'native_state_validation.json',dict(passed=True,identical_attempts_and_query_counts=True,float_prefix_checks=float_checks,retained_nodes=len(retained),native_anchors=len(anchors),extra_native_reservations=extra_native_reservations,
 rejected_path=rejected,conflicting_nodes=[r for r in rejected if r['occ']+1>r['capacity']],target=target))
driver=D/'current_sta_queries_01/critical_capacity_driver';assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
files=[Path(__file__),b/'registration.json',state/'completion.json',rd/'joint_native.log',old/'Tf_feedback_scope_audit/analysis.json',source/'routed.route',graph,binary,driver,q/'case.json']
write(q/'registration.json',dict(status='registered_before_queries',modes=[0,1],question='Capacity feasibility and relaxed physical opportunity on the exact exported native partial state, including native reservations.',source_sha256={str(p):sha(p) for p in files},limits=dict(query_seconds=120,memory_bytes=24*1024**3)))
t=time.monotonic()
with (q/'stdout.log').open('w') as out,(q/'stderr.log').open('w') as err:r=subprocess.run(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(q/'cases.txt')],stdout=out,stderr=err,timeout=120)
seconds=time.monotonic()-t;assert r.returncode==0
results={};edges=collections.defaultdict(list)
for line in (q/'stdout.log').read_text().splitlines():
 v=line.split();mode=int(v[3]);assert (int(v[1]),int(v[2]))==(net,pin)
 if v[0]=='RESULT':results[mode]=dict(mode=mode,stop=int(v[4]),expansions=int(v[5]),labels=int(v[6]),cost=float(v[8]),lower=float(v[9]),core_seconds=float(v[10]),edge_count=int(v[11]))
 else:edges[mode].append((int(v[5]),int(v[6]),float(v[7])))
wanted={(parent,node,w) for paths in edges.values() for node,parent,w in paths if parent!=len(caps)}
# Also validate every exported partial-tree edge against the XML-bound binary.
wanted.update((u,v,w) for tree in trees.values() for v,(u,sw,w) in tree['edges'].items());seen=set()
with binary.open('rb') as f:
 data=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);n=struct.unpack_from('<I',data,8)[0];m=struct.unpack_from('<Q',data,12)[0];offset=36+20*n
 for i in range(m):
  edge=struct.unpack_from('<IId',data,offset+16*i)
  if edge in wanted:seen.add(edge)
 data.close()
assert seen==wanted
for mode,row in results.items():
 assert row['stop'] in [0,2],'Resource truncation is unknown, not infeasibility'
 path=edges[mode];assert len(path)==row['edge_count']
 if row['stop']==0:
  assert row['cost']==row['lower'] and path[0][0]==case['sink'] and path[-1][1]==len(caps)
  assert all(x[1]==y[0] for x,y in zip(path,path[1:]));assert path[-1][0] in retained and path[-1][2]==anchors[str(path[-1][0])]
  assert not {u for u,v,w in path[:-1]}&retained
  if mode:assert not {u for u,v,w in path}&blocked
  assert abs(sum(w for u,v,w in path)-row['cost'])<1e-23
 else:assert not path
write(q/'completion.json',dict(status='exact_failure_state_query_terminal',passed=True,results=list(results.values()),query_process_seconds=seconds,complete_seconds=time.monotonic()-started,
 qualification='Exact zeroRC fixed-partial-tree graph only; identical native retained anchors and occupancy including reserved resources. Relaxed mode removes capacity filtering. No complete candidate or global STA claim.',source_sha256={str(p):sha(p) for p in [q/'registration.json',q/'native_state_validation.json',q/'stdout.log',q/'partial_trees.json']}))
print(dict(results=results,conflicting_nodes=[r for r in rejected if r['occ']+1>r['capacity']],extra_native_reservations=len(extra_native_reservations)),flush=True)
