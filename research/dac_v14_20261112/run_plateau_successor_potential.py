#!/usr/bin/env python3
"""Paired current-worst successor potential; reuse exact prior capacity data."""
import shutil,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_sta_selector import select
from run_native_frontier_queries import fingerprint,groups,write_cases

b=D/'plateau_successor_potential_01';b.mkdir(exist_ok=False);started=time.monotonic();assert shutil.disk_usage(D).free>=80*1024**3
study=D/'current_sta_policy_R1_near_01';done=read(study/'completion.json')
inputs=[('strict',Path(done['outcomes']['strict']['state']),study/'queries_000'),('endpoint',Path(done['outcomes']['endpoint_vector']['state']),study/'queries_004')]
driver=D/'current_sta_relaxed_01/critical_capacity_driver';binary=D/'residual_query_offline_01/graph.bin'
assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
write(b/'registration.json',dict(status='registered_before_queries',question='Do endpoint-only plateau changes alter current-worst physical successor potential?',
 source_sha256={str(p):sha(p) for p in [Path(__file__),D/'current_sta_plateau_successor_experiment_01.json',study/'completion.json',driver,binary]},
 limits=dict(query_seconds=120,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3)))
cache={};rows=[];calls=[]
for role,state,parent in inputs:
 q=b/role;q.mkdir();source=Path(read(state/'completion.json')['run']);selection=select(source/'native_sta_frontier.jsonl');selection['input_run']=str(source)
 keys={(r['net'],r['pin']) for r in selection['targets']};audit=read(parent/'analysis.json');ex=read(parent/'execution.json')
 assert audit['passed'] and all(sha(p)==h for p,h in audit['source_sha256'].items())
 assert all(sha(parent/p)==h for p,h in ex['output_sha256'].items())
 parent_source=Path(read(parent/'execution_registration.json')['input_run'])
 assert all(sha(source/n)==sha(parent_source/n) for n in ['routed.route','packed.net','placed.place','native_sta_frontier.jsonl'])
 cases=[c for c in read(parent/'cases.json') if (c['net'],c['pin']) in keys];assert len(cases)==len(keys)
 cap_rows=[r for r in audit['results'] if (r['net'],r['pin']) in keys];assert len(cap_rows)==len(cases)
 for name in ['capacities.bin','occupancy_owners.json','unit_validation.json']:shutil.copy2(parent/name,q/name)
 write(q/'selection.json',selection);write(q/'cases.json',cases);write_cases(q/'cases.txt',cases)
 bindings={str(p):sha(p) for p in [Path(__file__),parent/'analysis.json',parent/'execution.json',parent/'execution_registration.json',parent/'cases.json',source/'native_sta_frontier.jsonl',driver,binary]}
 write(q/'execution_registration.json',dict(status='registered_before_query',input_run=str(source),query_modes=[0],source_sha256=bindings,
  question='Current-worst relaxed physical distance from the same retained anchors. Capacity answers are reused from the sealed full-window experiment.'))
 missing=[c for c in cases if fingerprint(c,0) not in cache];answers={};query_seconds=0.
 if missing:
  write_cases(q/'missing.txt',missing);t=time.monotonic()
  with (q/'new.log').open('w') as out,(q/'query_stderr.log').open('w') as err:r=subprocess.run(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(q/'missing.txt')],stdout=out,stderr=err,timeout=120)
  query_seconds=time.monotonic()-t;assert r.returncode==0;fresh=groups(q/'new.log')
  for c in missing:cache[fingerprint(c,0)]=(fresh[c['net'],c['pin'],0],str(q/'new.log'),sha(q/'new.log'))
 else:(q/'query_stderr.log').write_text('')
 receipts=[]
 for c in cases:
  lines,path,h=cache[fingerprint(c,0)];assert sha(path)==h;answers[c['net'],c['pin'],0]=lines;bindings[path]=h
  receipts.append(dict(net=c['net'],pin=c['pin'],fingerprint=fingerprint(c,0),source=path,reused=c not in missing))
 with (q/'query_stdout.log').open('w') as f:
  for key in sorted(answers):f.writelines(answers[key])
 write(q/'reuse_receipts.json',receipts);write(q/'capacity_reference.json',dict(results=cap_rows,parent=str(parent),source_sha256={str(parent/'analysis.json'):sha(parent/'analysis.json')},reused=True))
 names=['cases.json','cases.txt','selection.json','capacities.bin','occupancy_owners.json','unit_validation.json','query_stdout.log','query_stderr.log']
 write(q/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=bindings,output_sha256={n:sha(q/n) for n in names},new_queries=len(missing),reused_queries=len(cases)-len(missing),query_process_seconds=query_seconds))
 t=time.monotonic()
 with (q/'audit.log').open('w') as out:r=subprocess.run([sys.executable,str(D/'audit_current_sta_queries.py'),'--batch',str(q)],stdout=out,stderr=subprocess.STDOUT,timeout=1800)
 calls.append(dict(role=role,phase='physical_audit',returncode=r.returncode,seconds=time.monotonic()-t));write(b/'process_costs.json',calls);assert r.returncode==0
 relaxed=read(q/'analysis.json');assert relaxed['passed']
 rows.append(dict(role=role,state=str(state),targets=selection['targets'],capacity=cap_rows,relaxed=relaxed['results'],new_queries=len(missing),reused_relaxed=len(cases)-len(missing)))
 write(b/'progress.json',rows)
write(b/'completion.json',dict(passed=True,rows=rows,complete_seconds=time.monotonic()-started,new_queries=sum(r['new_queries'] for r in rows),
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',*b.glob('*/analysis.json'),*b.glob('*/capacity_reference.json')]},
 qualification='Paired fixed-retained-tree current-worst potential. No global physical or STA bound; compatible joint paths and complete restoration remain separate if positive gain exists.'))
print([(r['role'],[(x['net'],x['pin'],x['improvement_ns']) for x in r['relaxed']]) for r in rows],flush=True)
