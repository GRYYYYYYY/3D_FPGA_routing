"""Exercise actual current R1 selection/controller requests, stopping before native."""
import os,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
report=D/'standalone_resource_owner_preparation_01';report.mkdir(exist_ok=False)
base=Path(read(D/'standalone_resource_controller_validation_01/completion.json')['workspace']);runtime=base/'runtime'
r1=Path(read(D/'standalone_transaction_native_check_01/plan.json')['workspace']);work=base/'R1';work.mkdir()
package=D/'standalone_resource_controller_dev_01';assert all(sha(runtime/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
original_inputs=read(r1/'inputs.json');physical={k:v for k,v in original_inputs['files'].items() if k not in ['binary','route']}
config=work/'runtime_config.json';write(config,dict(format='explicit_unified_phase_runtime_v1',physical_files=physical,phase_binaries={'resource':dict(path=str(base/'inputs/binary_resource'),sha256=sha(base/'inputs/binary_resource')),'owner':original_inputs['files']['binary']},full_graph_cache_completion_sha256=sha(r1/'full_cache/completion.json')))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(script,args,label,expected=0):
 cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/script),*map(str,args)];start=time.monotonic()
 with (report/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 write(report/(label+'_execution.json'),dict(command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-start));assert (r.returncode==0)==(expected==0),label
execute('current_escape_owner_selector_v1.py',['--state',r1/'state','--full-graph-cache',r1/'full_cache','--output',work/'owner_selection'],'owner_selection')
original=D/'current_escape_owner_selector_validation_01/R1'
for n in ['groups.json','certificates.json','screens.json','classifications.json']:assert read(work/'owner_selection'/n)==read(original/n),n
execute('current_owner_transaction_v1.py',['--state',r1/'state','--root-state',r1/'state','--selection',work/'owner_selection','--full-graph-cache',r1/'full_cache','--output',work/'owner_transaction'],'owner_transaction_prepare')
assert (work/'owner_transaction/request.txt').read_bytes()==(r1/'expected/request.txt').read_bytes()
assert read(work/'owner_transaction/preparation.json')['transaction_registered']
execute('run_unified_resource_repair_v1.py',['--runtime-config',config,'--initial-state',r1/'state','--batch',work/'controller','--seed-order','delay_rr_id','--full-graph-cache',r1/'full_cache','--domain-mode','paired','--domain-feedback','--bundle-size','8','--assert-no-native-work'],'controller_first_resource_request',1)
log=(report/'controller_first_resource_request.log').read_text();assert 'Read-only preflight encountered a candidate requiring native execution' in log
actor=work/'controller';assert not (actor/'completion.json').exists() and not (actor/'active_child.json').exists()
assert read(actor/'current_state.json')['accepted_steps']==0
selection=actor/'round_000/selection';reference=D/'stable_seed_transfer_recovery_01/bnn_R1_paired/round_008'
assert read(selection/'candidates.json')==read(reference/'selection/candidates.json')
request=actor/'round_000/candidate_00/request.txt';assert request.read_bytes()==(reference/'candidate_00/request.txt').read_bytes()
assert not any((actor/'round_000/candidate_00'/n).exists() for n in ['reuse_on','reuse_off'])
write(report/'completion.json',dict(passed=True,workspace=str(work),actual_R1_owner_groups=len(read(work/'owner_selection/groups.json')),owner_groups_certificates_screens_classifications_exact=True,actual_owner_request_bytes_exact=True,controller_first_resource_request_bytes_exact=True,controller_stopped_before_native=True,accepted_steps=0,native_calls_new=0,new_independent_inputs=0,positive_owner_commit_reentry_tested=False,full_method_frozen=False,source_sha256={str(package/'artifact_manifest.json'):sha(package/'artifact_manifest.json'),str(work/'owner_transaction/preparation.json'):sha(work/'owner_transaction/preparation.json'),str(work/'owner_selection/completion.json'):sha(work/'owner_selection/completion.json'),str(request):sha(request),str(Path(__file__).resolve()):sha(__file__)},qualification='Actual current R1 owner selector and preparation plus real controller first crossing selection/request executed outside project. Expected assert-no-native-work is a deliberate preparation stop, not solver failure/no-gain or a completed controller run. No automatic owner commit/reentry or native backend equivalence proven.'))
print(dict(passed=True,R1_owner_groups=8,owner_request_exact=True,first_resource_request_exact=True,native_calls_new=0),flush=True)
