#!/usr/bin/env python3
"""Verify permitted guide expansions against sealed tables and independent graph distances."""
from pathlib import Path
import csv,json,math,re,sys,hashlib
B=Path(sys.argv[1]).resolve();D=B.parent;O=D/'estimate_oracle_01'
assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text())
app=json.loads((D/'estimate_diagnostics/guide_flexibility_applicability.json').read_text())
exact={(int(r['endpoint']),int(r['reverse']),int(r['target'])):float(r['seconds']) for r in csv.DictReader((O/'exact.csv').open())}
units={}
for r in csv.DictReader((O/'estimates.csv').open()):
 if r['run'].endswith('_P'):units[r['run']]=float(r['unit'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def body(p):
 t=p.read_text();return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
rows={}
for c in reg['circuits']:
 rows[c]={};control=B/'runs'/f'{c}_P'
 assert json.loads((control/'equivalent_control_equivalence.json').read_text())['passed']
 original={(int(g['net']),int(g['pin'])):g for g in csv.DictReader((control/'h3d_final_guides.csv').open())}
 eligible={tuple(map(int,k.split('/'))):{r['candidate']:r for r in v} for k,v in app['circuits'][c]['cases'].items()}
 for arm in reg['arms']:
  p=B/'runs'/f'{c}_{arm}';m=json.loads((p/'manifest.json').read_text())
  if m['status']!='completed':rows[c][arm]=dict(status=m['status']);continue
  audit=json.loads((p/'independent_audit.json').read_text());assert audit['audit']['passed'] and m['metrics']['native_full_check_passed'];assert json.loads((p/'final_guide_audit.json').read_text())['passed']
  if arm!='P':assert json.loads((p/'same_planning_gate.json').read_text())['passed']
  env=m['environment'];assert env['VPR_H3D_EQUIVALENT_GUIDES']==('4' if arm=='Eq' else '0')
  assert env['VPR_H3D_TIMING_GUIDE']==env['VPR_H3D_FEEDBACK']=='0'
  assert env['VPR_H3D_DELAY_BUDGET']=='4096' and env['VPR_H3D_TARGET_QUOTA']=='256'
  lines=(p/'stdout.log').read_text().splitlines();actual={}
  for l in lines:
   if not l.startswith('H3D_EQUIVALENT_GUIDE '):continue
   r=dict(x.split('=') for x in l.split()[1:]);key=int(r['net']),int(r['pin']);node=int(r['alternative']);chosen=int(r['chosen']);assert (key,node) not in actual;actual[key,node]=r
   assert arm=='Eq' and node in eligible[key] and original[key]['preferred']==str(chosen)+';'
   ref=eligible[key][node];assert ref['chosen']==chosen
   for field,k in [('chosen_delay_units','chosen_units'),('alternative_delay_units','delay_units'),('chosen_charge','chosen_charge'),('alternative_charge','charge')]:assert math.isclose(float(r[field]),ref[k],rel_tol=1.e-10,abs_tol=1.e-10)
   g=original[key];src,sink=int(g['source']),int(g['sink']);unit=units[c+'_P']
   for node_id,field in [(chosen,'chosen_delay_units'),(node,'alternative_delay_units')]:
    truth=(exact[src,0,node_id]+exact[sink,1,node_id])/unit
    assert math.isclose(float(r[field]),truth,rel_tol=1.e-10,abs_tol=1.e-10)
  guides={(int(g['net']),int(g['pin'])):g for g in csv.DictReader((p/'h3d_final_guides.csv').open())};assert guides.keys()==original.keys()
  added_use=0;any_added=0
  for key,g in guides.items():
   prior={int(v) for v in original[key]['preferred'].split(';') if v};accepted={int(v) for v in g['preferred'].split(';') if v};observed={node for k,node in actual if k==key}
   assert accepted==prior|observed and len(accepted)<=4
   want=min(3,len(eligible.get(key,{}))) if arm=='Eq' else 0
   assert len(observed)==want
   crossings={int(v) for v in g['actual_crossings'].split(';') if v};added_use+=bool((accepted-prior)&crossings);any_added+=bool(observed)
  summaries=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_EQUIVALENT_GUIDES ')]
  assert int(summaries[-1]['added'])==len(actual) and int(summaries[-1]['pins'])==any_added
  rows[c][arm]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],expanded_connections=any_added,added_alternatives=len(actual),final_connections_using_added_alternative=added_use,same_route_as_P=body(p/'routed.route')==body(control/'routed.route'),planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'])
out=dict(passed=True,circuits=rows,scope='Exact P controls and unchanged pre-output table/query states; every actual expanded resource independently checked against sealed two-sided measured eligibility, graph oracle distances and no-higher opening charge. Primary selected crossing retained, caps checked, final adoption independently audited. Local equivalence not global timing proof; development timing only.',bindings={str(p):sha(p) for p in [Path(__file__),B/'input_seal.json',O/'input_seal.json',O/'exact.csv',D/'estimate_diagnostics/guide_flexibility_applicability.json']})
(B/'equivalent_guides_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
