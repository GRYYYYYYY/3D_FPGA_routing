#!/usr/bin/env python3
"""Verify native scope/witnesses and build actual isolated candidate routes."""
import argparse
import array
import collections
import math
from pathlib import Path
import re
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prune_sinks,attach,prefixes,serialize
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
p=argparse.ArgumentParser();p.add_argument('--native-state',type=Path,required=True);p.add_argument('--queries',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
start=time.monotonic();b=a.out.resolve();b.mkdir(exist_ok=False);state=a.native_state.resolve();q=a.queries.resolve()
assert read(state/'completion.json')['passed'];rd=Path(read(state/'completion.json')['run']);reg=read(state/'registration.json')
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
original=Path(read(q/'execution_registration.json')['input_run'])
assert all(sha(rd/n)==sha(original/n) for n in ['routed.route','packed.net','placed.place'])
cases={(c['net'],c['pin']):c for c in read(q/'cases.json')};rows=collections.defaultdict(lambda:dict(keep={},edges=[]))
lines=(rd/'native_queries.log').read_text().splitlines();assert lines[-1].endswith('occupancy_restored')
for line in lines[:-1]:
 v=line.split();key=tuple(map(int,v[1:4]));r=rows[key]
 if v[0]=='KEEP':r['keep'][int(v[4])]=dict(native_prefix_s=float(v[5]),re_expand=int(v[6]))
 elif v[0]=='RESULT':r.update(found=bool(int(v[4])),retry=bool(int(v[5])),criticality=float(v[6]),heap_pushes=int(v[7]),heap_pops=int(v[8]))
 elif v[0]=='EDGE':r['edges'].append((int(v[4]),int(v[5]),int(v[6]),float(v[7])))
 elif v[0]=='DELAY':r['native_sink_delay_s']=float(v[4])
 elif v[0]=='TIME':r['native_query_and_replacement_seconds']=float(v[4])
 else:raise AssertionError(v[0])
assert set(rows)=={(n,p,m) for n,p in cases for m in [0,1]}
m=read(original/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
traces=read_trace(original/'routed.route');owners=collections.defaultdict(set)
for net,t in traces.items():
 for node in {x.inode for x in t['trace']}:owners[node].add(net)
needed={n for c in cases.values() for n in c['original_nodes']}|{n for r in rows.values() for edge in r['edges'] for n in edge[:2]}
wanted={edge[:3] for r in rows.values() for edge in r['edges']};seen=set();switches={};metadata={};caps=array.array('I')
for section,e in graph_records(graph):
 at=e.attrib
 if section=='switches':
  t=e.find('timing');switches[int(at['id'])]=f32(t.attrib.get('Tdel',0)) if t is not None else 0.
 elif section=='rr_nodes':
  node=int(at['id']);assert node==len(caps);caps.append(int(at['capacity']))
  if node in needed:
   v=e.find('loc').attrib;z=int(v.get('layer_low',v.get('layer',0)))
   metadata[node]=dict(kind=at['type'],low=(int(v['xlow']),int(v['ylow']),z),high=(int(v['xhigh']),int(v['yhigh']),int(v.get('layer_high',z))),ptc=int(v['ptc']))
 else:
  edge=int(at['src_node']),int(at['sink_node']),int(at['switch_id'])
  if edge in wanted:seen.add(edge)
assert seen==wanted
out=[];text=(original/'routed.route').read_text()
for key,r in sorted(rows.items()):
 net,pin,mode=key;c=cases[net,pin];old=from_trace(traces[net]['trace'],switches);kept=prune_sinks(old,[pin]);r.update(net=net,pin=pin,mode=mode)
 r['same_retained_nodes']=set(r['keep'])==set(c['retained'])==nodes(kept)
 native_anchors={node for node,k in r['keep'].items() if k['re_expand']}
 r['same_eligible_anchors']=native_anchors==set(map(int,c['anchors']))
 assert r['same_retained_nodes'] and r['same_eligible_anchors'],'Fairness mismatch must be diagnosed before comparing quality'
 r['candidate_route']=None
 if not r['found']:
  r['status']='native_no_path';out.append(r);continue
 edges=list(reversed(r['edges']));assert all(e[3]==switches[e[2]] for e in edges)
 assert all(x[1]==y[0] for x,y in zip(edges,edges[1:]))
 forward=[edges[0][0]]+[e[1] for e in edges]
 tree=attach(kept,pin,c['sink'],forward,[e[2] for e in edges],[e[3] for e in edges])
 assert tree['sinks']==old['sinks']
 delay=prefixes(tree)[c['sink']];r.update(physical_seconds=delay,improvement_ns=(c['current_physical_seconds']-delay)*1e9)
 r['conflicts']={str(n):dict(capacity=caps[n],other_nets=sorted(owners[n]-{net})) for n in nodes(tree) if len(owners[n]-{net})+1>caps[n]}
 if r['conflicts']:r['status']='capacity_rejected'
 elif tree==old:r['status']='unchanged_tree_skipped'
 else:
  match=re.search(r'^Net '+str(net)+r' \(.*?\)\n.*?(?=^Net |\Z)',text,re.M|re.S);assert match
  replacement=match.group(0).splitlines()[0]+'\n\n'+serialize(tree,metadata)+'\n'
  dest=b/f'native_net{net}_pin{pin}_mode{mode}.route';dest.write_text(text[:match.start()]+replacement+text[match.end():])
  parsed=read_trace(dest);assert all(parsed[n]==traces[n] for n in traces if n!=net)
  assert from_trace(parsed[net]['trace'],switches)==tree
  r.update(status='candidate_pending_FULL_STA',candidate_route=str(dest),candidate_sha256=sha(dest))
 # Keep compact per-query state; detailed original native witness is immutable.
 r.pop('keep');out.append(r)
files=[Path(__file__),D/'coordinated_repair_tree.py',state/'completion.json',state/'registration.json',rd/'native_queries.log',q/'cases.json',q/'selection.json',original/'routed.route',graph]
write(b/'analysis.json',dict(passed=True,input_run=str(original),rows=out,native_query_count=len(rows),
 complete_audit_seconds=time.monotonic()-start,source_sha256={str(p):sha(p) for p in files},
 qualification='Actual native connection router and tree update, exactly matching retained nodes/anchors and full-device scope. Hard-capacity and native weighted/delay costs differ. Capacity reject is not native FULL pass. Changed legal candidates still require FULL/STA and identical acceptance opportunities.'))
print([{k:r.get(k) for k in ['net','pin','mode','status','improvement_ns','candidate_route']} for r in out],flush=True)
