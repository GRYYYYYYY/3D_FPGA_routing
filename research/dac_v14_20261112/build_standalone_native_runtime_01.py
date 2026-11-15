"""Build a relocatable native-runtime component without historical run prerequisites."""
import ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];old=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts'
out=D/'standalone_native_runtime_dev_01';out.mkdir(exist_ok=False);provenance={}
def copy(name,source):
 shutil.copy2(source,out/name);provenance[name]=dict(origin=str(source),origin_sha256=sha(source),transformation='byte_exact')
for n in ['seccomp_thread_guard','seccomp_thread_guard.c','test_seccomp_thread_guard.py','process_tree_observer.py']:copy(n,old/n)
copy('check_route.py',ROOT/'scripts/check_route.py')
def functions(path,names):
 source=path.read_text();tree=ast.parse(source)
 rows=[ast.get_source_segment(source,node) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
 assert len(rows)==len(names);return '\n\n'.join(rows)+'\n'
common=ROOT/'scripts/lazagna_common.py'
(out/'runtime_common.py').write_text('"""Portable hashing, receipts and explicit process interpreter identity."""\nimport datetime,hashlib,json,sys\nfrom pathlib import Path\nPYTHON=Path(sys.executable).resolve()\n'+functions(common,{'sha256','write_json','utc'}))
(out/'runtime_metrics.py').write_text('"""Unchanged native metric parser, extracted without unrelated CLI defaults."""\nimport re\n'+functions(ROOT/'scripts/run_vpr.py',{'parse_metrics'}))
(out/'xml_records.py').write_text('"""Unchanged bounded-memory XML record stream."""\nfrom lxml import etree\n'+functions(ROOT/'scripts/compare_lazagna_graphs.py',{'records'}))
(out/'runtime_audit.py').write_text('"""Unchanged physical audit functions with caller-supplied batch and graph."""\nfrom collections import Counter\nfrom pathlib import Path\nimport json\nimport check_route as cr\nfrom xml_records import records\nfrom runtime_common import sha256,utc,write_json\nBASE=None\ndef read(path):return json.loads(Path(path).read_text())\n'+functions(old/'flatland_benchmark.py',{'physical_route_metrics','audit_batch'}))
source=old/'flatland_timing_io_candidate.py';s=source.read_text()
s=s.replace('from lazagna_common import ROOT, PYTHON, sha256, utc, write_json','from runtime_common import PYTHON, sha256, utc, write_json\nfrom runtime_dependencies import bind_runtime')
s=s.replace('from run_vpr import parse_metrics','from runtime_metrics import parse_metrics')
s=s.replace("BASE = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/serial_strict_reexecution_20261103')",'BASE = None')
s=s.replace("GUARD_VALIDATION = Path(__file__).resolve().parent.parent/'seccomp_guard_unit_validation.json'", "GUARD_VALIDATION = Path(__file__).with_name('guard_manifest.json').resolve()")
s=s.replace("    directory = BASE/'runs'/name", "    assert BASE is not None, 'Caller must supply an explicit output directory'\n    directory = Path(BASE).resolve()/'runs'/name")
s=s.replace("assert validation['status']=='unit_tests_passed_not_approved_for_formal_timing'", "assert validation['format']=='portable_guard_artifact_v1'")
s=s.replace("validation['source_sha256'][str(GUARD.relative_to(ROOT))]", "validation['artifact_sha256']['seccomp_thread_guard']")
s += '''\n\ndef configure(output,binary):
    """Bind this exact executable's current dynamic libraries before native work."""
    global BASE
    assert BASE is None, 'One runtime instance belongs to one batch'
    BASE=Path(output).resolve();BASE.mkdir(parents=True,exist_ok=False)
    bind_runtime(binary,BASE/'runtime_dependency_binding.json')
    return BASE
'''
(out/'runtime_io.py').write_text(s)
provenance['runtime_io.py']=dict(origin=str(source),origin_sha256=sha(source),transformation='Replace historical imports/base/guard receipt with explicit caller output, locally bound guard artifact and per-executable current library binding. Native run/wait/sampling/limits/environment/input-integrity/metrics/sealing logic unchanged.')
for name,path,names in [('runtime_common.py',common,{'sha256','utc','write_json'}),('runtime_metrics.py',ROOT/'scripts/run_vpr.py',{'parse_metrics'}),('runtime_audit.py',old/'flatland_benchmark.py',{'physical_route_metrics','audit_batch'}),('xml_records.py',ROOT/'scripts/compare_lazagna_graphs.py',{'records'})]:
 provenance[name]=dict(origin=str(path),origin_sha256=sha(path),extracted_functions=sorted(names),function_AST_exact=True)
write(out/'guard_manifest.json',dict(format='portable_guard_artifact_v1',artifact_sha256={n:sha(out/n) for n in ['seccomp_thread_guard','seccomp_thread_guard.c','test_seccomp_thread_guard.py']},qualification='Actual byte-identical serial guard used by existing native runs; relocation self-tests must be run separately. This manifest is artifact identity, not a fabricated historical test result.'))
write(out/'provenance.json',dict(source_files=provenance,scientific_algorithm_changed=False,full_method_packaged=False,qualification='Native execution and physical-audit component only. Full unified selection/transaction/STA dependency closure and algorithm confirmation remain separate.'))
print(out)
