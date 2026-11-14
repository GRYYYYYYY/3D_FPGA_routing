#!/usr/bin/env python3
"""Reuse completed references to check the old static interface in the new binary."""
import json,os,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_analysis_pool import quoted
b=D/'analysis_queue_static_compatibility_01';b.mkdir(exist_ok=False);old=D/'analysis_queue_tiny_regression_01';assert read(old/'completion.json')['passed'];assert all(sha(p)==h for p,h in read(old/'registration.json')['source_sha256'].items());r=read(old/'pool/registration.json');cmd=r['command'];guard=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard';route=Path(cmd[cmd.index('--route_file')+1]);alt=D/'analysis_fork_tiny_regression_01/equivalent_pin.route';entries=[]
for i,input_ in enumerate([route,alt]):
 directory=b/('worker_'+str(i));directory.mkdir();entries.append((input_,directory))
manifest=b/'manifest.txt';manifest.write_text('2\n'+''.join(quoted(p)+' '+quoted(q)+' 1\n' for p,q in entries));env={k:v for k,v in os.environ.items() if not k.startswith('VPR_')};env.update(VPR_H3D_MODE='off',VPR_H3D_ANALYSIS_FORK_MANIFEST=str(manifest),VPR_H3D_ANALYSIS_FORK_RESULTS=str(b/'workers.tsv'));files=[Path(__file__).resolve(),D/'analysis_queue_stage_01/binding.json',old/'completion.json',old/'registration.json',manifest,route,alt];write(b/'registration.json',dict(status='before_static_native',source_sha256={str(p):sha(p) for p in files},question='Does the existing static manifest retain its exact FULLSTA interface under the dynamic-capable binary?',new_reference_processes=0,route_calls=0));t=time.monotonic()
with (b/'stdout.log').open('w') as out:
 p=subprocess.Popen(['prlimit','--core=0:0','--as='+str(64*1024**3),'--',str(guard),*cmd],cwd=b,env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=60)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();raise
assert code==0
for (route,directory),reference in zip(entries,['original','alternative']):
 for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo']:assert sha(directory/name)==sha(old/reference/name)
assert all(sha(p)==h for p,h in read(b/'registration.json')['source_sha256'].items());write(b/'completion.json',dict(passed=True,old_static_interface_exact=True,native_parents=1,workers=2,reused_completed_reference_processes=2,new_reference_processes=0,route_calls=0,complete_process_seconds=time.monotonic()-t,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'workers.tsv',Path(__file__).resolve()]}));print(dict(passed=True,workers=2),flush=True)
