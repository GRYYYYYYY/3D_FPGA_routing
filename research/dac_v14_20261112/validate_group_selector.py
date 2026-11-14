#!/usr/bin/env python3
"""Compare automatic selection to exhaustive references, including donor overlap."""
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from critical_action_patterns import patterns
from select_critical_action_group import select
start=time.monotonic();ref=read(D/'critical_group_cover_reference_01/completion.json');obs=read(D/'timing_cone_bnn_dev_02/completion.json');assert ref['passed'];checks=[];files=[Path(__file__).resolve(),D/'select_critical_action_group.py',D/'critical_action_patterns.py',D/'critical_group_cover_reference_01/completion.json']
for arm,r in ref['results'].items():
 path=Path(obs['roles'][arm]['cone']);c=read(path);p=patterns(c,r['actions']);files.append(path)
 for fraction in [.1,.5,.9,1.]:
  maximum=max(x['min_current_winning_path_gain_ns'] for x in r['profiles']);eligible=[x for x in r['profiles'] if x['all_current_paths_covered'] and x['min_current_winning_path_gain_ns']>=fraction*maximum]
  best=min(eligible,key=lambda x:(x['repair_connections'],-x['min_current_winning_path_gain_ns'],x['targets']))
  actual=select(p,r['actions'],fraction);assert actual['exact_within_proxy'] and actual['targets']==list(map(tuple,best['targets'])),(arm,fraction)
  checks.append(dict(state=arm,fraction=fraction,targets=actual['targets'],repair_connections=actual['profile']['repair_connections'],visited=actual['visited_nodes'],exact_match=True))
# A target already included as another action's donor has zero incremental
# search count. The higher-gain tie must survive primary-cost pruning.
actions=[dict(target=[1,1],donors=[[2,1]],atom_nodes=[],optimistic_gain_ns=1.),dict(target=[2,1],donors=[[1,1]],atom_nodes=[],optimistic_gain_ns=1.)]
p=dict(pattern_counts={3:1});a=select(p,actions,.5);assert a['selected']==[0,1] and a['profile']['repair_connections']==2
checks.append(dict(case='zero_incremental_donor_tie',passed=True))
guarded=select(p,actions,.9,timeout_seconds=1e-300);assert not guarded['exact_within_proxy'] and guarded['profile']['all_current_paths_covered']
checks.append(dict(case='planning_time_guard',feasible_incumbent_preserved=True,optimality_not_claimed=True))
out=D/'critical_group_selector_validation_01.json';assert not out.exists();write(out,dict(passed=True,checks=checks,source_sha256={str(p):sha(p) for p in files},complete_process_seconds=time.monotonic()-start,native_calls=0,
 qualification='Automatic policy selection agrees with exhaustive existing action subsets for four uniform fractions; no native routing or post-repair CPD claim. Registered native cohorts not modified.'))
print('Validated',len(checks),'selection cases',flush=True)
