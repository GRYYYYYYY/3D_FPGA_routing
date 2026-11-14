#!/usr/bin/env python3
"""Analyze the newly accepted own-current endpoint bridge from sealed native states."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare,decide
from run_native_scope_policy_v4 import run_dir
states={'root':D/'timing_cone_bnn_dev_02/A0','owner_only':D/'bnn_strong_release_joint_dev_01/A0_release_only_weighted_soft_evaluation','target_only':D/'bnn_strong_release_joint_dev_01/A0_target_only_weighted_soft_evaluation','owner_then_target':D/'portfolio_execution_dev_01/A0_endpoint/round_001/proposal_03/transaction/current_group_evaluation'}
rows={};files=[Path(__file__).resolve()];vectors={}
for name,path in states.items():
 c=read(path/'completion.json');assert c['passed'];gate=read(run_dir(path)/'analysis_gate.json');assert gate['passed']
 v=read(path/'endpoint_vector.json');vectors[name]=v;p=read(run_dir(path)/'independent_audit.json')['physical_metrics'];finite={k:x for k,x in v['setup'].items() if isinstance(x,(float,int))};worst=min(finite.values());near={str(ns):[k for k,x in finite.items() if x<=worst+ns*1e-9] for ns in [.01,.05,.1,.2]}
 rows[name]=dict(state=str(path),CPD_ns=v['cpd_s']*1e9,wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'],near_endpoint_sets=near,current_worst_endpoints=[k for k,x in finite.items() if x==worst],comparison_from_root=compare(vectors['root'],v),evaluation_seconds=c.get('timing'),complete_single_configuration_algorithm_seconds=None)
 files += [path/'completion.json',path/'endpoint_vector.json',run_dir(path)/'analysis_gate.json',run_dir(path)/'independent_audit.json']
b=D/'portfolio_execution_dev_01/A0_endpoint/round_001/proposal_03/transaction';new=read(b/'registration.json')['roles']['current_group'];old=read(D/'bnn_strong_release_joint_dev_01/registration.json')['roles']['A0_target_only_weighted_soft'];same=sha(new['request'])==sha(old['request']);assert same
assert all(sha(path)==h for path,h in read(b/'completion.json')['source_sha256'].items())
first=decide('strict',vectors['root'],vectors['owner_only'],True);second=decide('endpoint_vector',vectors['owner_only'],vectors['owner_then_target'],True);assert not first['accepted'] and second['accepted']
files += [b/'registration.json',b/'completion.json',Path(new['request']),Path(old['request']),b/'current_group_audit/analysis.json']
write(D/'A0_endpoint_bridge_checkpoint_01.json',dict(passed=True,scope='New accepted intermediate states; cohort still running, not a terminal algorithm result',rows=rows,same_target_request_bytes=True,strict_rejects_owner_plateau=first,endpoint_accepts_successor=second,queries=read(b/'current_group_audit/analysis.json')['queries'],changed_delays=read(b/'current_group_audit/analysis.json')['changed_delays'],timing_gain_ps=(vectors['root']['cpd_s']-vectors['owner_then_target']['cpd_s'])*1e12,source_sha256={str(p):sha(p) for p in files},qualification='A0 uses its own current STA. The exact same four-target native request is flat on pristine A0 but improves CPD after a legal vector-improving owner-only step rejected by strict CPD. This supports a state/resource/schedule interaction, not a new native-search primitive or global optimality. Strong strict branch remains independent; quality-state gains and workflow costs are not a cold algorithm speedup.'))
print({k:{f:v[f] for f in ['CPD_ns','wirelength','SB_pairs','CB_sources']} for k,v in rows.items()})
