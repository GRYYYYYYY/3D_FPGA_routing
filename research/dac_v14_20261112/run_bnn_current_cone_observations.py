#!/usr/bin/env python3
"""Observe pristine BNN states; derive new current endpoints without rerouting."""
import os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import input_identity,native_config

start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
b=D/'timing_cone_bnn_dev_01';b.mkdir(exist_ok=False)
sources={arm:D/f'native_reconvergence_bnn_dev_01/runs/bnn_{arm}' for arm in ['Tf','A0','R1']}
files=[Path(__file__).resolve(),D/'run_timing_cone_state_analysis_uncached.py',D/'current_sta_arrival_cone.py',D/'native_timing_echo_v2.py',D/'timing_cone_stage_03/binding.json',D/'spmv_current_worst_source_reference_01/completion.json']
for source in sources.values():
 for n in ['manifest.json','routed.route','packed.net','placed.place','independent_audit.json']:files.append(source/n)
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_work',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 question='Do unrepaired BNN Tf, strong native A0 and old R1 expose current dominant timing connections with scope for repair, after the SPMV current worst cone has zero fixed-terminal distance gain?',
 input_sources={k:str(v) for k,v in sources.items()},source_sha256=bindings,
 method='Fresh native FULL/STA with full-precision echo; exact endpoint-vector and dominant-arrival selection. No routing, no manual target list. Preserve independent strict/endpoint policies for subsequent capacity/native transactions; new observations are not quality improvements.',
 controls='Same frozen observer, unchanged source routes, packed/place files and constraints. Different BNN graph must get its own binary/cache before queries. Initial physical audit reuse explicitly recorded; native FULL always runs.',
 limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),no_overall_research_stop=True))
rows={};calls=[];seen={}
def invoke(script,args,tag):
 assert shutil.disk_usage(D).free>=80*1024**3
 cmd=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'
 with (b/(tag+'.log')).open('w') as log:
  p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=p.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(p.pid,signal.SIGTERM)
   try:code=p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);code=p.wait()
 calls.append(dict(tag=tag,command=cmd,status=status if code==0 or status=='timeout' else 'failed',returncode=code,complete_process_seconds=time.monotonic()-t))
 write(b/'process_costs.json',calls);return code==0
for arm,source in sources.items():
 key=str([route_body(source/'routed.route'),input_identity(source),native_config(source)])
 if key in seen:
  rows[arm]=dict(status='reused_identical_initial_state',source=str(source),state=str(seen[key]),reused=True)
 else:
  state=b/arm
  ok=invoke('run_timing_cone_state_analysis_uncached.py',['--source',source,'--batch',state,'--timing-echo'],arm)
  if not ok or not read(state/'completion.json')['passed']:
   rows[arm]=dict(status='observation_failed',source=str(source),state=str(state));write(b/'progress.json',rows);continue
  assert route_body(Path(read(state/'completion.json')['run'])/'routed.route')==route_body(source/'routed.route')
  seen[key]=state
  ok=invoke('current_sta_arrival_cone.py',['--state',state,'--output',b/(arm+'_current_cone.json')],arm+'_cone')
  rows[arm]=dict(status='observed_and_selected' if ok else 'selection_failed',source=str(source),state=str(state),reused=False,
                 cpd_s=read(state/'endpoint_vector.json')['cpd_s'],cone=str(b/(arm+'_current_cone.json')) if ok else None)
 write(b/'progress.json',rows)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=all(r['status'] in ['observed_and_selected','reused_identical_initial_state'] for r in rows.values()),roles=rows,
 source_sha256=bindings,new_native_observations=sum(c['tag'] in sources for c in calls),route_search_calls=0,
 complete_orchestrator_seconds=time.monotonic()-start,qualification='Necessary new BNN initial full-precision observations and automatic target selections. No accepted repair or CPD improvement yet. Individual failure is recorded and other input arms continue.'))
print(rows,flush=True)
