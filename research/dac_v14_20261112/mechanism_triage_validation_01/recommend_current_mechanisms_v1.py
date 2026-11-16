"""Development mechanism triage, not a predictor of QoR or a live-controller patch.

Resource-owner eligibility and timing-owner evidence are deliberately different.
All actions still require the fixed whole-candidate checks/acceptance/terminal
rules. No circuit, net, architecture label or measured outcome selects a branch.
"""
import argparse,json,math

def recommend(state):
    assert state['objective'] in ['resources_under_timing','timing_under_resources']
    def result(action,reason,**extra):
        return dict(next_mechanism=action,reason=reason,
            objective=state['objective'],fixed_envelope=state.get('fixed_envelope'),
            expected_gain=None,complete_candidate_acceptance_required=True,
            global_optimality_or_research_stop=False,installed_in_frozen_controller=False,**extra)
    if not state['legal_root']:
        assert state.get('sharing_scopes') is None and state.get('eligible_owner_groups') is None
        return result('retain_initial_outcome','No legal root; mechanism applicability/quality remain unknown.')
    envelope=state['fixed_envelope'];assert math.isfinite(envelope['CPD_limit_s']) and envelope['CPD_limit_s']>0
    assert set(envelope['resource_limits'])=={'wirelength','SB_pairs','CB_sources'}
    assert all(type(v) is int and v>=0 for v in envelope['resource_limits'].values())
    failure=state.get('guided_failure')
    if failure is not None:
        assert state.get('private_transaction_active') is True
        assert failure['operational_search_failed'] is True
        active=state['active_domain_nets'];released=state.get('already_released_nets',[])
        assert len(active)==len(set(active)) and len(released)==len(set(released))
        net=failure['net'];assert net in active and net not in released
        return result('release_only_failed_net','Actual guided search failed; preserve other private restorations and domains. No infeasibility certificate.',
            released_net=net,remaining_guided_nets=[n for n in active if n!=net])
    if state.get('private_transaction_active'):
        return result('finish_current_group','Intermediate states do not select another mechanism or require separate CPD improvement.')
    if state['objective']=='timing_under_resources':
        queries=state.get('timing_queries')
        if queries is None or not queries['complete'] or queries['count']==0:
            return result('query_current_timing_targets','Need current selected-connection physical witnesses before timing-owner expansion.')
        n=queries['count'];positive=queries['positive_gain_count'];conflict=queries['capacity_conflicting_count'];joint=queries['positive_gain_capacity_conflicts']
        assert all(type(x) is int for x in [n,positive,conflict,joint])
        assert 0<=joint<=min(positive,conflict)<=max(positive,conflict)<=n
        if positive==0:
            return result('advance_selected_timing_menu','No positive witness in these selected connections; capacity conflicts alone do not motivate timing-owner expansion. Other targets are not globally excluded.')
        if joint>0:
            groups=state.get('eligible_owner_groups')
            if groups is None:return result('screen_timing_blocking_owners','A positive delay witness conflicts with current capacity; screen the relevant owner scope and margins.')
            if groups>0:return result('evaluate_timing_owner_group','Positive conflicting witness and eligible coordinated scope; native whole-candidate acceptance remains decisive.')
        return result('evaluate_timing_target_group','Positive selected-connection witness; do not infer a useful owner scope from separate marginal conflict counts.')
    scopes=state.get('sharing_scopes');groups=state.get('eligible_owner_groups')
    assert scopes is None or type(scopes) is int and scopes>=0
    assert groups is None or type(groups) is int and groups>=0
    if not state.get('sharing_menu_closed',False):
        if scopes is None:return result('screen_current_sharing_cuts','Need current crossing redundancy, retained alternatives and slack-eligible complete cuts.')
        if scopes>0:return result('evaluate_matched_sharing_group','Screened applicability permits a same-scope native/domain proposal; no final benefit follows from the count.')
    if groups is None:
        return result('screen_resource_blocking_owners','Sharing menu closes or has no eligible cut. Resource coordination uses avoidable crossing excess and slack-eligible target/owner cuts, without requiring a positive delay witness.')
    if groups>0:return result('evaluate_resource_owner_group','Eligible capacity-certified resource scope; zero predicted CPD gain does not exclude a useful vertical-resource tradeoff.')
    return result('apply_fixed_resource_terminal_rule','No eligible current sharing/owner move. Preserve legal observations for terminal wire selection, then continue the registered timing stage.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');args=p.parse_args()
    with open(args.input) as f:state=json.load(f)
    print(json.dumps(recommend(state),indent=2))
