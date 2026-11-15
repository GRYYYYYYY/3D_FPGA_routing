"""Verify a real ON-rejection/OFF-acceptance window without sealing a live actor."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from resource_policy_scheduling_v1 import accepted_resource_role
from multiobjective_acceptance_v2 import decide

actor=D/'complete_serial_architecture_transfer_01/sb_domain/flow/repair'
attempt=next(r for r in read(actor/'attempts.json') if r.get('accepted_role')=='reuse_off')
tx=Path(attempt['transaction']);closed=read(tx/'completion.json');assert closed['passed']
assert all(sha(f)==h for f,h in closed['source_sha256'].items())
reg=read(tx/'registration.json');roles=reg['roles'];progress=read(tx/'progress.json')
assert accepted_resource_role(progress)=='reuse_off'
assert not progress['reuse_on']['policies']['resources_under_timing']['accepted']
assert progress['reuse_off']['policies']['resources_under_timing']['accepted']
assert all(p['status']=='legal_evaluated' and not p['native_reused'] for p in progress.values())
assert roles['reuse_on']['state']==roles['reuse_off']['state']==attempt['current_state']
source=Path(attempt['current_state']);before=read(source/'endpoint_vector.json')
physical=read(run_dir(source)/'independent_audit.json')['physical_metrics']
current=dict(wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'])
tags=[r['tag'] for r in read(tx/'process_costs.json')]
assert tags.index('reuse_on_native')<tags.index('reuse_off_native')
files=[Path(__file__).resolve(),D/'resource_policy_scheduling_v1.py',D/'multiobjective_acceptance_v2.py',tx/'registration.json',tx/'completion.json',tx/'progress.json',tx/'process_costs.json',source/'completion.json',source/'endpoint_vector.json',run_dir(source)/'independent_audit.json']
outcomes={}
for name,row in progress.items():
    role=roles[name];native=read(tx/name/'endpoint_vector.json')
    assert all(before[k]==native[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    state=Path(row['evaluation']);after=read(state/'endpoint_vector.json');audit=read(run_dir(state)/'independent_audit.json');assert audit['audit']['passed']
    p=audit['physical_metrics'];actual=dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'])
    assert actual==row['resources']
    decision=decide('resources_under_timing',before,after,current,actual,cpd_limit_s=role['original_budget']['CPD_s'],resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
    assert decision==read(tx/(name+'_decisions.json'))['resources_under_timing']
    outcomes[name]=dict(accepted=decision['accepted'],reason=decision['reason'],resources=actual,CPD_ns=after['cpd_s']*1e9,evaluation=str(state))
    files += [tx/name/'completion.json',tx/name/'endpoint_vector.json',state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'independent_audit.json',tx/(name+'_decisions.json')]
assert attempt['committed_evaluation']==progress['reuse_off']['evaluation']
out=D/'lazy_real_fallback_validation_01';out.mkdir(exist_ok=False);write(out/'observed_completed_attempt.json',attempt);files.append(out/'observed_completed_attempt.json')
write(out/'completion.json',dict(passed=True,native_calls_new=0,source_state=str(source),transaction=str(tx),outcomes=outcomes,
    native_executed_after_domain_rejection=True,source_full_vector_exact_in_both_workers=True,selected_actual_state=attempt['committed_evaluation'],
    source_sha256={str(f):sha(f) for f in files},
    qualification='Read-only verification of one completed window in an otherwise live SB-only architecture trajectory. Both actual same-source native workers restore the complete source vector; independently audited resources and exact acceptance recompute agree. The ON candidate is rejected, OFF is actually executed afterward and its actual accepted state is selected. Not a whole-actor/context seal, complete-cost claim, new independent sample or an inferred result for an unexecuted arm.'))
print(dict(passed=True,outcomes=outcomes),flush=True)
