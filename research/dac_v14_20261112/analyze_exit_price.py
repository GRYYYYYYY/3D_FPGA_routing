#!/usr/bin/env python3
"""Price-only native checks, initial-table preservation and logged bounded surcharge accounting."""
from pathlib import Path
import json,re,sys,math,hashlib
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());results={}
def body(p):
 t=p.read_text();return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
def initial_tables(lines):
 result=[]
 for l in lines:
  if l.startswith('H3D_PLAN '):break
  if l.startswith('H3D_TABLE '):result.append(l)
 assert result
 return result
for c in reg['circuits']:
 results[c]={};control=B/'runs'/f'{c}_V';baseline=(control/'stdout.log').read_text().splitlines()
 assert json.loads((control/'optimization_equivalence.json').read_text())['passed']
 for arm in reg['arms']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text())
  if m['status']!='completed':results[c][arm]=dict(status=m['status']);continue
  audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed'] and m['metrics']['native_full_check_passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
  env=m['environment'];assert float(env['VPR_H3D_EXIT_PRICE'])==(0. if arm=='V' else .25)
  assert env['VPR_H3D_PLANAR_FEEDBACK']==env['VPR_H3D_TRACE_PLANAR_FEEDBACK']==env['VPR_H3D_MIXED_DELAY']==env['VPR_H3D_TIMING_GUIDE']==env['VPR_H3D_EQUIVALENT_GUIDES']=='0'
  assert env['VPR_H3D_FEEDBACK']=='1' and env['VPR_H3D_DELAY_BUDGET']=='4096'
  lines=(rd/'stdout.log').read_text().splitlines();assert initial_tables(lines)==initial_tables(baseline)
  records=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_EXIT_PRICE ')];total=0.;minimum=math.inf;maximum=0.
  for r in records:
   price,opening,weight,premium=map(float,[r['price'],r['opening_weight'],r['weight'],r['premium']]);assert weight==.25 and opening==16. and price>1. and 0.<premium<=4.
   assert math.isclose(premium,opening*weight*min(1.,max(0.,price-1.)),rel_tol=1.e-12,abs_tol=1.e-12)
   assert int(r['candidate'])!=int(r['destination']);total+=premium;minimum=min(minimum,premium);maximum=max(maximum,premium)
  counters={}
  for prefix in ['H3D_EXIT_PRICE_SUMMARY ','H3D_FEEDBACK ','H3D_DELAY ']:
   r=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith(prefix)][-1];counters[prefix.strip()]=r
  price=counters['H3D_EXIT_PRICE_SUMMARY'];assert int(price['positive'])==len(records)<=int(price['pairs'])
  if arm=='V':assert int(price['pairs'])==int(price['cross_edges'])==0
  results[c][arm]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],counters=counters,initial_tables=len(initial_tables(lines)),same_route_as_V=body(rd/'routed.route')==body(control/'routed.route'),same_final_guides=(rd/'h3d_final_guides.csv').read_bytes()==(control/'h3d_final_guides.csv').read_bytes(),positive_surcharge_records=len(records),positive_sum=total,min_positive=minimum if records else None,max_positive=maximum,planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'])
out=dict(passed=True,circuits=results,scope='Exact Uoff control; identical initial planning-table sequence; bounded positive exit-price log formula and accounting; native/independent final route/guide audits and seal. Destination feasibility and minimum selection use production SCC; these log checks are not an independent reconstruction of intermediate occupancy or joint delay/congestion optimum. Development instrumentation costs not formal speedup.',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'exit_price_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(results,indent=2))
