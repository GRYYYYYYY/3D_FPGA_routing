#!/usr/bin/env python3
import csv,collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'retained_outside_trace_eltwise_dev_01';a=read(b/'outside_trace_analysis.json');dp=read(D/'outside_dp_table_replay_01/analysis.json');assert a['passed'] and dp['passed'];sources={str(Path(__file__)):sha(__file__)};P=D/'paper/data'
p=P/'outside_trace_v14.csv';assert not p.exists()
with p.open('w') as f:
    w=csv.writer(f);w.writerow(['arm','max_convergences','status','CPD_ns','iterations','SB_net_occupancy','CB_source_net_occupancy','planning_seconds','router_seconds','complete_process_seconds'])
    for r in a['observations']:
        pm=r['physical_metrics'];w.writerow([r['arm'],r['count'],r['status'],r['legal_cpd_ns'],r['iterations'],pm['sb_pair_net_occupancy'],pm['cb_crossing_output_source_net_occupancy'],r['planning_seconds'],r['router_seconds'],r['process_seconds']])
sources[str(p)]=sha(p);p=P/'outside_candidates_v14.csv';assert not p.exists()
with p.open('w') as f:
    keys=['event','net','pin','refresh','anchor','origin','reason','prefix_seconds','physical_seconds','premium','raw','standalone','criticality','raw_improves'];w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(a['rows'])
sources[str(p)]=sha(p);p=P/'outside_dp_replay_v14.csv';assert not p.exists()
with p.open('w') as f:
    w=csv.writer(f);w.writerow(['plan','event','net','baseline_cost','eta0_cost','eta25_cost','prior_cost','baseline_accept','eta25_accept','changed_proposal','outside_leaves'])
    for r in dp['rows']:w.writerow([r['plan'],r['event'],r['net'],r['baseline']['cost'],r['eta0']['cost'],r['eta25']['cost'],r['baseline']['previous'],r['baseline_accepted'],r['eta25_accepted'],r['proposal_changed'],r['eta25_outside']])
sources[str(p)]=sha(p)
for p in [b/'outside_trace_analysis.json',b/'input_seal.json',b/'completion.json',D/'outside_dp_core_01/unit_validation.json',D/'outside_dp_core_01/implementation_binding.json',D/'outside_dp_table_replay_01/analysis.json',D/'outside_dp_table_replay_01/registration.json']:sources[str(p)]=sha(p)
write(D/'outside_candidate_report_binding_01.json',dict(passed=True,source_sha256=sources,new_native_roles=2,new_native_legal=2,statistics=a['statistics'],DP_replay=dp['summary'],quality_native_promoted=False,qualification='Read-only native observer plus isolated extended DP core and captured-table counterfactual. No native outside-choice method integrated or routed yet. Raw costs are surrogate units and25% bound is on per-leaf surrogate benefit, not physical CPD or full search priority.'))
