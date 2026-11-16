"""Use common-root receipts to reject additive composition before new native work."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
out=D/'robot_mechanism_composition_screen_01';assert not out.exists()
sharing=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00'
owner=D/'robot_owner_scope_pair_01/transaction'
sreg=read(sharing/'registration.json');oreg=read(owner/'registration.json')
roles={'sharing':sreg['roles']['reuse_on'],'owner':oreg['roles']['target_plus_owner']}
states={key:Path(read(path/'progress.json')[role]['evaluation']) for key,path,role in [('sharing',sharing,'reuse_on'),('owner',owner,'target_plus_owner')]}
roots={key:Path(role['state']).resolve() for key,role in roles.items()};assert roots['sharing']==roots['owner'];root=roots['sharing'];base=read(root/'endpoint_vector.json')
assert read(root/'completion.json')['passed']
comparisons={key:compare(base,read(state/'endpoint_vector.json')) for key,state in states.items()}
assert all(row['compatible'] for row in comparisons.values())
files=[Path(__file__).resolve(),D/'endpoint_timing_policy_streaming_v2.py',root/'completion.json',root/'endpoint_vector.json',sharing/'registration.json',sharing/'progress.json',owner/'registration.json',owner/'progress.json',D/'robot_owner_scope_pair_01/verification.json',D/'robot_domain_first_scope_analysis_02/completion.json']
resources={}
for key,state in states.items():
 assert read(state/'completion.json')['passed'];run=Path(read(state/'completion.json')['run']);audit=read(run/'independent_audit.json');assert audit['audit']['passed']
 pm=audit['physical_metrics'];resources[key]=dict(wirelength=pm['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=pm['sb_pairs_used'],CB_sources=pm['cb_crossing_output_sources_used'])
 files += [state/'completion.json',state/'endpoint_vector.json',run/'independent_audit.json']
rootrun=Path(read(root/'completion.json')['run']);pm=read(rootrun/'independent_audit.json')['physical_metrics'];baseline=dict(wirelength=pm['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=pm['sb_pairs_used'],CB_sources=pm['cb_crossing_output_sources_used']);files += [rootrun/'independent_audit.json',rootrun/'manifest.json']
requested={key:{(int(net),pin) for net,pins in role['removed_pins'].items() for pin in pins} for key,role in roles.items()}
nets={key:{n for n,p in req} for key,req in requested.items()}
endpoint_deltas={key:{r['endpoint_domain']:r['delta_s'] for r in cmp['changes'] if r['kind']=='setup'} for key,cmp in comparisons.items()}
sregress={key for key,delta in endpoint_deltas['sharing'].items() if delta<0};ogains={key for key,delta in endpoint_deltas['owner'].items() if delta>0}
intersection=nets['sharing']&nets['owner'];assert intersection,'Expected actual root-scope overlap, otherwise reassess'
result=dict(passed=True,source_state=str(root),same_actual_source=True,root_resources=baseline,candidate_resources=resources,root_to_candidate_endpoints={key:{k:v for k,v in row.items() if k!='changes'} for key,row in comparisons.items()},requested_connections={key:len(value) for key,value in requested.items()},shared_requested_nets=sorted(intersection),shared_requested_connections=sorted(requested['sharing']&requested['owner']),union_requested_connections=len(requested['sharing']|requested['owner']),sharing_setup_regression_components=len(sregress),owner_setup_improvement_components=len(ogains),regressions_with_same_endpoint_owner_improvement=len(sregress&ogains),scalar_addition_validated=False,whole_combination_capacity_checked=False,whole_combination_STA_checked=False,native_calls_new=0,new_independent_inputs=0,decision='Do not splice these two accepted/evaluated routes or sum their scalar deltas. Shared target network has different cut boundaries; reconstruct a union request and recompute native legality/STA to test any combined tradeoff. Such development must be separate from frozen CP1.',qualification='Both endpoint comparisons use the exact same initial root, unlike final N/D or target-only-relative comparisons. Endpoint sets expose direct overlap only; absence of overlap does not prove timing independence. Scope overlap rules out naive independent-tree composition, not existence of a legal joint candidate. No new physical benefit or formal infeasibility claim.',source_sha256={str(f):sha(f) for f in files})
out.mkdir();write(out/'completion.json',result)
write(out/'endpoint_comparisons.json',comparisons)
result['endpoint_artifact_sha256']=sha(out/'endpoint_comparisons.json');write(out/'completion.json',result)
print({k:result[k] for k in ['passed','requested_connections','shared_requested_nets','shared_requested_connections','union_requested_connections','sharing_setup_regression_components','owner_setup_improvement_components','regressions_with_same_endpoint_owner_improvement','native_calls_new']})
