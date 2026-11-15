"""Assemble portable endpoint/acceptance/index dependencies without experiment aliases."""
import ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
out=D/'standalone_observation_dev_01';out.mkdir(exist_ok=False);origins={}
runtime=D/'standalone_native_runtime_dev_01';sealed=read(runtime/'artifact_manifest.json')
for name in ['runtime_io.py','runtime_dependencies.py','runtime_common.py','runtime_metrics.py','runtime_audit.py','check_route.py','xml_records.py','process_tree_observer.py','seccomp_thread_guard','seccomp_thread_guard.c','guard_manifest.json','test_seccomp_thread_guard.py']:
    source=runtime/name;assert sha(source)==sealed['sha256'][name];shutil.copy2(source,out/name)
    origins[name]=dict(origin=str(source),sha256=sha(source),transformation='byte_exact')
for name in ['endpoint_timing_policy.py','endpoint_timing_policy_streaming_v2.py','multiobjective_acceptance_v2.py','immutable_rr_audit_cache.py','full_route_graph_cache.py','build_joint_graph_indexes_v1.py']:
    source=D/name;shutil.copy2(source,out/name);origins[name]=dict(origin=str(source),sha256=sha(source),transformation='byte_exact')
def extract(name,origin,names,imports):
    text=origin.read_text();tree=ast.parse(text)
    parts=[ast.get_source_segment(text,node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert len(parts)==len(names)
    (out/name).write_text(imports+'\n\n'+'\n\n'.join(parts)+'\n')
    originals={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    for node in ast.parse((out/name).read_text()).body:
        if isinstance(node,ast.FunctionDef):assert ast.dump(node,include_attributes=False)==originals[node.name]
    origins[name]=dict(origin=str(origin),sha256=sha(origin),transformation='function_AST_exact',functions=sorted(names))
extract('retained_prefix_workflow.py',D/'retained_prefix_workflow.py',{'read','write','sha','route_body'},'"""Portable exact serialization/identity helpers; no historical admission state."""\nfrom pathlib import Path\nimport hashlib,json\nD=Path(__file__).resolve().parent')
extract('verify_path_witnesses_v2.py',D/'verify_path_witnesses_v2.py',{'graph_records','f32'},'"""Exact XML stream and native float32 conversion, without old experiment CLI."""\nimport struct\nfrom lxml import etree')
extract('seed_census_analysis_pool_v2.py',D/'seed_census_analysis_pool_v2.py',{'process_identity'},'"""Exact process identity helper; this module does not implement the native pool."""\nfrom pathlib import Path')
write(out/'source_provenance.json',dict(files=origins,full_method_frozen=False,native_calls_new=0,
    qualification='Portable observation dependency closure. Scientific policy, endpoint parser and all three graph payload generators copied byte-exact; only required identity/XML helpers extracted. Historical terminal/proof aliases are not fabricated. A new explicit observation input interface is separate from the registered original workers.'))
print(dict(package=str(out),copied_or_extracted=len(origins),VPR_calls_new=0))
