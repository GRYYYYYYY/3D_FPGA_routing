#!/usr/bin/env python3
"""Read-only failed-route occupancy evidence; never reclassify native failures as legal."""
from pathlib import Path
import collections,hashlib,json,os,re,shutil,sys,time
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path[:0]=[str(R/'scripts'),str(D)]
import flatland_benchmark as study
import check_route as cr
from compare_lazagna_graphs import records
from routing_log_metrics import last_iteration
sha=lambda p:study.sha256(Path(p))
out=D/'failed_attention_diagnostic_01';out.mkdir(exist_ok=False);shutil.copy2(__file__,out/'runner.py');assert shutil.disk_usage(out).free>=80*1024**3
source=D/'feedback_expansion_01/runs/attention_layer_U';m=json.loads((source/'manifest.json').read_text());assert m['status']=='failed'
assert json.loads((source.parent.parent/'input_seal.json').read_text())['passed']
assert sha(source/'routed.route')==m['outputs']['routed.route']['sha256']
ctx=study.context('attention_layer','hybrid_o',11,100);graph=Path(ctx['fixture']['original_graph']);paths=[source/'manifest.json',source/'routed.route',source/'stdout.log',source.parent.parent/'input_seal.json',Path(ctx['model_path']),graph,out/'runner.py',Path(study.__file__),Path(cr.__file__)]
bindings={str(p):sha(p) for p in paths};(out/'registration.json').write_text(json.dumps(dict(question='Which physical resources remain overused in the saved failed attention U route? Record actual reported crossings and distinguish this artifact from native last-iteration counts and legal QoR.',source=str(source),native_status='failed',pid=os.getpid(),start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],bindings=bindings,timeout_seconds=1800,address_space_bytes=32*1024**3,disk_reserve_bytes=80*1024**3,scope='Read-only saved failure artifact, no route calls; original scoped audit caveats retained.'),indent=2)+'\n')
start=time.monotonic();cr.graph_records=records;evidence=cr.batch_graph_evidence(graph,[source/'routed.route']);audit=cr.audit(graph,source/'routed.route',graph_evidence=evidence)
traces=cr.read_trace(source/'routed.route');occupancy=collections.Counter();nets=collections.defaultdict(list);cross_entries=set();cross_destinations=set()
for net_id,net in traces.items():
 trace=net['trace']
 for node in {x.inode for x in trace}:occupancy[node]+=1;nets[node].append(net_id)
 for a,b in zip(trace,trace[1:]):
  if a.switch!=-1 and a.low[2]!=b.low[2]:cross_entries.add(a.inode);cross_destinations.add(b.inode)
overused=[]
for node,occ in occupancy.items():
 meta=evidence['nodes'].get(node)
 if meta and occ>meta['capacity']:
  overused.append(dict(node=node,occupancy=occ,capacity=meta['capacity'],kind=meta['kind'],direction=meta['direction'],low=meta['low'],high=meta['high'],is_used_crossing_entry=node in cross_entries,is_used_crossing_destination=node in cross_destinations,nets=nets[node]))
assert len(overused)==audit['route']['overused_rr_nodes']
physical=study.physical_route_metrics(source/'routed.route',evidence)
(out/'scoped_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
result=dict(diagnostic_completed=True,native_status='failed',not_legal_qor=True,physical_metrics_of_saved_failed_artifact=physical,native_last_iteration=last_iteration((source/'stdout.log').read_text().splitlines()),saved_route_summary=audit['route'],overused_by_kind=dict(collections.Counter(r['kind'] for r in overused)),overused_crossing_entries=sum(r['is_used_crossing_entry'] for r in overused),overused_crossing_destinations=sum(r['is_used_crossing_destination'] for r in overused),overused=overused,scoped_audit_passed=audit['passed'],audit_error_count=len(audit['errors']),caveats=audit['not_checked'],meaning='Reported saved failure-route occupancy, not a legal physical layout or native last-iteration state unless independently matched. No STA/QoR improvement or guide causality claim.',wall_seconds=time.monotonic()-start)
(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');checks={p:sha(p)==h for p,h in bindings.items()};(out/'input_seal.json').write_text(json.dumps(dict(passed=all(checks.values()),checks=checks),indent=2)+'\n');assert all(checks.values());(out/'completion.json').write_text(json.dumps(dict(status='read_only_diagnostic_complete',wall_seconds=time.monotonic()-start),indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='overused'},indent=2))
