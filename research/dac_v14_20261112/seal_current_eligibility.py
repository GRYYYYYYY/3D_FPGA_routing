#!/usr/bin/env python3
"""Seal the completed eligibility pilot; never marks the research goal complete."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
r=read(D/'current_eligibility_eltwise_dev_02/eligibility_analysis.json');assert r['passed']
for p,h in r['source_sha256'].items():assert sha(p)==h,p
owners=[];role_statuses=[]
for name in ['current_eligibility_eltwise_dev_01','current_eligibility_eltwise_dev_02']:
 b=D/name;reg=read(b/'registration.json');proc=Path('/proc')/str(reg['pid'])/'stat';live=proc.exists() and proc.read_text().split(') ',1)[1].split()[19]==reg['start_ticks'];assert not live
 assert read(b/'input_seal.json')['passed'] and read(b/'completion.json')['gate_passed'] and not read(b/'completion.json')['missing_arms']
 owners.append(dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],live=live))
 for a in reg['arms']:
  rd=b/'runs'/('eltwise_layer_'+a);m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and read(rd/'independent_audit.json')['audit']['passed'] and read(rd/'final_guide_audit.json')['passed']
  role_statuses.append(dict(batch=name,arm=a,status='legal',diagnostic_reproduction=name.endswith('02')))
  if name.endswith('02'):assert read(rd/'diagnostic_recovery_reproduction.json')['passed']
stage=D/'current_eligibility_stage_02';s=read(stage/'binding.json');checks={p:sha(D/'src'/p)==h and sha(stage/'src'/p)==h for p,h in s['source_sha256'].items()};assert all(checks.values());assert sha(stage/'bin/vpr')==s['binary_sha256']
base=read(D/'baseline_source_sha256.json');root=D.parents[1]/'vendor/vtr-architecture-src';original={p:sha(root/p)==base[p] for p in read(D/'outside_native_study_closure_01.json')['original_source_checks']};assert all(original.values())
out=D/'current_eligibility_study_closure_01.json';assert not out.exists()
write(out,dict(passed=True,status='eligibility_pilot_sealed_not_promoted_research_active',owners=owners,roles=role_statuses,mutable_source_checks=checks,original_source_checks=original,analysis_sha256=sha(D/'current_eligibility_eltwise_dev_02/eligibility_analysis.json'),quality_promoted=False,source_stage='current_eligibility_stage_02',qualification='Three completed roles plus three diagnostic-equivalence reproductions; not six independent scientific samples. Attempt01 capped unguided logs prematurely, so its QoR is retained but its complete mechanism trace is not certified. Corrected rows cover all actual guided searches. Same final route/CPD with +7 count2 iterations and no count1 iteration gain. No new publication is implied; public snapshot remains f7167bd.'))
print(dict(passed=True,roles=len(role_statuses),source_checks=len(checks),original_checks=len(original)))
