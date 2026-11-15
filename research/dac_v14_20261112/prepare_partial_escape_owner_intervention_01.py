"""Freeze one complete proposal and matched native two-connection controls."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from current_resource_bundle_v2 import serialize_request

root=D/'partial_escape_owner_intervention_01';root.mkdir(exist_ok=False)
candidate=D/'R1_escape_owner_BFS_candidate_01';proof=read(candidate/'completion.json')
assert proof['passed'] and proof['status']=='complete_structural_candidate_pending_native_FULL_STA'
assert all(sha(candidate/n)==h for n,h in proof['artifact_sha256'].items())
selection=read(Path(proof['selection'])/'groups.json')[0]
assert (selection['target_net'],selection['owner_net'])==(proof['selected_target'],proof['selected_owner'])
old=read(D/'R1_owner_release_joint_probe_01/prepared_transaction_registration.json')
base=old['roles']['joint_native'];assert base['state']==proof['state']
removed={str(proof['selected_target']):[proof['target_local_pin']],str(proof['selected_owner']):proof['selected_owner_pins']}
allowed={(int(n),p) for n,pins in removed.items() for p in pins}
queries=[q for q in base['queries'] if (q['net'],q['pin']) in allowed]
cuts=[dict(net=int(n),pins=pins,ordered_queries=[q for q in queries if q['net']==int(n)]) for n,pins in removed.items()]
request,_,queries=serialize_request(cuts);assert len(queries)==2
(root/'request.txt').write_text(request)
(root/'domain_nets.txt').write_text('1\n'+str(proof['selected_target'])+'\n')
cb=read(Path(proof['selection'])/'certificates.json')[0]['only_OPIN']
(root/'target_CB_sources.txt').write_text(f"1\n{proof['selected_target']} 1 {cb}\n")
files=[Path(__file__).resolve(),D/'run_partial_escape_owner_transactions_v1.py',D/'audit_partial_escape_owner_domain_v1.py',
       D/'queue_partial_escape_owner_intervention_01.py',D/'verify_partial_escape_owner_intervention_v1.py',
       D/'run_serial_census_state_analysis_v1.py',D/'native_resource_census_stage_01/binding.json',
       D/'native_resource_census_stage_01/bin/vpr',candidate/'completion.json',candidate/'candidate.route',
       root/'request.txt',root/'domain_nets.txt',root/'target_CB_sources.txt']
assert all(p.exists() for p in files)
bindings={str(p):sha(p) for p in files}
roles={}
for name,enabled in [('native_2pins',False),('retained_CB_2pins',True)]:
 role=copy.deepcopy(base)
 role.update(scope='same_selected_owner_and_only_target_local_sink_preserving_other_target_branches',
   request=str(root/'request.txt'),queries=queries,removed_pins=removed,domain_target_net=proof['selected_target'],
   crossing_reuse_enabled=enabled,crossing_domain=str(root/'domain_nets.txt'),
   explicit_crossings=str(root/'target_CB_sources.txt') if enabled else None,allowed_resource_kind='CB',
   fixed_target_paths=False,domain_failure_release=False)
 role['source_sha256'].update(bindings)
 roles[name]=role
reg=copy.deepcopy(old);reg.update(roles=roles,current_resource_selector_after_commit=True)
reg['source_sha256'].update(bindings)
write(root/'prepared_transaction_registration.json',reg)
write(root/'plan.json',dict(source_state=proof['state'],candidate_construction=str(candidate),candidate_route=proof['candidate_route'],
 candidate_route_sha256=proof['candidate_sha256'],fixed_order=['BFS_candidate_LOAD','native_2pins','retained_CB_2pins'],
 target_net=proof['selected_target'],owner_net=proof['selected_owner'],removed_pins=removed,queries=queries,
 original_budget=base['original_budget'],fixed_resource_limits=base['fixed_resource_limits'],
 predecessor=str(D/'R1_owner_release_joint_probe_01/queue'),prepared_files=[str(p) for p in files],
 qualification='Separate two-connection development intervention on prospectively selected owner; only target local pin plus owner pin, other target branches retained. One concrete deterministic same-layer BFS proposal is FULL/STA-evaluated first; then matched private-binary unrestricted/retained-CB-domain native searches on identical two-connection scope/current weights/ordering/envelopes. BFS construction changes search/objective, not only domain, and imported LOAD uses the explicitly different Census STA binary; equivalence is checked from actual physical/native evidence, never assumed. Compare against same-source whole-five-connection pair separately as scope intervention. No original actor commit, no selection over final quality, all failures/rejections retained. Global slot/predecessor ownership unchanged. Full configuration/cold speedup remains unknown; offline selection/construction and actual imported native/validation costs remain separate.'))
print(dict(prepared=True,root=str(root),scope=removed,structural_proposal_only=proof['structural_full_route_resources']),flush=True)
