"""Durably bind one real owner transaction interface check, after existing work."""
import copy,os,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
v=read(D/'standalone_transactions_validation_03/completion.json');assert v['passed']
old=Path(v['relocated_directory'])/'fixture';package=D/'standalone_transactions_dev_02'
root=D/'standalone_transaction_native_check_01';root.mkdir(exist_ok=False)
w=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/native_transaction_01');w.mkdir(exist_ok=False)
shutil.copytree(old.parent/'runtime_v2',w/'runtime',ignore=shutil.ignore_patterns('__pycache__'))
assert all(sha(w/'runtime'/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
mapping={};originals={};relocated=[]
def exact(src,dst):
 src=Path(src).resolve();dst=Path(dst).resolve();dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src)
 if not dst.exists():shutil.copy2(src,dst)
 assert sha(dst)==h;mapping[str(src)]=str(dst);originals[str(src)]=h;return dst
spec=read(old/'explicit_inputs.json');oldfull=Path(spec['full_graph_cache']['path']);oldparent=Path(read(oldfull/'completion.json')['parent_cache'])
for k,row in spec['files'].items():
 name={'packed':'source/packed.net','placement':'source/placed.place','route':'source/routed.route'}.get(k,'inputs/'+k+Path(row['path']).suffix)
 row['path']=str(exact(row['path'],w/name))
for srcdir,dstdir in [(oldparent,w/'audit_cache'),(oldfull,w/'full_cache')]:
 for name in read(srcdir/'completion.json')['payload_sha256']:exact(srcdir/name,dstdir/name)
def translated(v):
 if isinstance(v,str):return mapping.get(v,v)
 if isinstance(v,list):return [translated(x) for x in v]
 if isinstance(v,dict):return {translated(k):translated(x) for k,x in v.items()}
 return v
def metadata(src,dst,changes):
 raw=read(src);exact(src,dst.with_name(dst.name+'.origin'));data=translated(raw);data.update(changes)
 data['receipt_relocation']=dict(original_receipt=str(dst.with_name(dst.name+'.origin')),original_sha256=sha(src),native_execution_new=False,qualification='Derived path binding of existing evidence; scientific data unchanged.')
 write(dst,data);mapping[str(Path(src).resolve())]=str(dst.resolve());relocated.append(dict(source=str(src),target=str(dst),source_sha256=sha(src),target_sha256=sha(dst)))
metadata(oldparent/'completion.json',w/'audit_cache/completion.json',dict(graph=spec['files']['graph']['path']))
metadata(oldfull/'completion.json',w/'full_cache/completion.json',dict(parent_cache=str(w/'audit_cache'),parent_completion_sha256=sha(w/'audit_cache/completion.json')))
spec['full_graph_cache']=dict(path=str(w/'full_cache'),completion_sha256=sha(w/'full_cache/completion.json'));write(w/'inputs.json',spec)
for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','independent_audit.json']:exact(old/'source'/name,w/'source'/name)
exact(old/'state/endpoint_vector.json',w/'state/endpoint_vector.json')
metadata(old/'source/manifest.json',w/'source/manifest.json',{})
metadata(old/'state/completion.json',w/'state/completion.json',dict(run=str(w/'source')))
for name in ['owner.json','crossing.json','sta.json']:exact(old/'selection'/name,w/'selection'/name)
selected=read(old/'selection/completion.json');bindings={}
for name,digest in selected['source_sha256'].items():
 assert sha(name)==digest
 if name not in mapping:exact(name,w/'provenance'/('selected_'+Path(name).name))
 target=Path(mapping[name]);bindings[str(target)]=sha(target)
metadata(old/'selection/completion.json',w/'selection/completion.json',dict(source_sha256=bindings))
expected=w/'expected';expected.mkdir();origin=D/'R1_owner_release_joint_probe_01/transaction'
for src,dst in [(origin/'joint_native_evaluation/endpoint_vector.json',expected/'endpoint_vector.json'),(origin/'joint_native_evaluation/runs/state/independent_audit.json',expected/'independent_audit.json'),(origin/'joint_native_audit/candidate.route',expected/'candidate.route'),(origin/'joint_native_decisions.json',expected/'original_decisions.json'),(old/'prepared_owner_v2/request.txt',expected/'request.txt')]:exact(src,dst)
write(w/'relocation.json',dict(passed=True,original_sha256=originals,derived_receipts=relocated,new_native_execution=False))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
cmd=['/usr/bin/python3',str(w/'runtime/guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(w/'runtime/transact.py'),'--inputs',str(w/'inputs.json'),'--state',str(w/'state'),'--root-state',str(w/'state'),'--selection',str(w/'selection'),'--output',str(w/'preflight'),'--kind','owner','--domain-mode','unrestricted','--prepare-only']
with (root/'preflight.log').open('x') as log:r=subprocess.run(cmd,cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
write(root/'preflight_execution.json',dict(command=cmd,returncode=r.returncode,native_calls_new=0));assert r.returncode==0
assert (w/'preflight/request.txt').read_bytes()==(expected/'request.txt').read_bytes()
files=[f for sub in ['runtime','inputs','source','state','selection','audit_cache','full_cache','provenance','expected'] for f in (w/sub).rglob('*') if f.is_file()]
files += [w/'inputs.json',w/'relocation.json',Path(__file__).resolve(),D/'run_standalone_transaction_native_check_01.py',D/'queue_standalone_transaction_native_check_01.py',D/'supervise_component_process_v1.py',D/'component_subreaper_validation_01/completion.json']
write(root/'plan.json',dict(passed=True,registered_before_native=True,workspace=str(w),predecessor=str(D/'standalone_native_observation_equivalence_01/queue'),input_sha256={str(f):sha(f) for f in files},native_calls_planned=2,nonempty_transaction_calls_planned=1,new_independent_inputs=0,full_method_frozen=False,transaction_root_is_current_R1=True,limits=dict(native_seconds=1800,whole_component_seconds=7200,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),expected=dict(full_endpoint_vector_exact=True,candidate_route_body_exact=True,physical_scientific_audit_exact=True,owner_request_exact=True,resource_acceptance=True),qualification='New execution check for the explicit portable transaction adapter, using a copied known R1 state and five-connection request. Empty serialization control plus actual repair, full restored/candidate gates, physical/scope audits and fixed-root acceptance. Not a repeat of a scientific batch or an independent input. Exact binary and dependencies bound; current R1 is the declared test root, not a new complete-method baseline. Original optimized resource pool/lazy/snapshot implementation remains distinct.'))
print(dict(registered=True,workspace=str(w),files=len(files),native_calls_planned=2,native_calls_executed=0),flush=True)
