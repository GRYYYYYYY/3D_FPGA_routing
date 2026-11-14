#!/usr/bin/env python3
"""Create an independent engineering variant; never edit a registered actor."""
from pathlib import Path
from retained_prefix_workflow import D,read,sha,write

source = D/'run_seed_census_shadow_resource_repair.py'
target = D/'run_direct_scope_shadow_resource_repair.py'
assert not target.exists()
assert read(D/'direct_native_transaction_validation_01/completion.json')['passed']
text = source.read_text()
def replace(old,new):
    global text
    assert text.count(old)==1, old[:120]
    text=text.replace(old,new)
replace('from actual_route_tree_identity import same_actual_trees',
        'from direct_native_transaction_audit import DirectTransactionAudit')
replace("pool=NativeAnalysisPool(b/'pool',command,static,guard,seed_order=a.seed_order,native_census=True);evaluator=PoolStateEvaluator(pool,initial,a.full_graph_cache,b/'evaluation_context');costs=",
        "pool=NativeAnalysisPool(b/'pool',command,static,guard,seed_order=a.seed_order,native_census=True);evaluator=PoolStateEvaluator(pool,initial,a.full_graph_cache,b/'evaluation_context');direct_auditor=DirectTransactionAudit(evaluator.graph,audit_cache);costs=")
replace("files += [D/'native_resources_from_receipt.py',", "files += [D/'direct_native_transaction_audit.py',D/'direct_native_transaction_validation_01/completion.json',D/'native_resources_from_receipt.py',")
replace("assert all(read(D/n)['passed'] for n in ['seed_census_client_validation_01/completion.json'",
        "assert all(read(D/n)['passed'] for n in ['direct_native_transaction_validation_01/completion.json','seed_census_client_validation_01/completion.json'")
replace("unchanged_selection_and_acceptance=True,", "unchanged_selection_and_acceptance=True,transaction_scope_audit='direct_actual_native_tree_no_reconstruction',")
replace("question='Does a globally fixed native seed policy transfer from pristine A0/R1/Tf roots with common own-current native/domain controls, and do actual native counters agree with every independent accepted/rejected candidate physical audit?'",
        "question='Does direct actual-candidate scope/edge/capacity audit preserve the complete automatic own-current trajectory while reducing construction/check overhead against the same globally fixed seed-policy and independent-physical-audit actor?' ")
replace("qualification='Independent fixed seed-policy and native-count shadow version; original cohorts unchanged.",
        "qualification='Independent direct-scope engineering version; original cohorts unchanged. No alternate candidate route is serialized or installed by the auditor. Full independent physical audits and native counter shadow checks remain.")
replace("ok=invoke('audit_native_feedback_objective_cached.py',['--batch',tx,'--role',name,'--cache',audit_cache,'--output',tx/(name+'_audit')],f'{len(steps):03d}_{ci:02d}_{name}_transaction_audit')",
        "t=time.monotonic();direct_auditor.audit(worker,role,tx/(name+'_audit'));costs.append(dict(tag=f'{len(steps):03d}_{ci:02d}_{name}_direct_transaction_audit',status='completed',complete_process_seconds=time.monotonic()-t));persist()")
replace("actual=Path(view['native_directory'])/'routed.route';t=time.monotonic();assert same_actual_trees(actual,audit['candidate_route']);costs.append(dict(tag=f'{len(steps):03d}_{ci:02d}_{name}_actual_vs_reconstructed_tree_check',status='completed',complete_process_seconds=time.monotonic()-t));state=",
        "actual=Path(view['native_directory'])/'routed.route';assert actual.resolve()==Path(audit['candidate_route']).resolve() and sha(actual)==audit['candidate_sha256'];state=")
replace("Independent automatic current selector→native request pool→whole multi-net transaction→real replacement→complete physical/FULLSTA→fixed-budget accept/rollback flow.",
        "Independent automatic current selector→native request pool→direct actual multi-net scope/edges/capacity audit→complete independent physical/FULLSTA→fixed-budget accept/rollback flow.")
compile(text,str(target),'exec')
target.write_text(text)
write(D/'direct_scope_actor_preparation_01.json',dict(passed=True,
    source=str(source),source_sha256=sha(source),target=str(target),target_sha256=sha(target),
    direct_audit_validation='direct_native_transaction_validation_01/completion.json',
    native_calls=0,route_calls=0,unchanged_selector_and_acceptance=True,
    original_registered_versions_unchanged=True,independent_physical_audits_retained=True,
    end_to_end_validated=False,complete_algorithm_speedup=None,
    qualification='Independent implementation prepared and syntax checked. Actual integrated trajectory comparison must pass before equivalence or runtime benefit is claimed.'))
print(dict(prepared=str(target),unchanged_registered_source=sha(source)),flush=True)
