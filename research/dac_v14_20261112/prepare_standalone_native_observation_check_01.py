"""Freeze one new portable native adapter check in durable storage outside the project."""
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
validation=D/'standalone_observation_dependencies_validation_02/completion.json';v=read(validation);assert v['passed'] and v['native_interface_execution_pending']
assert all(sha(f)==h for f,h in v['source_sha256'].items())
old=read(D/'standalone_observation_dependencies_validation_01/registration.json');assert all(sha(f)==h for f,h in old['source_sha256'].items())
temporary=Path(v['relocated_directory']);package=D/'standalone_observation_dev_02'
workspace=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/native_observation_01');workspace.mkdir(parents=True,exist_ok=False)
shutil.copytree(temporary/'runtime_v2',workspace/'runtime',ignore=shutil.ignore_patterns('__pycache__'))
for name,digest in read(package/'artifact_manifest.json')['sha256'].items():assert sha(workspace/'runtime'/name)==digest
inputs=workspace/'inputs';inputs.mkdir();expected=workspace/'expected';expected.mkdir()
spec=read(temporary/'fixture/inputs.json');spec.pop('full_graph_cache')
for row in spec['files'].values():
    source=temporary/'fixture'/row['path'];dest=inputs/source.name;shutil.copy2(source,dest);assert sha(dest)==row['sha256'];row['path']=str(dest.relative_to(workspace))
for name in ['endpoint_vector.json','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:shutil.copy2(temporary/'fixture'/name,expected/name)
write(expected/'independent_audit.json',read(temporary/'fixture/expected.json')['physical_audit'])
write(workspace/'input_template.json',spec)
root=D/'standalone_native_observation_equivalence_01';root.mkdir(exist_ok=False)
files=[f for f in workspace.rglob('*') if f.is_file()]
files += [Path(__file__).resolve(),validation,D/'run_standalone_native_observation_check_01.py',D/'queue_standalone_native_observation_check_01.py']
for f in files:
    if f.suffix=='.py':compile(f.read_text(),str(f),'exec')
write(root/'plan.json',dict(passed=True,registered_before_native=True,workspace=str(workspace),predecessor=str(D/'unified_input_integration_01/queue'),
    input_sha256={str(f):sha(f) for f in files},native_calls_planned=1,route_search_calls=0,actual_native_execution_performed=False,
    expected_full_vector_and_raw_trace_exact=True,expected_physical_audit_exact=True,current_binary_sha256=spec['files']['binary']['sha256'],
    limits=dict(native_timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='One new native observation-interface check after all existing queued work, with exact copied existing tiny physical inputs and reference outputs. Build indexes fresh inside this new check; no original completed batch rerun. Native process does not use expected outputs for routing/STA. This is a relocation/interface test, not a new independent circuit result or full-method frozen confirmation.'))
(root/'README.md').write_text('''# Portable native observation interface validation

The endpoint parser, exact acceptance rules and single-pass graph index code are
copied without numerical changes. An explicit input descriptor binds all physical
inputs, the native binary and cache receipts. The native child executes from a
durable directory outside the historical project, with local NumPy/lxml copies;
Python reads from the historical project are forbidden in the diagnostic launcher.
This does not claim OS-level sandboxing of the C++ binary.

Actual relocated dependency checks passed: five cache payloads and the cached
physical audit match; a complete native endpoint vector matches after JSON
serialization; real accepted and rejected BNN policy decisions match exactly.
Incomplete transactions, foreign constraints, incomplete traces, corrupt caches
and wrong input hashes are rejected. The initial tuple/list test mismatch and its
correction are retained. Completed index generation was reused, not repeated.

The queue will make one newly registered native FULL/STA analysis call on an
existing tiny route after the current recovery and unified-input chain. It must
preserve the full vector, raw native trace, physical audit and input bytes. Timing
echo is also required. No route search is requested. The native run remains
pending until its own completion receipt exists; failed calls are never retried
automatically. This package is an observation component, not the complete frozen
selection/transaction/owner/timing method.
''')
print(dict(registered=True,workspace=str(workspace),bound_files=len(files),native_calls_planned=1,native_calls_executed=0))
