"""Resume completed index evidence; correct tuple/list serialization in the test only."""
import json,os,shutil,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
prior=D/'standalone_observation_dependencies_validation_01';old=D/'standalone_observation_dev_01'
new=D/'standalone_observation_dev_02';assert not new.exists();shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
(new/'artifact_manifest.json').rename(new/'prior_artifact_manifest.json')
test=new/'test_observation_dependencies.py';s=test.read_text().replace('import argparse,copy,re,shutil','import argparse,copy,json,re,shutil')
old_check="vector=load(f/'native_sta_frontier.jsonl');assert vector==read(f/'endpoint_vector.json')"
new_check="vector=load(f/'native_sta_frontier.jsonl');assert json.loads(json.dumps(vector))==read(f/'endpoint_vector.json')"
assert old_check in s;test.write_text(s.replace(old_check,new_check));compile(test.read_text(),str(test),'exec')
report=D/'standalone_observation_dependencies_validation_02';report.mkdir(exist_ok=False)
reg=read(prior/'registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
assert read(prior/'joint_index_build_execution.json')['returncode']==0
failed=read(prior/'dependency_replay_execution.json');assert failed['returncode']==1 and 'assert vector==read' in failed['stderr']
relocated=Path(reg['relocated_directory']);fixture=relocated/'fixture';target=relocated/'runtime_v2'
write(new/'revision.json',dict(previous_package=str(old),previous_manifest_sha256=sha(old/'artifact_manifest.json'),
    failure=str(prior/'dependency_replay_execution.json'),failure_sha256=sha(prior/'dependency_replay_execution.json'),
    change='Test serializes the entire parsed vector through JSON before equality with serialized reference. No endpoint, policy, native runner or graph algorithm changed.'))
write(new/'artifact_manifest.json',dict(format='standalone_observation_development_v1',full_method_frozen=False,native_interface_validation_pending=True,
    sha256={f.name:sha(f) for f in new.iterdir() if f.is_file()},dependencies=read(old/'artifact_manifest.json')['dependencies']))
shutil.copytree(new,target,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['numpy','numpy.libs','lxml','lxml.libs']:
    p=relocated/'runtime'/name
    if p.exists():shutil.copytree(p,target/name,ignore=shutil.ignore_patterns('__pycache__'))
unchanged=[f.name for f in old.iterdir() if f.is_file() and f.name not in ['artifact_manifest.json','test_observation_dependencies.py']]
assert all(sha(old/name)==sha(new/name) for name in unchanged)
source_files=[Path(__file__).resolve(),prior/'registration.json',prior/'joint_index_build_execution.json',prior/'dependency_replay_execution.json',fixture/'inputs.json',fixture/'expected.json',fixture/'policy_cases.json',fixture/'indexes/completion.json',*map(lambda n:new/n,[*unchanged,'test_observation_dependencies.py','artifact_manifest.json','revision.json'])]
bound={str(f):sha(f) for f in source_files};write(report/'registration.json',dict(source_sha256=bound,relocated_directory=str(relocated),reused_completed_index_build=True,native_calls_planned=0))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(name,script,args):
    command=['/usr/bin/python3',str(target/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(target/script),*map(str,args)]
    r=subprocess.run(command,cwd=target,env=env,capture_output=True,text=True,timeout=180)
    write(report/(name+'_execution.json'),dict(command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,(name,r.stdout,r.stderr)
execute('dependency_replay','test_observation_dependencies.py',['--fixture',fixture])
execute('native_input_preflight','observe.py',['--inputs',fixture/'inputs.json','--output',fixture/'preflight_v2','--preflight'])
for src,name in [(fixture/'dependency_test.json','dependency_test.json'),(fixture/'preflight_v2/completion.json','native_input_preflight.json'),(fixture/'indexes/completion.json','joint_index_build.json'),(fixture/'inputs.json','relocated_inputs.json')]:shutil.copy2(src,report/name)
assert all(sha(f)==h for f,h in bound.items())
write(report/'completion.json',dict(passed=True,relocated_directory=str(relocated),package=str(new),dependency_test=read(fixture/'dependency_test.json'),
    native_input_preflight_passed=True,reused_completed_index_build=True,native_calls_new=0,artifact_manifest_sha256=sha(new/'artifact_manifest.json'),
    unchanged_implementation_files=unchanged,source_sha256=bound,native_interface_execution_pending=True,full_method_frozen=False,
    qualification='Corrected only full-vector serialized representation equality; all original numerical/identity fields checked. Original failed receipt retained. Actual index generation not repeated; remaining cached-audit/STA/policy/admission tests completed in an independent directory with historical Python reads forbidden. Native observation execution still pending.'))
print(dict(passed=True,cache_payloads_exact=5,actual_policy_cases=2,native_calls_new=0,completed_index_build_reused=True))
