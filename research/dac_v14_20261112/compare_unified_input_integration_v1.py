"""Compare fixed within-input complete pairs; preserve failures and negative effects."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import compare
root=D/'unified_input_integration_01';q=root/'queue';plan=read(root/'plan.json');closed=read(q/'completion.json')
assert closed['passed'] and closed['status']=='all_registered_roles_terminal'
assert not (root/'comparison.json').exists()
files=[Path(__file__).resolve(),root/'plan.json',q/'completion.json',q/'results.json'];pairs={};outcomes=read(q/'results.json')
for label in ['attention','robot_s23_SDC']:
 names=[label+'_'+arm for arm in ['native','domain']];configs=[read(plan['cases'][name]) for name in names]
 assert {k for k in configs[0] if configs[0][k]!=configs[1][k]}=={'domain_mode','domain_feedback'}
 files += [Path(plan['cases'][name]) for name in names]
 rows=[outcomes[n] for n in names]
 if any(r['status']!='complete_legal_verified' for r in rows):
  pairs[label]=dict(complete_quality_comparison_available=False,outcomes={n:outcomes[n] for n in names},reason='Initial failure or incomplete execution/verification remains in the paired denominator; no quality or relative benefit inferred.');continue
 native,domain=[read(r['completion']) for r in rows]
 for r in rows:files.append(Path(r['completion']))
 for case in [native,domain]:
  assert case['passed'] and case['complete_configuration_verified']
  assert all(sha(f)==h for f,h in case['source_sha256'].items())
 nroot,droot=[Path(c['initial_state']) for c in [native,domain]]
 ni,di=[read(x/'endpoint_vector.json') for x in [nroot,droot]]
 assert all(ni[k]==di[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
 assert route_body(run_dir(nroot)/'routed.route')==route_body(run_dir(droot)/'routed.route')
 nf,df=[Path(c['final_state']) for c in [native,domain]];delta=compare(read(nf/'endpoint_vector.json'),read(df/'endpoint_vector.json'));assert delta['compatible']
 for state in [nroot,droot,nf,df]:files += [state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json']
 dr={k:domain['resources'][k]-native['resources'][k] for k in native['resources']}
 total_before=native['resources']['SB_pairs']+native['resources']['CB_sources'];total_after=domain['resources']['SB_pairs']+domain['resources']['CB_sources']
 pairs[label]=dict(complete_quality_comparison_available=True,initial_full_vector_and_ordered_route_exact=True,input_is_known_historical=True,independent_frozen_confirmation=False,
  native={k:native[k] for k in ['CPD_ns','resources','complete_wall_seconds','sampled_tree_PSS_peak_kib','missing_memory_observations','owner_commits','explicit_SDC_result']},
  domain={k:domain[k] for k in ['CPD_ns','resources','complete_wall_seconds','sampled_tree_PSS_peak_kib','missing_memory_observations','owner_commits','explicit_SDC_result']},
  final_endpoint_comparison=delta,domain_minus_native_resources=dr,domain_minus_native_CPD_ns=domain['CPD_ns']-native['CPD_ns'],
  descriptive_domain_minus_native_seconds=domain['complete_wall_seconds']-native['complete_wall_seconds'],
  descriptive_full_time_overhead_percent=(domain['complete_wall_seconds']/native['complete_wall_seconds']-1)*100,
  SB_reduction_percent=None if not native['resources']['SB_pairs'] else -dr['SB_pairs']/native['resources']['SB_pairs']*100,
  total_SB_CB_reduction_percent=None if not total_before else (total_before-total_after)/total_before*100,
  interpretation='Within-input matched complete outputs. Owner escalation unrestricted in both arms; any final difference is not isolated domain-only or release-only causation. Shared-host single timings are descriptive. Keep no improvement, regressions, zero commits and no cuts.')
write(root/'comparison.json',dict(passed=True,registered_roles=len(plan['fixed_order']),verified_legal_roles=sum(v['status']=='complete_legal_verified' for v in outcomes.values()),outcomes=outcomes,pairs=pairs,native_calls_new=0,source_sha256={str(f):sha(f) for f in files},qualification='Own exact full-command quality/time/endpoint comparisons. No imported native result, no dropping failed input roles, no seed-based independent-start count, no universal full-method benefit or external application requirement inferred.'))
print(dict(passed=True,roles=len(outcomes),legal=sum(v['status']=='complete_legal_verified' for v in outcomes.values())),flush=True)
