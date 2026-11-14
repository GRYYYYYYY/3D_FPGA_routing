#!/usr/bin/env python3
"""Compare exact graph evidence and unchanged full-route auditors, without STA."""
import argparse,copy,re,resource,shutil,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import check_route as cr
import flatland_benchmark as study

p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
b=a.batch.resolve();b.mkdir(exist_ok=False);cache=a.cache.resolve()
states=[D/n for n in ['current_sta_policy_native_spmv_R1_01/attempt_001/evaluation','current_sta_policy_native_Tf_01/attempt_001/evaluation','current_sta_policy_native_R1_01/attempt_004/evaluation']]
routes=[Path(read(s/'completion.json')['run'])/'routed.route' for s in states]
graph=Path(read(D/'rr_audit_cache_e695_dev_01/completion.json')['graph'])
bindings={str(q):sha(q) for q in [Path(__file__).resolve(),D/'full_route_graph_cache.py',D/'immutable_rr_audit_cache.py',cache/'completion.json',ROOT/'scripts/check_route.py',OLD/'execution_scripts/flatland_benchmark.py',*routes]}
write(b/'registration.json',dict(status='registered_before_validation',question='Does cached full graph evidence exactly equal the production XML reader and preserve all audit/resource/delay results, including illegal routes?',source_sha256=bindings,native_calls=0))
cr.graph_records=study.records
t=time.monotonic();reference=cr.batch_graph_evidence(graph,routes);reference_seconds=time.monotonic()-t
t=time.monotonic();g=FullRouteGraphCache(graph,cache);cached=g.evidence(graph,reference['wanted_nodes'],reference['wanted_edges']);cached_seconds=time.monotonic()-t
assert reference==cached,'Full graph evidence differs (including raw timing strings/directions)'
def normalized(result):
    result=copy.deepcopy(result);result.pop('audit_wall_seconds',None);return result
rows=[]
for route in routes:
    t=time.monotonic();left=cr.audit(graph,route,graph_evidence=reference);xml_audit_seconds=time.monotonic()-t
    t=time.monotonic();right=cr.audit(graph,route,graph_evidence=cached);cached_audit_seconds=time.monotonic()-t
    assert left['passed'] and normalized(left)==normalized(right)
    assert study.physical_route_metrics(route,reference)==study.physical_route_metrics(route,cached)
    rows.append(dict(route=str(route),full_audit_equal_except_walltime=True,resource_metrics_equal=True,xml_evidence_audit_seconds=xml_audit_seconds,cached_evidence_audit_seconds=cached_audit_seconds))
    write(b/f'audit_{len(rows)}.json',right)
# Deliberate invalid routes never reach native analysis or an accepted state.
original=routes[0].read_text();trace=cr.read_trace(routes[0]);net=next(n for n,v in trace.items() if any(x.kind in ['CHANX','CHANY'] and cached['nodes'][x.inode]['capacity']==1 for x in v['trace']))
block=re.search(r'^Net '+str(net)+r' \(.*?\)\n.*?(?=^Net |\Z)',original,re.M|re.S);assert block
duplicate=block.group(0).replace('Net '+str(net)+' (','Net '+str(max(trace)+1)+' (',1)
over=b/'over_capacity.route';over.write_text(original+'\n'+duplicate)
bad=b/'bad_switch.route';changed,count=re.subn(r'(Switch:\s*)\d+',lambda m:m.group(1)+str(g.g.stride),original,count=1);assert count==1;bad.write_text(changed)
negative=[]
for route,expect in [(over,'capacity exceeded'),(bad,'missing directed edge/switch')]:
    wn,we=set(),set()
    for net in cr.read_trace(route).values():
        tr=net['trace'];wn.update(n.inode for n in tr);we.update((u.inode,v.inode,u.switch) for u,v in zip(tr,tr[1:]) if u.switch!=-1)
    # No rescan: the immutable union reference already covers every original node/edge.
    assert wn<=reference['wanted_nodes']
    ref=reference.copy();ref['wanted_nodes']=wn;ref['wanted_edges']=we;ref['available_edges']=reference['available_edges']&we
    other=g.evidence(graph,wn,we)
    left=cr.audit(graph,route,graph_evidence=ref);right=cr.audit(graph,route,graph_evidence=other)
    assert not left['passed'] and normalized(left)==normalized(right)
    assert any(expect in e for e in right['errors'])
    negative.append(dict(kind=expect,route=str(route),identical_errors=True,error_count=len(right['errors'])))
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,full_raw_graph_evidence_equal=True,positive_cases=rows,negative_cases=negative,XML_union_evidence_seconds=reference_seconds,cache_load_plus_evidence_seconds=cached_seconds,cache_receipt=g.receipt,complete_validation_seconds=time.monotonic()-start,source_sha256=bindings,native_calls=0,qualification='Contemporaneous data-access comparison and exact full-audit/resource equivalence; not a complete routing speedup. Original auditors and FULL/STA remain unchanged. Negative routes are diagnostic files only.'))
print(dict(passed=True,positive_cases=len(rows),negative_cases=len(negative),XML_seconds=reference_seconds,cached_seconds=cached_seconds),flush=True)
