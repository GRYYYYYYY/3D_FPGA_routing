#!/usr/bin/env python3
"""Read-only, bounded pre-closure audit; no solver or frozen-file writes."""
from pathlib import Path
from collections import Counter,defaultdict
import datetime,hashlib,json,time
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
B=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
LIMIT=2*1024**2
maps=[('evaluation_analysis/input_bindings.json','sha256'),('serial_analysis/input_bindings.json','sha256'),('balance_analysis/summary.json','input_bindings'),('execution_contract.json','sha256'),('runtime_dependency_binding.json','sha256'),('training_analysis/summary.json','input_sha256'),('selected_configs.json','evidence_sha256')]
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for c in iter(lambda:f.read(1024**2),b''):h.update(c)
 return h.hexdigest()
def identity(p):
 s=Path(p).stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
expected={};origins=defaultdict(list);conflicts=[];sources={}
for name,key in maps:
 f=B/name;sources[str(f.relative_to(ROOT))]=digest(f);d=json.loads(f.read_text())[key]
 for path,value in d.items():
  if path in expected and expected[path]!=value:conflicts.append(dict(path=path,old=expected[path],new=value))
  expected[path]=value;origins[path].append(name)
groups={};missing=[]
for path,value in expected.items():
 try:ident=identity(path)
 except FileNotFoundError:missing.append(path);continue
 group=groups.setdefault(ident[:2],dict(identity=ident,paths=[],expected=set()))
 group['paths'].append(path);group['expected'].add(value)
for g in groups.values():
 if len(g['expected'])!=1:conflicts.append(dict(inode_aliases=g['paths'],expected=sorted(g['expected'])))
records=[];mismatches=[];start=time.monotonic();last=start;read_bytes=0
for g in sorted(groups.values(),key=lambda g:(g['identity'][2],g['paths'][0])):
 ident=g['identity'];paths=g['paths'];entry=dict(paths=paths,identity=ident,expected_sha256=sorted(g['expected']))
 # Include the four small VPR executables even above the metadata size cutoff.
 must_hash=ident[2]<=LIMIT or Path(paths[0]).name in ['vpr','seccomp_thread_guard']
 if must_hash:
  actual=digest(paths[0]);stable=all(identity(p)==ident for p in paths)
  passed=stable and set(g['expected'])=={actual}
  entry.update(status='verified' if passed else 'mismatch_or_changed',sha256=actual,identity_stable=stable)
  read_bytes+=ident[2]
  if not passed:mismatches.append(paths)
 else:entry['status']='deferred_large_file'
 records.append(entry)
 if time.monotonic()-last>15:
  print('metadata audit',len(records),'of',len(groups),'readGiB',round(read_bytes/2**30,3),flush=True);last=time.monotonic()
# Reconcile execution metadata without reusing a positive CPD as proof of legality.
rows=json.loads((B/'evaluation_analysis/role_observations.json').read_text())['rows']
run_checks=[];counts=Counter();seen=set();failed_positive=[]
for row in rows:
 if row['run'] is None:continue
 name=row['run']
 if name in seen:continue
 seen.add(name);run=B/'runs'/name;m=json.loads((run/'manifest.json').read_text());log=(run/'stdout.log').read_text(errors='replace')
 status=m['status'];actual='process_timeout' if status=='timeout' else 'allocation_failure_under_registered_limit' if any(x in log for x in ['bad_alloc','Cannot allocate memory','cannot allocate memory']) else 'routing_failure' if any(x in log for x in ['Routing failed','routing failed','Circuit is unroutable']) else 'legal' if status=='completed' and m.get('metrics',{}).get('native_full_check_passed') and m.get('metrics',{}).get('routing_success_reported') else status
 stored='legal' if row['status']=='legal' else row.get('failure_class',row['status'])
 flags=m['process_tree_observation'];threads_ok=flags['samples']>0 and flags['processes'] and not flags['violation_observed'] and flags['peak_threads']<=1
 trace=m.get('thread_syscall_trace',{});trace_ok=trace.get('clone_thread_flag_lines')==0 and 'CLONE_THREAD' not in (run/'thread_syscalls.log').read_text(errors='replace') if trace else False
 passed=actual==stored and bool(threads_ok) and trace_ok and m.get('metrics',{})==row.get('metrics',{})
 counts[actual]+=1
 run_checks.append(dict(run=name,passed=passed,classification=actual,thread_observation_ok=bool(threads_ok),thread_trace_ok=trace_ok))
 if row['status']!='legal' and m.get('metrics',{}).get('critical_path_ns',0)>0:failed_positive.append(name)
training=json.loads((B/'training_analysis/summary.json').read_text())
train_counts=Counter((x['status'],x.get('failure_class','legal')) for x in training['observations'])
selection=json.loads((B/'selected_configs.json').read_text())
eval_start=min(json.loads((B/'runs'/r['run']/'manifest.json').read_text())['start_utc'] for r in rows if r['phase']=='heldout' and r['run'])
selection_precedes=selection['utc']<eval_start
records_path=P/'data/closed_metadata_records.jsonl'
with records_path.open('w') as f:
 for x in records:f.write(json.dumps(x)+'\n')
summary=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='small_files_and_execution_metadata_verified_large_files_pending' if not conflicts and not missing and not mismatches and all(x['passed'] for x in run_checks) and selection_precedes else 'issues_found',source_maps_sha256=sources,unique_paths=len(expected),unique_inodes=len(groups),total_unique_GiB=sum(g['identity'][2] for g in groups.values())/2**30,hashed_unique_GiB=read_bytes/2**30,hashed_unique_files=sum(r['status']=='verified' for r in records),deferred_unique_files=sum(r['status']=='deferred_large_file' for r in records),missing=missing,conflicts=conflicts,mismatches=mismatches,metadata_byte_limit=LIMIT,run_checks=run_checks,unique_evaluation_failure_counts=dict(counts),nonlegal_runs_with_positive_logged_cpd=len(failed_positive),nonlegal_positive_cpd_runs=failed_positive,training_counts=[dict(status=k[0],failure_class=k[1],count=v) for k,v in train_counts.items()],selection_utc=selection['utc'],first_heldout_route_start_utc=eval_start,selection_precedes_heldout=selection_precedes,elapsed_seconds=time.monotonic()-start,records_file='data/closed_metadata_records.jsonl',records_sha256=digest(records_path),scope='Checks completed training/evaluation/serial/balance binding inventory, hashes small files and VPR binaries, verifies unique evaluation run classifications and recorded thread evidence. Does not rehash large routes/graphs/packed inputs or re-run the independent route checker; not final acceptance.')
(P/'data/closed_metadata_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(summary['status'],'files',summary['hashed_unique_files'],'deferred',summary['deferred_unique_files'],'runs',len(run_checks),'nonlegal CPDs',len(failed_positive),'seconds',round(summary['elapsed_seconds'],1),flush=True)
raise SystemExit(0 if summary['status']!='issues_found' else 1)
