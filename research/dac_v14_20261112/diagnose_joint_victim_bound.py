#!/usr/bin/env python3
"""Exact zero-RC victim opportunity before any blocker restoration occurs."""
import array,collections,json,mmap,struct,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prefixes,prune_sinks,attach
from run_native_frontier_queries import write_cases
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
b=D/'joint_victim_bound_01';b.mkdir(exist_ok=False);start=time.monotonic()
tx=D/'current_sta_Tf_transaction_02';r=read(tx/'analysis.json');first=read(tx/'initial_transaction.json');final=read(tx/'final_transaction_trees.json');source=Path(r['input_run'])
# Select the constrained output connection whose measured delay increase matches
# the sole regressed endpoint; identity is derived from exported atom pin name.
state=D/'current_sta_policy_Tf_01/evaluation_002';losses=[x for x in read(D/'current_sta_Tf_joint_evaluation_02/policy_decision.json')['strict']['comparison']['changes'] if x['kind']=='setup' and x['delta_s']<0]
assert len(losses)==1;endpoint=json.loads(losses[0]['endpoint_domain']);matches=[]
for line in (Path(read(state/'completion.json')['run'])/'native_sta_frontier.jsonl').open():
 x=json.loads(line)
 if x['type']=='pin' and not x['driver'] and any(atom['id']==endpoint[1] for atom in x['atoms']):matches.append(x)
assert len(matches)==1;target=matches[0];net,pin=target['net'],target['pin']
manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);binary=D/'residual_query_offline_01/graph.bin';binding=read(binary.with_name('graph_binding.json'))
assert sha(graph)==binding['source_rrg_sha256'] and sha(binary)==binding['binary_graph_sha256']
switches={}
for section,e in graph_records(graph):
 if section!='switches':break
 t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
caps=array.array('I');caps.frombytes((D/'current_sta_Tf_relaxed_02/capacities.bin').read_bytes())
traces=read_trace(source/'routed.route');owners=collections.defaultdict(set)
for n,t in traces.items():
 for node in {x.inode for x in t['trace']}:owners[node].add(n)
removed={int(n):[int(p) for p,sink in pairs] for n,pairs in first['pending'].items()}
for t in r['targets']:removed.setdefault(t['net'],[]).append(t['pin'])
original={n:from_trace(traces[n]['trace'],switches) for n in removed};partial={n:prune_sinks(original[n],pins) for n,pins in removed.items()}
for t in r['targets']:
 n,p=t['net'],t['pin'];path=first['target_reserved_nodes'][str(n)];edges=final[str(n)]['edges'];sw=[edges[str(v)][1] for v in path[1:]]
 partial[n]=attach(partial[n],p,original[n]['sinks'][p],path,sw,[switches[s] for s in sw])
for n,tree in partial.items():
 for node in nodes(original[n])-nodes(tree):owners[node].remove(n)
 for node in nodes(tree)-nodes(original[n]):owners[node].add(n)
assert all(len(o)<=caps[n] for n,o in owners.items())
retained=nodes(partial[net]);prefix=prefixes(partial[net]);kinds={x.inode:x.kind for x in traces[net]['trace']}
anchors={str(n):prefix[n] for n in sorted(retained) if kinds[n] not in ['IPIN','SINK']}
zero={n for n,c in enumerate(caps) if not c}
full_blocked=zero|{n for n,o in owners.items() if len(o)-int(net in o)>=caps[n]}
preset_owners=collections.defaultdict(set)
for t in r['targets']:
 for node in nodes(partial[t['net']]):preset_owners[node].add(t['net'])
preset_blocked=zero|{n for n,o in preset_owners.items() if len(o)>=caps[n]}
driver=D/'current_sta_queries_01/critical_capacity_driver';assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
files=[Path(__file__),tx/'analysis.json',tx/'initial_transaction.json',tx/'final_transaction_trees.json',D/'current_sta_Tf_joint_evaluation_02/policy_decision.json',binary,graph,driver]
write(b/'registration.json',dict(status='registered_before_queries',selected_net=net,selected_pin=pin,endpoint=endpoint,
 question='Is the output-victim delay regression avoidable by changing blocker restoration order under the fixed target path?',
 domains=['All other blocker pins remain pruned; unchanged background and fixed targets retained.','Optimistic further relaxation: retain only fixed target trees as other-net occupancy.'],
 limits=dict(query_seconds=120,memory_bytes=24*1024**3),source_sha256={str(p):sha(p) for p in files}))
results=[]
for name,blocked in [('before_any_blocker',full_blocked),('only_fixed_targets',preset_blocked)]:
 q=b/name;q.mkdir();case=dict(net=net,pin=pin,sink=original[net]['sinks'][pin],retained=sorted(retained),anchors=anchors,blocked=sorted(blocked))
 write(q/'case.json',case);write_cases(q/'cases.txt',[case]);assert not retained&blocked
 t=time.monotonic()
 with (q/'stdout.log').open('w') as out,(q/'stderr.log').open('w') as err:p=subprocess.run(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(q/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=120)
 elapsed=time.monotonic()-t;assert p.returncode==0
 lines=(q/'stdout.log').read_text().splitlines();v=lines[0].split();assert int(v[4])==0 and float(v[8])==float(v[9]);cost=float(v[8])
 edges=[(int(v[5]),int(v[6]),float(v[7])) for v in [s.split() for s in lines[1:]]]
 assert edges[0][0]==case['sink'] and edges[-1][1]==len(caps);assert all(x[1]==y[0] for x,y in zip(edges,edges[1:]))
 assert edges[-1][0] in retained and edges[-1][2]==anchors[str(edges[-1][0])]
 assert not {u for u,v,w in edges[:-1]}&retained and not {u for u,v,w in edges}&blocked
 assert abs(sum(e[2] for e in edges)-cost)<1e-23
 # Independent witness lookup in the previously XML-bound binary graph.
 wanted={(v,u,w) for u,v,w in edges[:-1]};seen=set()
 with binary.open('rb') as stream:
  data=mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ)
  n=struct.unpack_from('<I',data,8)[0];m=struct.unpack_from('<Q',data,12)[0];offset=36+20*n
  assert n==len(caps) and len(data)==offset+16*m
  for i in range(m):
   edge=struct.unpack_from('<IId',data,offset+16*i)
   if edge in wanted:seen.add(edge)
  data.close()
 assert seen==wanted
 row=dict(domain=name,minimum_seconds=cost,original_seconds=prefixes(original[net])[case['sink']],excess_ns=(cost-prefixes(original[net])[case['sink']])*1e9,
          process_seconds=elapsed,exact_stop=True,witness_edges_verified=len(wanted),case_sha256=sha(q/'cases.txt'))
 results.append(row);write(q/'result.json',row)
write(b/'completion.json',dict(status='exact_local_bound_terminal',passed=True,results=results,complete_seconds=time.monotonic()-start,
 qualification='Exact minimum only for this zeroRC fixed-retained-tree graph. The target-only relaxation is an optimistic physical-connection bound, not a global STA bound or feasible full routing.',source_sha256={str(p):sha(p) for p in [b/'registration.json',*b.glob('*/result.json')]}));print(results)
