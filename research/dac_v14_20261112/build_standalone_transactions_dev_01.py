"""Move worker/audit/materialization closure into explicit-input development package."""
import ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
old=D/'standalone_selection_dev_01';out=D/'standalone_transactions_dev_01';assert not out.exists()
assert all(sha(old/n)==h for n,h in read(old/'artifact_manifest.json')['sha256'].items())
shutil.copytree(old,out,ignore=shutil.ignore_patterns('__pycache__'))
(out/'artifact_manifest.json').rename(out/'selection_artifact_manifest.json')
origins={}
for name in ['coordinated_repair_tree.py','fixed_anchor_acceptance.py','audit_native_objective.py',
             'audit_retained_crossing_domain.py','audit_failure_release_domain.py','audit_explicit_crossing_source_domain_v2.py']:
    shutil.copy2(D/name,out/name);origins[name]=dict(origin=str(D/name),sha256=sha(D/name),transformation='byte_exact')
text=(D/'run_native_scope_policy_v4.py').read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='run_dir')
(out/'run_native_scope_policy_v4.py').write_text('from pathlib import Path\nfrom retained_prefix_workflow import read\n'+ast.get_source_segment(text,node)+'\n')
origins['run_native_scope_policy_v4.py']=dict(origin=str(D/'run_native_scope_policy_v4.py'),sha256=sha(D/'run_native_scope_policy_v4.py'),transformation='run_dir_function_AST_exact')
name='audit_native_feedback_objective_cached.py';text=(D/name).read_text()
text=text.replace("sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace","from check_route import read_trace")
(out/name).write_text(text)
origins[name]=dict(origin=str(D/name),sha256=sha(D/name),transformation='remove_repository_import_path_only')
name='materialize_crossing_source_candidate_v1.py';text=(D/name).read_text()
text=text.replace("sys.path.insert(0,str(D.parents[1]/'scripts'))\nimport flatland_benchmark as study","import runtime_audit as study")
(out/name).write_text(text)
def function(path,name):return ast.dump(next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name))
assert function(D/name,'materialize')==function(out/name,'materialize')
origins[name]=dict(origin=str(D/name),sha256=sha(D/name),transformation='materialize_function_AST_exact_portable_physical_auditor_import')

origin=D/'run_crossing_source_seed_analysis_v1.py';text=origin.read_text()
text=text.replace('D, read, write, sha, require_formal_terminal, route_body','D, read, write, sha, route_body')
start=text.index('ROOT = D.parents[1]');end=text.index('\n\ndef main():',start)
text=text[:start]+'''import runtime_io as io
import runtime_audit as study
from observe import inputs
'''+text[end:]
text=text.replace("parser = argparse.ArgumentParser()","parser = argparse.ArgumentParser()\n    parser.add_argument('--inputs',type=Path,required=True)",1)
text=text.replace('    require_formal_terminal()',"    config, paths, cache, portable_command = inputs(args.inputs,args.batch)")
text=text.replace("    stage = D / 'crossing_source_stage_01'\n    binding = read(stage / 'binding.json')\n    assert sha(stage / 'bin/vpr') == binding['binary_sha256']\n",'')
text=text.replace('    b.mkdir(exist_ok=False)',"    assert args.candidate_route is None, 'Use a separately admitted observation for a new candidate source'\n    assert paths['route'] == route and paths['graph'] == graph\n    for key,name in [('packed','packed.net'),('placement','placed.place')]:\n        assert sha(paths[key])==sha(source/name),'Physical source mismatch'\n    assert sha(paths['architecture'])==sha(manifest['command'][1]) and sha(paths['circuit'])==sha(manifest['command'][2])\n    for key in list(os.environ):\n        if key.startswith('VPR_'):del os.environ[key]\n    io.configure(b,paths['binary'])",1)
text=text.replace("shutil.copy2(stage / 'bin/vpr', b / 'bin/vpr')","shutil.copy2(paths['binary'], b / 'bin/vpr')")
text=text.replace("    shutil.copy2(OLD / 'runtime_dependency_binding.json', b / 'runtime_dependency_binding.json')\n",'')
text=text.replace("files = [Path(__file__), D / 'endpoint_timing_policy.py', D / 'native_endpoint_vector_experiment_01.json',\n             stage / 'binding.json', source / 'manifest.json'","files = [Path(__file__), D / 'endpoint_timing_policy.py', args.inputs.resolve(), *paths.values(),\n             D / 'artifact_manifest.json', *[D/n for n in read(D/'artifact_manifest.json')['sha256']], source / 'manifest.json'")
text=text.replace("    env = {'VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS'","    assert cmd[1:]==portable_command[1:], 'Explicit analysis arguments differ from actual source command'\n    env = {'VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS'",1)
start=text.index('    if observation:\n',text.index('    audit_start ='))
end=text.index('    audit_seconds =',start)
text=text[:start]+'''    # Fresh source audit over the supplied graph for both arms; no historical
    # copied-audit aliases enter this independent development entry.
    study.BASE = b
    reader = study.cr.read_graph_evidence
    study.cr.read_graph_evidence = cache.evidence
    try:
        audit = study.audit_batch({'fixture': {'original_graph': str(graph)}}, [result], b/'independent_native_analysis_audit.json')
    finally:
        study.cr.read_graph_evidence = reader
    checks['physical_audit'] = audit['passed'] and audit['legal_count']==1 and audit['failed_count']==0
    if args.native_cases:
        query_lines=(rd/'joint_native.log').read_text().splitlines() if (rd/'joint_native.log').exists() else []
        checks['native_control_complete'] = bool(query_lines) and 'occupancy_restored' in query_lines[-1]
    checks['reported_CPD_matches_source_at_report_precision'] = result['metrics'].get('critical_path_ns') == float(format(manifest['metrics']['critical_path_ns'], '.6g'))
'''+text[end:]
text=text.replace("    (b / 'bin').mkdir()\n    shutil.copy2(paths['binary'], b / 'bin/vpr')\n",'').replace("route, graph, b / 'bin/vpr']","route, graph, paths['binary']]").replace("cmd[0] = str(b / 'bin/vpr')","cmd[0] = str(paths['binary'])")
text=text.replace('import os\n','import os\nimport resource\n').replace('    started = time.monotonic()','    started = time.monotonic()\n    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))')
text=text.replace('    hashes = {str(p): sha(p) for p in files}',"    for directory in [cache.directory,cache.g.directory]:\n        files += [directory/'completion.json',*[directory/n for n in read(directory/'completion.json')['payload_sha256']]]\n    hashes = {str(p): sha(p) for p in files}")
(out/'run_native_transaction_worker.py').write_text(text)
# Candidate/restored scientific gates must remain exactly those of the original.
def callback_gate(path):
    f=next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    matches=[n for n in f.body if isinstance(n,ast.If) and ast.unparse(n.test)=='args.candidate_full_sta']
    return ast.dump(matches[-1])
assert callback_gate(origin)==callback_gate(out/'run_native_transaction_worker.py')
origins['run_native_transaction_worker.py']=dict(origin=str(origin),sha256=sha(origin),
    transformation='Explicit descriptor/package/runtime admission; fresh cached source audit in both arms; candidate/restored scientific gate AST exact',
    runtime_libraries='Current exact binary ldd binding, not copied historical library list',candidate_and_restoration_gates_AST_exact=True)
for p in out.glob('*.py'):compile(p.read_text(),str(p),'exec')
write(out/'transaction_source_provenance.json',dict(files=origins,full_method_frozen=False,native_calls_new=0,
    qualification='New portable worker and unchanged scope/domain/materialization kernels. Execution equivalence remains to be tested; this package does not alter registered workers or prove complete method behavior. Fresh source audit is an explicit engineering cost, applied symmetrically.'))
print(dict(package=str(out),candidate_restoration_gate_AST_exact=True,materialization_function_AST_exact=True))
