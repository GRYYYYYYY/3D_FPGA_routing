#!/usr/bin/env python3
"""Summarize the completed frozen strong-baseline cohort and full observed cost."""
import collections,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'bnn_strong_release_joint_dev_01';c=read(b/'completion.json');assert c['passed']
assert all(sha(p)==h for p,h in c['source_sha256'].items())
reg=read(b/'registration.json');costs=read(b/'process_costs.json');rows=[];bound={str(b/'completion.json'):sha(b/'completion.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
aggregate=collections.defaultdict(float)
for name,role in reg['roles'].items():
 r=c['roles'][name];assert r['status']=='legal_evaluated'
 d=read(b/(name+'_decisions.json'));cp=d['endpoint_vector']['comparison'];current=read(Path(role['state'])/'endpoint_vector.json');old=role['original_budget'];res=r['resources']
 phases={}
 for item in costs:
  if item['tag'].startswith(name+'_'):
   phase=item['tag'][len(name)+1:];phases[phase]=item['complete_process_seconds'];aggregate[phase]+=item['complete_process_seconds']
 changed=cp['changes'];setup=[x for x in changed if x['kind']=='setup'];negative=[x for x in setup if x['delta_s']<0]
 row=dict(role=name,baseline=role['baseline'],scope=role['scope'],objective=role['objective'],source_state=role['state'],evaluation=r['evaluation'],status=r['status'],
 CPD_before_ns=current['cpd_s']*1e9,CPD_ns=r['cpd_s']*1e9,resources=res,resource_delta={k:res[k]-old[k] for k in res},
 setup_improved=cp['setup_improved'],setup_regressed=cp['setup_regressed'],hold_violation_regressions=cp['hold_violation_regressions'],
 worst_setup_regression_ps=max([-x['delta_s']*1e12 for x in negative],default=0),
 accepted={k:v['accepted'] for k,v in d.items()},process_phases_seconds=phases,complete_arm_child_process_seconds=sum(phases.values()),native_repair_core_seconds=r['native_core_seconds'],complete_single_configuration_seconds=None)
 rows.append(row)
 for p in [b/(name+'_decisions.json'),Path(r['evaluation'])/'completion.json']:bound[str(p)]=sha(p)
assert len(rows)==12 and math.isclose(sum(aggregate.values()),c['complete_child_process_seconds'],abs_tol=1e-9)
write(D/'bnn_strong_scope_summary_01.json',dict(passed=True,rows=rows,status_counts=dict(collections.Counter(r['status'] for r in rows)),
 shared_workflow_seconds=c['complete_orchestrator_seconds'],executed_child_seconds=c['complete_child_process_seconds'],shared_coordinator_and_unattributed_seconds=c['complete_orchestrator_seconds']-c['complete_child_process_seconds'],
 process_phase_seconds=dict(aggregate),native_core_seconds_sum=sum(r['native_repair_core_seconds'] for r in rows),native_calls_launched=24,
 controls='Within each pristine A0/R1 source, paired objectives have identical full-device domain, target selection, request order, modifiable-tree scope and repair opportunity. Cost and capacity treatment differ together; not a single-factor capacity ablation.',
 interpretation='A0: only combined lowers CPD; target-only/owner-only weighted preserve resource tradeoffs. R1: target-only reaches the same CPD with fewer resources and no endpoint regressions, whereas adding donor changes is unnecessary in this state. Native weighted weakly improves quality versus physical-capacity at every paired scope; whole configuration timing is still unknown. The greedy target-only physical A0 regression has independently reproduced temporary-state capacity competition.',
 qualification='12 legal development observations with complete FULL/STA and physical audits. Each arm cost includes executed preparation/native search, candidate audit, full candidate evaluation and successor selection as present; input graph/cache construction and original routing excluded. Shared12-arm workflow and core sums are not single-configuration algorithm timing. 24 launched native processes = diagnostic12 + candidate FULLSTA12, not initial router executions.',source_sha256=bound))
print(dict(roles=len(rows),shared_seconds=c['complete_orchestrator_seconds'],phases=dict(aggregate),core_sum_seconds=sum(r['native_repair_core_seconds'] for r in rows)))
