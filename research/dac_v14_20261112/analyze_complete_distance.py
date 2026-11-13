#!/usr/bin/env python3
"""Gate complete-distance diagnostic by exhaustive query and selected coverage."""
from pathlib import Path
import hashlib,json,re,sys
B=Path(sys.argv[1]);D=B.parent
assert json.loads((B/'input_seal.json').read_text())['passed']
reg=json.loads((B/'registration.json').read_text());nodes=json.loads((D/'query_prototype/rrg_spmv/binding.json').read_text())['nodes'];rows={}
for c in reg['circuits']:
 rd=B/'runs'/f'{c}_Ed';m=json.loads((rd/'manifest.json').read_text())
 if m['status']!='completed':rows[c]=dict(status=m['status']);continue
 assert m['metrics']['native_full_check_passed']
 audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed']
 assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
 env=m['environment'];assert env['VPR_H3D_MIXED_DELAY']=='1' and int(env['VPR_H3D_DELAY_BUDGET'])==json.loads((D/'complete_distance_bounds.json').read_text())['budget']
 for k in ['TARGET_DELAY','TARGET_FRONTIER','TARGET_QUOTA','BOUND_CLAMP','QUERY_CRITICALITY_ORDER','SOURCE_QUERY_SHARE','REVERSE_RERANK','SOURCE_GEOMETRY_FLOOR','TRACE_ESTIMATES','LAYER_BB_DELAYED','ALL_LAYER_BB','LAYER_BB_FEEDBACK','TIMING_GUIDE','FEEDBACK']:assert env['VPR_H3D_'+k]=='0'
 assert env['VPR_H3D_VALIDATE_DELAY']=='1' and m['tags']['diagnostic_only']
 lines=(rd/'stdout.log').read_text().splitlines();counters={}
 for prefix in ['H3D_DELAY ','H3D_MIXED ','H3D_SELECTED_DELAY ','H3D_TARGET_DELAY ']:
  matched=[l for l in lines if l.startswith(prefix)];assert matched
  counters[prefix.strip()]={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matched[-1])}
 assert counters['H3D_DELAY']['truncated']==0
 assert counters['H3D_TARGET_DELAY']['queries']==counters['H3D_TARGET_DELAY']['settled']==0
 for kind in ['H3D_MIXED','H3D_SELECTED_DELAY']:
  r=counters[kind];assert r['source_only']==r['sink_only']==r['estimated']==0 and r['both']>=r['pins']==r['informed_pins']>0
 validation=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)} for l in lines if l.startswith('H3D_EDGE_DELAY_VALIDATED ')]
 assert len(validation)==min(8,counters['H3D_DELAY']['queries']) and all(v['returned']==v['reference'] and v['budget_exhausted']==0 for v in validation)
 rows[c]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],counters=counters,independent_initial_query_checks=validation,planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)', '\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'])
out=dict(scope='Complete-distance surrogate diagnostic, not a proposed increased-budget method or a ceiling on achievable QoR. Zero query truncation and full mixed/selected candidate coverage required. Development acquisition costs include explicit validation work and must not support acceleration claims.',circuits=rows,passed=True,complete_legal_cases=sum(r['status']=='legal' for r in rows.values()),declared_cases=len(reg['circuits']),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seal_sha256=hashlib.sha256((B/'input_seal.json').read_bytes()).hexdigest())
(B/'complete_distance_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
