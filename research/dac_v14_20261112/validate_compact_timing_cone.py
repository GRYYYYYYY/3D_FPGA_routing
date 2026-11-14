#!/usr/bin/env python3
"""Differential selection checks: timing-domain fixtures and actual native states."""
import math,resource,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_timing_echo_v2 import read_echo
from current_sta_arrival_cone import trace,f32
from compact_timing_cone import read_compact,trace_compact
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
b=D/'compact_timing_cone_validation_01';b.mkdir(exist_ok=False);checks=[]
def fixture(name,disable=False,ulp=False,unknown=False,bad=False):
 edges=[(0,1),(0,2),(1,3),(2,3),(3,4)];delays=[1.,1.+(2**-22 if ulp else 0.),1.,1.,1.]
 s=['timing_graph:']
 for n,kind in enumerate(['SOURCE','IPIN','IPIN','OPIN','SINK']):
  s += [f' node: {n}',f'  type: {kind}','  in_edges: '+' '.join(str(i) for i,(u,v) in enumerate(edges) if v==n),'  out_edges: '+' '.join(str(i) for i,(u,v) in enumerate(edges) if u==n)]
 for i,(u,v) in enumerate(edges):s += [f' edge: {i}','  type: INTERCONNECT',f'  src_node: {u}',f'  sink_node: {v}','  disabled: '+('yes' if bad and i==3 else 'true' if disable and i==3 else 'false')]
 s += ['timing_constraints:',' domain: 0',' domain: 1','delay_model:']
 for i,d in enumerate(delays):s += [f' edge: {i} min_delay: {d:.17g} max_delay: {d:.17g}']
 s+=['analysis_result:']
 for domain in [0,1]:
  arr={0:0.,1:1.,2:delays[1]}
  arr[3]=1.+arr[1] if disable or domain==1 else max(f32(arr[1]+1.),f32(arr[2]+1.))
  if unknown:arr[3]=2.5
  arr[4]=f32(arr[3]+1.)
  for n,v in arr.items():
   if domain==1 and n==2:continue
   s += [f' type: SETUP_DATA_ARRIVAL node: {n} launch_domain: {domain} capture_domain: -1 time: {v:.17g}']
  s += [f' type: SETUP_SLACK node: 4 launch_domain: {domain} capture_domain: {domain} slack: {-arr[4]:.17g}']
 path=b/(name+'.echo');path.write_text('\n'.join(s)+'\n');return path
for name,opts in [('ties',{}),('disabled',dict(disable=True)),('float32_distinct',dict(ulp=True)),('unknown',dict(unknown=True))]:
 path=fixture(name,**opts);g=read_echo(path);c=read_compact(path,{0,1},{(4,0,0),(4,1,1)})
 assert c['constraints_text_sha256']==g['constraints_text_sha256']
 for domain in [0,1]:
  old=trace(g,[4],domain);new=trace_compact(c,[4],domain);assert old==new,(name,domain);checks.append(dict(case=name,domain=domain,identical=True,unknown=bool(new['unresolved'])))
bad=fixture('bad_disabled',bad=True)
for fn in [lambda:read_echo(bad),lambda:read_compact(bad,{0},{(4,0,0)})]:
 try:fn()
 except AssertionError:pass
 else:raise AssertionError('Invalid disabled flag accepted')
checks.append(dict(case='bad_disabled',both_reject=True))
candidate=D/'bnn_compact_cone_candidate_01.json';reference=D/'bnn_release_joint_dev_01/Tf_combined_weighted_soft_successor_cone.json'
if candidate.exists():
 old,new=read(reference),read(candidate)
 for key in ['passed','near_ns','worst_slack_s','selected_endpoints','cones','routed_connections','unresolved_non_source_nodes']:assert old[key]==new[key],key
 checks.append(dict(case='actual_BNN_accepted_state',identical=True,nodes=sum(len(c['nodes']) for c in new['cones'].values()),targets=len(new['routed_connections'])))
files=[Path(__file__).resolve(),D/'compact_timing_cone.py',D/'current_sta_arrival_cone_compact.py',D/'current_sta_arrival_cone.py',D/'native_timing_echo_v2.py',*b.glob('*.echo')]
if candidate.exists():files += [candidate,reference]
write(b/'completion.json',dict(passed=True,checks=checks,source_sha256={str(p):sha(p) for p in files},complete_process_seconds=time.monotonic()-start,native_calls=0,
 qualification='Differential selector checks only. Does not replace original native FULL/STA or physical audits, and is not a formal runtime comparison. Existing native batches keep frozen original selector.'))
print(dict(passed=True,checks=len(checks),seconds=time.monotonic()-start),flush=True)
