#!/usr/bin/env python3
"""Report completed joint native controls and bounded victim mechanism evidence."""
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
b=D/'joint_native_repair_dev_01';done=read(b/'completion.json');assert done['all_roles_completed']
rows=[];failures=[];sources=[b/'completion.json',D/'joint_victim_bound_01/completion.json',b/'R1_fixed_oracle_comparison.json',b/'R1_joint_choice_ablation.json']
for batch in [b,D/'joint_native_feedback_dev_01']:
 final=read(batch/'completion.json');reg=read(batch/'registration.json')
 for role,result in final['roles'].items():
  if result['status']!='legal_candidate':
   audit=read(batch/(role+'_audit')/'analysis.json')
   failures.append(dict(role=role,status=result['status'],audit=audit,complete_orchestrator_seconds=final['complete_orchestrator_seconds'],accepted_state_unchanged=True))
   sources.append(batch/(role+'_audit')/'analysis.json')
   continue
  state=batch/(role+'_evaluation');out=read(state/'completion.json');audit=read(batch/(role+'_audit')/'analysis.json')
  rd=Path(out['run']);resources=read(rd/'independent_audit.json')['physical_metrics']
  original=Path(reg['roles'][role]['state']);changes=compare(read(original/'endpoint_vector.json'),read(state/'endpoint_vector.json'));changes.pop('changes',None)
  costs=[r for r in read(batch/'process_costs.json') if r['tag'].startswith(role+'_')]
  rows.append(dict(role=role,cpd_ns=out['full_precision_cpd_s']*1e9,decisions=result['decisions'],endpoint_change=changes,resources=resources,
    native_core_seconds=audit['native_transaction_seconds'],native_queries=len(audit['queries']),native_attempts=len(audit['attempts']),
    independent_audit_and_serialization_seconds=audit['audit_and_serialization_seconds'],complete_wrapper_process_seconds=sum(r['complete_process_seconds'] for r in costs),
    full_evaluation_timing=out['timing'],source=str(original),final_state=str(state)))
  sources += [state/'completion.json',state/'endpoint_vector.json',batch/(role+'_decision.json'),batch/(role+'_audit')/'analysis.json',rd/'independent_audit.json']
 sources += [batch/'completion.json',batch/'registration.json',batch/'process_costs.json']
write(D/'joint_native_repair_summary_01.json',dict(passed=True,rows=rows,failed_transactions=failures,
 conclusions=['Given identical released sink/tree scope, native sequential repair reproduces R1CPD and complete setup-vector gain without preset target paths; do not attribute this gain to a distinct capacity oracle or compatible-path solver.',
 'Matched scope came from prior automatic transaction discovery. Native autonomous scope discovery is not yet demonstrated by that control.',
 'Tf fixed-scope current-slack scheduling cannot avoid the output-victim connection loss: an exact fixed-tree physical minimum before any blocker recovery is1.681467215ns versus original1.220990892ns. Relaxing other background lowers that bound to0.849339293ns, motivating feedback scope expansion. This is not a global STA bound.'],
 timing_scope='Full wrapper processes measured including preparation, actual search/replacement, audits and evaluation. Core is a subset. Development timings, not cold formal native route comparisons.',
 quality_promoted=False,research_complete=False,source_sha256={str(p):sha(p) for p in dict.fromkeys(sources)}))
with (D/'paper/data/joint_native_repair_v14.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['role','cpd_ns','setup_improved','setup_regressed','strict_accept','endpoint_accept','sb_pairs','cb_sources','planar_wirelength','native_queries','native_attempts','native_core_s','complete_wrapper_process_s'])
 writer.writeheader()
 for r in rows:
  writer.writerow(dict(role=r['role'],cpd_ns=r['cpd_ns'],setup_improved=r['endpoint_change']['setup_improved'],setup_regressed=r['endpoint_change']['setup_regressed'],strict_accept=r['decisions']['strict']['accepted'],endpoint_accept=r['decisions']['endpoint_vector']['accepted'],sb_pairs=r['resources']['sb_pairs_used'],cb_sources=r['resources']['cb_crossing_output_sources_used'],planar_wirelength=r['resources']['planar_wirelength_excluding_sb_half_nodes'],native_queries=r['native_queries'],native_attempts=r['native_attempts'],native_core_s=r['native_core_seconds'],complete_wrapper_process_s=r['complete_wrapper_process_seconds']))
print([(r['role'],r['cpd_ns'],r['decisions']) for r in rows])
