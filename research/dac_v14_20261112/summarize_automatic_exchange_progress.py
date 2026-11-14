#!/usr/bin/env python3
"""Summarize completed actors, current operator limits and exchange diagnostics."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
from fixed_anchor_acceptance import decisions
from run_native_scope_policy_v4 import run_dir,input_identity,native_config
b=D/'bnn_automatic_trajectories_dev_02';c=read(b/'completion.json');assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items());rows=[];bound={str(p):sha(p) for p in [Path(__file__).resolve(),b/'completion.json',D/'endpoint_timing_policy.py',D/'fixed_anchor_acceptance.py']}
for name in ['Tf_strict','Tf_endpoint_vector','A0_strict','A0_endpoint_vector']:
 actor=b/name;r=read(actor/'completion.json');assert r['passed'] and all(sha(p)==h for p,h in r['source_sha256'].items())
 before=read(Path(r['initial_state'])/'endpoint_vector.json');after=read(Path(r['final_state'])/'endpoint_vector.json');cmp=compare(before,after)
 rows.append(dict(actor=name,accepted_steps=r['accepted_steps'],operator_stop=r['operator_stop'],initial_state=r['initial_state'],final_state=r['final_state'],initial_CPD_ns=before['cpd_s']*1e9,final_CPD_ns=after['cpd_s']*1e9,final_resources=r['final_resources'],setup_improved=cmp['setup_improved'],setup_regressed=cmp['setup_regressed'],hold_violation_regressions=cmp['hold_violation_regressions'],complete_imported_state_workflow_seconds=r['complete_imported_state_workflow_seconds'],complete_single_configuration_algorithm_seconds=None))
 bound[str(actor/'completion.json')]=sha(actor/'completion.json')
# Exact current-state availability check. This is a diagnostic reference, not a
# history-dependent algorithm policy or a reason to rewrite the frozen actors.
endpoint=read(b/'A0_endpoint_vector/completion.json');current=Path(endpoint['final_state']);before=read(current/'endpoint_vector.json');source=run_dir(current);root=read(b/'A0_endpoint_vector/registration.json')['anchor'];available=[]
old=D/'bnn_strong_release_joint_dev_01';reg=read(old/'registration.json');comp=read(old/'completion.json');assert comp['passed']
for name,role in reg['roles'].items():
 if Path(role['state'])!=current:continue
 result=comp['roles'][name];assert result['status']=='legal_evaluated';state=Path(result['evaluation']);assert read(state/'completion.json')['passed'];run=run_dir(state)
 assert input_identity(source)==input_identity(run) and native_config(source)==native_config(run)
 after=read(state/'endpoint_vector.json');old_res=read(source/'independent_audit.json')['physical_metrics'];new_res=read(run/'independent_audit.json')['physical_metrics'];keys={'wirelength':'planar_wirelength_excluding_sb_half_nodes','SB_pairs':'sb_pairs_used','CB_sources':'cb_crossing_output_sources_used'}
 cur={k:old_res[v] for k,v in keys.items()};new={k:new_res[v] for k,v in keys.items()};d=decisions(before,after,cur,new,root)
 available.append(dict(role=name,state=str(state),CPD_ns=after['cpd_s']*1e9,resources=new,accepted={k:v['accepted'] for k,v in d.items()},setup_improved=d['endpoint_vector']['comparison']['setup_improved'],setup_regressed=d['endpoint_vector']['comparison']['setup_regressed']))
 for p in [state/'completion.json',state/'endpoint_vector.json',run/'independent_audit.json',old/(name+'_decisions.json')]:bound[str(p)]=sha(p)
assert any(x['accepted']['endpoint_vector'] for x in available),'Expected current-state endpoint reference not available; inspect before claiming a proposal-class limit'
a0=next(r for r in rows if r['actor']=='A0_strict');full=read(D/'bnn_strong_scope_summary_01.json');ref=next(r for r in full['rows'] if r['role']=='A0_combined_weighted_soft');assert a0['final_CPD_ns']==ref['CPD_ns'];delta={k:a0['final_resources'][k]-ref['resources'][k] for k in a0['final_resources']}
write(D/'automatic_exchange_progress_summary_01.json',dict(passed=True,actors=rows,A0_strict_vs_all_positive=dict(CPD_change_ns=0.,resource_change=delta,quality_projection_dominated_by=ref['evaluation'],complete_runtime_dominance='unknown'),endpoint_current_state_available_reference=available,
 proposal_class_limit='A0 endpoint actor stops because its selected positive-winning-path group is rejected, although two already legal owner-only alternatives from its identical current state satisfy exact endpoint acceptance. This limits the proposal class, not the endpoint strategy or research objective. References are not a per-circuit historical-best policy.',
 critical_exchange_query='critical_owner_exchange_query_01/completion.json',critical_exchange_expansion='critical_owner_exchange_expansion_01/completion.json',native_controls='critical_owner_exchange_dev_01/registration.json',source_sha256=bound,new_native_calls=0,
 qualification='Summary/recomputation on completed evidence only. Actor times include explicitly executed imported-state work but exclude historical creation and initial routing/caches; no cold whole-configuration or cross-policy speedup comparison. Local operator stops do not end research.'))
print(dict(actors=[(r['actor'],r['accepted_steps'],r['final_CPD_ns']) for r in rows],A0_wire_vs_all_positive=delta['wirelength'],available_endpoint_alternatives=[x['role'] for x in available if x['accepted']['endpoint_vector']]))
