"""Replay an actual released-net protocol outside the project, without native work."""
import copy,json,os,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
report=D/'standalone_release_replay_01';report.mkdir(exist_ok=False)
work=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/robot_release_replay_01');work.mkdir(exist_ok=False)
package=D/'standalone_transactions_dev_02';runtime=work/'runtime'
assert all(sha(package/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
shutil.copytree(package,runtime,ignore=shutil.ignore_patterns('__pycache__'))
original=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00'
role=read(original/'registration.json')['roles']['reuse_on'];run=Path(read(original/'reuse_on/completion.json')['run'])
fixture=work/'positive';fixture.mkdir();nr=fixture/'reuse_on/runs/state';nr.mkdir(parents=True)
source=fixture/'source';source.mkdir();auditdir=fixture/'reuse_on_audit';auditdir.mkdir()
sources={};copies={}
def exact(old,new):
 old=Path(old);new.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,new);h=sha(old);assert sha(new)==h;sources[str(old)]=h;copies[str(new)]=h
exact(Path(role['source'])/'routed.route',source/'routed.route')
exact(Path(role['crossing_domain']),fixture/'domain.txt')
for name in ['joint_native.log','vertical_domain.log']:exact(run/name,nr/name)
audit=read(original/'reuse_on_audit/analysis.json');exact(Path(audit['candidate_route']),auditdir/'candidate.route')
for name in ['registration.json','reuse_on/completion.json','reuse_on_audit/analysis.json','reuse_on_domain_audit.json']:exact(original/name,fixture/'original_receipts'/name)
role=copy.deepcopy(role);role.update(source=str(source),crossing_domain=str(fixture/'domain.txt'))
write(fixture/'registration.json',dict(roles={'reuse_on':role},receipt_relocation='Imported metadata only; original bytes retained, no new native run.'))
closed=read(original/'reuse_on/completion.json');closed['run']=str(nr);closed['receipt_relocation']='Imported existing native result, no execution';write(fixture/'reuse_on/completion.json',closed)
audit['candidate_route']=str(auditdir/'candidate.route');audit['receipt_relocation']='Imported existing physical/scope audit, candidate copied byte-exact; not a new scope audit';write(auditdir/'analysis.json',audit)
write(report/'registration.json',dict(workspace=str(work),source_sha256=sources,copy_sha256=copies,package_manifest_sha256=sha(package/'artifact_manifest.json'),native_calls=0,validation_scope='Per-net failure-release audit replay and altered-protocol rejection; physical/scope results imported, not regenerated.'))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
def execute(batch,label,passed):
 cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'audit_failure_release_domain.py'),'--batch',str(batch),'--role','reuse_on'];start=time.monotonic()
 with (report/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 out=batch/'reuse_on_domain_audit.json';record=dict(command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-start,audit_written=out.exists(),expected_accept=passed)
 write(report/(label+'_execution.json'),record)
 assert (r.returncode==0)==passed and out.exists()==passed,label
 if not passed:assert 'AssertionError' in (report/(label+'.log')).read_text(),label
execute(fixture,'positive',True)
actual=read(fixture/'reuse_on_domain_audit.json');expected=read(original/'reuse_on_domain_audit.json')
for key in expected:
 if key!='source_sha256':assert actual[key]==expected[key],key
write(report/'positive_audit.json',actual)
negative=[]
for label in ['release_after_success','duplicate_release','wrong_retained_domain']:
 b=work/label;b.mkdir();(b/'reuse_on/runs/state').mkdir(parents=True);(b/'reuse_on_audit').mkdir()
 write(b/'registration.json',read(fixture/'registration.json'))
 c=read(fixture/'reuse_on/completion.json');c['run']=str(b/'reuse_on/runs/state');write(b/'reuse_on/completion.json',c)
 write(b/'reuse_on_audit/analysis.json',read(auditdir/'analysis.json'))
 joint=(nr/'joint_native.log').read_text();vertical=(nr/'vertical_domain.log').read_text()
 if label=='release_after_success':
  lines=joint.splitlines();idx=lines.index('DOMAIN_RELEASE 3454 1');prev=lines[idx-1].split();assert prev[0]=='ATTEMPT' and prev[-1]=='0';prev[-1]='1';lines[idx-1]=' '.join(prev);joint='\n'.join(lines)+'\n'
 elif label=='duplicate_release':
  joint=joint.replace('DOMAIN_RELEASE 3454 1\n','DOMAIN_RELEASE 3454 1\nDOMAIN_RELEASE 3454 1\n',1);vertical=vertical.replace('RELEASE 3454 1 domain_search_infeasible\n','RELEASE 3454 1 domain_search_infeasible\nRELEASE 3454 1 domain_search_infeasible\n',1)
 else:
  assert 'ALLOW 3140 4 1 1368369' in vertical;vertical=vertical.replace('ALLOW 3140 4 1 1368369','ALLOW 3140 4 1 171278',1)
 (b/'reuse_on/runs/state/joint_native.log').write_text(joint);(b/'reuse_on/runs/state/vertical_domain.log').write_text(vertical)
 execute(b,label,False);negative.append(label)
assert all(sha(f)==h for f,h in sources.items()) and all(sha(f)==h for f,h in copies.items())
assert all(sha(runtime/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
write(report/'completion.json',dict(passed=True,workspace=str(work),actual_released_queries=actual['released_queries'],remaining_guided_nets=actual['final_domain_nets'],actual_candidate_guided_sources=actual['actual_candidate_guided_sources'],original_scientific_fields_exact=True,negative_protocols_rejected=negative,original_inputs_unchanged=True,historical_project_Python_reads_forbidden=True,native_calls_new=0,new_independent_inputs=0,no_release_ablation_executed=False,full_method_frozen=False,source_sha256={str(Path(__file__).resolve()):sha(__file__),str(package/'artifact_manifest.json'):sha(package/'artifact_manifest.json'),str(report/'registration.json'):sha(report/'registration.json')},qualification='Existing robot released-domain protocol actually re-audited outside project. Scope/physical audit and candidate imported byte-exact; no new native search, no no-release comparison, no mathematical infeasibility claim.'))
print(dict(passed=True,released=actual['released_queries'],guided=actual['final_domain_nets'],negative_rejections=negative,native_calls_new=0),flush=True)
