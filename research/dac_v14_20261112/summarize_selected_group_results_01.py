#!/usr/bin/env python3
"""Compare completed uniform current-path group selection with all-positive scope."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'bnn_cover_selected_dev_01';c=read(b/'completion.json');assert c['passed'];reg=read(b/'registration.json');rows=[];bound={str(p):sha(p) for p in [Path(__file__).resolve(),b/'completion.json',D/'critical_group_cover_policy_01.json']}
for arm,old in [('Tf',D/'bnn_release_joint_dev_01'),('A0',D/'bnn_strong_release_joint_dev_01')]:
 name=arm+'_cover90_weighted_soft';role=reg['roles'][name];result=c['roles'][name];oldname=arm+'_combined_weighted_soft';ref=read(old/'completion.json')['roles'][oldname];oldreg=read(old/'registration.json')['roles'][oldname]
 assert role['source']==oldreg['source'] and role['state']==oldreg['state'] and role['original_budget']==oldreg['original_budget'] and role['objective']==oldreg['objective']=='weighted_soft'
 d=read(b/(name+'_decisions.json'));comparison=d['endpoint_vector']['comparison'];old_d=read(old/(oldname+'_decisions.json'))
 rows.append(dict(baseline=arm,rule='uniform 0.9 of best current-winning-path gain proxy, then minimize union of repair branches',selected_connections=len(role['queries']),old_connections=len(oldreg['queries']),
 CPD_ns=result['cpd_s']*1e9,old_CPD_ns=ref['cpd_s']*1e9,CPD_change_vs_old_ps=(result['cpd_s']-ref['cpd_s'])*1e12,resources=result['resources'],old_resources=ref['resources'],resource_change_vs_old={k:result['resources'][k]-ref['resources'][k] for k in result['resources']},
 setup_improved=comparison['setup_improved'],setup_regressed=comparison['setup_regressed'],hold_violation_regressions=comparison['hold_violation_regressions'],policies={k:v['accepted'] for k,v in d.items()},old_policies={k:v['accepted'] for k,v in old_d.items()},native_core_seconds=result['native_core_seconds'],old_native_core_seconds=ref['native_core_seconds'],evaluation=result['evaluation'],old_evaluation=ref['evaluation']))
 for p in [b/(name+'_decisions.json'),old/(oldname+'_decisions.json'),Path(result['evaluation'])/'completion.json',b/'registration.json',old/'registration.json',old/'completion.json']:bound[str(p)]=sha(p)
write(D/'bnn_selected_group_summary_01.json',dict(passed=True,rows=rows,complete_shared_workflow_seconds=c['complete_orchestrator_seconds'],complete_child_process_seconds=c['complete_child_process_seconds'],complete_single_configuration_algorithm_seconds=None,native_calls_launched=4,R1_exact_request_reused=True,source_sha256=bound,
 qualification='Two completed legal transactions under one previously frozen circuit-independent selection rule, not a per-circuit historical-best configuration. Same pristine source/native objective/domain/initial budgets and one acceptance opportunity; selected modifiable subsets intentionally differ to test grouping. Full candidate physical/FULLSTA checks pass. Shared workflow and core timing are not single-configuration cold algorithm timing. R1 selected request matches an existing completed native pair; no duplicate native test.'))
print(rows)
