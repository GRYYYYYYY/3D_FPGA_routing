#!/usr/bin/env python3
"""Summarize completed cross-circuit repair and physical-cache evidence."""
from retained_prefix_workflow import D,read,write,sha

names=['native_scope_spmv_R1_summary_01.json','native_scope_spmv_A0_summary_01.json','native_scope_spmv_Tf_reuse_summary_01.json','spmv_R1_Tf_exact_reuse_identity_01.json','rr_audit_cache_validation_01/completion.json','rr_audit_cache_e695_dev_01/completion.json','spmv_near_endpoint_cache_experiment_01.json']
bindings={};reports={}
for name in names:
 o=read(D/name);assert o.get('passed',True),name
 for p,h in o.get('source_sha256',{}).items():
  if p not in bindings:bindings[p]=sha(p)
  assert bindings[p]==h,p
 bindings[str(D/name)]=sha(D/name);reports[name]=o
ref=read(D/'current_sta_policy_native_spmv_R1_01/attempt_001/candidate_audit/analysis.json');cached=read(D/'cached_native_audit_spmv_01/analysis.json')
fields=['passed','status','scope','queries','attempts','changed_delays','native_transaction_seconds']
assert all(ref[k]==cached[k] for k in fields)
assert sha(ref['candidate_route'])==sha(cached['candidate_route'])
for n in ['current_sta_policy_native_spmv_R1_01/attempt_001/candidate_audit/analysis.json','cached_native_audit_spmv_01/analysis.json','immutable_rr_audit_cache.py','audit_native_objective_cached.py','run_native_scope_policy_v4.py','report_spmv_cache_progress.py']:bindings[str(D/n)]=sha(D/n)
r=reports[names[0]]['batches'][0];a=reports[names[1]]['batches'][0];t=reports[names[2]]['batches'][0]
assert r['policies']['strict']['final']['cpd_ns']==a['initial']['cpd_ns']
assert t['costs']['native_core_seconds']==0
for policy in ['strict','endpoint_vector']:
 assert r['policies'][policy]['final']['state']==t['policies'][policy]['final']['state']
write(D/'spmv_cache_progress_summary_01.json',dict(passed=True,research_complete=False,quality_promoted=False,batches=[r,a,t],cache_validation=reports[names[4]],additional_cache_equivalence=dict(case='SPMV joint accepted transaction',complete_candidate_bytes_equal=True,equivalent_fields=fields,audit_segment_seconds=cached['audit_and_serialization_seconds'],load_seconds=cached['graph_cache']['load_and_digest_seconds'],full_child_time_not_measured=True),source_sha256=bindings,qualification='SPMV R1 repairs recover but do not beat A0 CPD and use more resources than A0. Tf is exact reuse, not an independent sample. Cache changes physical data access only; formal paired runtime and broader circuit promotion remain unproven. Active near-endpoint experiment excluded.',next_registered='spmv_near_endpoint_cache_experiment_01.json',new_work_pushed=False))
print(dict(passed=True,sources=len(bindings),SPMV_CPD_ns=r['policies']['strict']['final']['cpd_ns'],A0_steps=a['policies']['strict']['accepted_steps'],cache_negative_controls=len(reports[names[4]]['negative_controls_rejected'])))
