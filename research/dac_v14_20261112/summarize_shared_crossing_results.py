#!/usr/bin/env python3
"""Summarize all frozen resource pairs, costs, tails and domain adoption."""
import collections,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
from run_native_scope_policy_v4 import run_dir
b=D/'shared_crossing_repair_dev_01';c=read(b/'completion.json');assert c['passed'];reg=read(b/'registration.json');rows=[];cost=read(b/'process_costs.json');bound=[Path(__file__).resolve(),b/'completion.json',b/'registration.json',b/'progress.json',b/'process_costs.json',Path(reg['shared_design_requirements'])]
for name,r in read(b/'progress.json').items():
 assert r['status']=='legal_evaluated';role=reg['roles'][name];state=Path(r['evaluation']);before=read(Path(role['state'])/'endpoint_vector.json');after=read(state/'endpoint_vector.json');diff=compare(before,after);finite={k:x for k,x in after['setup'].items() if isinstance(x,(int,float)) and math.isfinite(x)};worst=min(finite.values());regressed=[x for x in diff['changes'] if x['kind']=='setup' and x['delta_s']<0];domain=b/(name+'_domain_audit.json');assert read(domain)['passed'];selection=b/(name+'_successor_cone.json');root=role['original_budget'];near={}
 for label,v in [('before',before),('after',after)]:
  values=[x for x in v['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x)];w=min(values);near[label]={str(ns):sum(x<=w+ns*1e-9 for x in values) for ns in [.05,.1,.2,.5,1.]}
 phases=collections.defaultdict(float)
 for x in cost:
  if x['tag'].startswith(name+'_'):
   tag=x['tag'][len(name)+1:];phases[tag]+=x['complete_process_seconds']
 rows.append(dict(role=name,baseline=role['baseline'],crossing_reuse_enabled=role['crossing_reuse_enabled'],CPD_ns=after['cpd_s']*1e9,CPD_exactly_unchanged=after['cpd_s']==before['cpd_s'],resources=r['resources'],resource_delta={k:r['resources'][k]-root[k] for k in r['resources']},policies=r['policies'],changed_connections=r['changed_connections'],setup_improved=diff['setup_improved'],setup_regressed=diff['setup_regressed'],hold_violation_regressions=diff['hold_violation_regressions'],closest_regressed_margin_ns=min((finite[x['endpoint_domain']]-worst)*1e9 for x in regressed) if regressed else None,near_endpoint_counts=near,domain_audit=str(domain),domain_sources=read(domain).get('actual_candidate_sources'),native_core_seconds=r['native_core_seconds'],nested_process_costs_seconds=dict(phases),sum_sequential_process_seconds=sum(phases.values()),complete_single_configuration_algorithm_seconds=None,evaluation=str(state)))
 bound += [state/'completion.json',state/'endpoint_vector.json',domain,b/(name+'_decisions.json')]
write(D/'shared_crossing_results_summary_01.json',dict(passed=True,rows=rows,whole_six_arm_development_workflow_seconds=c['complete_orchestrator_seconds'],native_repair_core_seconds=sum(r['native_core_seconds'] for r in rows),complete_single_configuration_algorithm_seconds=None,source_sha256={str(p):sha(p) for p in bound},qualification='Within-root off/on pairs only differ in optional crossing-source domain, with real physical delays and complete native/physical/STA gates. Each ON saves one CB at +92/+96 wire and no CPD change, while endpoint vector regresses; accepted only by registered fixed timing/resource envelope. Small local tradeoffs, not cumulative savings, critical-path improvement, area/power savings or whole-algorithm speedup. Stronger original native reconvergence remains a joint-frontier comparator.'))
print([(r['role'],r['setup_regressed'],r['closest_regressed_margin_ns'],r['sum_sequential_process_seconds']) for r in rows],flush=True)
