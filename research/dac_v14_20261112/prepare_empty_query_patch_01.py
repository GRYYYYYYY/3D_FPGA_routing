"""Stage exact empty-menu exits after existing proof checks; no live runtime edits."""
import difflib
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r2/runtime')
out=D/'empty_query_patch_01';out.mkdir(exist_ok=False)
changes=[];patch=[]
name='query_current_protected_critical.py';source=parent/name;old=source.read_text()
anchor="g=GraphAuditCache(graph,a.audit_cache);binary=a.query_graph/'graph.bin';binding=read(binary.with_name('graph_binding.json'));driver=query_driver('capacity')"
assert old.count(anchor)==1
early='''# No selected owner target means no protected query case can be constructed.
# All upstream proof digests and the current-state identity were checked above.
if not op['rows']:
 binding_path=a.query_graph/'graph_binding.json';cache_path=a.audit_cache/'completion.json'
 binding=read(binding_path);cache_proof=read(cache_path);source_manifest=read(source/'manifest.json')
 source_graph=source_manifest['command'][source_manifest['command'].index('--read_rr_graph')+1]
 assert binding['passed'] and cache_proof['passed'] and binding['source_rrg_sha256']==cache_proof['graph_sha256']==source_manifest['shared_inputs'][source_graph]['sha256'],'Empty-menu graph argument identity mismatch'
 driver=query_driver('capacity');assert driver.is_file()
 critical=select(source/'native_sta_frontier.jsonl');protected={r['net'] for r in critical['targets']}
 files=[Path(__file__).resolve(),D/'current_sta_selector.py',q/'analysis.json',q/'execution.json',q/'occupancy_owners.json',a.opportunities,source/'native_sta_frontier.jsonl',source/'manifest.json',Path(op['input_state'])/'completion.json',*package_files(),*runtime_files()]
 files += [binding_path,cache_path,driver]
 bound={str(p):sha(p) for p in files}
 write(b/'registration.json',dict(status='registered_empty_target_set',input_run=str(source),protected_nets=sorted(protected),selector=critical,source_sha256=bound,native_calls=0,empty_menu_certificate='Verified current owner opportunity rows are empty.'))
 write(b/'cases.json',[]);write_cases(b/'cases.txt',[])
 write(b/'completion.json',dict(passed=True,rows=[],protected_nets=sorted(protected),actual_XML_bound_edges_checked=0,query_process_seconds=None,query_subprocess_executed=False,graph_mapping_executed=False,complete_process_seconds=time.monotonic()-start,source_sha256=bound,native_calls=0,qualification='Empty owner target set proved after original upstream digest/state checks. No query process or graph witness was executed; their metrics are absent. Complete command/proof/selector costs remain measured. No early global no-gain or timing-optimality claim.'))
 raise SystemExit(0)
'''
new=old.replace(anchor,early+anchor);compile(new,str(out/name),'exec');(out/name).write_text(new)
patch+=list(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='CP1r2/'+name,tofile='future-runtime/'+name));changes.append(dict(file=name,original_sha256=sha(source),patched_sha256=sha(out/name)))
name='query_critical_owner_exchange.py';source=parent/name;old=source.read_text()
anchor="m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);g=GraphAuditCache(graph,a.audit_cache)"
assert old.count(anchor)==1
early='''# The exact original exchange predicate can be evaluated before graph loading.
protected={r['net'] for r in cone['routed_connections']}
selected=[r for r in op['rows'] if r['capacity_gap_ns']>0 and any(o['net'] in protected for o in r['owner_release_scope'])]
if not selected:
 binding_path=a.query_graph/'graph_binding.json';cache_path=a.audit_cache/'completion.json'
 binding=read(binding_path);cache_proof=read(cache_path);source_manifest=read(source/'manifest.json')
 source_graph=source_manifest['command'][source_manifest['command'].index('--read_rr_graph')+1]
 assert binding['passed'] and cache_proof['passed'] and binding['source_rrg_sha256']==cache_proof['graph_sha256']==source_manifest['shared_inputs'][source_graph]['sha256'],'Empty-menu graph argument identity mismatch'
 driver=query_driver('capacity');assert driver.is_file()
 files=[Path(__file__).resolve(),f/'owners/completion.json',f/'cone.json',f/'capacity/analysis.json',f/'relaxed/analysis.json',source/'manifest.json',state/'completion.json',*package_files(),*runtime_files()]
 files += [binding_path,cache_path,driver]
 bound={str(p):sha(p) for p in files}
 write(b/'registration.json',dict(status='registered_empty_exchange_target_set',input_state=str(state),input_run=str(source),targets=[],protected_current_cone_nets=sorted(protected),source_sha256=bound,native_calls=0,empty_menu_certificate='No positive capacity-gap target has a current critical owner, under the original predicate.'))
 write(b/'completion.json',dict(passed=True,rows=[],native_calls=0,source_sha256=bound,query_subprocess_executed=False,graph_mapping_executed=False,complete_process_seconds=time.monotonic()-started,qualification='No current target with a critical-owner conflict; original source/proof/state checks passed. Empty menu omitted graph mapping, not a global search or final candidate. No imputed query cost or quality.'))
 raise SystemExit(0)
'''
new=old.replace(anchor,early+anchor);compile(new,str(out/name),'exec');(out/name).write_text(new)
patch+=list(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='CP1r2/'+name,tofile='future-runtime/'+name));changes.append(dict(file=name,original_sha256=sha(source),patched_sha256=sha(out/name)))
(out/'workers.patch').write_text(''.join(patch))
# Actual completed no-op evidence motivates this patch; timings are nested, not savings.
case=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r2_cross_circuit_01/conv_hls/native/flow/timing')
owner=read(case/'round_000/feedback/owners/completion.json');protected=read(case/'round_000/feedback/protected/completion.json');exchange=read(case/'round_000/exchange_query/completion.json')
assert not owner['rows'] and not protected['rows'] and not exchange['rows']
costs=read(case/'process_costs.json');observed=[r for r in costs if r['tag'] in ['000_protected_query','000_exchange_query']]
assert len(observed)==2
write(out/'preparation.json',dict(passed=True,status='staged_development_patch_not_installed',changes=changes,
    motivating_complete_input='CP1r2 conv_hls/native, verified505.16725363209844s complete no-op arm',
    actual_empty_protected_query_process_seconds=protected['query_process_seconds'],
    actual_original_nested_phase_seconds=observed,
    projected_or_measured_savings=None,nested_times_are_not_predicted_savings=True,
    syntax_checked=True,actual_patched_worker_execution=False,native_calls_new=0,
    nonempty_case_body_preserved_byte_exact=True,
    future_validation='Run staged workers on exact completed empty and nonempty inputs under exclusive serial slot. Verify downstream proposal/terminal identity and source guards, then package a new version and apply symmetrically in complete native/domain controls. No changes to current registered timing03.',
    original_frozen_files_unchanged=all(sha(parent/r['file'])==r['original_sha256'] for r in changes),
    qualification='Only exact current empty target sets omit unused graph mapping/query processes. Existing upstream digest and state checks execute first. Protected-net selector still executes for matching metadata; no guessed protection list. Unexecuted query seconds are null and execution flags explicit. No universal mechanism gain, early optimality certificate or end-to-end saving established.'))
print(dict(passed=True,staged_workers=2,installed=False,native_calls_new=0))
