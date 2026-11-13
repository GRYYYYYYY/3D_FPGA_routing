#!/usr/bin/env python3
"""Audit active-target refresh applicability and native correctness, not causal QoR claims."""
from pathlib import Path
import json,re,sys,hashlib,csv,math,collections,struct,statistics
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());results={}
def body(p):
 t=p.read_text();return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
def initial(lines):
 out=[]
 for l in lines:
  if l.startswith('H3D_PLAN '):break
  if l.startswith('H3D_TABLE '):out.append(l)
 assert out
 return out
for c in reg['circuits']:
 results[c]={};control=B/'runs'/f'{c}_C';base=(control/'stdout.log').read_text().splitlines()
 assert json.loads((control/'relative_pressure_control_equivalence.json').read_text())['passed']
 for arm in reg['arms']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text());env=m['environment']
  if m['status']!='completed':results[c][arm]=dict(status=m['status']);continue
  audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed'] and m['metrics']['native_full_check_passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
  assert env['VPR_H3D_TARGET_FEEDBACK']=='1'
  assert env['VPR_H3D_DP_TIE_PRESSURE']=='0'
  assert env['VPR_H3D_DP_MARGIN_PRESSURE']==('0' if arm=='C' else '1')
  assert env['VPR_H3D_MISS_WEIGHT']=='2'
  assert env['VPR_H3D_TRACE_GUIDE_MARGIN']==env['VPR_H3D_TRACE_DP_SENSITIVITY']=='1'
  assert env['VPR_H3D_TRACE_UPDATE_PINS']==env['VPR_H3D_FEEDBACK']==env['VPR_H3D_ALL_LAYER_BB']=='1'
  assert env['VPR_H3D_LAYER_BB_FEEDBACK']==env['VPR_H3D_TARGET_DRIFT']=='0'
  for key in ['VPR_H3D_PLANAR_FEEDBACK','VPR_H3D_EXIT_PRICE','VPR_H3D_MIXED_DELAY','VPR_H3D_TIMING_GUIDE','VPR_H3D_EQUIVALENT_GUIDES','VPR_H3D_TARGET_DELAY','VPR_H3D_LAYER_BB_DELAYED']:
   assert float(env[key])==0
  lines=(rd/'stdout.log').read_text().splitlines();rows=[];refresh=None;target_events=[]
  for l in lines:
   if l.startswith('H3D_REFRESH '):refresh=dict(re.findall(r'(\w+)=(\S+)',l))
   if l.startswith('H3D_TARGET_REFRESH '):
    r={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)};assert r['targets']>=0 and r['preserved']>=0;target_events.append(r)
   if l.startswith('H3D_UPDATE_PIN '):
    r=dict(x.split('=',1) for x in l.split()[1:]);r.update({k:int(r[k]) for k in ['net','iter','pin','retained','targeted']})
    assert refresh and refresh['accepted']=='1' and int(refresh['net'])==r['net'] and int(refresh['iter'])==r['iter']
    assert r['old']!=r['new'] and not(r['retained'] and r['targeted'])
    assert r['targeted']==1 and r['retained']==0
    rows.append(r)
  counters={}
  for prefix in ['H3D_UPDATE_PINS_SUMMARY ','H3D_FEEDBACK ','H3D_DELAY ','H3D_FINAL ']:
   r=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith(prefix)][-1];counters[prefix.strip()]=r
  summary=counters['H3D_UPDATE_PINS_SUMMARY'];assert int(summary['records'])==len(rows) and int(summary['retained'])==sum(r['retained'] for r in rows) and int(summary['targeted'])==sum(r['targeted'] for r in rows)
  assert len(target_events)==int(counters['H3D_FEEDBACK']['attempts'])
  if arm=='X':assert int(counters['H3D_FINAL']['guide_rollbacks'])==1
  else:
   assert initial(lines)==initial(base)
   assert int(counters['H3D_FINAL']['guide_rollbacks'])==0
  results[c][arm]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],counters=counters,initial_tables=len(initial(lines)),initial_equal_C=initial(lines)==initial(base),same_route_as_C=body(rd/'routed.route')==body(control/'routed.route'),same_final_guides=(rd/'h3d_final_guides.csv').read_bytes()==(control/'h3d_final_guides.csv').read_bytes(),changed_preferences=len(rows),changed_retained=sum(r['retained'] for r in rows),changed_targeted=sum(r['targeted'] for r in rows),target_refresh_calls=len(target_events),target_pin_events=sum(r['targets'] for r in target_events),preserved_pin_events=sum(r['preserved'] for r in target_events),planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'],rows=rows)
  margin_rows=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_DP_MARGIN ')]
  pressure_rows=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_DP_RELATIVE_PRESSURE ')]
  final_rows=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_FINAL_PRESSURE ')]
  if arm=='C':assert not pressure_rows and not final_rows
  else:
   assert len(pressure_rows)==len(margin_rows)>0
   allowed_weights=collections.defaultdict(set)
   local_rows=collections.defaultdict(collections.deque)
   key_of=lambda r:tuple(int(r[k]) for k in ['net','pin','refresh','candidate'])
   for line in lines:
    if line.startswith('H3D_GUIDE_MARGIN '):
     r=dict(re.findall(r'(\w+)=(\S+)',line));local_rows[key_of(r)].append(r)
   for p,q in zip(pressure_rows,margin_rows):
    assert all(p[k]==q[k] for k in ['net','pin','refresh','candidate','base','exclusion'])
    local=local_rows[key_of(p)].popleft()
    base,alt,leaf=float(p['base']),float(p['exclusion']),float(p['leaf_cost'])
    assert math.isfinite(base) and math.isfinite(leaf) and leaf>=0 and leaf==float(local['chosen'])
    gap=alt-base
    raw=2. if not math.isfinite(alt) else 0. if gap<=0. else 2./(1.+leaf/gap)
    expected=struct.unpack('f',struct.pack('f',raw))[0]
    assert float(p['original'])==2. and math.isclose(float(p['applied']),expected,rel_tol=1e-8,abs_tol=1e-12)
    assert 0.<=float(p['applied'])<=2.
    allowed_weights[(int(p['net']),int(p['pin']),int(p['candidate']))].add(float(p['applied']))
   assert all(not q for q in local_rows.values())
   guides={(int(r['net']),int(r['pin'])):r for r in csv.DictReader((rd/'h3d_final_guides.csv').open())}
   final={(int(r['net']),int(r['pin'])):float(r['miss_weight']) for r in final_rows}
   assert len(final)==len(final_rows) and set(final)==set(guides)
   for key,w in final.items():
    assert 0.<=w<=2.
    if w<2.:
     preferred=[int(x) for x in guides[key]['preferred'].split(';') if x]
     assert len(preferred)==1 and w in allowed_weights[(*key,preferred[0])]
   assert 'VTR_ASSERT_LEVEL:STRING=2' in (B/'CMakeCache.txt').read_text()
   results[c][arm]['pressure_audit']=dict(passed=True,events=len(pressure_rows),zero_events=sum(float(r['applied'])==0. for r in pressure_rows),final_nominal_guides=len(final),final_zero_miss_weight=sum(w==0 for w in final.values()),final_positive_miss_weight=sum(w>0 for w in final.values()),final_pressure_min=min(final.values(),default=None),final_pressure_median=statistics.median(final.values()) if final else None,final_pressure_max=max(final.values(),default=None),scope='Relative pressure rule checked against paired DP/local-cost records with float32 rounding. Final saved weights below2 each match an earlier candidate-weight assignment; original2 remains allowed for unchanged fallback. Existing enabled assertions preserve all non-target guide fields including miss_weight; no claim of event causality or active search influence from nominal guide count.')
out=dict(passed=True,circuits=results,scope='Same initial tables/global scope, default-off C exactly reproduces Tf1. G changes only connection missweight using bounded relative shared-DP sensitivity, with no fitted threshold and no physical-confidence claim. Native/independent/finalguide audits and inputseal. Queries/trajectories may change subsequently. Final pressure separately audited, enabled non-target assertions preserve weights. Diagnostic time included; not formal speedup.',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'relative_pressure_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:{a:{k:v for k,v in r.items() if k!='rows'} for a,r in arms.items()} for c,arms in results.items()},indent=2))
