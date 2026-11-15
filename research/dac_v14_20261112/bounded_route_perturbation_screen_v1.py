"""Conservative path-slack screen in a fixed zero-RC single-clock timing DAG.

Sum all positive/negative edge perturbations rather than independently spending
one slack allowance several times along a path. Atom fanout multiplicity is an
upper bound on modified timing edges. A passing model never replaces fresh STA.
"""
import json,math


def screen(vector, pin_rows, changes, *, fixed_zero_rc, single_zero_clock_constraints):
    reasons=[]
    worst=vector['metrics']['least_slack_s']
    if not fixed_zero_rc or not single_zero_clock_constraints:
        reasons.append('Unsupported graph/clock-constraint class')
    domains={tuple(json.loads(key)[-2:]) for kind in ['setup','hold'] for key in vector[kind]}
    if len(domains)!=1 or vector['cpd_s']!=-worst:
        reasons.append('Native CPD is not the supported single-domain negative-worst-slack form')
    rows=[];positive=negative=0.
    for change in changes:
        net,pin=change['net'],change['pin'];delta=change['after_s']-change['before_s']
        assert math.isfinite(delta)
        if delta==0:continue
        source=pin_rows.get((net,0));row=pin_rows.get((net,pin))
        if not row or not source or row['driver'] or row['ignored'] or row['global'] or not row['route_tree_present']:
            reasons.append(f'Unknown/ineligible current sink {net}/{pin}');continue
        atoms=[atom for atom in row['atoms'] if atom.get('tnode_external',-1)>=0]
        drivers=[atom for atom in source['atoms'] if atom.get('tnode_external',-1)>=0]
        if not atoms or not drivers or any(not a.get(k+'_tags') for a in atoms for k in ['setup','hold']):
            reasons.append(f'Incomplete atom timing coverage {net}/{pin}');continue
        setup=[tag['slack_s'] for atom in atoms for tag in atom['setup_tags']]
        hold=[tag['slack_s'] for atom in atoms for tag in atom['hold_tags']]
        atom_domains={(tag['launch'],tag['capture']) for atom in atoms for kind in ['setup','hold'] for tag in atom[kind+'_tags']}
        if atom_domains!=domains or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in [*setup,*hold,row['setup_slack_s']]):
            reasons.append(f'Unconstrained/nonfinite/domain-mismatched pin {net}/{pin}');continue
        multiplicity=len({a['tnode_external'] for a in atoms})*len({a['tnode_external'] for a in drivers})
        positive+=max(delta,0.)*multiplicity;negative+=max(-delta,0.)*multiplicity
        rows.append(dict(net=net,pin=pin,delta_s=delta,atom_edge_multiplicity_upper_bound=multiplicity,
             current_setup_gap_to_worst_s=min([row['setup_slack_s'],*setup])-worst,
             current_minimum_hold_slack_s=min(hold)))
    setup_checks=[dict(net=r['net'],pin=r['pin'],available_gap_s=r['current_setup_gap_to_worst_s'],
                       total_positive_edge_bound_s=positive,passes=r['current_setup_gap_to_worst_s']>positive)
                  for r in rows if r['delta_s']>0]
    hold_checks=[dict(net=r['net'],pin=r['pin'],available_hold_s=r['current_minimum_hold_slack_s'],
                      total_negative_edge_bound_s=negative,passes=r['current_minimum_hold_slack_s']>negative)
                 for r in rows if r['delta_s']<0]
    supported=not reasons
    return dict(supported=supported,abstention_reasons=reasons,changed_connections=rows,
        total_positive_timing_edge_perturbation_bound_s=positive,total_negative_timing_edge_perturbation_bound_s=negative,
        setup_checks=setup_checks,hold_checks=hold_checks,
        model_no_worst_setup_degradation=supported and all(x['passes'] for x in setup_checks),
        model_no_new_or_increased_hold_violation=supported and all(x['passes'] for x in hold_checks),
        model_screen_passed=supported and all(x['passes'] for x in [*setup_checks,*hold_checks]),
        original_worst_setup_paths_unmodified_under_model=supported and all(r['current_setup_gap_to_worst_s']>0 for r in rows),
        native_FULL_STA_required=True,used_for_acceptance=False,
        qualification='Fixed timing-DAG perturbation screen only. Every path accumulates at most the sum of positive/negative changed timing edges; any path containing a positive change has the recorded current setup gap, and any path containing a negative change has the recorded current hold slack. Distinct atom-driver/receiver combinations conservatively bound repeated cluster-connection contributions. Unknown mappings/constraints abstain. Zero RC, unchanged packed/placed/clock/logic mapping and exact declared connection changes are prerequisites. Endpoint vectors may trade setup slack. Native route legality, actual native arithmetic/STA and original envelopes remain independent mandatory gates; no tolerance or predicted quality substitutes for them.')
