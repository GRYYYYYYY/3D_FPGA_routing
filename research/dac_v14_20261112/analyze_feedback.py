#!/usr/bin/env python3
"""Check selective-refresh accounting and report paired final guide adoption."""
from pathlib import Path
import csv,json,re,sys,math
D=Path(__file__).resolve().parent
B=Path(sys.argv[1]) if len(sys.argv)>1 else D/'feedback_dev_01'
reg=json.loads((B/'registration.json').read_text());results={}
def counters(line):return {k:float(v) if '.' in v else int(v) for k,v in re.findall(r'(\w+)=([\d.]+)',line)}
def read_arm(circuit,arm):
 rd=B/'runs'/f'{circuit}_{arm}'
 if not (rd/'final_guide_audit.json').exists():return None
 audit=json.loads((rd/'final_guide_audit.json').read_text());assert audit['passed']
 lines=(rd/'stdout.log').read_text().splitlines();feedback=counters([x for x in lines if x.startswith('H3D_FEEDBACK ')][-1]);final=counters([x for x in lines if x.startswith('H3D_FINAL ')][-1]);planning=counters([x for x in lines if x.startswith('H3D_PLAN ')][-1]);rows=list(csv.DictReader((rd/'h3d_final_guides.csv').open()))
 updates=[];clear=None;last={}
 for line in lines:
  if line.startswith('H3D_REFRESH_CLEAR '):clear=int(re.search(r'net=(\d+)',line)[1])
  if not line.startswith('H3D_REFRESH '):continue
  m=re.search(r'net=(\d+) iter=(\d+) accepted=(\d+) old_cost=([^ ]+) new_cost=([^ ]+)',line);assert m
  net,it,accepted=map(int,m.group(1,2,3));old,new=map(float,m.group(4,5));is_clear=net==clear;clear=None
  if arm!='X' and net in last:assert it-last[net]>=3,(net,it,last[net])
  last[net]=it
  # Printed costs have six significant digits: allow rounding at the margin.
  if accepted and not is_clear and math.isfinite(old):assert new <= old*.95001,(old,new)
  updates.append(dict(net=net,iteration=it,accepted=bool(accepted),deactivation=is_clear,prior_finite=math.isfinite(old),equal_finite_cost=math.isfinite(old) and math.isfinite(new) and old==new))
 assert len(updates)==feedback['attempts'] and sum(x['accepted'] for x in updates)==feedback['accepted']
 assert feedback['checks']==feedback['skipped']+feedback['attempts']
 if arm=='F':assert feedback['attempts']==0 and final['guide_rollbacks']==0
 if arm=='X':assert final['guide_rollbacks']>=1
 return dict(summary=dict(feedback=feedback,final=final,planning=planning,deactivations=sum(x['accepted'] and x['deactivation'] for x in updates),finite_cost_accepted=sum(x['accepted'] and not x['deactivation'] and x['prior_finite'] for x in updates),incomplete_prior_accepted=sum(x['accepted'] and not x['deactivation'] and not x['prior_finite'] for x in updates),finite_equal_rejections=sum(not x['accepted'] and x['equal_finite_cost'] for x in updates),role='forced_rollback_diagnostic_not_method_benefit' if arm=='X' else 'method'),rows={(int(r['net']),int(r['pin'])):r for r in rows})
for circuit in reg['circuits']:
 arms={a:r for a in reg['arms'] if (r:=read_arm(circuit,a)) is not None}
 result={'arms':{a:r['summary'] for a,r in arms.items()},'paired_adoption':{}}
 if 'F' in arms:
  old=arms['F']['rows']
  for arm in reg['arms']:
   if arm=='F':continue
   if arm not in arms:continue
   new=arms[arm]['rows'];common=set(old)&set(new)
   assert all(old[k]['source']==new[k]['source'] and old[k]['sink']==new[k]['sink'] for k in common)
   result['paired_adoption'][arm]=dict(common_guided_pins=len(common),newly_guided=len(set(new)-set(old)),no_longer_guided=len(set(old)-set(new)),reference_adopted=sum(int(old[k]['adopted']) for k in common),variant_adopted=sum(int(new[k]['adopted']) for k in common),lost_adoption=sum(old[k]['adopted']=='1' and new[k]['adopted']=='0' for k in common),gained_adoption=sum(old[k]['adopted']=='0' and new[k]['adopted']=='1' for k in common))
 results[circuit]=result
(B/'feedback_mechanisms.json').write_text(json.dumps({'scope':'Only arms with completed independent final-guide audits. Common-pin adoption is paired; overall counts have different guided-pin populations. Planned criticality is not final STA. X is a transaction diagnostic, never algorithm QoR evidence.','circuits':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
