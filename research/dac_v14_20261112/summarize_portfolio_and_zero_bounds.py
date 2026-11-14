#!/usr/bin/env python3
"""Report automated starts and exact fixed-root bounds without borrowing timing."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
from run_native_scope_policy_v4 import run_dir
rows=[];files=[Path(__file__).resolve()]
for name in ['portfolio_endpoint_replay_dev_01','portfolio_Tf_exchange_replay_dev_01','portfolio_Tf_zero_timing_replay_dev_01','portfolio_Tf_zero_resource_replay_dev_01']:
 b=D/name;c=read(b/'completion.json');assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items());r=read(b/'registration.json');initial=Path(c['initial_state']);final=Path(c['final_state']);before=read(initial/'endpoint_vector.json');after=read(final/'endpoint_vector.json');v=compare(before,after)
 steps=read(b/'steps.json');rows.append(dict(case=name,policy=c['policy'],budget_mode=c.get('budget_mode','legacy'),initial_state=str(initial),final_state=str(final),accepted_steps=c['accepted_steps'],attempted_proposals=c['attempted_proposals'],operator_stop=c['operator_stop'],CPD_before_ns=before['cpd_s']*1e9,CPD_ns=after['cpd_s']*1e9,resources=c['final_resources'],root_resources={k:r['anchor'][k] for k in c['final_resources']},setup_improved=v['setup_improved'],setup_regressed=v['setup_regressed'],native_coordinators_started=c['native_transaction_coordinators_started'],executed_segment_seconds=c['complete_current_segment_seconds'],complete_single_configuration_algorithm_seconds=None,accepted_proposals=[s['proposal'] for s in steps]))
 if c.get('budget_mode')=='zero_headroom':
  assert after['cpd_s']<=r['anchor']['CPD_s']
  assert all(c['final_resources'][k]<=r['anchor'][k] for k in c['final_resources'])
 files += [b/'completion.json',b/'registration.json',b/'steps.json',b/'attempts.json']
write(D/'portfolio_zero_bounds_summary_01.json',dict(passed=True,rows=rows,source_sha256={str(p):sha(p) for p in files},new_native_calls=0,
 qualification='Actual automated proposal/acceptance flows from sealed pristine routed starts, with exact native quality replay and fresh current-state query work where needed. No manually injected initial repairs. Timings are warm imported-state segments excluding historical creation and initial routing/static-cache preparation. Root-relative caps are not one common absolute budget across different starting methods. Pending native proposals have not been evaluated; no cold algorithm or general routability claim.'))
print([{k:r[k] for k in ['case','accepted_steps','CPD_ns','resources','operator_stop']} for r in rows])
