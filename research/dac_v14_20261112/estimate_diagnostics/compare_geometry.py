#!/usr/bin/env python3
"""Compare observed calibrated unknowns to the existing unit-scale geometry prior."""
from pathlib import Path
import csv,json,math,statistics,hashlib
from collections import defaultdict
D=Path(__file__).resolve().parents[1]/'estimate_oracle_01'
assert json.loads((D/'input_seal.json').read_text())['passed']
exact={}
with (D/'exact.csv').open() as f:
 for r in csv.DictReader(f):exact[int(r['endpoint']),int(r['reverse']),int(r['target'])]=float(r['seconds'])
values=defaultdict(lambda:defaultdict(list))
with (D/'estimates.csv').open() as f:
 for r in csv.DictReader(f):
  if r['phase'] not in ['source','selected']:continue
  for side,direction in [('source',0),('sink',1)]:
   if r[side+'_known']=='1':continue
   t=exact[int(r[side]),direction,int(r['candidate'])]/float(r['unit'])
   if not math.isfinite(t) or t<=0:continue
   v=values[r['run'],r['phase'],side];cal=float(r[side+'_value']);raw=float(r[side+'_proxy']);floor=max(cal,raw)
   for name,x in [('calibrated',cal),('geometry',raw),('floor_geometry',floor)]:
    v[name+'_ratio'].append(x/t);v[name+'_relative_abs_error'].append(abs(x-t)/t)
   v['scale'].append(float(r[side+'_scale']))
out={'/'.join(k):{n:dict(count=len(x),median=statistics.median(x),mean=statistics.fmean(x),under20=sum(y<.8 for y in x) if n.endswith('_ratio') else None) for n,x in v.items()} for k,v in values.items()}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(scope='Exploratory same records and exact graph oracle. Floor is max(existing effective estimate,unit-scaled geometry), not an admissible bound. Not route reruns or prospective QoR.',summary=out,input_sha256={str(p):sha(p) for p in [D/'estimates.csv',D/'exact.csv',Path(__file__)]})
(D/'geometry_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print('source-scale geometry comparison complete',len(out),'groups')
