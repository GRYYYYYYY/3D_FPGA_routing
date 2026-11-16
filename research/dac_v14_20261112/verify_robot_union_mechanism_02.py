"""Audit exact same-root scope contrast and retain all native outcome classes."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy_streaming_v2 import compare
from multiobjective_acceptance_v2 import decide

root=D/'robot_union_mechanism_02'
def check_pair(plan,reg):
    from compose_current_scope_union_v1 import compose
    sharing=read(Path(plan['sharing_registration']))['roles']['reuse_on']
    owner=read(Path(plan['owner_registration']))['roles']['target_plus_owner']
    union=compose(sharing,owner)
    assert list(reg['roles'])==plan['fixed_order']==['union_native','union_domain_no_release','union_domain_release']
    for name,role in reg['roles'].items():
        for key in ['state','source','objective','seed_order','original_budget','fixed_resource_limits','fixed_target_paths']:
            assert role[key]==owner[key],key
        assert role['queries']==union['queries'] and role['removed_pins']==union['removed_pins']
        assert Path(role['request']).read_text()==union['request']
        assert Path(role['crossing_domain']).read_text()==union['domain_text']
        assert role['crossing_reuse_enabled']==(name!='union_native')
        assert role['domain_failure_release']==(name=='union_domain_release')
        assert role['explicit_crossings'] is None
    return union

def main(preflight=False):
    plan=read(root/'plan.json');reg=read(root/'prepared_transaction_registration.json');group=check_pair(plan,reg)
    assert all(sha(f)==h for f,h in plan['source_sha256'].items() if not preflight or Path(f).stat().st_size<2*1024*1024)
    before_state=Path(plan['source_state']);before=read(before_state/'endpoint_vector.json');original=require_publication_proof(before_state)['resource_axes']
    files=[Path(__file__).resolve(),root/'plan.json',root/'prepared_transaction_registration.json']
    if preflight:
        write(root/'preflight.json',dict(passed=True,union_scope_exact=True,exact_current_weights_and_global_order=True,selected_before_outcomes=True,three_matched_treatments=True,large_digest_checks_deferred=True,native_calls_new=0,source_sha256={str(f):sha(f) for f in files}));print(dict(passed=True,native_calls_new=0));return
    tx=root/'transaction';assert read(tx/'registration.json')==reg
    execution=read(root/'queue/execution_receipt.json');measurement=read(root/'measurement/completion.json');supervision=read(root/'supervision.json')
    assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants']
    progress=read(tx/'progress.json') if (tx/'progress.json').exists() else {};outcomes={};native_calls=0
    for f in tx.glob('*/runs/state/manifest.json'):
        if 'process_group_id' in read(f): native_calls+=1
    for name,role in reg['roles'].items():
        row=progress.get(name,{});status=row.get('status','unexecuted_or_controller_incomplete')
        outcomes[name]=dict(status=status,quality=None,committed_to_original_actor=False)
        if status not in ['legal_evaluated','transaction_failed_rolled_back']: continue
        worker=tx/name;wc=read(worker/'completion.json');assert wc['passed'] and all(wc['checks'].values())
        restored=read(worker/'endpoint_vector.json');assert all(restored[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        manifest=read(run_dir(worker)/'manifest.json');assert sha(manifest['command'][0])==read(D/'crossing_source_stage_01/binding.json')['binary_sha256']
        assert route_body(run_dir(worker)/'routed.route')==route_body(Path(role['source'])/'routed.route')
        audit=read(tx/(name+'_audit/analysis.json'));domain=read(tx/(name+'_domain_audit.json'))
        assert audit['passed'] and domain['passed'] and domain['enabled']==role['crossing_reuse_enabled']
        if domain['enabled']:
            assert domain['initial_domain_nets']==group['domain_nets']
            assert role['domain_failure_release'] or not domain['released_queries']
        for receipt in [audit,domain]: assert all(sha(f)==h for f,h in receipt['source_sha256'].items())
        actual_order=[(q['net'],q['pin']) for q in audit['queries']];expected_order=[(q['net'],q['pin']) for q in role['queries']]
        assert actual_order==expected_order[:len(actual_order)]
        outcomes[name].update(native_core_seconds=audit['native_transaction_seconds'],actual_queries=len(actual_order),actual_attempts=len(audit['attempts']))
        files.extend([worker/'completion.json',worker/'endpoint_vector.json',run_dir(worker)/'manifest.json',tx/(name+'_audit/analysis.json'),tx/(name+'_domain_audit.json')])
        if status=='transaction_failed_rolled_back': assert not audit.get('candidate_route');continue
        assert actual_order==expected_order and all(s['terminal_set_unchanged'] and s['other_branch_edges_unchanged'] for s in audit['scope'])
        state=Path(row['evaluation']);view=require_publication_proof(state);after=read(state/'endpoint_vector.json')
        m=read(run_dir(state)/'manifest.json');assert m['metrics']['native_full_check_passed']
        for filename in ['packed.net','placed.place','routed.route']: assert sha(run_dir(state)/filename)==m['outputs'][filename]['sha256']
        resources=view['resource_axes'];comparison=compare(before,after);assert comparison['compatible']
        decision=decide('resources_under_timing',before,after,original,resources,cpd_limit_s=plan['original_budget']['CPD_s'],resource_limits=plan['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
        assert decision==read(tx/(name+'_decisions.json'))['resources_under_timing']
        outcomes[name].update(quality=dict(CPD_ns=after['cpd_s']*1e9,resources=resources),evaluation=str(state),endpoint_comparison=comparison,resource_policy_decision=decision,all_policies=read(tx/(name+'_decisions.json')))
        files.extend([state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'independent_audit.json',run_dir(state)/'routed.route',tx/(name+'_decisions.json')])
    paired={}
    for left,right,attribution in [('union_native','union_domain_no_release','Retained domain with release disabled at identical union scope'),('union_domain_no_release','union_domain_release','Failure release at identical retained domains and union scope')]:
        a,b=outcomes[left],outcomes[right]
        if a['quality'] is not None and b['quality'] is not None:
            ra,rb=[v['quality']['resources'] for v in [a,b]]
            paired[left+'__'+right]=dict(CPD_delta_ns=b['quality']['CPD_ns']-a['quality']['CPD_ns'],resource_deltas={k:rb[k]-ra[k] for k in ra},endpoint_comparison=compare(read(Path(a['evaluation'])/'endpoint_vector.json'),read(Path(b['evaluation'])/'endpoint_vector.json')),attribution=attribution)
        else:paired[left+'__'+right]=dict(left_status=a['status'],right_status=b['status'],quality_delta=None,attribution=attribution)
    files.extend([root/'queue/execution_receipt.json',root/'measurement/completion.json',root/'supervision.json',tx/'registration.json'])
    for name in ['completion.json','progress.json','process_costs.json','execution_registration.json']:
        if (tx/name).exists():files.append(tx/name)
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    write(root/'verification.json',dict(passed=True,native_calls_observed=native_calls,new_independent_physical_inputs=0,source_resources=original,outcomes=outcomes,paired_comparison=paired,measurement=measurement,complete_imported_three_arm_seconds=measurement['complete_command_wall_seconds'],process_costs=read(tx/'process_costs.json'),source_sha256={str(f):sha(f) for f in files},qualification='Registered denominator retained. Complete shared imported pair includes one source control, three union repairs and required gates/materialization, not initial-route algorithm cost. Failed or incomplete roles have no candidate quality. Ordered three-arm component, not independent-input confirmation or statistical speedup. Full endpoint changes retained; no commitment or automatic freeze of whole method.'))
    print(dict(passed=True,native_calls_observed=native_calls,roles={k:v['status'] for k,v in outcomes.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preflight',action='store_true');args=p.parse_args();main(args.preflight)
