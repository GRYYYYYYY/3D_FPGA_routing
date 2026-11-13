#!/usr/bin/env python3
"""Circuit-balanced medians and paired repeat ratios; retain all registered roles."""
from pathlib import Path
import collections, hashlib, json, math, statistics, sys
B=Path(sys.argv[1]);reg=json.loads((B/'registration.json').read_text())
rows=json.loads((B/'observations.json').read_text()) if (B/'observations.json').exists() else []
index={(x['circuit'],x['repeat'],x['arm']):x for x in rows}
sealed=(B/'input_seal.json').exists() and json.loads((B/'input_seal.json').read_text())['passed']
for circuit in reg['circuits']:
 for repeat,order in enumerate(reg['orders']):
  for arm in order:
   if (circuit,repeat,arm) not in index:
    row=dict(circuit=circuit,repeat=repeat,arm=arm,status='missing_or_pending')
    rows.append(row);index[circuit,repeat,arm]=row
   row=index[circuit,repeat,arm]
   if row['status']=='legal':
    rd=Path(row['path']);q=json.loads((rd/'quality_reuse.json').read_text());assert q['passed']
    m=json.loads((rd/'manifest.json').read_text());assert m['status']=='completed' and m['metrics']['native_full_check_passed']
    if not sealed:row['status']='legal_pending_batch_seal'
medians={};pairs={}
for circuit in reg['circuits']:
 medians[circuit]={}
 for arm in reg['arms']:
  group=[index[circuit,r,arm] for r in range(len(reg['orders']))]
  complete=all(x['status']=='legal' for x in group)
  medians[circuit][arm]=dict(complete=complete,process_repeats=[x.get('process_seconds') for x in group],planning_repeats=[x.get('planning_seconds') for x in group],
    process_median=statistics.median(x['process_seconds'] for x in group) if complete else None,
    planning_median=statistics.median(x['planning_seconds'] for x in group) if complete and all(x.get('planning_seconds') is not None for x in group) else None)
for left,right in [('A0','R1'),('A0','U'),('R1','U')]:
 values=[]
 for circuit in reg['circuits']:
  a,b=medians[circuit][left],medians[circuit][right]
  if a['complete'] and b['complete']:
   values.append(dict(circuit=circuit,reference_seconds=a['process_median'],new_seconds=b['process_median'],
    new_over_reference=b['process_median']/a['process_median'],paired_repeat_ratios=[index[circuit,r,right]['process_seconds']/index[circuit,r,left]['process_seconds'] for r in range(3)]))
 pairs[left+'->'+right]=dict(declared_circuits=len(reg['circuits']),complete_circuits=len(values),cases=values,
    circuit_geomean_new_over_reference=math.exp(statistics.mean(math.log(v['new_over_reference']) for v in values)) if values else None,
    worst_new_over_reference=max((v['new_over_reference'] for v in values),default=None))
result=dict(sealed=sealed,scope=reg['timing_scope'],population=reg['population'],statuses=dict(collections.Counter(x['status'] for x in rows)),medians=medians,comparisons=pairs,observations=rows,
 script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),registration_sha256=hashlib.sha256((B/'registration.json').read_bytes()).hexdigest())
(B/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(sealed=sealed,statuses=result['statuses'],comparisons=pairs),indent=2))
