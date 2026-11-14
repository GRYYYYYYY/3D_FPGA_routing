#!/usr/bin/env python3
"""Derive a restoration precedence from a failed sink's occupied access cut.

This changes only order, never scope, target paths, costs or acceptance. It is
a diagnostic scheduling intervention, not a proof that an ordering will work.
"""
import argparse,array,collections,copy,mmap,struct,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

p=argparse.ArgumentParser()
p.add_argument('--registration',type=Path,required=True)
p.add_argument('--role',required=True)
p.add_argument('--diagnostic',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();started=time.monotonic()
reg=read(a.registration);r=copy.deepcopy(reg['roles'][a.role]);b=a.output.resolve();b.mkdir(exist_ok=False)
rd=Path(read(a.diagnostic/'completion.json')['run']);log=rd/'joint_native.log'
lines=log.read_text().splitlines();assert lines[-1].startswith('COMPLETE 0 ') and lines[-1].endswith('occupancy_restored')
kept=collections.defaultdict(set);partial=collections.defaultdict(set);occ={};successful=[];target=None
for line in lines:
 v=line.split()
 if v[0]=='KEEP':kept[int(v[1])].add(int(v[2]))
 elif v[0]=='NODE':partial[int(v[1])].add(int(v[2]))
 elif v[0]=='OCC':occ[int(v[1])]=int(v[2])
 elif v[0]=='QUERY' and v[3]=='1':successful.append((int(v[1]),int(v[2])))
 elif v[0]=='FAIL_TARGET':target=dict(net=int(v[1]),pin=int(v[2]),sink=int(v[3]))
assert target and occ and partial
caps_path=D/'current_sta_Tf_relaxed_02/capacities.bin'
caps=array.array('I');caps.frombytes(caps_path.read_bytes())
binary=D/'residual_query_offline_01/graph.bin'
assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
# Restrict only to positive-capacity topology; every traversable sink path has
# to pass the discovered frontier. Stop at the first fully occupied cut.
chain=[target['sink']];frontier=None;pred_history={}
with binary.open('rb') as f:
 data=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
 n=struct.unpack_from('<I',data,8)[0];m=struct.unpack_from('<Q',data,12)[0];offset=36+20*n
 assert n==len(caps)
 while True:
  at=chain[-1];pred=set()
  for i in range(m):
   u,v,w=struct.unpack_from('<IId',data,offset+16*i)
   if v==at and caps[u]>0:pred.add(u)
  pred_history[str(at)]=sorted(pred)
  assert pred,'No positive-capacity predecessor; distinguish architecture disconnection'
  if all(occ.get(u,0)-int(u in partial[target['net']])>=caps[u] for u in pred):frontier=pred;break
  assert len(pred)==1,'Not an immediate access cut; requires general cut analysis'
  nxt=next(iter(pred));assert nxt not in chain and nxt not in partial[target['net']];chain.append(nxt)
 data.close()
source=Path(r['source']);traces=read_trace(source/'routed.route');current_owners=collections.defaultdict(set);original_owners=collections.defaultdict(set)
for net,t in traces.items():
 owned={x.inode for x in t['trace']}
 for node in owned&frontier:original_owners[node].add(net)
 for node in partial.get(net,owned)&frontier:current_owners[node].add(net)
assert all(len(current_owners[u])==occ.get(u,0) for u in frontier)
rows=[];blocking_queries=[]
for node in sorted(frontier):
 newowners=[net for net in current_owners[node] if net in partial and node not in kept[net]]
 rows.append(dict(node=node,capacity=caps[node],occupancy=occ.get(node,0),original_owners=sorted(original_owners[node]),current_owners=sorted(current_owners[node]),new_partial_owners=sorted(newowners)))
 for query in successful:
  if query[0] in newowners:blocking_queries.append(query)
assert blocking_queries,'Current cut has no previously restored owner to reorder; scope/path change needed'
old=[(q['net'],q['pin']) for q in r['queries']];failed=(target['net'],target['pin'])
before=min(blocking_queries,key=old.index);new=list(old);new.remove(failed);new.insert(new.index(before),failed)
assert new!=old and set(new)==set(old)
history=reg.get('order_history',[old]);assert new not in [list(map(tuple,x)) for x in history],'Repeated ordering; needs backtracking/path alternatives, not retry'
history.append(new)
request=b/'Tf_cut_order.txt';old_request=Path(r['request']);text=old_request.read_text().splitlines();prefix=text[:len(text)-len(old)]
querymap={(q['net'],q['pin']):q for q in r['queries']}
request.write_text('\n'.join(prefix+[f"{n} {p} {querymap[n,p]['raw_criticality']:.17g}" for n,p in new])+'\n')
assert int(prefix[-1])==len(new)
r.update(request=str(request),order='failed_sink_before_new_owner_of_occupied_access_cut',queries=[querymap[k] for k in new])
files=[Path(__file__),a.registration,a.diagnostic/'completion.json',log,request,binary,caps_path,source/'routed.route']
r['source_sha256'].update({str(p.resolve()):sha(p) for p in files})
write(b/'registration.json',dict(status='registered_before_native',roles={'Tf_cut_order':r},
 hypothesis='A prior restoration occupies all remaining sink-entry alternatives; moving the failed connection before that owner may restore feasibility without widening scope.',
 qualification='Scheduling counterfactual on the same diagnostic state/scope. Not autonomous initial selection or a static mandatory-gate claim. FULL/STA and independent policy decisions remain required.',
 order_history=history,source_sha256={str(p.resolve()):sha(p) for p in files}))
write(b/'cut_evidence.json',dict(passed=True,target=target,chain_to_cut=chain,positive_capacity_predecessors=pred_history,cut=rows,precedence=[failed,before],old_order=old,new_order=new,
 preparation_seconds=time.monotonic()-started,scope_unchanged=True,fixed_target_paths_unchanged=True,
 qualification='All sink paths in the positive-capacity graph cross this currently fully occupied cut. It is not globally infeasible: unchanged background, pruning and earlier restorations define this state.'))
print(dict(target=target,frontier=rows,precedence=[failed,before],output=str(b)),flush=True)
