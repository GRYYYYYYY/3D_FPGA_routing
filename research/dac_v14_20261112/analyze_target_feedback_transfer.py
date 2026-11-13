#!/usr/bin/env python3
"""Audit active-target refresh applicability and native correctness, not causal QoR claims."""
from pathlib import Path
import json,re,sys,hashlib
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());results={}
def body(p):
 t=p.read_text();return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
def initial(lines):
 out=[]
 for l in lines:
  if l.startswith('H3D_PLAN '):break
  if l.startswith('H3D_TABLE '):out.append(l)
 return out
for c in reg['circuits']:
 results[c]={};control=B/'runs'/f'{c}_V';base=(control/'stdout.log').read_text().splitlines()
 assert json.loads((B/'runs'/f'{c}_F/static_reproduction.json').read_text())['passed']
 for arm in ['V','Tf']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text());env=m['environment']
  legal=m['status']=='completed'
  audit=None
  if legal:
   audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed'] and m['metrics']['native_full_check_passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
  assert env['VPR_H3D_TARGET_FEEDBACK']==('0' if arm=='V' else '1')
  assert env['VPR_H3D_TRACE_UPDATE_PINS']==env['VPR_H3D_FEEDBACK']=='1'
  for key in ['VPR_H3D_PLANAR_FEEDBACK','VPR_H3D_EXIT_PRICE','VPR_H3D_MIXED_DELAY','VPR_H3D_TIMING_GUIDE','VPR_H3D_EQUIVALENT_GUIDES','VPR_H3D_TARGET_DELAY','VPR_H3D_LAYER_BB_DELAYED','VPR_H3D_ALL_LAYER_BB']:
   assert float(env[key])==0
  lines=(rd/'stdout.log').read_text().splitlines();rows=[];refresh=None;target_events=[]
  if not any(l.startswith('H3D_FINAL ') for l in lines):
   assert not legal
   results[c][arm]=dict(status=m['status'],mechanism_status='incomplete_terminal_trace',process_seconds=m.get('wall_seconds'));continue
  for l in lines:
   if l.startswith('H3D_REFRESH '):refresh=dict(re.findall(r'(\w+)=(\S+)',l))
   if l.startswith('H3D_TARGET_REFRESH '):
    r={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)};assert r['targets']>=0 and r['preserved']>=0;target_events.append(r)
   if l.startswith('H3D_UPDATE_PIN '):
    r=dict(x.split('=',1) for x in l.split()[1:]);r.update({k:int(r[k]) for k in ['net','iter','pin','retained','targeted']})
    assert refresh and refresh['accepted']=='1' and int(refresh['net'])==r['net'] and int(refresh['iter'])==r['iter']
    assert r['old']!=r['new'] and not(r['retained'] and r['targeted'])
    if arm!='V':assert r['targeted']==1 and r['retained']==0
    rows.append(r)
  counters={}
  for prefix in ['H3D_UPDATE_PINS_SUMMARY ','H3D_FEEDBACK ','H3D_DELAY ','H3D_FINAL ']:
   r=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith(prefix)][-1];counters[prefix.strip()]=r
  summary=counters['H3D_UPDATE_PINS_SUMMARY'];assert int(summary['records'])==len(rows) and int(summary['retained'])==sum(r['retained'] for r in rows) and int(summary['targeted'])==sum(r['targeted'] for r in rows)
  assert len(target_events)==(0 if arm=='V' else int(counters['H3D_FEEDBACK']['attempts']))
  assert initial(lines)==initial(base)
  assert int(counters['H3D_FINAL']['guide_rollbacks'])==0
  assert int(counters['H3D_FINAL']['success'])==int(legal)
  metrics=dict(m['metrics']);provisional=None
  if not legal:provisional=metrics.get('critical_path_ns');metrics['critical_path_ns']=None
  results[c][arm]=dict(status='legal' if legal else m['status'],mechanism_status='complete_terminal_trace_verified',metrics=metrics,failed_provisional_cpd_ns=provisional,physical_metrics=audit['physical_metrics'] if audit else None,counters=counters,initial_tables=len(initial(lines)),initial_equal_V=initial(lines)==initial(base),same_route_as_V=body(rd/'routed.route')==body(control/'routed.route'),same_final_guides=(rd/'h3d_final_guides.csv').read_bytes()==(control/'h3d_final_guides.csv').read_bytes(),changed_preferences=len(rows),changed_retained=sum(r['retained'] for r in rows),changed_targeted=sum(r['targeted'] for r in rows),target_refresh_calls=len(target_events),target_pin_events=sum(r['targets'] for r in target_events),preserved_pin_events=sum(r['preserved'] for r in target_events),planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'],rows=rows)
 for arm in ['F','A1']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text())
  assert m['environment']['VPR_H3D_FEEDBACK']=='0'
  if arm=='A1':assert m['environment']['VPR_H3D_MODE']=='off' and m['environment']['VPR_H3D_ALL_LAYER_BB']=='1'
  else:assert m['environment']['VPR_H3D_ALL_LAYER_BB']=='0'
  if m['status']!='completed':
   metrics=dict(m.get('metrics',{}));provisional=metrics.get('critical_path_ns');metrics['critical_path_ns']=None
   results[c][arm]=dict(status=m['status'],metrics=metrics,failed_provisional_cpd_ns=provisional,process_seconds=m.get('wall_seconds'));continue
  audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed'] and m['metrics']['native_full_check_passed']
  if arm=='F':assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
  results[c][arm]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],process_seconds=m['wall_seconds'])
out=dict(passed=True,circuits=results,scope='Fixed-parameter seed21 new-circuit transfer. F reproduces frozen R1 including failed terminal route. V/Tf share original scope; A1 initial-global native control is a distinct scope. Initial finite tables identical, including empty tables. Every accepted changed preference is an actual native target for Tf; production assertions preserve non-target fields and generation criticality. Legal runs require native/independent/guide audits as applicable and input seal. Failed terminal traces are mechanism diagnostics only; provisional CPD excluded from legal metrics. Development timing only.',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'target_feedback_transfer_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:{a:{k:v for k,v in r.items() if k!='rows'} for a,r in arms.items()} for c,arms in results.items()},indent=2))
