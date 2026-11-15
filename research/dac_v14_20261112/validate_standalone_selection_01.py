"""Relocate real R1 and tiny observations; compare original selectors without routing."""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_sta_selector import select

report=D/'standalone_selection_validation_01';report.mkdir(exist_ok=False)
package=D/'standalone_selection_dev_01'
for p in package.glob('*.py'):compile(p.read_text(),str(p),'exec')
write(package/'artifact_manifest.json',dict(format='standalone_selection_development_v1',full_method_frozen=False,
    sha256={p.name:sha(p) for p in package.iterdir() if p.is_file()},
    qualification='Observation plus exact scientific selector kernels and byte-exact persistent pool; full controller/transactions not yet portable.'))
relocated=Path(tempfile.mkdtemp(prefix='standalone-selection-'));target=relocated/'runtime'
shutil.copytree(package,target,ignore=shutil.ignore_patterns('__pycache__'))
oldrel=Path(read(D/'standalone_observation_dependencies_validation_02/completion.json')['relocated_directory'])
for name in ['numpy','numpy.libs','lxml','lxml.libs']:
    p=oldrel/'runtime_v2'/name
    if p.exists():shutil.copytree(p,target/name,ignore=shutil.ignore_patterns('__pycache__'))
write(report/'registration.json',dict(relocated=str(relocated),package_sha256=sha(package/'artifact_manifest.json'),
    native_calls_planned=0,physical_observations=['known_BNN_R1','known_tiny'],new_independent_scientific_inputs=0))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
sources={};cases={}
def copied(src,dst):
    src=Path(src);shutil.copy2(src,dst);h=sha(src);assert sha(dst)==h
    sources[str(src)]=h
def fixture(name,state,graph_cache):
    f=relocated/name;f.mkdir();run=Path(read(state/'completion.json')['run'])
    for n in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','independent_audit.json']:
        copied(run/n,f/n)
    copied(state/'endpoint_vector.json',f/'endpoint_vector.json')
    parent=Path(read(graph_cache/'completion.json')['parent_cache'])
    graph=Path(read(parent/'completion.json')['graph']);copied(graph,f/'rr_graph.xml')
    for old,new in [(parent,f/'audit_cache'),(graph_cache,f/'full_cache')]:
        new.mkdir();c=read(old/'completion.json')
        copied(old/'completion.json',new/'origin_completion.json')
        for n in c['payload_sha256']:copied(old/n,new/n)
        # Explicit metadata relocation, not an invented native execution/build.
        if new.name=='audit_cache':c['graph']=str(f/'rr_graph.xml')
        else:c.update(parent_cache=str(f/'audit_cache'),parent_completion_sha256=sha(f/'audit_cache/completion.json'))
        c['relocation']=dict(origin_completion_sha256=sha(new/'origin_completion.json'),payloads_unchanged=True,new_build=False)
        write(new/'completion.json',c)
    files=dict(route='routed.route',trace='native_sta_frontier.jsonl',constraints='native_sta_frontier.jsonl.constraints.echo',vector='endpoint_vector.json',audit='independent_audit.json',graph='rr_graph.xml')
    write(f/'inputs.json',dict(format='explicit_selection_observation_v1',files={k:dict(path=n,sha256=sha(f/n)) for k,n in files.items()},
        cache=dict(path='full_cache',completion_sha256=sha(f/'full_cache/completion.json')),minimum_margin_ns=.2,near_ns=0.))
    write(f/'expected_sta.json',select(run/'native_sta_frontier.jsonl'))
    return f

r1sel=D/'current_escape_owner_selector_validation_01/R1'
r1state=Path(read(r1sel/'completion.json')['state'])
f=fixture('R1',r1state,D/'full_route_graph_cache_bnn_01')
for n in ['certificates.json','screens.json','groups.json','classifications.json','selected_request.txt']:
    copied(r1sel/n,f/('expected_'+n))
cross=D/'stable_seed_transfer_recovery_01/bnn_R1_paired/round_008/selection'
assert Path(read(cross/'completion.json')['source_state'])==r1state
copied(cross/'candidates.json',f/'expected_crossing_candidates.json')
copied(cross/'completion.json',f/'expected_crossing_completion.json')
cases['R1']=f
tiny=D/'fresh_route_entry_preflight_01/flow'
cases['tiny']=fixture('tiny',tiny/'initial',tiny/'full_graph_cache')

results={}
for name,f in cases.items():
    cmd=['/usr/bin/python3',str(target/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(target/'select_scopes.py'),
         '--inputs',str(f/'inputs.json'),'--output',str(f/'selection')]
    start=time.monotonic()
    with (report/(name+'.log')).open('w') as log:
        process=subprocess.run(cmd,cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    write(report/(name+'_execution.json'),dict(command=cmd,returncode=process.returncode,elapsed_seconds=time.monotonic()-start))
    assert process.returncode==0,name
    output=f/'selection';c=read(output/'completion.json')
    assert read(output/'sta.json')==read(f/'expected_sta.json')
    owner=read(output/'owner.json');crossing=read(output/'crossing.json')
    if name=='R1':
        for k in ['certificates','screens','groups','classifications']:assert owner[k]==read(f/('expected_'+k+'.json')),k
        assert owner['groups'][0]['request']==(f/'expected_selected_request.txt').read_text()
        assert crossing['candidates']==read(f/'expected_crossing_candidates.json')
        old=read(f/'expected_crossing_completion.json')
        assert crossing['actual_resources']==old['actual_resources'] and crossing['multi_crossing_nets']==old['multi_crossing_nets']
        assert len(owner['groups'])==8 and len(crossing['candidates'])==1
    else:
        assert not owner['groups'] and not crossing['candidates']
    results[name]=dict(passed=True,STA_exact=True,owner_groups=len(owner['groups']),crossing_scopes=len(crossing['candidates']),
        complete_selection_seconds=c['complete_selection_seconds'],native_calls_new=0)
    shutil.copy2(output/'completion.json',report/(name+'_selection.json'))

# Fail before creating outputs if a declared physical input differs.
bad=read(cases['tiny']/'inputs.json');bad['files']['route']['sha256']='0'*64
write(cases['tiny']/'bad_inputs.json',bad)
cmd=['/usr/bin/python3',str(target/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(target/'select_scopes.py'),
     '--inputs',str(cases['tiny']/'bad_inputs.json'),'--output',str(cases['tiny']/'bad_selection')]
r=subprocess.run(cmd,cwd=target,env=env,capture_output=True,text=True,timeout=30)
write(report/'bad_input_execution.json',dict(command=cmd,returncode=r.returncode,stderr=r.stderr))
assert r.returncode!=0 and 'Observation input changed' in r.stderr and not (cases['tiny']/'bad_selection').exists()
assert all(sha(p)==h for p,h in sources.items())
write(report/'completion.json',dict(passed=True,relocated_directory=str(relocated),results=results,
    full_serial_pool_byte_exact=sha(target/'seed_census_analysis_pool_v2.py')==sha(D/'seed_census_analysis_pool_v2.py'),
    native_pool_execution_tested=False,wrong_input_rejected=True,historical_project_Python_reads_forbidden=True,
    native_calls_new=0,new_independent_scientific_inputs=0,full_method_frozen=False,source_sha256=sources,
    qualification='Actual relocated selector replay on full known BNN R1 and tiny observation. R1 has eight eligible owner groups and one sharing scope; all exact certificates/screens/ranks/requests and STA targets match historical originals. Tiny zero scopes retained. Cache payloads copied, metadata transparently relocated; no graph regeneration/native call. Persistent pool only copied byte-exact, not executed in this validation.'))
print(results,flush=True)
