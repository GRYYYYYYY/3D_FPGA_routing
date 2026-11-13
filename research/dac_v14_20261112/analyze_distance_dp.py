#!/usr/bin/env python3
"""Same input/table/query-state checks, assignment-only route and guide differences."""
from pathlib import Path
import csv,hashlib,json,re,sys
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def body(p):
 t=p.read_text();return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
def guides(p):return {(r['net'],r['pin']):r['preferred'] for r in csv.DictReader(p.open())}
rows={}
for c in reg['circuits']:
 rows[c]={};refs=json.loads((B/f'{c}_references.json').read_text())
 for a,base in [('Pn','P'),('En','Ed')]:
  rd=B/'runs'/f'{c}_{a}';m=json.loads((rd/'manifest.json').read_text());prior=Path(refs[base]['path']);pm=json.loads((prior/'manifest.json').read_text());e=m['environment'];pe=pm['environment']
  assert {k:v for k,v in e.items() if k!='VPR_H3D_ASSIGNMENT'}=={k:v for k,v in pe.items() if k!='VPR_H3D_ASSIGNMENT'}
  assert e['VPR_H3D_ASSIGNMENT']=='independent' and pe['VPR_H3D_ASSIGNMENT']=='shared'
  assert json.loads((rd/'same_table_gate.json').read_text())['passed']
  audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed']
  assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
  p,q=guides(prior/'h3d_final_guides.csv'),guides(rd/'h3d_final_guides.csv');assert p.keys()==q.keys()
  log=(rd/'stdout.log').read_text();p_sec=float(re.findall(r'H3D_PLAN .*planning_seconds=([0-9.]+)',log)[-1])
  rows[c][a]=dict(status='legal',reference=base,metrics=m['metrics'],reference_metrics=pm['metrics'],physical_metrics=audit['physical_metrics'],same_route_body=body(prior/'routed.route')==body(rd/'routed.route'),guide_connections=len(p),changed_guides=sum(p[k]!=q[k] for k in p),planning_seconds=p_sec,process_seconds=m['wall_seconds'])
(B/'distance_dp_mechanisms.json').write_text(json.dumps(dict(passed=True,circuits=rows,scope='Identical complete candidate-table fingerprint sequence and distinct/final cumulative query states. Static logging repeats per route iteration; differing repetition counts are legitimate. Reused three native runs after verifier correction; only missing fourth run launched. Diagnostic only; not a production increased-budget method.',script_sha256=sha(Path(__file__)),seal_sha256=sha(B/'input_seal.json')),indent=2)+'\n');print(json.dumps(rows,indent=2))
