#!/usr/bin/env python3
"""Verify exact membership optimization and report paired development costs without speedup claims."""
from pathlib import Path
import json,re,sys,hashlib
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());rows=[]
def logs(rd):
 lines=(rd/'stdout.log').read_text().splitlines();out={}
 for prefix in ['H3D_PLAN ','H3D_DELAY ','H3D_FEEDBACK ','H3D_UPDATE_PINS_SUMMARY ','H3D_FINAL ']:
  selected=[l for l in lines if l.startswith(prefix)];assert selected;out[prefix.strip()]=dict(re.findall(r'(\w+)=(\S+)',selected[-1]))
 out['profiles']={}
 for l in lines:
  if l.startswith('H3D_PLAN_PROFILE '):
   r=dict(re.findall(r'(\w+)=(\S+)',l));out['profiles'][r['mode']]=r
 return out
for c in reg['circuits']:
 rd=B/'runs'/f'{c}_O';refs=json.loads((B/f'{c}_references.json').read_text());prior=Path(refs['Tf']['path']);m=json.loads((rd/'manifest.json').read_text());pm=json.loads((prior/'manifest.json').read_text())
 if m['status']!='completed':rows.append(dict(circuit=c,status=m['status']));continue
 assert m['metrics']['native_full_check_passed'] and json.loads((rd/'independent_audit.json').read_text())['audit']['passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
 assert json.loads((rd/'target_membership_equivalence.json').read_text())['passed']
 a,b=logs(prior),logs(rd)
 for key in ['H3D_PLAN','H3D_DELAY','H3D_FEEDBACK','H3D_UPDATE_PINS_SUMMARY','H3D_FINAL']:
  filtered=lambda r:{k:v for k,v in r.items() if not k.endswith('_seconds')}
  assert filtered(a[key])==filtered(b[key]),(c,key)
 for mode in ['initial','refresh']:assert a['profiles'][mode]['calls']==b['profiles'][mode]['calls']
 rows.append(dict(circuit=c,status='legal',metrics=m['metrics'],physical_metrics=json.loads((rd/'independent_audit.json').read_text())['physical_metrics'],reference=str(prior),optimized=str(rd),reference_counters=a,optimized_counters=b,planning_seconds=[float(a['H3D_PLAN']['planning_seconds']),float(b['H3D_PLAN']['planning_seconds'])],process_seconds=[pm['wall_seconds'],m['wall_seconds']]))
out=dict(passed=all(r['status']=='legal' for r in rows),scope='Matched sealedTf controls; fullroute/table/refresh/guide/query/pinchange equality plus final counters excludingseconds, independent legality/guideaudit and seal. Times are development observations under concurrent workloads, not formal speedup.',rows=rows,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'target_membership_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({r['circuit']:{k:v for k,v in r.items() if k in ['status','planning_seconds','process_seconds']} for r in rows},indent=2))
