"""Stage two corrected workers for a future package; never alter frozen runtimes."""
import difflib
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'observation_precision_patch_02';assert not out.exists();out.mkdir()
parent=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r2/runtime')
helper=D/'observation_timing_identity_v2.py';shutil.copy2(helper,out/helper.name)
names=['run_serial_census_state_analysis_stream_v1.py','run_serial_seed_resource_state_analysis_stream_v1.py']
before={};after={};diffs=[]
for name in names:
    source=parent/name;old=source.read_text();text=old
    anchor='from endpoint_timing_policy_streaming_v2 import load'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\nfrom observation_timing_identity_v2 import check as check_observation_timing')
    anchor="    observation = sha(route) == sha(source / 'routed.route')"
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'''
    source_vector = None
    source_vector_path = None
    if observation and not args.trace_off:
        cached = source.parent.parent / 'endpoint_vector.json'
        if source.name == 'state' and source.parent.name == 'runs' and cached.is_file():
            source_vector_path = cached
            source_vector = read(cached)
        else:
            source_vector_path = source / 'native_sta_frontier.jsonl'
            source_vector = load(source_vector_path)
''')
    anchor='    hashes = {str(p): sha(p) for p in files}'
    assert text.count(anchor)==1
    text=text.replace(anchor,"    if source_vector_path is not None: files.append(source_vector_path)\n"+anchor)
    anchor="checks['CPD_matches_original'] = result['metrics'].get('critical_path_ns') == manifest['metrics']['critical_path_ns']"
    assert text.count(anchor)==1
    text=text.replace(anchor,"checks['CPD_matches_original'] = result['metrics'].get('critical_path_ns') == float(format(manifest['metrics']['critical_path_ns'], '.6g'))")
    anchor="        write(b / 'endpoint_vector.json', vector)"
    assert text.count(anchor)==1
    text=text.replace(anchor,"""        if observation:
            identity = check_observation_timing(result['metrics']['critical_path_ns'], manifest['metrics']['critical_path_ns'], source_vector, vector)
            checks['observation_full_precision_and_endpoints_exact'] = identity['passed']
            write(b / 'observation_timing_identity.json', identity)
"""+anchor)
    compile(text,str(out/name),'exec')
    (out/name).write_text(text)
    before[name]=sha(source);after[name]=sha(out/name)
    diffs += list(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile='CP1r2/'+name,tofile='future-runtime/'+name))
(out/'workers.patch').write_text(''.join(diffs))
write(out/'preparation.json',dict(passed=True,status='staged_development_patch_not_installed',
    original_runtime=str(parent),parent_workers_sha256=before,patched_workers_sha256=after,
    helper_sha256=sha(helper),original_frozen_files_unchanged=all(sha(parent/n)==h for n,h in before.items()),
    syntax_checked=True,numerical_regression=str(D/'observation_timing_identity_validation_02/completion.json'),
    actual_existing_trace_audit='robot_owner_reentry_audit_02/queue',actual_existing_trace_audit_pending=True,
    native_calls_new=0,algorithm_selection_acceptance_and_terminal_rules_changed=False,
    future_packaging_requirements='Include helper, bind source vector/trace in worker input seal (implemented), rebuild active package and release manifests, preserve executable modes, then separately register prospective execution. Do not copy these workers into a live/frozen package.',
    qualification='VPR displayed CPD normalized only for report comparison; observation must also match full precision CPD/setup/hold/endpoint identity/constraints exactly. No tolerance is added to actual timing acceptance. Trace-off remains report-only diagnostic, without a new exact-vector claim. Patch syntax and numerical regressions are not actual native worker replay or complete-method proof.'))
print(dict(passed=True,patched_workers=len(names),installed=False,native_calls_new=0))
