#!/usr/bin/env python3
"""Independent-distance error and single-pin rank diagnosis; not STA attribution."""
from pathlib import Path
from collections import defaultdict, Counter
import csv, hashlib, itertools, json, math, statistics, sys
D=Path(__file__).resolve().parent;B=D/'estimate_trace_dev_01';O=D/'estimate_oracle_01'
assert json.loads((O/'completion.json').read_text())['status']=='completed'
assert json.loads((O/'input_seal.json').read_text())['passed']
reg=json.loads((O/'registration.json').read_text())
exact={}
with (O/'exact.csv').open() as f:
 for row in csv.DictReader(f):
  key=int(row['endpoint']),int(row['reverse']),int(row['target']);assert key not in exact
  value=float(row['seconds']);assert value>=0
  exact[key]=value
assert len(exact)==reg['unique_requests']
# Replay the recorded target lists, not an inferred candidate-selection policy.
events={}
for p in (B/'runs').glob('*/stdout.log'):
 with p.open() as f:
  for line in f:
   if not line.startswith('H3D_REVERSE_TARGETS '):continue
   fields=dict(item.split('=',1) for item in line.split()[1:]);key=p.parent.name,int(fields['net']),int(fields['pin'])
   assert key not in events
   events[key]={name:[int(x) for x in fields[name].split(';') if x] for name in ['old','new']}
stats=defaultdict(lambda:dict(count=0,known=0,unknown=0,unreachable=0,under20=0,ratios=[],errors=[]))
ranks=defaultdict(lambda:dict(groups=0,flips=0,nonfinite_oracle_best=0,chosen_unreachable=0,regrets=[],worst=[]))
targets=defaultdict(lambda:dict(count=0,source_known=0,unknown_source_under20=0,unknown_source_ratios=[]))
known_rows=0;known_keys=set();record_count=0

def prepared():
 global known_rows,record_count
 with (O/'estimates.csv').open() as f:
  for raw in csv.DictReader(f):
   r={k:(v if k in ['run','phase'] else int(v) if k in ['net','pin','source','sink','candidate','source_known','sink_known'] else float(v)) for k,v in raw.items()}
   record_count+=1
   for side,reverse in [('source',0),('sink',1)]:
    key=r[side],reverse,r['candidate'];truth=exact[key];value=r[side+'_value'];known=bool(r[side+'_known'])
    r[side+'_truth']=truth/r['unit']
    s=stats[r['run'],r['phase'],side];s['count']+=1;s['known' if known else 'unknown']+=1
    if known:
     assert math.isfinite(truth) and math.isclose(value*r['unit'],truth,rel_tol=1e-10,abs_tol=1e-18),(key,value*r['unit'],truth)
     known_rows+=1;known_keys.add(key)
    elif not math.isfinite(truth):s['unreachable']+=1
    else:
     actual=truth/r['unit'];s['errors'].append(value-actual)
     if actual>0:s['ratios'].append(value/actual);s['under20']+=value<.8*actual
   congestion=r['opening']-r['source_value'];assert congestion>=-1e-8
   r['estimated_total']=r['opening']+r['branch']
   r['exact_total']=congestion+(1+4*r['criticality'])*(r['source_truth']+r['sink_truth'])
   yield r

for key,group in itertools.groupby(prepared(),key=lambda r:(r['run'],r['phase'],r['net'],r['pin'])):
 rows=list(group);by_candidate={r['candidate']:r for r in rows};assert len(rows)==len(by_candidate)
 run,phase,net,pin=key
 if phase!='selected' and len(rows)>1:
  a=min(rows,key=lambda r:(r['estimated_total'],r['candidate']));b=min(rows,key=lambda r:(r['exact_total'],r['candidate']))
  s=ranks[run,phase];s['groups']+=1
  if not math.isfinite(b['exact_total']):s['nonfinite_oracle_best']+=1
  elif not math.isfinite(a['exact_total']):s['chosen_unreachable']+=1;s['flips']+=1
  else:
   excess=a['exact_total']-b['exact_total'];flip=excess>max(1e-9,1e-10*b['exact_total']);s['flips']+=flip
   regret=100*excess/b['exact_total'] if b['exact_total']>0 else 0 if excess==0 else math.inf
   if math.isfinite(regret):s['regrets'].append(regret)
   s['worst'].append(dict(net=net,pin=pin,candidates=len(rows),estimated_best=a['candidate'],oracle_best=b['candidate'],estimated_best_source_known=a['source_known'],estimated_best_sink_known=a['sink_known'],estimated_best_true_score=a['exact_total'],oracle_best_score=b['exact_total'],regret_pct=regret))
   s['worst']=sorted(s['worst'],key=lambda r:r['regret_pct'],reverse=True)[:12]
 if phase=='source' and (run,net,pin) in events:
  for label,selected in events[run,net,pin].items():
   t=targets[run,label]
   for candidate in selected:
    r=by_candidate[candidate];t['count']+=1;t['source_known']+=r['source_known']
    if not r['source_known'] and math.isfinite(r['source_truth']) and r['source_truth']>0:
     ratio=r['source_value']/r['source_truth'];t['unknown_source_ratios'].append(ratio);t['unknown_source_under20']+=ratio<.8
assert known_rows==reg['logged_measured_sides'] and record_count==sum(reg['rows'].values())
def describe(values):
 if not values:return dict(count=0)
 v=sorted(values)
 return dict(count=len(v),mean=statistics.fmean(v),median=statistics.median(v),p10=v[int(.1*(len(v)-1))],p90=v[int(.9*(len(v)-1))],min=v[0],max=v[-1])
for s in stats.values():
 s['unknown_estimate_over_truth']=describe(s.pop('ratios'));s['unknown_signed_error_units']=describe(s.pop('errors'))
for s in ranks.values():s['regret_pct']=describe(s.pop('regrets'))
for s in targets.values():s['unknown_source_estimate_over_truth']=describe(s.pop('unknown_source_ratios'))
def keyed(mapping):return {'/'.join(key):value for key,value in mapping.items()}
result=dict(passed=True,known_side_observations_checked=known_rows,distinct_known_distances_checked=len(known_keys),rows=record_count,error=keyed(stats),single_pin_ranking=keyed(ranks),reverse_targets=keyed(targets),scope='All traced feasible candidates; exact switch-delay graph proxy on zero-RC RRG, not final STA. Individual-pin score substitutes exact source+sink while retaining that record\'s congestion opening term; DP shared-opening objective differs. Ranking regret and estimation error do not prove a particular final critical-path cause. Repeated phase records are observations, not independent statistical samples. Diagnostic runs exactly reproduce routes/tables/guides/query work.',input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [O/'registration.json',O/'input_seal.json',O/'estimates.csv',O/'exact.csv',Path(__file__)]})
(O/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(known_rows=known_rows,distinct_known=len(known_keys),rows=record_count,selected={k:v for k,v in result['error'].items() if '/selected/' in k},reverse_targets=result['reverse_targets']),indent=2))
