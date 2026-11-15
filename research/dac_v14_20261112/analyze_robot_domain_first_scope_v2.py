"""Inspect the actual first same-current request, crossing sources and domain releases."""
import hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from resource_opportunity_census import stream_trace
from endpoint_timing_policy_streaming_v2 import compare
from run_native_scope_policy_v4 import run_dir

out=D/'robot_domain_first_scope_analysis_02';out.mkdir(exist_ok=False)
cohort=D/'complete_serial_additional_circuits_01';report=read(cohort/'comparison.json');assert report['passed'] and report['pairs']['robot_rl']['quality_comparison_available']
transactions=[cohort/('robot_rl_'+side)/'flow/repair/round_000/candidate_00' for side in ['native','domain']]
roles=[read(t/'registration.json')['roles'][name] for t,name in zip(transactions,['reuse_off','reuse_on'])]
matched={k:roles[0][k]==roles[1][k] for k in ['queries','removed_pins','objective','seed_order','original_budget','fixed_resource_limits','fixed_target_paths']};assert all(matched.values())
assert sha(transactions[0]/'request.txt')==sha(transactions[1]/'request.txt')
initials=[Path(r['state']) for r in roles];assert route_body(run_dir(initials[0])/'routed.route')==route_body(run_dir(initials[1])/'routed.route')
assert read(initials[0]/'endpoint_vector.json')==read(initials[1]/'endpoint_vector.json')
finals=[Path(report['results']['robot_rl_'+side]['final_state']) for side in ['native','domain']]
files=[Path(__file__).resolve(),D/'resource_opportunity_census.py',cohort/'comparison.json']
for t,role in zip(transactions,roles):
 files += [t/'registration.json',t/'request.txt',Path(role['state'])/'endpoint_vector.json',run_dir(Path(role['state']))/'routed.route']
binary=[sha(read(run_dir(s)/'manifest.json')['command'][0]) for s in finals];assert len(set(binary))==1
log=transactions[1]/'reuse_on/runs/state/vertical_domain.log';lines=log.read_text().splitlines()
releases=[dict(net=int(f[1]),pin=int(f[2]),reason=f[3]) for l in lines if (f:=l.split()) and f[0]=='RELEASE'];assert len(releases)==2
assert {(r['net'],r['pin']) for r in releases}=={(3454,1),(3438,3)}
checks=[dict(net=int(f[1]),pin=int(f[2])) for l in lines if (f:=l.split()) and f[0]=='CHECK']
assert len(checks)==14 and 'COMPLETE 1 occupancy_restored' in lines
files.append(log)
def crossing_views(state):
 result={}
 for r in stream_trace(run_dir(state)/'routed.route'):
  cb=set();sb=set();edges=set();sinks=set()
  for n in r['trace']:
   if n.kind=='SINK':sinks.add((n.pin,n.inode))
  for a,b in zip(r['trace'],r['trace'][1:]):
   if a.switch==-1:continue
   edges.add((a.inode,b.inode,a.switch))
   if a.low[2]!=b.low[2]:
    if a.kind=='OPIN':cb.add(a.inode)
    else:assert a.kind=='CHANX';sb.add(a.inode)
  result[r['net']]=dict(CB=sorted(cb),SB=sorted(sb),sinks=sorted(sinks),tree_sha256=hashlib.sha256(json.dumps(sorted(edges)).encode()).hexdigest())
 return result
views=[crossing_views(s) for s in [initials[0],*finals]]
assert views[0].keys()==views[1].keys()==views[2].keys()
assert all(views[0][n]['sinks']==views[1][n]['sinks']==views[2][n]['sinks'] for n in views[0])
changed=[]
for net in views[0]:
 src,n,d=[v[net] for v in views]
 if len({x['tree_sha256'] for x in [src,n,d]})==1:continue
 changed.append(dict(net=net,source_CB=src['CB'],native_CB=n['CB'],domain_CB=d['CB'],source_SB=src['SB'],native_SB=n['SB'],domain_SB=d['SB'],native_minus_source_CB=len(n['CB'])-len(src['CB']),domain_minus_source_CB=len(d['CB'])-len(src['CB']),domain_minus_native_CB=len(d['CB'])-len(n['CB']),domain_released_here=any(r['net']==net for r in releases)))
assert {r['net'] for r in changed}<=set(map(int,roles[0]['removed_pins']))
assert sum(r['domain_minus_native_CB'] for r in changed)==-1
cp=compare(read(finals[0]/'endpoint_vector.json'),read(finals[1]/'endpoint_vector.json'))
write(out/'crossing_source_differences.json',changed)
for state in finals:files += [state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'routed.route',run_dir(state)/'independent_audit.json']
write(out/'completion.json',dict(passed=True,matched_first_scope_fields=matched,request_bytes_exact=True,initial_full_vector_and_ordered_route_exact=True,candidate_STA_binary_exact=True,first_scope_domain_releases=releases,remaining_domain_checks=len(checks),changed_net_crossing_sources=changed,final_endpoint_comparison=cp,actual_complete_domain_minus_native_resources=dict(wirelength=20,SB_pairs=0,CB_sources=-1),actual_complete_domain_minus_native_seconds=report['pairs']['robot_rl']['descriptive_domain_minus_native_seconds'],native_calls_new=0,source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},artifact_sha256={'crossing_source_differences.json':sha(out/'crossing_source_differences.json')},qualification='Actual first transaction has identical current source/requests/cuts/weights/order/binary; domain plus per-failed-network release is the combined change. Crossing sources reconstructed from already validated actual traces; all fixed sinks match. Native/domain trajectories subsequently have different own-current menu work, so full cost is descriptive, not equal-work or isolated-release speedup. Operational release reasons do not prove mathematical infeasibility.'))
print(dict(passed=True,first_scope_releases=releases,changed_nets=[r['net'] for r in changed],CB_delta_by_net={r['net']:r['domain_minus_native_CB'] for r in changed},native_calls_new=0),flush=True)
