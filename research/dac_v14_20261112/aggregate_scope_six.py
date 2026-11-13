#!/usr/bin/env python3
"""Uniform six-circuit scope/guide comparisons; missing and failed roles stay declared."""
from pathlib import Path
import collections,hashlib,json,math
D=Path(__file__).resolve().parent
circuits=['spmv','softmax','eltwise_layer','attention_layer','bnn','gemm_layer']
roles=['A0','R1','U','A1','F1','U1','A3','F3','U3'];rows=[];binding={}
def read(p):
 data=Path(p).read_bytes();binding[str(p)]=hashlib.sha256(data).hexdigest();return json.loads(data)
def norm(command):
 x=list(command[1:])
 for opt in ['--net_file','--place_file','--route_file']:x[x.index(opt)+1]='<paired-private-file>'
 return x
for c in circuits:
 first=D/('layer_bbox_dev_01' if c in ['eltwise_layer','attention_layer'] else 'layer_bbox_expansion_dev_01')
 later=D/('delayed_layer_dev_01' if c=='eltwise_layer' else 'delayed_attention_dev_01' if c=='attention_layer' else 'delayed_scope_expansion_dev_01')
 if c=='gemm_layer':first=later=D/'scope_gemm_dev_01'
 refs=read(first/f'{c}_references.json')
 paths={a:Path(refs[a]['path']) for a in ['A0','R1']}
 feedback='feedback_expansion_01' if c in ['eltwise_layer','attention_layer'] else 'feedback_bnn_dev_01' if c=='bnn' else 'feedback_dev_01'
 paths['U']=Path(refs['U']['path']) if c=='gemm_layer' else D/feedback/'runs'/f'{c}_U'
 paths.update({a:first/'runs'/f'{c}_{a}' for a in ['A1','F1','U1']})
 paths.update({a:later/'runs'/f'{c}_{a}' for a in ['A3','F3','U3']})
 base=read(paths['R1']/'manifest.json')
 physical=[base['command'][1],base['command'][2],base['command'][base['command'].index('--read_rr_graph')+1]]
 for role,rd in paths.items():
  if not (rd/'manifest.json').exists():rows.append(dict(circuit=c,arm=role,status='missing_or_pending',path=str(rd)));continue
  m=read(rd/'manifest.json');assert norm(m['command'])==norm(base['command'])
  for p in physical:assert m['shared_inputs'][p]['sha256']==base['shared_inputs'][p]['sha256']
  for f in ['packed.net','placed.place']:
   if f in m.get('outputs',{}):assert m['outputs'][f]['sha256']==base['outputs'][f]['sha256']
  env=m['environment']
  assert env.get('VPR_H3D_ALL_LAYER_BB','0')==('1' if role in ['A1','F1','U1'] else '0')
  assert env.get('VPR_H3D_LAYER_BB_DELAYED','0')==('1' if role in ['A3','F3','U3'] else '0')
  assert env.get('VPR_H3D_LAYER_BB_FEEDBACK','0')=='0'
  assert env.get('VPR_H3D_FEEDBACK','0')==('1' if role in ['U','U1','U3'] else '0')
  for flag in ['VPR_H3D_MIXED_DELAY','VPR_H3D_TARGET_FRONTIER','VPR_H3D_SOURCE_QUERY_SHARE','VPR_H3D_QUERY_CRITICALITY_ORDER']:
   assert env.get(flag,'0')=='0'
  assert float(env.get('VPR_H3D_TIMING_GUIDE','0'))==0
  if role in ['A0','A1','A3']:assert env.get('VPR_H3D_MODE','off')=='off'
  else:
   for k,v in {'VPR_H3D_MODE':'static','VPR_H3D_CANDIDATES':'16','VPR_H3D_DELAY_BUDGET':'4096','VPR_H3D_MIN_CRITICALITY':'0.7','VPR_H3D_OPENING_WEIGHT':'16','VPR_H3D_MISS_WEIGHT':'2'}.items():assert env[k]==v,(c,role,k,env.get(k))
  status=m['status'];audit=read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
  sealed=role in ['A0','R1'] or ((rd.parent.parent/'input_seal.json').exists() and read(rd.parent.parent/'input_seal.json')['passed'])
  guide=role in ['A0','R1','A1','A3'] or ((rd/'final_guide_audit.json').exists() and read(rd/'final_guide_audit.json')['passed'])
  if status=='completed':status='legal' if m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed'] and sealed and guide else 'completed_pending_audit_or_seal'
  if status=='running':status='recorded_running'
  rows.append(dict(circuit=c,arm=role,status=status,metrics=m.get('metrics') or {},physical_metrics=audit.get('physical_metrics') if audit else None,path=str(rd),environment=env,process_seconds=m.get('wall_seconds')))
index={(r['circuit'],r['arm']):r for r in rows};comparisons={}
for left,right in [('A0','R1'),('A0','U'),('A1','F1'),('A1','U1'),('A3','F3'),('A3','U3'),('R1','F1'),('R1','F3'),('U','U1'),('U','U3'),('A0','A1'),('A0','A3'),('A1','A3'),('F1','F3'),('U1','U3')]:
 pairs=[];recoveries=[];lost=[]
 for c in circuits:
  a,b=index[c,left],index[c,right]
  if a['status']==b['status']=='legal':
   ac,bc=a['metrics']['critical_path_ns'],b['metrics']['critical_path_ns'];pairs.append(dict(circuit=c,reference_ns=ac,new_ns=bc,improvement_pct=100*(1-bc/ac)))
  if a['status'] in ['failed','timeout'] and b['status']=='legal':recoveries.append(c)
  if a['status']=='legal' and b['status'] in ['failed','timeout']:lost.append(c)
 comparisons[left+'->'+right]=dict(declared_circuits=len(circuits),both_legal=len(pairs),recovered=recoveries,lost=lost,improved=sum(p['new_ns']<p['reference_ns'] for p in pairs),tied=sum(p['new_ns']==p['reference_ns'] for p in pairs),regressed=sum(p['new_ns']>p['reference_ns'] for p in pairs),geomean_improvement_pct=100*(1-math.exp(sum(math.log(p['new_ns']/p['reference_ns']) for p in pairs)/len(pairs))) if pairs else None,worst_improvement_pct=min((p['improvement_pct'] for p in pairs),default=None),pairs=pairs)
result=dict(scope='Six declared previously seen seed11 HybridO/P0/W100 circuits. Uniform original, initial-global and iteration2-global scope for A0/R1/fullU; no per-circuit best selection. Direct controls/independent audits/input seals gate legal comparisons. Missing or running delayed roles stay declared; failed CPD excluded. Process times are development observations, never formal speedup ratios.',comparisons=comparisons,statuses={a:dict(collections.Counter(r['status'] for r in rows if r['arm']==a)) for a in roles},observations=rows,input_sha256=binding,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D/'scope_six_circuit_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(statuses=result['statuses'],comparisons={k:{a:b for a,b in v.items() if a!='pairs'} for k,v in comparisons.items()}),indent=2))
