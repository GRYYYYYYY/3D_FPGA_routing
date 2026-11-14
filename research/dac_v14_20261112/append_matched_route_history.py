#!/usr/bin/env python3
"""Admit existing complete routes only after exact raw provenance checks."""
import argparse,copy,csv,hashlib,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha as raw_sha,route_body
from pareto_archive_dimensions import annotate
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();started=time.monotonic();out=a.output.resolve();out.mkdir(exist_ok=False);parent=a.parent.resolve();inventory=D/'matching_route_history_inventory_01';ic=read(inventory/'completion.json');pc=read(parent/'completion.json');assert ic['passed'] and pc['passed'];cache={};verified={}
def sha(path):
 path=Path(path).resolve();s=path.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 if key not in cache:cache[key]=raw_sha(path)
 verified[str(path)]=dict(sha256=cache[key],stat=list(key));return cache[key]
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items());assert all(sha(inventory/n)==h for n,h in ic['artifact_sha256'].items());points=read(parent/'points.json');template=next(x for x in points if x['circuit']=='bnn' and x['arm']=='R1');added=[];failures=[];skipped=[]
for row in read(inventory/'records.json'):
 rd=Path(row['id']);ident=str(rd.relative_to(D)) if rd.is_relative_to(D) else str(rd);manifest=Path(row['manifest']);audit=Path(row['audit'])
 if any(x['id']==ident for x in points):skipped.append(ident);continue
 try:
  assert sha(manifest)==row['manifest_sha256'] and sha(audit)==row['audit_sha256'];m=read(manifest);assert m['status']=='completed' and m['metrics']['native_full_check_passed'];pa=read(audit);assert pa['audit']['passed']
  for path,record in m['shared_inputs'].items():assert sha(path)==record['sha256'],('shared_input_drift',path)
  for path,h in m.get('private_input_sha256',{}).items():assert sha(path)==h,('private_input_drift',path)
  for name,record in m['outputs'].items():assert sha(rd/name)==record['sha256'],('output_drift',str(rd/name))
  cmd=m['command'];binary=cmd[0];assert sha(binary)==row['binary_sha256'];physical=pa['physical_metrics'];x=copy.deepcopy(template)
  arm=rd.name.removeprefix('bnn_');is_native_control=rd.parent.parent.name=='native_extra_opportunity_bnn_01';arm='A0' if is_native_control and arm=='A0' else 'historical_'+arm
  x.update(id=ident,arm=arm,batch=str(rd.parent.parent.relative_to(D)) if rd.is_relative_to(D) else str(rd.parent.parent),batch_full_path=str(rd.parent.parent),state=None,status='legal',record_kind='verified_existing_full_route',run_manifest=str(manifest),binary_sha256=sha(binary),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=cmd,environment=m.get('environment'),convergence='max_'+row['convergence_max']+'_threshold_'+row['reconvergence_threshold'],opportunity='initial_route_with_declared_native_reconvergence',CPD_ns=row['CPD_ns'],CPD_interval_ns=row['CPD_interval_ns'],CPD_precision=row['CPD_precision'],wirelength=row['wirelength'],SB_pairs=row['SB_pairs'],CB_sources=row['CB_sources'],SB_net_occupancy=physical['sb_pair_net_occupancy'],CB_net_occupancy=physical['cb_crossing_output_source_net_occupancy'],iterations=m['metrics'].get('iterations'),complete_single_configuration_seconds=m['wall_seconds'],timing_cohort=None,analysis_only_native_seconds=None,observation_workflow=None,shared_research_workflow=None,audit_provenance=str(audit),unknowns=['Comparable rotated timing cohort; exact CPD if no full-precision native observer exists.'],historical_metadata_inventory=str(inventory/'records.json'),planning_seconds=None)
  if is_native_control:
   observation=rd.parent.parent/(rd.name+'_observation');c=read(observation/'completion.json');run=Path(c['run']);assert c['passed'] and sha(rd/'routed.route')==sha(run/'routed.route');v=read(observation/'endpoint_vector.json');assert v['constraints_sha256']==read(D/'timing_cone_bnn_dev_02/R1/endpoint_vector.json')['constraints_sha256'];cpd=v['cpd_s']*1e9;x.update(CPD_ns=cpd,CPD_interval_ns=[cpd,cpd],CPD_precision='Full-precision native observation of this exact full-route output',state=str(observation),final_STA_binary_sha256=sha(read(run/'manifest.json')['command'][0]),posthoc_observer=str(observation),posthoc_observer_seconds=c['timing'],unknowns=['Comparable rotated complete runtime cohort.']);sha(observation/'completion.json');sha(observation/'endpoint_vector.json')
  points.append(x);added.append(ident)
 except (AssertionError,FileNotFoundError,KeyError) as error:failures.append(dict(id=ident,error_type=type(error).__name__,reason=str(error)))
 write(out/'progress.json',dict(added=len(added),failed=len(failures),current=ident))
annotate(points);write(out/'points.json',points);write(out/'verification_failures.json',failures);write(out/'verified_files.json',verified)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:x[k] for k in fields} for x in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,skipped_existing_ids=skipped,failed_verifications=len(failures),unique_files_verified=len(verified),source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',inventory/'completion.json']},artifact_sha256={n:raw_sha(out/n) for n in ['points.json','points.csv','verification_failures.json','verified_files.json']},native_calls=0,route_calls=0,complete_process_seconds=time.monotonic()-started,qualification='Existing complete route runs, never selected as a per-circuit history-best algorithm. Physical inputs exact; actual binaries/environments/convergence/opportunity retained separately. Printed CPD stays an interval unless this exact route has full precision. Measured whole route time is its own observation; no cross-batch statistical runtime frontier or borrowed repair time. Failed raw verifications stay outside admitted archive with explicit reasons.'))
print(dict(records=len(points),added=len(added),failed=len(failures)),flush=True)
