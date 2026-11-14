#!/usr/bin/env python3
"""Prepare the complete private native-count/final-independent acceptance flow."""
from retained_prefix_workflow import D,read,write,sha

source=D/'run_direct_scope_shadow_resource_repair.py'
target=D/'run_native_census_resource_repair.py';assert not target.exists();t=source.read_text()
def rep(a,b,count=1):
    global t
    assert t.count(a)==count,(t.count(a),a[:120])
    t=t.replace(a,b)
rep('from pool_state_evaluator_v7 import PoolStateEvaluator','from pool_state_evaluator_v8 import PoolStateEvaluator\nfrom state_resource_assurance import resource_assurance,require_publication_proof')
rep('from current_crossing_share_selector_v2 import select','from current_crossing_share_selector_v3 import select')
rep("D/'pool_state_evaluator_v7.py'","D/'pool_state_evaluator_v8.py'")
rep("D/'current_crossing_share_selector_v2.py'","D/'current_crossing_share_selector_v3.py'")
rep("files += [D/'direct_native_transaction_audit.py',", "files += [D/'state_resource_assurance.py',D/'native_census_state_evaluator_validation_01/completion.json',D/'resource_assurance_selector_validation_01/completion.json',D/'direct_native_transaction_audit.py',")
rep("assert all(read(D/n)['passed'] for n in ['direct_native_transaction_validation_01/completion.json'", "assert all(read(D/n)['passed'] for n in ['native_census_state_evaluator_validation_01/completion.json','resource_assurance_selector_validation_01/completion.json','direct_native_transaction_validation_01/completion.json'")
rep(" x=read(run_dir(state)/'independent_audit.json')['physical_metrics'];return dict(wirelength=x['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=x['sb_pairs_used'],CB_sources=x['cb_crossing_output_sources_used'])", " return resource_assurance(state)['resource_axes']")
rep('native_resource_census_shadow=True,','native_resource_census_shadow=False,resource_assurance_policy=\'native_per_candidate_final_independent\',')
rep("question='Does direct actual-candidate scope/edge/capacity audit preserve the complete automatic own-current trajectory while reducing construction/check overhead against the same globally fixed seed-policy and independent-physical-audit actor?' ",
    "question='Can actual native counters replace repeated complete independent physical audits during private acceptance while preserving the direct-scope actor trajectory and passing an explicit final independent route check?' ")
rep("Independent direct-scope engineering version; original cohorts unchanged. No alternate candidate route is serialized or installed by the auditor. Full independent physical audits and native counter shadow checks remain. Shadow counts never replace independent audits in this version.",
    "Independent native-count acceptance engineering version; original cohorts unchanged. Direct actual scope/edges/capacity and native FULL/freshSTA remain per transaction; actual native resource counts are explicit native assurance, not an independent audit. Selected final state must pass independent physical validation; other deferred states need their own validation before publication.")
rep(" view=bound_native_resources(worker,kind);expected=read(run_dir(state)/'independent_audit.json');assert expected['audit']['passed'];assert all(value==expected['physical_metrics'][key] for key,value in view['physical_metrics'].items()),'Native counter diverged from independent physical audit';write(output,dict(passed=True,native_view=view,independent_audit=str(run_dir(state)/'independent_audit.json'),independent_audit_sha256=sha(run_dir(state)/'independent_audit.json'),qualification='Shadow check only; acceptance still uses full independent physical audit and native FULL/freshSTA.'))",
    " view=bound_native_resources(worker,kind);expected=resource_assurance(state);assert all(value==expected['physical_metrics'][key] for key,value in view['physical_metrics'].items()),'Actual source/candidate/restored resource counts disagree with the current state';write(output,dict(passed=True,native_view=view,state_resource_evidence=expected['evidence'],state_assurance_kind=expected['assurance_kind'],independent_audit_performed=False,qualification='Native counter/source recovery check only. Final selected state needs separate complete independent physical verification.'))")
rep("first=evaluator.evaluate(source/'routed.route',b/'initial',physical_reference=initial,native_observation=initial_worker)",
    "first=evaluator.evaluate(source/'routed.route',b/'initial',native_resource_worker=initial_worker,native_resource_kind='input',physical_reference=initial,native_observation=initial_worker)")
rep("material=evaluator.evaluate(run_dir(current)/'routed.route',tx/name,physical_reference=current,native_observation=worker)",
    "material=evaluator.evaluate(run_dir(current)/'routed.route',tx/name,native_resource_worker=worker,native_resource_kind='input',native_observation=worker)")
rep('result=evaluator.evaluate(actual,state,native_observation=view)',
    "result=evaluator.evaluate(actual,state,native_resource_worker=worker,native_resource_kind='candidate',native_observation=view)")
rep('evaluator.close();costs.append(', 'evaluator.close(final_state=current);require_publication_proof(current);costs.append(')
rep('complete independent physical/FULLSTA→fixed-budget accept/rollback flow.',
    'native-census/FULLSTA→fixed-budget private accept/rollback→selected-final independent physical validation flow.')
compile(t,str(target),'exec');target.write_text(t)
write(D/'native_census_resource_actor_preparation_01.json',dict(passed=True,
    source=str(source),source_sha256=sha(source),target=str(target),target_sha256=sha(target),
    native_calls=0,route_calls=0,actual_actor_integration_pending=True,
    actual_census_state_replay='native_census_state_evaluator_validation_01',
    assurance_selector_replay='resource_assurance_selector_validation_01',
    qualification='Complete independent private acceptance implementation prepared, not validated as an automatic algorithm yet. Actual replay prerequisites must pass before launch; final independent physical validation is mandatory and every deferred state remains separately publication-gated. Same seed/search/scope/selector ranking/acceptance as direct-scope predecessor; no complete speed claim.'))
print(dict(prepared=str(target),actual_integration_pending=True),flush=True)
