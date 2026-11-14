#!/usr/bin/env python3
"""Audit explicit reservations for one critical target per net and full cleanup."""
import argparse,collections,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace
from immutable_rr_audit_cache import GraphAuditCache
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--role',required=True);a=p.parse_args();b=a.batch.resolve();role=read(b/'registration.json')['roles'][a.role];state=b/a.role;c=read(state/'completion.json');assert c['passed'];run=Path(c['run']);path=run/'pending_reservations.log';out=b/(a.role+'_reservation_audit.json')
if not role['reservations_enabled']:
 assert not path.exists() and c['checks']['reservations_disabled'];write(out,dict(passed=True,reservations_enabled=False,native_state=str(state),qualification='New binary default-off control; no reservation trace or hidden virtual occupancy.'));raise SystemExit(0)
assert path.exists() and c['checks']['reservations_cleared'];source=Path(role['source']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);g=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01')
targets=list(map(tuple,role['targets']));assert len({n for n,pin in targets})==len(targets),'This trace audit covers one critical target per net'
kept=collections.defaultdict(set);queried=[];native_lines=(run/'joint_native.log').read_text().splitlines()
for line in native_lines:
 v=line.split()
 if v[0]=='KEEP':kept[int(v[1])].add(int(v[2]))
 if v[0]=='QUERY':queried.append((int(v[1]),int(v[2])))
success=int(native_lines[-1].split()[1]);traces=read_trace(source/'routed.route');expected={}
for net,pin in targets:
 tree=from_trace(traces[net]['trace'],g.switches);node=tree['sinks'][pin];required={}
 while True:
  if int(g.nodes[node,1])==1:required[node]=required.get(node,0)+1 # SINK multiplicity.
  elif node not in kept[net]:required[node]=1
  if node==tree['root']:break
  node=tree['edges'][node][0]
 expected[net]=required
held={};initial={};released=[];first_release=False;lines=path.read_text().splitlines();assert lines[-1]==f'COMPLETE {success} reservations_cleared'
for line in lines[:-1]:
 tag,ns,rs,cs,bs,as_=line.split();net,node,count,before,after=map(int,[ns,rs,cs,bs,as_]);assert net in expected and count>0
 if tag=='HOLD':
  assert not first_release,'One-target-per-net case should need only initial holds'
  assert (net,node) not in held and after==before+count and after<=g.capacities[node]
  held[net,node]=count;initial.setdefault(net,{})[node]=count
 elif tag=='RELEASE':
  first_release=True;assert held.pop((net,node))==count and after==before-count and after>=0
  if not released or released[-1]!=net:released.append(net)
 else:raise AssertionError(tag)
assert initial==expected and not held
expected_order=[net for net,pin in queried if (net,pin) in targets]
if not success:expected_order+=sorted(set(expected)-set(expected_order))
assert released==expected_order
write(out,dict(passed=True,reservations_enabled=True,success=bool(success),initial_reserved_nodes=sum(len(v) for v in expected.values()),released_net_order=released,all_reservations_cleared=True,
 source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',state/'completion.json',path,run/'joint_native.log',source/'routed.route']},
 qualification='Checks initial target-path membership/SINK counts, native capacity checks, future-target hold until own turn, and cleanup on success/failure for this one-target-per-net design. Independent final native FULL/STA/physical audit remains mandatory; no all-architecture nonconfig-closure guarantee inferred.'))
