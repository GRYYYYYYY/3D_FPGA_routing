#!/usr/bin/env python3
"""Validate phase accounting and behavior equivalence before interpreting cost."""
from pathlib import Path
import json,re,sys,math
D=Path(__file__).resolve().parent;B=Path(sys.argv[1]) if len(sys.argv)>1 else D/'profile_generation_dev_01'
reg=json.loads((B/'registration.json').read_text());rows=[]
def numbers(line):
 return {k:float(v) for k,v in re.findall(r'(\w+)=([0-9]+(?:\.[0-9]+)?)',line)}
for circuit in reg['circuits']:
 for arm in reg['arms']:
  rd=B/'runs'/f'{circuit}_{arm}';mfile=rd/'manifest.json'
  if not mfile.exists():continue
  m=json.loads(mfile.read_text())
  if m['status']!='completed':continue
  lines=(rd/'stdout.log').read_text().splitlines();last=lambda prefix:[x for x in lines if x.startswith(prefix)][-1]
  phases={mode:numbers(last('H3D_PLAN_PROFILE mode='+mode+' ')) for mode in ['initial','refresh']}
  parent=numbers(last('H3D_PLAN '));reach=numbers(last('H3D_REACH_PROFILE '))
  total=sum(v['total_seconds'] for v in phases.values())
  for mode,data in phases.items():
   summed=sum(v for k,v in data.items() if k.endswith('_seconds') and k!='total_seconds')
   assert abs(summed-data['total_seconds'])<1e-7,(mode,summed,data)
   assert all(math.isfinite(v) and v>=0 for v in data.values())
  assert sum(v['calls'] for v in phases.values())==parent['plans']
  assert reach['seconds']<=total+1e-6 and total<=parent['planning_seconds']+1e-6
  equivalence=rd/('equivalence.json' if arm=='F' else 'optimization_equivalence.json')
  assert json.loads(equivalence.read_text())['passed']
  storage_lines=[line for line in lines if line.startswith('H3D_SHARED_STORAGE ')]
  storage=numbers(storage_lines[-1]) if storage_lines else None
  if storage:assert storage['stored_words']<=4194304 and storage['stored_words']<=storage['logical_entries']
  view_lines=[line for line in lines if line.startswith('H3D_CLOSURE_VIEW ')]
  view=numbers(view_lines[-1]) if view_lines else None
  if view:assert view['endpoints']==reach['misses']
  timefile=rd/'time.txt';rss=re.search(r'Maximum resident set size \(kbytes\): (\d+)',timefile.read_text()) if timefile.exists() else None
  audit=rd/'independent_audit.json';final=rd/'final_guide_audit.json'
  audited=audit.exists() and final.exists() and json.loads(audit.read_text())['audit']['passed'] and json.loads(final.read_text())['passed']
  rows.append(dict(circuit=circuit,arm=arm,status='legal_audited' if audited else 'completed_pending_audit',cpd_ns=m['metrics']['critical_path_ns'],iterations=m['metrics']['iterations'],planning_seconds=parent['planning_seconds'],profile_total_seconds=total,phases=phases,closure_view=view,peak_rss_kib=int(rss[1]) if rss else None,closure_storage=storage,inclusive_reachability=reach,reach_fraction=reach['seconds']/total if total else None,process_seconds=m['wall_seconds'],equivalence=str(equivalence)))
result=dict(scope='Concurrent instrumented development phase attribution only. Closure time is inclusive and overlaps candidate phases, never add it to phase totals. Expected exact route/table/refresh/guide equivalence required. No formal speedup or generalization from one circuit.',rows=rows)
(B/'profile_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for r in rows:
 print(r['circuit'],r['arm'],r['status'],'plan',r['planning_seconds'],'closure',r['inclusive_reachability']['seconds'],'closure_fraction',round(r['reach_fraction'],4),'process',r['process_seconds'])
 print(' phases',r['phases'])
