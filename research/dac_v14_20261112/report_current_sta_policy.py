#!/usr/bin/env python3
"""Summarize completed automatic branches, endpoint gates and actual costs."""
import csv
import json
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare

def endpoint_summary(vector):
    values={}
    for key,value in vector['setup'].items():
        if not isinstance(value,(int,float)) or not math.isfinite(value):continue
        identity=tuple(json.loads(key)[:3]);values[identity]=min(values.get(identity,math.inf),value)
    worst=min(values.values())
    return dict(total_endpoint_rows=len(vector['endpoint_ids']),setup_domain_components=len(vector['setup']),
                finite_constrained_endpoints=len(values),worst_setup_slack_s=worst,
                near_0p2ns_of_current_worst=sum(v<=worst+.2e-9 for v in values.values()),
                qualification='Near-critical count uses each current state’s own worst endpoint slack; moving-window count alone is not an improvement criterion.')

rows=[];sources=[]
for role,batch,initial in [('R1',D/'current_sta_policy_R1_01',D/'native_endpoint_vector_dev_01/R1'),
                            ('Tf',D/'current_sta_policy_Tf_02',D/'joint_endpoint_diagnostics_01/Tf')]:
    done=read(batch/'completion.json');before=read(initial/'endpoint_vector.json')
    original=Path(read(initial/'completion.json')['run'])
    for policy,outcome in done['outcomes'].items():
        state=Path(outcome['state']);current=Path(read(state/'completion.json')['run']);after=read(state/'endpoint_vector.json')
        change=compare(before,after);change.pop('changes',None)
        accepted=[r for r in read(batch/'decisions.json') if r['policy']==policy and r.get('decision',{}).get('accepted')]
        rejected=[r for r in read(batch/'decisions.json') if r['policy']==policy and not r.get('decision',{}).get('accepted')]
        rows.append(dict(role=role,policy=policy,status=outcome['status'],legal=read(state/'completion.json')['passed'],
          initial_state=str(initial),final_state=str(state),before_cpd_ns=before['cpd_s']*1e9,after_cpd_ns=after['cpd_s']*1e9,
          accepted=len(accepted),rejected=len(rejected),endpoint_comparison=change,
          endpoints_before=endpoint_summary(before),endpoints_after=endpoint_summary(after),
          resources_before=read(original/'independent_audit.json')['physical_metrics'],resources_after=read(current/'independent_audit.json')['physical_metrics'],
          complete_shared_orchestrator_seconds=done['complete_orchestrator_seconds'],
          cost_scope='Shared two-policy orchestration with explicitly reused observations/queries/transactions. Not an independent per-arm or cold-start full-method timing.',
          accepted_targets=[r['candidate']['targets'] for r in accepted]))
        sources += [state/'completion.json',state/'endpoint_vector.json',current/'independent_audit.json']
    sources += [batch/'completion.json',batch/'decisions.json',batch/'registration.json',batch/'process_costs.json',initial/'endpoint_vector.json']
comparisons=read(D/'joint_endpoint_diagnostics_01/policy_comparison.json')
write(D/'current_sta_policy_summary_01.json',dict(passed=True,rows=rows,
  fixed_constraints='Requested eltwise_layer.sdc absent. Export actual native default virtual_io_clock, clk, clk_mem; cross netlist-clock domains ignored, virtual-I/O domains retained. Exact applied constraint echo is sealed per state.',
  policy='Strict: CPD strictly lower. Endpoint: CPD nonincrease AND every fixed endpoint/domain setup slack nondecreasing and at least one increasing. Both require FULL/physical legality and no increase in negative hold violations. Full native precision, no acceptance epsilon.',
  initial_joint_failure='Native legal four-target Tf transaction regressed CPD6.208121572→6.734843794ns and was rejected; 78 blocker sinks/67 physical changes. Not a reason to stop research.',
  native_control='Actual VPR connection router and update_from_heap exercised, same retained nodes/anchors/full-device scope verified. After pressure1 rejection, pressure10 produces exactly the same complete route trees as the hard-capacity operator for two R1 targets; FULL/STA plateaus rejected by both policies. Joint-native scope still pending.',
  formal_current_prototype_timing='Unknown; do not substitute historical U timing. Original 78-sink transaction lacked prebinding timer; recorded549.936s excludes that work. New outer wrappers and loop costs include preparation/evaluation/failures with reuse disclosed.',
  quality_promoted=False,research_complete=False,public_snapshot='f7167bd',this_work_pushed=False,
  source_sha256={str(p):sha(p) for p in dict.fromkeys(sources)}))
path=D/'paper/data/current_sta_policy_v14.csv'
with path.open('w') as f:
    writer=csv.DictWriter(f,fieldnames=['role','policy','before_cpd_ns','after_cpd_ns','accepted','rejected','setup_improved','setup_regressed','near_endpoints_before','near_endpoints_after','sb_before','sb_after','cb_before','cb_after','wire_before','wire_after','shared_orchestrator_s'])
    writer.writeheader()
    for r in rows:
        writer.writerow(dict(role=r['role'],policy=r['policy'],before_cpd_ns=r['before_cpd_ns'],after_cpd_ns=r['after_cpd_ns'],accepted=r['accepted'],rejected=r['rejected'],
            setup_improved=r['endpoint_comparison']['setup_improved'],setup_regressed=r['endpoint_comparison']['setup_regressed'],
            near_endpoints_before=r['endpoints_before']['near_0p2ns_of_current_worst'],near_endpoints_after=r['endpoints_after']['near_0p2ns_of_current_worst'],
            sb_before=r['resources_before']['sb_pairs_used'],sb_after=r['resources_after']['sb_pairs_used'],cb_before=r['resources_before']['cb_crossing_output_sources_used'],cb_after=r['resources_after']['cb_crossing_output_sources_used'],
            wire_before=r['resources_before']['planar_wirelength_excluding_sb_half_nodes'],wire_after=r['resources_after']['planar_wirelength_excluding_sb_half_nodes'],shared_orchestrator_s=r['complete_shared_orchestrator_seconds']))
print([(r['role'],r['policy'],r['after_cpd_ns'],r['accepted'],r['rejected']) for r in rows])
