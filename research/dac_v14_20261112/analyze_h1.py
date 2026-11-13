#!/usr/bin/env python3
"""Circuit-balanced paired QoR and coverage; no timing ratios to historical runs."""
from pathlib import Path
import json,sys,math,collections,re
base=Path(sys.argv[1]); rows=json.loads((base/'observations.json').read_text())
index={(r['circuit'],r['arm']):r for r in rows};circuits=sorted({r['circuit'] for r in rows})
summary={'circuits':circuits,'seed':11,'family':'hybrid_o','flow':'p0','width':100,'status_counts':{},'paired':{},'timing_caveat':'Development times only; no ratio to historical timing; formal rotated repeats pending.'}
for arm in ['A0','R1','F','M']:
 summary['status_counts'][arm]=dict(collections.Counter(index.get((c,arm),{}).get('status','missing') for c in circuits))
for left,right in [('R1','F'),('R1','M'),('A0','M')]:
 pairs=[]
 for c in circuits:
  a=index.get((c,left),{});b=index.get((c,right),{})
  if a.get('status')=='legal' and b.get('status')=='legal':
   ac=a['metrics']['critical_path_ns'];bc=b['metrics']['critical_path_ns'];pairs.append({'circuit':c,'reference_ns':ac,'new_ns':bc,'improvement_pct':100*(1-bc/ac)})
 summary['paired'][left+'->'+right]={'pairs':pairs,'both_legal':len(pairs),'declared_circuits':len(circuits),'circuit_geomean_improvement_pct':100*(1-math.exp(sum(math.log(p['new_ns']/p['reference_ns']) for p in pairs)/len(pairs))) if pairs else None,'worst_improvement_pct':min((p['improvement_pct'] for p in pairs),default=None)}
lines=['# H1 开发集配对结果','',summary['timing_caveat'],'','每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。','','| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |','|---|---|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
 h3d=r.get('h3d',[]);planning=None
 for line in h3d:
  if line.startswith('H3D_PLAN '):planning=float(re.search(r'planning_seconds=([\d.]+)',line)[1])
 r['planning_seconds']=planning
 m=r['metrics'] if r['status']=='legal' else {};ph=r.get('physical_metrics') or {}
 lines.append(f"| {r['circuit']} | {r['arm']} | {r['status']} | {m.get('critical_path_ns','—')} | {m.get('iterations','—')} | {planning if planning is not None else '—'} | {r.get('process_seconds','—')} | {ph.get('sb_pair_net_occupancy','—')} | {ph.get('cb_crossing_output_source_net_occupancy','—')} |")
for comp,x in summary['paired'].items():lines.extend(['',f"{comp}: 双方合法 {x['both_legal']}/{x['declared_circuits']}；按电路CPD几何均值改善 {x['circuit_geomean_improvement_pct']}%；最差改善 {x['worst_improvement_pct']}%。"])
summary['observations']=rows
(base/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n');(base/'analysis.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
