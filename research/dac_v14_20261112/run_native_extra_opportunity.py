#!/usr/bin/env python3
"""Native-only larger post-legal opportunity with unchanged original router binaries."""
import fcntl,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,normalized_command
from full_route_graph_cache import FullRouteGraphCache
from routing_log_metrics import ROW
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103';sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit
b=D/'native_extra_opportunity_bnn_01';reg=read(b/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items());resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));started=time.monotonic();shutil.copy2(OLD/'runtime_dependency_binding.json',b/'runtime_dependency_binding.json');io.BASE=b;io.ADDRESS_SPACE_BYTES=64*1024**3;results={};costs=[];cache=None
write(b/'execution_registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256={str(Path(__file__).resolve()):sha(__file__),str(b/'registration.json'):sha(b/'registration.json')}))
def iteration_rows(path):return [l.split()[:1]+l.split()[2:] for l in path.read_text().splitlines() if ROW.match(l)]
def invoke(script,args,tag):
 t=time.monotonic();cmd=[sys.executable,str(D/script),*map(str,args)]
 with (b/(tag+'.log')).open('w') as out:
  proc=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(tag=tag,pid=proc.pid,command=cmd))
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,returncode=code,complete_child_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);return code==0
for arm,role in reg['roles'].items():
 assert shutil.disk_usage(b).free>=80*1024**3;source=Path(role['source_route_run']);before=read(source/'manifest.json');rd=b/'runs'/arm;rd.mkdir(parents=True);(b/'bin'/arm).mkdir(parents=True);binary=b/'bin'/arm/'vpr';shutil.copy2(before['command'][0],binary);assert sha(binary)==role['original_binary_sha256']
 for n in ['packed.net','placed.place']:shutil.copy2(source/n,rd/n)
 cmd=list(role['command']);cmd[0]=str(binary)
 for option,name in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(option)+1]=str(rd/name)
 lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 write(b/'status.json',dict(status='native_route_running',arm=arm,pid=os.getpid()))
 try:
  result=io.run(arm,cmd,environment=role['environment'],frozen=[binary,Path(cmd[1]),Path(cmd[2]),Path(cmd[cmd.index('--read_rr_graph')+1]),b/'registration.json'],private_inputs=[rd/'packed.net',rd/'placed.place'],timeout=1800,tags=dict(circuit='bnn',arm=arm,operation='full_native_extra_convergence',convergence_max=8,reconvergence_threshold=1.01))
  checks={n:sha(rd/n)==sha(source/n) for n in ['packed.net','placed.place']};write(rd/'pair_check.json',dict(passed=all(checks.values()),checks=checks,reference=str(source)))
  reference=Path(role['first_legal_reference']);old=iteration_rows(reference/'stdout.log');new=iteration_rows(rd/'stdout.log');prefix=len(new)>=len(old) and new[:len(old)]==old;write(rd/'first_legal_prefix.json',dict(passed=prefix,reference=str(reference),reference_iterations=len(old),treatment_iterations=len(new),scope='Only printed native iteration values excluding elapsed time before first legal convergence; not full intermediate route equivalence.'))
  row=dict(status=result['status'],route_process_seconds=result['wall_seconds'],metrics=result['metrics'],first_legal_prefix_passed=prefix,packed_placement_exact=all(checks.values()),whole_single_configuration_native_route_seconds=result['wall_seconds'],posthoc_observer_seconds=None)
  if result['status']=='completed' and result['metrics'].get('native_full_check_passed') and result['metrics'].get('routing_success_reported'):
   graph=Path(cmd[cmd.index('--read_rr_graph')+1])
   if cache is None:cache=FullRouteGraphCache(graph,D/'full_route_graph_cache_bnn_01')
   saved=study.cr.read_graph_evidence;study.cr.read_graph_evidence=cache.evidence;study.BASE=b
   try:audit=study.audit_batch({'fixture':{'original_graph':str(graph)}},[result],b/(arm+'_independent_audit.json'))
   finally:study.cr.read_graph_evidence=saved
   row['physical_audit_passed']=audit['passed']
   if (rd/'h3d_final_guides.csv').exists():guide_audit(rd);row['guide_audit_passed']=read(rd/'final_guide_audit.json')['passed']
  else:row['physical_audit_passed']=False
 finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
 if row['physical_audit_passed']:
  t=time.monotonic();ok=invoke('run_timing_cone_state_analysis_v2.py',['--source',rd,'--batch',b/(arm+'_observation'),'--full-graph-cache',D/'full_route_graph_cache_bnn_01','--timing-echo'],arm+'_full_precision_observer');row['posthoc_observer_seconds']=time.monotonic()-t
  if ok:
   obs=read(b/(arm+'_observation/completion.json'));v=read(b/(arm+'_observation/endpoint_vector.json'));row.update(status='legal_evaluated',CPD_s=v['cpd_s'],full_precision_observer=str(b/(arm+'_observation')),posthoc_observer_passed=obs['passed'],actual_resources=read(rd/'independent_audit.json')['physical_metrics'])
  else:row.update(status='native_legal_observer_failed',posthoc_observer_passed=False)
 results[arm]=row;write(b/'progress.json',results);print(arm,row,flush=True)
io.seal_inputs(b/'input_seal.json');write(b/'completion.json',dict(passed=all(r['status'] in ['legal_evaluated','failed','timeout'] for r in results.values()),roles=results,complete_shared_research_workflow_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'execution_registration.json',b/'progress.json',b/'input_seal.json',*b.glob('*_independent_audit.json')]},qualification='Each original native algorithm executes one complete fresh route process with additional post-legal opportunity. Separate posthoc full-precision/physical audits are evidence creation, not substituted as algorithm runtime. This diagnostic is not a formally rotated timing comparison with imported-state repair prototypes. Initial/native convergence differences remain explicit. A failed role does not complete the active research goal.'))
