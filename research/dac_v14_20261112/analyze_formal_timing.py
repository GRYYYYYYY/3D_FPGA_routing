#!/usr/bin/env python3
"""Circuit-balanced medians and paired repeat ratios; retain all registered roles."""
from pathlib import Path
import collections, hashlib, json, math, statistics, sys
from formal_timing_statistics import sha, planned_roles, parse_time, group_statistics
from routing_log_metrics import last_iteration
B=Path(sys.argv[1]);reg=json.loads((B/'registration.json').read_text())
rows=json.loads((B/'observations.json').read_text()) if (B/'observations.json').exists() else []
index={(x['circuit'],x['repeat'],x['arm']):x for x in rows}
roles=planned_roles(reg)
assert len(index)==len(rows), 'Duplicate observed roles'
assert set(index)<=set(roles), 'Unregistered observed role'
bindings={str(B/'registration.json'):sha(B/'registration.json')}
sealed=(B/'input_seal.json').exists() and json.loads((B/'input_seal.json').read_text())['passed']
batch_complete=(B/'completion.json').exists()
if batch_complete:assert json.loads((B/'completion.json').read_text())['roles']==len(roles)
for circuit in reg['circuits']:
 for repeat,order in enumerate(reg['orders']):
  for position,arm in enumerate(order):
   if (circuit,repeat,arm) not in index:
    row=dict(circuit=circuit,repeat=repeat,arm=arm,status='missing' if batch_complete else 'not_started')
    rows.append(row);index[circuit,repeat,arm]=row
   row=index[circuit,repeat,arm]
   row['position']=position
   rd=Path(row.get('path',B/'runs'/f'{circuit}_r{repeat}_{arm}'));row['path']=str(rd)
   mp=rd/'manifest.json'
   if mp.exists():
    m=json.loads(mp.read_text());bindings[str(mp)]=sha(mp)
    row['native_status']=m['status'];row['returncode']=m.get('returncode');row['execution_status']=m.get('execution_status')
    if row.get('process_seconds') is not None:assert row['process_seconds']==m.get('wall_seconds')
    row['process_seconds']=m.get('wall_seconds')
    row['router_seconds']=m.get('metrics',{}).get('router_seconds')
    row['iterations']=m.get('metrics',{}).get('iterations')
    row['iteration_evidence']='manifest' if row['iterations'] is not None else None
    if row['iterations'] is None and m['status']!='running' and (rd/'stdout.log').exists():
     last=last_iteration((rd/'stdout.log').read_text().splitlines())
     row['iterations']=last['iteration'] if last else None;row['last_overused_rr_nodes']=last['overused_rr_nodes'] if last else None
     row['iteration_evidence']='last_completed_native_log_row' if last else None
    row['native_cpd_ns']=m.get('metrics',{}).get('critical_path_ns')
    if row['status'] in ['not_started','missing']:
     row['status']='running' if m['status']=='running' else 'pending_role_reconciliation'
    ep=rd/'environment.json'
    if ep.exists():
     row['measurement_environment']=json.loads(ep.read_text());bindings[str(ep)]=sha(ep)
     assert row['measurement_environment']['affinity']==[reg['cpu']]
    tp=rd/'time.txt'
    if tp.exists() and m['status']!='running':
     assert sha(tp)==m['outputs']['time.txt']['sha256'];bindings[str(tp)]=sha(tp)
     row.update(parse_time(tp.read_text()))
   if row['status']=='legal':
    rd=Path(row['path']);q=json.loads((rd/'quality_reuse.json').read_text());assert q['passed']
    m=json.loads((rd/'manifest.json').read_text());assert m['status']=='completed' and m['metrics']['native_full_check_passed']
    assert all(q['checks'].values()) and row.get('max_rss_kib',0)>0 and row['process_seconds']>0
    bindings[str(rd/'quality_reuse.json')]=sha(rd/'quality_reuse.json')
    if sealed:
     # Rehash route artifacts only after measurements are sealed, avoiding heavy concurrent reads.
     rp=rd/'routed.route';digest=sha(rp);assert digest==m['outputs']['routed.route']['sha256'];bindings[str(rp)]=digest
    if not sealed:row['status']='legal_pending_batch_seal'
   row['legal_cpd_ns']=row.get('native_cpd_ns') if row['status']=='legal' else None
medians={};pairs={}
for circuit in reg['circuits']:
 medians[circuit]={}
 for arm in reg['arms']:
  group=[index[circuit,r,arm] for r in range(len(reg['orders']))]
  medians[circuit][arm]=group_statistics(group)
for left,right in [('A0','R1'),('A0','U'),('R1','U')]:
 values=[]
 for circuit in reg['circuits']:
  a,b=medians[circuit][left],medians[circuit][right]
  if a['complete'] and b['complete']:
   values.append(dict(circuit=circuit,reference_seconds=a['process_median'],new_seconds=b['process_median'],
    new_over_reference=b['process_median']/a['process_median'],paired_repeat_ratios=[index[circuit,r,right]['process_seconds']/index[circuit,r,left]['process_seconds'] for r in range(len(reg['orders']))],
    reference_rss_median_kib=a['max_rss_kib_median'],new_rss_median_kib=b['max_rss_kib_median']))
 pairs[left+'->'+right]=dict(declared_circuits=len(reg['circuits']),complete_circuits=len(values),cases=values,
    circuit_geomean_new_over_reference=math.exp(statistics.mean(math.log(v['new_over_reference']) for v in values)) if values else None,
    worst_new_over_reference=max((v['new_over_reference'] for v in values),default=None))
result=dict(sealed=sealed,batch_complete=batch_complete,declared_roles=len(roles),scope=reg['timing_scope'],population=reg['population'],statuses=dict(collections.Counter(x['status'] for x in rows)),medians=medians,comparisons=pairs,observations=rows,
 input_sha256=bindings,memory_definition='GNU time maximum resident set size in Linux KiB, not a simultaneous process-tree RSS sum.',
 wall_definition='Registered whole-process observer wall interval; GNU time elapsed is recorded separately and rounded. Planning/router times are components, never added to process wall.',
 script_sha256=sha(Path(__file__)),helper_sha256=sha(Path(__file__).with_name('formal_timing_statistics.py')),registration_sha256=sha(B/'registration.json'))
(B/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(sealed=sealed,statuses=result['statuses'],comparisons=pairs),indent=2))
