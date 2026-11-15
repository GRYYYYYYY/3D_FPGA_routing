"""Exercise relocated indexing, actual endpoint/policy evidence and observation admission."""
import ast,json,os,shutil,subprocess,tempfile
from pathlib import Path
import numpy,lxml
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
package=D/'standalone_observation_dev_01';report=D/'standalone_observation_dependencies_validation_01';report.mkdir(exist_ok=False)
provenance=read(package/'source_provenance.json')
for name,row in provenance['files'].items():
    assert sha(row['origin'])==row['sha256']
    if row['transformation']=='byte_exact':assert sha(package/name)==row['sha256']
    else:
        def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(p).read_text()).body if isinstance(n,ast.FunctionDef)}
        a,b=functions(row['origin']),functions(package/name)
        assert all(a[n]==b[n] for n in row['functions'])
for f in package.glob('*.py'):compile(f.read_text(),str(f),'exec')
manifest=package/'artifact_manifest.json';assert not manifest.exists()
write(manifest,dict(format='standalone_observation_development_v1',full_method_frozen=False,native_interface_validation_pending=True,
    sha256={f.name:sha(f) for f in package.iterdir() if f.is_file()},
    dependencies=dict(python='3.10.12',numpy=numpy.__version__,lxml=lxml.__version__)))
relocated=Path(tempfile.mkdtemp(prefix='standalone-observation-'));target=relocated/'runtime';fixture=relocated/'fixture';fixture.mkdir()
shutil.copytree(package,target,ignore=shutil.ignore_patterns('__pycache__'))
external=[]
for module in [numpy,lxml]:
    path=Path(module.__file__).parent;shutil.copytree(path,target/path.name,ignore=shutil.ignore_patterns('__pycache__'))
    external.extend(f for f in path.rglob('*') if f.is_file() and '__pycache__' not in f.parts)
    libs=path.with_name(path.name+'.libs')
    if libs.exists():shutil.copytree(libs,target/libs.name);external.extend(f for f in libs.rglob('*') if f.is_file())
old=D/'fresh_route_entry_preflight_01/flow';run=old/'initial/runs/state';native=read(run/'manifest.json');command=native['command']
paths=dict(binary=Path(command[0]),architecture=Path(command[1]),circuit=Path(command[2]),graph=Path(command[command.index('--read_rr_graph')+1]),
    packed=run/'packed.net',placement=run/'placed.place',route=run/'routed.route')
names=dict(binary='vpr',architecture='architecture.xml',circuit='fixture.blif',graph='rr_graph.xml',packed='packed.net',placement='placed.place',route='routed.route')
for key,p in paths.items():shutil.copy2(p,fixture/names[key])
for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:shutil.copy2(run/name,fixture/name)
shutil.copy2(old/'initial/endpoint_vector.json',fixture/'endpoint_vector.json')
payloads={}
for oldpath,newpath,names_list in [('graph_audit_cache','audit_cache',['nodes.npy','edges.npy','switches.npy']),('full_graph_cache','full_cache',['extra.npy','metadata.json'])]:
    for name in names_list:payloads[newpath+'/'+name]=sha(old/oldpath/name)
write(fixture/'expected.json',dict(physical_audit=read(run/'independent_audit.json'),payload_sha256=payloads))
source_files=[Path(__file__).resolve(),*paths.values(),run/'manifest.json',run/'independent_audit.json',old/'initial/endpoint_vector.json',run/'native_sta_frontier.jsonl',run/'native_sta_frontier.jsonl.constraints.echo']
def axes(state):
    p=run_dir(Path(state))/'independent_audit.json';source_files.append(p);m=read(p)['physical_metrics']
    return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
actor=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream/flow/resource_flow/repair';cases=[];seen=set()
for attempt in read(actor/'attempts.json'):
    tx=Path(attempt['transaction']);reg=read(tx/'registration.json')
    for name,row in read(tx/'progress.json').items():
        if row['status']!='legal_evaluated':continue
        decision=read(tx/(name+'_decisions.json'))['resources_under_timing']
        if decision['accepted'] in seen:continue
        seen.add(decision['accepted']);role=reg['roles'][name];before=Path(role['state'])/'endpoint_vector.json';after=Path(row['evaluation'])/'endpoint_vector.json'
        cases.append(dict(arguments=dict(mode='resources_under_timing',before_vector=read(before),after_vector=read(after),before_resources=axes(role['state']),after_resources=axes(row['evaluation']),cpd_limit_s=role['original_budget']['CPD_s'],resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=['SB_pairs','CB_sources']),expected=decision))
        source_files += [before,after,tx/'registration.json',tx/'progress.json',tx/(name+'_decisions.json')]
    if len(seen)==2:break
assert seen=={True,False};write(fixture/'policy_cases.json',cases)
bound={str(f):sha(f) for f in dict.fromkeys([*source_files,*[f for f in package.iterdir() if f.is_file()],*external])}
write(report/'registration.json',dict(relocated_directory=str(relocated),source_sha256=bound,external_versions=read(manifest)['dependencies'],native_calls_planned=0))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(name,script,args):
    cmd=['/usr/bin/python3',str(target/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(target/script),*map(str,args)]
    r=subprocess.run(cmd,cwd=target,env=env,capture_output=True,text=True,timeout=180)
    write(report/(name+'_execution.json'),dict(command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
    assert r.returncode==0,(name,r.stdout,r.stderr)
execute('joint_index_build','build_joint_graph_indexes_v1.py',['--graph',fixture/'rr_graph.xml','--output',fixture/'indexes'])
arguments=command[3:];arguments.remove('--route')
for option,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement'),('--route_file','route')]:arguments[arguments.index(option)+1]='{'+key+'}'
spec=dict(format='standalone_native_observation_input_v1',files={key:dict(path=name,sha256=sha(fixture/name)) for key,name in names.items()},analysis_arguments=arguments,
    full_graph_cache=dict(path='indexes/full_cache',completion_sha256=sha(fixture/'indexes/full_cache/completion.json')))
write(fixture/'inputs.json',spec)
execute('dependency_replay','test_observation_dependencies.py',['--fixture',fixture])
execute('native_input_preflight','observe.py',['--inputs',fixture/'inputs.json','--output',fixture/'preflight','--preflight'])
for src,name in [(fixture/'dependency_test.json','dependency_test.json'),(fixture/'preflight/completion.json','native_input_preflight.json'),(fixture/'indexes/completion.json','joint_index_build.json'),(fixture/'inputs.json','relocated_inputs.json')]:shutil.copy2(src,report/name)
assert all(sha(f)==h for f,h in bound.items())
write(report/'completion.json',dict(passed=True,relocated_directory=str(relocated),dependency_test=read(fixture/'dependency_test.json'),
    native_input_preflight_passed=read(fixture/'preflight/completion.json')['passed'],native_calls_new=0,
    original_joint_index_generator_byte_exact=True,artifact_manifest_sha256=sha(manifest),source_sha256=bound,
    native_interface_execution_pending=True,full_method_frozen=False,
    qualification='Actual relocated zero-native dependency test: single-pass graph generation, five payload byte checks, cached physical audit, full endpoint parser, actual accepted/rejected policy decisions and malformed-input guards. Native observation entry only preflighted; register a new native interface check before claiming execution equivalence.'))
print(dict(passed=True,native_calls_new=0,cache_payloads_exact=5,actual_policy_cases=2,native_interface_execution_pending=True,relocated_directory=str(relocated)))
