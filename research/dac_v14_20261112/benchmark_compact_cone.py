#!/usr/bin/env python3
"""Interleaved same-state selector benchmark; no native routing or STA calls."""
import os,resource,shutil,signal,statistics,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
b=D/'compact_cone_benchmark_01';b.mkdir(exist_ok=False)
refs=dict(bnn_initial=D/'timing_cone_bnn_dev_02/Tf_current_cone.json',bnn_accepted=D/'bnn_release_joint_dev_01/Tf_combined_weighted_soft_successor_cone.json',spmv=D/'spmv_current_worst_arrival_cone_01.json')
roles={n:dict(reference=str(p),state=read(p)['source_state']) for n,p in refs.items()}
files=[Path(__file__).resolve(),D/'compact_timing_cone.py',D/'current_sta_arrival_cone_compact.py',D/'current_sta_arrival_cone.py',D/'native_timing_echo_v2.py',D/'compact_timing_cone_validation_01/completion.json',*refs.values()]
bindings={str(p):sha(p) for p in files};write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],roles=roles,
 question='Does compact setup-only storage preserve exact scheduling and reduce the completed selector process cost on the same existing native states?',
 order='BNN_initial full/compact/compact/full; BNN_accepted compact/full/full/compact; SPMV full/compact',source_sha256=bindings,
 qualification='Component engineering development benchmark during existing native jobs; not formal whole-router or full-algorithm speedup. No native/route/STA reruns.',native_calls=0))
rows=[];keys=['passed','near_ns','worst_slack_s','selected_endpoints','cones','routed_connections','unresolved_non_source_nodes']
for name,role in roles.items():
 reference=read(role['reference']);assert reference['passed']
 order=['full','compact','compact','full'] if name=='bnn_initial' else ['compact','full','full','compact'] if name=='bnn_accepted' else ['full','compact']
 for i,mode in enumerate(order):
  assert shutil.disk_usage(D).free>=80*1024**3
  output=b/f'{name}_{i}_{mode}.json';script=D/('current_sta_arrival_cone_compact.py' if mode=='compact' else 'current_sta_arrival_cone.py')
  command=[sys.executable,str(script),'--state',role['state'],'--output',str(output)];t=time.monotonic()
  with output.with_suffix('.log').open('w') as log:
   proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   write(b/'active_child.json',dict(pid=proc.pid,state=name,mode=mode,repeat=i,command=command))
   try:code=proc.wait(timeout=900)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();code=124
  elapsed=time.monotonic()-t
  if code:
   rows.append(dict(state=name,mode=mode,status='timeout' if code==124 else 'failed',returncode=code,complete_process_seconds=elapsed));write(b/'progress.json',rows);continue
  actual=read(output);assert all(reference[k]==actual[k] for k in keys),(name,mode,'selection changed')
  rows.append(dict(state=name,mode=mode,repeat=i,status='identical',complete_process_seconds=elapsed,output=str(output),output_sha256=sha(output)));write(b/'progress.json',rows)
 summaries={}
 for n in roles:
  times={m:[r['complete_process_seconds'] for r in rows if r['state']==n and r['mode']==m and r['status']=='identical'] for m in ['full','compact']}
  if all(times.values()):summaries[n]=dict(median_seconds={m:statistics.median(t) for m,t in times.items()},samples={m:len(t) for m,t in times.items()},compact_over_full=statistics.median(times['compact'])/statistics.median(times['full']))
 write(b/'summary_progress.json',summaries)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=all(r['status']=='identical' for r in rows),rows=rows,summary=summaries,source_sha256=bindings,complete_process_seconds=time.monotonic()-start,native_calls=0,
 qualification='Identical selected endpoints, every winning fanin/proposal/gap, mapped routed connections and unknown statuses on all successful observations. Small interleaved component sample; no whole algorithm or formal router runtime claim. Existing native cohorts unchanged.'))
print(summaries,flush=True)
