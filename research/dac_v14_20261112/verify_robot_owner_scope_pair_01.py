"""Audit exact same-root scope contrast and retain all native outcome classes."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy_streaming_v2 import compare
from multiobjective_acceptance_v2 import decide

root=D/'robot_owner_scope_pair_01'
def check_pair(plan,reg):
    assert list(reg['roles'])==plan['fixed_order']==['target_only','target_plus_owner']
    a,b=reg['roles'].values();group=read(Path(plan['selector'])/'groups.json')[plan['selector_rank']]
    assert a['state']==b['state']==plan['source_state']
    for key in ['source','baseline','objective','seed_order','original_budget','fixed_resource_limits','fixed_target_paths','crossing_reuse_enabled','domain_failure_release','explicit_crossings','allowed_resource_kind']:
        assert a[key]==b[key],key
    assert not a['crossing_reuse_enabled'] and not a['domain_failure_release'] and a['explicit_crossings'] is None
    target,owner=group['target_net'],group['owner_net']
    assert a['queries']==[q for q in b['queries'] if q['net']==target]==plan['target_queries']
    assert b['queries']==group['queries']==plan['joint_queries']
    assert a['removed_pins']=={str(target):group['target_pins']}
    assert b['removed_pins']=={str(target):group['target_pins'],str(owner):group['owner_pins']}
    # Parse executable request text independently of the serializer.
    for role in [a,b]:
        lines=Path(role['request']).read_text().splitlines();n=int(lines[0]);cuts={}
        for line in lines[1:n+1]:
            tokens=list(map(int,line.split()));assert tokens[1]==len(tokens[2:]);cuts[str(tokens[0])]=tokens[2:]
        assert cuts==role['removed_pins'] and lines[n+1]=='0' and int(lines[n+2])==len(role['queries'])
        actual=[dict(net=int(r.split()[0]),pin=int(r.split()[1]),raw_criticality=float(r.split()[2])) for r in lines[n+3:]]
        assert actual==role['queries']
    return group

def main(preflight=False):
    plan=read(root/'plan.json');reg=read(root/'prepared_transaction_registration.json');group=check_pair(plan,reg)
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    before_state=Path(plan['source_state']);before=read(before_state/'endpoint_vector.json');original=require_publication_proof(before_state)['resource_axes']
    files=[Path(__file__).resolve(),root/'plan.json',root/'prepared_transaction_registration.json']
    if preflight:
        write(root/'preflight.json',dict(passed=True,scope_only_contrast=True,exact_target_weights_and_relative_order=True,selected_before_outcomes=True,unrestricted_both_roles=True,native_calls_new=0,source_sha256={str(f):sha(f) for f in files}));print(dict(passed=True,native_calls_new=0));return
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
        assert audit['passed'] and domain['passed'] and not domain['enabled']
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
    paired=None
    if all(v['quality'] is not None for v in outcomes.values()):
        a,b=outcomes.values();ra,rb=[v['quality']['resources'] for v in [a,b]]
        paired=dict(CPD_delta_ns=b['quality']['CPD_ns']-a['quality']['CPD_ns'],resource_deltas={k:rb[k]-ra[k] for k in ra},endpoint_comparison=compare(read(Path(a['evaluation'])/'endpoint_vector.json'),read(Path(b['evaluation'])/'endpoint_vector.json')),attribution='Added owner coordination scope under unrestricted search; no domain/release attribution or complete-method gain.')
    files.extend([root/'queue/execution_receipt.json',root/'measurement/completion.json',root/'supervision.json',tx/'registration.json'])
    for name in ['completion.json','progress.json','process_costs.json','execution_registration.json']:
        if (tx/name).exists():files.append(tx/name)
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    write(root/'verification.json',dict(passed=True,native_calls_observed=native_calls,new_independent_physical_inputs=0,source_resources=original,outcomes=outcomes,paired_comparison=paired,measurement=measurement,complete_imported_pair_seconds=measurement['complete_command_wall_seconds'],process_costs=read(tx/'process_costs.json'),source_sha256={str(f):sha(f) for f in files},qualification='Registered denominator retained. Complete shared imported pair includes one source control, both native repairs and required gates/materialization, not initial-route algorithm cost. Failed or incomplete roles have no candidate quality. Ordered pair not statistical speedup. Full endpoint changes retained; no commitment or automatic freeze of whole method.'))
    print(dict(passed=True,native_calls_observed=native_calls,roles={k:v['status'] for k,v in outcomes.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preflight',action='store_true');args=p.parse_args();main(args.preflight)
