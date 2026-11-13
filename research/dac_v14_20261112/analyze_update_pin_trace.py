#!/usr/bin/env python3
"""Accepted guide changes versus native targets and retained sinks; exact decision-neutral controls."""
from pathlib import Path
import collections,csv,json,re,sys,hashlib
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());results={}
for c in reg['circuits']:
 results[c]={}
 for arm in reg['arms']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text());assert m['status']=='completed' and m['metrics']['native_full_check_passed']
  assert json.loads((rd/'independent_audit.json').read_text())['audit']['passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
  assert json.loads((rd/'pin_trace_equivalence.json').read_text())['passed']
  assert m['environment']['VPR_H3D_TRACE_UPDATE_PINS']=='1'
  rows=[];refresh=None
  for l in (rd/'stdout.log').read_text().splitlines():
   if l.startswith('H3D_REFRESH '):refresh=dict(re.findall(r'(\w+)=(\S+)',l))
   elif l.startswith('H3D_UPDATE_PIN '):
    r=dict(x.split('=',1) for x in l.split()[1:]);r.update({k:int(r[k]) for k in ['net','iter','pin','retained','targeted']});r['criticality']=float(r['criticality'])
    assert refresh and refresh['accepted']=='1' and int(refresh['net'])==r['net'] and int(refresh['iter'])==r['iter']
    assert r['old']!=r['new'] and 0<=r['criticality']<=1 and r['retained'] in [0,1] and r['targeted'] in [0,1] and not (r['retained'] and r['targeted'])
    rows.append(r)
   elif l.startswith('H3D_UPDATE_PINS_SUMMARY '):summary={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)}
  assert summary['enabled']==1 and summary['records']==len(rows) and summary['retained']==sum(r['retained'] for r in rows) and summary['targeted']==sum(r['targeted'] for r in rows)
  types={}
  for kind,selected in [('cleared',[r for r in rows if not r['new']]),('newly_guided',[r for r in rows if not r['old']]),('reassigned',[r for r in rows if r['old'] and r['new']])]:
   types[kind]=dict(total=len(selected),retained=sum(r['retained'] for r in selected),targeted=sum(r['targeted'] for r in selected),neither=sum(not r['retained'] and not r['targeted'] for r in selected))
  final={(int(g['net']),int(g['pin'])):g for g in csv.DictReader((rd/'h3d_final_guides.csv').open())}
  unadopted=[]
  for key,g in final.items():
   if g['adopted']!='0':continue
   matches=[r for r in rows if (r['net'],r['pin'])==key and r['new']==g['preferred']]
   unadopted.append(dict(net=key[0],pin=key[1],preferred=g['preferred'],matching_updates=len(matches),matching_retained=sum(r['retained'] for r in matches),matching_targeted=sum(r['targeted'] for r in matches)))
  results[c][arm]=dict(metrics=m['metrics'],summary=summary,types=types,unique_changed_connections=len({(r['net'],r['pin']) for r in rows}),final_unadopted=unadopted,rows=rows,scope='Direct native remaining-target membership and post-prune tree sink presence, immutable diagnostic observations. Matching final-preference events need not identify the exact saved-best snapshot version; all matching events reported. No force-reroute or causal performance claim.')
out=dict(passed=True,circuits=results,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'update_pin_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:{a:{k:v for k,v in r.items() if k not in ['rows','final_unadopted']} for a,r in arms.items()} for c,arms in results.items()},indent=2))
