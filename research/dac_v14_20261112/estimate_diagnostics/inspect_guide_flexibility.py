#!/usr/bin/env python3
"""Retrospective applicability of measured no-slower, no-pricier alternatives; no QoR claim."""
from pathlib import Path
import csv,json,hashlib,collections
D=Path(__file__).resolve().parents[1];O=D/'estimate_oracle_01';assert json.loads((O/'input_seal.json').read_text())['passed']
records={}
for r in csv.DictReader((O/'estimates.csv').open()):
 if r['run'].endswith('_P') and r['phase'] in ['table','selected']:
  records[r['run'],int(r['net']),int(r['pin']),int(r['candidate'])]=r
result={}
for c in ['spmv','eltwise_layer']:
 rd=D/'source_floor_dev_01/runs'/f'{c}_P';rows=list(csv.DictReader((rd/'h3d_final_guides.csv').open()));selected={(int(r['net']),int(r['pin'])):int(r['preferred'].strip(';')) for r in rows};alternatives=collections.defaultdict(list);known=0
 for (run,net,pin,candidate),r in records.items():
  if run!=c+'_P' or candidate==selected[net,pin]:continue
  ref=records[run,net,pin,selected[net,pin]]
  if not all(x[k]=='1' for x in [r,ref] for k in ['source_known','sink_known']):continue
  delay=float(r['source_value'])+float(r['sink_value']);reference=float(ref['source_value'])+float(ref['sink_value'])
  charge=float(r['opening'])-float(r['source_value']);refcharge=float(ref['opening'])-float(ref['source_value'])
  known+=1
  if delay<=reference+.02 and charge<=refcharge+1.e-10:
   alternatives[net,pin].append(dict(candidate=candidate,chosen=selected[net,pin],delay_units=delay,chosen_units=reference,charge=charge,chosen_charge=refcharge,strictly_faster=delay<reference-.02))
 result[c]=dict(guided_connections=len(rows),fully_measured_comparable_pairs=known,eligible_connections=len(alternatives),eligible_alternatives=sum(map(len,alternatives.values())),faster=sum(r['strictly_faster'] for a in alternatives.values() for r in a),histogram=dict(collections.Counter(map(len,alternatives.values()))),cases={f'{k[0]}/{k[1]}':v for k,v in alternatives.items()})
out=dict(scope='Offline applicability only from preexisting P candidate tables, no new queries or outcome-conditioned subset. Both chosen/alternative require two exact sides. Total graph-delay gap <=.02unit and alternative negotiated opening charge<=chosen; actual STA and global congestion remain unproven.',circuits=result,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),O/'input_seal.json',O/'estimates.csv']})
(D/'estimate_diagnostics/guide_flexibility_applicability.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:{k:v for k,v in r.items() if k!='cases'} for c,r in result.items()},indent=2))
