#!/usr/bin/env python3
"""Check exact BNN case equivalence and capacity-credit edge conditions."""
import array,resource,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache,KINDS
from current_query_case_cache import saturated_nodes,make_case_fast
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));start=time.monotonic()
out=D/'current_query_case_cache_validation_01';out.mkdir(exist_ok=False)
q=D/'bnn_slack_release_screen_01/Tf_capacity';proof=read(q/'analysis.json');assert proof['passed']
reg=read(q/'execution_registration.json');source=Path(reg['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
files=[Path(__file__).resolve(),D/'current_query_case_cache.py',D/'run_native_frontier_queries.py',q/'analysis.json',q/'cases.json',q/'selection.json',q/'occupancy_owners.json',source/'routed.route',D/'rr_audit_cache_bnn_01/completion.json']
write(out/'registration.json',dict(status='registered_before_validation',question='Can same-state saturation be computed once instead of scanning all10.26M nodes for each of13 targets without changing any actual solver input?',source_sha256={str(p):sha(p) for p in files},native_calls=0,new_queries=0))
g=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');owners={int(k):v for k,v in read(q/'occupancy_owners.json').items()};traces=read_trace(source/'routed.route')
caps=array.array('I',map(int,g.capacities));kinds=[KINDS[int(k)] for k in g.nodes[:,1]]
old=read(q/'cases.json');selection=read(q/'selection.json')['targets'];t=time.monotonic();sat=saturated_nodes(owners,caps);index_seconds=time.monotonic()-t
t=time.monotonic();new=[make_case_fast(row,traces,kinds,g.switches,owners,caps,sat) for row in selection];cases_seconds=time.monotonic()-t
assert new==old,'Actual solver cases differ'
# Independent small capacity states include zero capacity, shared ownership,
# spare capacity and already overused resources: own-net credit must be exact.
checks=0
for capacities in [array.array('I',[0,1,2,1]),array.array('I',[1,2,3,0])]:
 for counts in [(0,0,0,0),(0,1,2,1),(1,2,3,2)]:
  owner={n:list(range(c)) for n,c in enumerate(counts)};s=saturated_nodes(owner,capacities)
  for mask in range(16):
   own={n for n in range(4) if mask & (1<<n)}
   expected={n for n,c in enumerate(capacities) if len(owner.get(n,[]))-int(n in own)>=c}
   got=s-{n for n in own if len(owner.get(n,[]))-1<capacities[n]}
   assert got==expected;checks+=1
write(out/'completion.json',dict(passed=True,actual_cases=len(new),all_solver_fields_exact=True,edge_condition_checks=checks,
 current_graph_nodes=len(caps),saturated_nodes=len(sat),shared_index_seconds=index_seconds,case_construction_seconds=cases_seconds,
 complete_validation_seconds=time.monotonic()-start,native_calls=0,new_queries=0,source_sha256={str(p):sha(p) for p in files},
 qualification='Exact current BNN cases, plus zero/shared/spare/overused and own-credit conditions. New component timing only; old151.868s complete preparation is a different scope and is not a speedup denominator. Not yet used in an end-to-end controller.'))
print(dict(passed=True,cases=len(new),index_seconds=index_seconds,case_seconds=cases_seconds),flush=True)
