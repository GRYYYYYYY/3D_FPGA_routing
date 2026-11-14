#!/usr/bin/env python3
"""Verify a static unique-predecessor access chain and its current owner."""
import mmap,struct
from retained_prefix_workflow import D,read,write,sha
q=D/'joint_native_failure_state_01/exact_query';state=read(q/'native_state_validation.json');conflicts=state['conflicting_nodes'];assert len(conflicts)==1;gate=conflicts[0]['node'];sink=state['target']['sink']
by_node={r['node']:r['parent'] for r in state['rejected_path']};chain=[sink]
while chain[-1]!=gate:chain.append(by_node[chain[-1]])
assert len(chain)==len(set(chain));wanted=set(chain[:-1]);pred={n:set() for n in wanted}
binary=D/'residual_query_offline_01/graph.bin';assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
with binary.open('rb') as f:
 data=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);n=struct.unpack_from('<I',data,8)[0];m=struct.unpack_from('<Q',data,12)[0];offset=36+20*n
 for i in range(m):
  u,v,w=struct.unpack_from('<IId',data,offset+16*i)
  if v in pred:pred[v].add(u)
 data.close()
unique=all(pred[node]=={parent} for node,parent in zip(chain,chain[1:]))
trees=read(q/'partial_trees.json');owners=[int(net) for net,t in trees.items() if gate==t['root'] or str(gate) in t['edges']]
write(q/'static_entry_certificate.json',dict(passed=unique,sink=sink,gate=gate,reverse_chain=chain,all_graph_predecessors={str(k):sorted(v) for k,v in pred.items()},current_partial_owners=owners,
 conclusion=('Every directed RR path to this sink must pass the gate: unique-predecessor chain.' if unique else 'Unique-entry hypothesis rejected; multiple predecessors exist. No static mandatory-gate claim.'),
 qualification='Static access certificate for this RR sink. Does not prove a whole routing/STA optimum.',source_sha256={str(p):sha(p) for p in [__file__,q/'native_state_validation.json',q/'partial_trees.json',binary]}))
print(dict(unique_entry=unique,chain=chain,owners=owners))
