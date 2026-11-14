#!/usr/bin/env python3
"""Summarize the failed-state discrimination and occupancy-cut intervention."""
import json,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_sta_selector import select
from endpoint_timing_policy import compare

b=D/'joint_native_cut_order_dev_01';done=read(b/'completion.json');reg=read(b/'registration.json')['roles']['Tf_cut_order']
assert done['all_roles_completed'];audit=read(b/'Tf_cut_order_audit/analysis.json');cut=read(b/'cut_evidence.json')
state=b/'Tf_cut_order_evaluation';evaluation=read(state/'completion.json');rd=Path(evaluation['run']);before_state=Path(reg['state']);source=Path(reg['source'])
before,after=read(before_state/'endpoint_vector.json'),read(state/'endpoint_vector.json');change=compare(before,after)
finite=lambda v:[x for x in v['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x)]
threshold=min(finite(before))+.2e-9
def near(v,threshold):
 values=[key for key,value in v['setup'].items() if isinstance(value,(int,float)) and math.isfinite(value) and value<=threshold]
 return dict(components=len(values),endpoints=len({tuple(json.loads(k)[:3]) for k in values}),threshold_s=threshold)
resources={name:read(path/'independent_audit.json')['physical_metrics'] for name,path in [('before',source),('after',rd)]}
processes=read(b/'process_costs.json');failure=D/'joint_native_failure_state_01';failure_state=read(failure/'diagnostic/completion.json')
failure_log=Path(failure_state['run'])/'joint_native.log';failure_lines=failure_log.read_text().splitlines()
cost=dict(preparation_seconds=cut['preparation_seconds'],orchestration_seconds=done['complete_orchestrator_seconds'],
 preparation_plus_orchestration_seconds=cut['preparation_seconds']+done['complete_orchestrator_seconds'],
 measured_wrapper_process_sum_seconds=sum(x['complete_process_seconds'] for x in processes),native_transaction_seconds=audit['native_transaction_seconds'],
 phases={x['tag']:x['complete_process_seconds'] for x in processes},evaluation_breakdown=evaluation['timing'],
 diagnostic_wrapper_seconds=failure_state['timing']['complete_evaluation_seconds'],exact_partial_query=read(failure/'exact_query/completion.json'),scope_bound=read(D/'joint_native_cut_scope_bound_01/completion.json'),
 qualification='Development elapsed times. Native transaction and evaluation breakdown are subsets, not additive to wrappers. Instrumentation build, historical reused work and human analysis are separate; no U runtime substitution.')
files=[b/'registration.json',b/'completion.json',b/'cut_evidence.json',b/'process_costs.json',b/'Tf_cut_order_decision.json',b/'Tf_cut_order_audit/analysis.json',state/'completion.json',state/'endpoint_vector.json',before_state/'endpoint_vector.json',source/'native_sta_frontier.jsonl',rd/'native_sta_frontier.jsonl',source/'independent_audit.json',rd/'independent_audit.json',failure/'exact_query/completion.json',failure/'exact_query/native_state_validation.json',failure/'exact_query/static_entry_certificate.json',D/'joint_native_cut_scope_bound_01/completion.json',failure_log]
result=dict(passed=True,research_complete=False,quality_promoted=False,cpd_before_ns=before['cpd_s']*1e9,cpd_after_ns=after['cpd_s']*1e9,
 decisions=done['roles']['Tf_cut_order']['decisions'],changed_connections=audit['changed_delays'],
 endpoint_change={k:v for k,v in change.items() if k!='changes'},setup_regressions=[x for x in change['changes'] if x['kind']=='setup' and x['delta_s']<0],
 near_0p2ns=dict(fixed_initial_window_before=near(before,threshold),fixed_initial_window_after=near(after,threshold),current_window_after=near(after,min(finite(after))+.2e-9)),
 selection_before=select(source/'native_sta_frontier.jsonl'),selection_after=select(rd/'native_sta_frontier.jsonl'),resources=resources,cost=cost,
 new_execution_accounting=dict(native_whole_analysis_processes=3,native_connection_search_calls=sum(x.startswith('ATTEMPT ') for x in failure_lines)+len(audit['attempts']),new_offline_exact_query_modes=4,partial_failures=1,complete_legal_candidates=1),
 conclusions=['Diagnostic stage preserves all prior query outcomes/counts. Identical-state capacity query exhausts after2expansions; native final congestion price is positive. This is state infeasibility, not a demonstrated soft-price failure.',
 'Raw static unique-entry hypothesis is false: fourteen positive-capacity entries. Thirteen are owned outside the released scope; last416990 is newly used by7541. Scope-conditional required entry motivates derived1960p1-before7541p1 order.',
 'Same scope/path order intervention restores16connections and lowersCPD, but worsens2setupcomponents. Strictaccept/endpointreject; no strictreject/endpointaccept in this branch.',
 'Even before restoring other sinks, excluding scope-required416990 gives victim minimum1.495641416ns>original1.220990892ns. Reordering within this scope cannot avoid this physical-connection loss. Not a global STA bound.',
 'Selection is refreshed to the new nativeSTA frontier. This diagnostic scheduling candidate does not replace the stronger previously accepted Tf strict state or the R1best state.'],
 public_snapshot='f7167bd',new_work_pushed=False,source_sha256={str(p):sha(p) for p in files})
write(D/'joint_native_cut_feedback_summary_01.json',result)
print(dict(cpd=[result['cpd_before_ns'],result['cpd_after_ns']],near=result['near_0p2ns'],cost=cost['preparation_plus_orchestration_seconds'],native_calls=result['new_execution_accounting']),flush=True)
