"""Copy real inputs and the installed XML dependency outside the project, then audit."""
import json,os,shutil,subprocess,tempfile
from pathlib import Path
import lxml,lxml.etree
from retained_prefix_workflow import D,read,write,sha
root=D.parents[1];package=D/'standalone_native_runtime_dev_01'
report=D/'standalone_physical_audit_validation_01';report.mkdir(exist_ok=False)
origin=D/'fresh_route_entry_preflight_01/flow/initial/runs/state'
manifest=read(origin/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
relocated=Path(tempfile.mkdtemp(prefix='standalone-routing-audit-'));target=relocated/'runtime'
shutil.copytree(package,target,ignore=shutil.ignore_patterns('__pycache__'))
xml_package=Path(lxml.__file__).parent
shutil.copytree(xml_package,target/'lxml',ignore=shutil.ignore_patterns('__pycache__'))
fixture=relocated/'fixture';rd=fixture/'runs/state';rd.mkdir(parents=True)
for name in ['routed.route','pair_check.json','manifest.json']:shutil.copy2(origin/name,rd/name)
shutil.copy2(origin/'independent_audit.json',fixture/'expected.json');shutil.copy2(graph,fixture/'rr_graph.xml')
files=[graph,origin/'independent_audit.json',*[origin/n for n in ['routed.route','pair_check.json','manifest.json']],
       *[f for f in package.iterdir() if f.is_file()],*[f for f in xml_package.rglob('*') if f.is_file() and '__pycache__' not in f.parts]]
sources={str(f):sha(f) for f in files}
write(report/'registration.json',dict(source_sha256=sources,relocated_directory=str(relocated),lxml_version=lxml.__version__,VPR_calls_planned=0))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']};env['PYTHONDONTWRITEBYTECODE']='1'
command=['/usr/bin/python3',str(target/'test_runtime_audit.py'),'--fixture',str(fixture),'--forbid-prefix',str(root)]
r=subprocess.run(command,capture_output=True,text=True,cwd=target,env=env,timeout=120)
write(report/'execution.json',dict(command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
assert r.returncode==0,(r.stdout,r.stderr)
for name in ['test.json','audit.json','invalid_audit.json','failed_batch.json']:shutil.copy2(fixture/name,report/name)
assert all(sha(f)==h for f,h in sources.items())
write(report/'completion.json',dict(**read(fixture/'test.json'),source_sha256=sources,relocated_directory=str(relocated),
    lxml_version=lxml.__version__,python='/usr/bin/python3',full_method_packaged=False))
print(read(fixture/'test.json'))
