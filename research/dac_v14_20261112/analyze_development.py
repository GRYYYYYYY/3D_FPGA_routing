#!/usr/bin/env python3
"""Circuit-balanced paired QoR and coverage; no timing ratios to historical runs."""
from pathlib import Path
import json,sys,math,collections,re
base=Path(sys.argv[1]); rows=json.loads((base/'observations.json').read_text()) if (base/'observations.json').exists() else []
registration=json.loads((base/'registration.json').read_text())
index={(r['circuit'],r['arm']):r for r in rows};circuits=list(registration['circuits'])
reference_arms=registration.get('reference_arms',['A0','R1'])
# Preserve the full registered population during partial completion as well.
for circuit in circuits:
    refpath=base/f'{circuit}_references.json'
    refs=json.loads(refpath.read_text()) if refpath.exists() else {}
    for arm in reference_arms+registration['arms']:
        if (circuit,arm) in index:continue
        if arm in refs:
            row=dict(circuit=circuit,arm=arm,**refs[arm])
        else:
            rd=base/'runs'/f'{circuit}_{arm}';mp=rd/'manifest.json'
            m=json.loads(mp.read_text()) if mp.exists() else {}
            status=m.get('status','missing')
            if status=='completed':status='completed_pending_audit'
            if status=='running':status='recorded_running'
            row=dict(circuit=circuit,arm=arm,status=status,metrics=m.get('metrics',{}),physical_metrics=None,path=str(rd),process_seconds=m.get('wall_seconds'))
        rows.append(row);index[circuit,arm]=row

# New runs become quality evidence only after their own batch input seal.
for row in rows:
 rd=Path(row['path']).resolve()
 if row['status']=='legal' and rd.is_relative_to(base.resolve().parent):
  seal=rd.parent.parent/'input_seal.json'
  if not seal.exists() or not json.loads(seal.read_text())['passed']:row['status']='legal_pending_batch_seal'

summary={'circuits':circuits,'seed':registration.get('seed',11),'family':registration.get('family','hybrid_o'),'flow':registration.get('flow','p0'),'width':registration.get('width',100),'status_counts':{},'paired':{},'timing_caveat':'Development times only; no ratio to historical timing; formal rotated repeats pending.'}
if (base/'attempt_review.json').exists():summary['attempt_review']=json.loads((base/'attempt_review.json').read_text())
arms=list(dict.fromkeys(reference_arms+registration['arms']))
for arm in arms:
 summary['status_counts'][arm]=dict(collections.Counter(index.get((c,arm),{}).get('status','missing') for c in circuits))
comparisons=([('R1','F')] if 'F' in arms else [])+[(ref,arm) for arm in registration['arms'] if arm!='F' for ref in [('F' if 'F' in arms else 'R1'),'A0']]
if 'U' in arms and 'O' in arms:comparisons.append(('U','O'))
if 'O' in arms and 'S' in arms:comparisons.append(('O','S'))
if 'U' in arms and 'S' in arms:comparisons.append(('U','S'))
if 'S' in arms and 'C' in arms:comparisons.append(('S','C'))
if 'U' in arms and 'C' in arms:comparisons.append(('U','C'))
if 'C' in arms and 'V' in arms:comparisons.append(('C','V'))
if 'U' in arms and 'V' in arms:comparisons.append(('U','V'))
if 'U' in arms and 'I' in arms:comparisons.append(('U','I'))
if 'U' in arms and 'B' in arms:comparisons.append(('U','B'))
for prior_arm in ['P','I']:
 if 'R' in arms and prior_arm in arms:comparisons.append(('R',prior_arm))
for action_arm in ['D','R','N','G','Z','T','B']:
 if 'V' in arms and action_arm in arms:comparisons.append(('V',action_arm))
if 'M' in arms and 'T' in arms:comparisons.append(('M','T'))
if 'T' in arms and 'Q' in arms:comparisons.append(('T','Q'))
if 'Q' in arms and 'E' in arms:comparisons.append(('Q','E'))
if 'E' in arms and 'P' in arms:comparisons.append(('E','P'))
if 'P' in arms and 'O' in arms:comparisons.append(('P','O'))
for right in ['Z','D','L','Cq','Bq','Rq','Sf','Ed','Pn','Hc','Tg','Eq']:
 if 'P' in arms and right in arms:comparisons.append(('P',right))
for left,right in [('A0','A1'),('F','F1'),('A1','F1'),('A1','U1'),('F1','U1'),('U','U1')]:
 if left in arms and right in arms:comparisons.append((left,right))
for left,right in [('A','A2'),('F','F2'),('U','U2'),('Uref','U2'),('A1','A2'),('F1','F2'),('U1','U2'),('A2','F2'),('A2','U2')]:
 if left in arms and right in arms:comparisons.append((left,right))
for left,right in [('F1','F1c'),('F2','S'),('A2','A3'),('F2','F3'),('U2','U3'),('A1','A3'),('F1','F3'),('U1','U3'),('A3','F3'),('A3','U3')]:
 if left in arms and right in arms:comparisons.append((left,right))
for left,right in [('Ed','En'),('Pn','En'),('Hc','Tg'),('U','Pl'),('V','Pl'),('U','Xp'),('V','Xp'),('U','Tf'),('V','Tf'),('C','Df'),('Tf','O'),('C','Ri'),('Tf','Ri'),('C1','Tf1'),('U1','Tf1'),('A1','Tf1'),('F1','Tf1'),('A1','W0'),('A1','W1'),('Tf1','W1'),('U1','W1'),('C','Z'),('Tf1','Z'),('W1','Z'),('A1','Z'),('U1','Z'),('C','G'),('Tf1','G'),('W1','G'),('A1','G'),('Z','G'),('A1','H'),('W1','H'),('Z','H'),('Tf1','H'),('F','V'),('F','Tf'),('A1','Tf')]:
 if left in arms and right in arms:comparisons.append((left,right))
diagnostic_arms=set()
for arm in registration['arms']:
 manifests=[base/'runs'/f'{c}_{arm}'/'manifest.json' for c in circuits]
 available=[json.loads(p.read_text()) for p in manifests if p.exists()]
 if available and all(m.get('tags',{}).get('diagnostic_only',False) for m in available):diagnostic_arms.add(arm)
for left,right in comparisons:
 pairs=[]
 for c in circuits:
  a=index.get((c,left),{});b=index.get((c,right),{})
  if a.get('status')=='legal' and b.get('status')=='legal':
   ac=a['metrics']['critical_path_ns'];bc=b['metrics']['critical_path_ns'];pairs.append({'circuit':c,'reference_ns':ac,'new_ns':bc,'improvement_pct':100*(1-bc/ac)})
 summary['paired'][left+'->'+right]={'comparison_role':'transaction_diagnostic_not_method_benefit' if right in ['X','X2'] else 'accuracy_or_assignment_diagnostic' if right in ['Ed','En','Pn'] else 'mechanism_diagnostic_not_method_benefit' if right in diagnostic_arms else 'method_or_reproduction','pairs':pairs,'both_legal':len(pairs),'declared_circuits':len(circuits),'circuit_geomean_improvement_pct':100*(1-math.exp(sum(math.log(p['new_ns']/p['reference_ns']) for p in pairs)/len(pairs))) if pairs else None,'worst_improvement_pct':min((p['improvement_pct'] for p in pairs),default=None)}
lines=['# 独立机制开发集配对结果','',summary['timing_caveat'],'','每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。','','| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |','|---|---|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
 h3d=r.get('h3d',[]);planning=None
 for line in h3d:
  if line.startswith('H3D_PLAN '):planning=float(re.search(r'planning_seconds=([\d.]+)',line)[1])
 r['planning_seconds']=planning
 m=r['metrics'] if r['status']=='legal' else {};ph=r.get('physical_metrics') or {}
 lines.append(f"| {r['circuit']} | {r['arm']} | {r['status']} | {m.get('critical_path_ns','—')} | {m.get('iterations','—')} | {planning if planning is not None else '—'} | {r.get('process_seconds','—')} | {ph.get('sb_pair_net_occupancy','—')} | {ph.get('cb_crossing_output_source_net_occupancy','—')} |")
for comp,x in summary['paired'].items():lines.extend(['',f"{comp} ({x['comparison_role']}): 双方合法 {x['both_legal']}/{x['declared_circuits']}；按电路CPD几何均值改善 {x['circuit_geomean_improvement_pct']}%；最差改善 {x['worst_improvement_pct']}%。"])
table_checks={}
for circuit in circuits:
    def tables(arm):
        return [line for line in index.get((circuit,arm),{}).get('h3d',[]) if line.startswith('H3D_TABLE ')]
    for arm in ['H','N']:
        if 'F' not in arms or arm not in arms:continue
        a,b=tables('F'),tables(arm)
        table_checks[circuit+' F/'+arm]={'reference_count':len(a),'variant_count':len(b),'exact_sequence_equal':bool(a) and a==b,'first_mismatch':next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)}
summary['table_fingerprint_diagnostics']=table_checks
lines.extend(['','候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：', '', '```json',json.dumps(table_checks,indent=2),'```'])
summary['observations']=rows
(base/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n');(base/'analysis.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
