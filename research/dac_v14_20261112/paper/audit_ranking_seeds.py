#!/usr/bin/env python3
"""Recompute ranking cohort and per-seed ranks from archived role observations."""
from pathlib import Path
import hashlib, itertools, json, math, statistics

P=Path(__file__).resolve().parent
ROOT=P.parents[1]
B=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
obs=B/'evaluation_analysis/role_observations.json'
summary=B/'evaluation_analysis/summary.json'
rows=json.loads(obs.read_text())['rows']
reported=json.loads(summary.read_text())['architecture_rankings']
families=('sb','cb_o','hybrid_o'); flows=('p0','p1'); roles=('A0','R1'); seeds=(21,23,25)
selected=[r for r in rows if r['phase']=='heldout' and r['width']==100 and r['role'] in roles and (r['family'] in families or (r['family']=='matched_2d' and r['flow']=='p0' and r['role']=='A0'))]
index={}
for row in selected:
 key=tuple(row[k] for k in ('circuit','seed','family','flow','role'))
 if key in index: raise RuntimeError(f'duplicate role observation: {key}')
 index[key]=row
circuits=sorted({r['circuit'] for r in selected})
def legal(k):
 r=index.get(k)
 return bool(r and r['status']=='legal' and r['metrics'].get('native_full_check_passed') and r['metrics'].get('critical_path_ns',0)>0)
def needed(c,s):
 return [(c,s,'matched_2d','p0','A0')]+[(c,s,f,p,r) for f,p,r in itertools.product(families,flows,roles)]
common=[c for c in circuits if all(legal(k) for s in seeds for k in needed(c,s))]
assert len(circuits)==reported['registered_circuits']==14
assert common==reported['complete_common_circuits']==['conv_layer_hls']
def cpd(k): return index[k]['metrics']['critical_path_ns']
def rank(vals):
 groups=[]
 for f in sorted(vals,key=lambda x:vals[x]):
  if groups and math.isclose(vals[f],vals[groups[-1][0]],rel_tol=1e-12,abs_tol=1e-12):groups[-1].append(f)
  else: groups.append([f])
 return groups
checked=0;out={};errors=[]
for seed in seeds:
 out[str(seed)]={}
 for flow,role in itertools.product(flows,roles):
  c=common[0]; vals={f:cpd((c,seed,f,flow,role)) for f in families}
  denominator=cpd((c,seed,'matched_2d','p0','A0'))
  ref=reported['by_seed'][str(seed)][f'{flow}_{role}']
  groups=rank(vals)
  if groups!=ref['rank_groups']:errors.append(f'{seed}/{flow}/{role} rank')
  for f in families:
   if not math.isclose(vals[f],ref['absolute_geomean_cpd_ns'][f],rel_tol=1e-12):errors.append(f'{seed}/{flow}/{role}/{f} cpd')
   if not math.isclose(vals[f]/denominator,ref['common_2d_geomean_ratio'][f],rel_tol=1e-12):errors.append(f'{seed}/{flow}/{role}/{f} ratio')
   checked+=2
  out[str(seed)][f'{flow}_{role}']={'cpd_ns':vals,'matched_2d_ns':denominator,'rank_groups':groups}
for flow,role in itertools.product(flows,roles):
 for f in families:
  value=statistics.mean(cpd((common[0],s,f,flow,role)) for s in seeds)
  if not math.isclose(value,reported['by_flow'][f'{flow}_{role}']['absolute_geomean_cpd_ns'][f],rel_tol=1e-12):errors.append(f'{flow}/{role}/{f} seed mean')
  checked+=1
for seed,flow in itertools.product(seeds,flows):
 if out[str(seed)][f'{flow}_A0']['cpd_ns']!=out[str(seed)][f'{flow}_R1']['cpd_ns']:errors.append(f'{seed}/{flow} changed A0 vs R1')
result={'status':'passed' if not errors else 'failed','circuits_registered':len(circuits),'common_circuits':common,'seeds':out,'numeric_comparisons':checked,'errors':errors,
 'scope':'One circuit common to all three seeds, two flows, three architectures, both A0/R1 and matched 2D; role records and existing summary, no new experiments or independent timing extraction.',
 'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (obs,summary)}}
(P/'data/ranking_seed_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'common_circuits':common,'numeric_comparisons':checked,'errors':errors,'seeds':{s:{p:out[s][p]['rank_groups'] for p in ('p0_A0','p1_A0')} for s in out}},indent=2))
raise SystemExit(bool(errors))
