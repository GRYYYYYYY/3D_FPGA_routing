#!/usr/bin/env python3
"""Metadata-first inventory of old complete routes under exactly matched physical inputs."""
import collections,json,math,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from pareto_archive_dimensions import dominates
b=D/'matching_route_history_inventory_01';b.mkdir(exist_ok=False);started=time.monotonic();root=D/'timing_cone_bnn_dev_02/R1/runs/state';rm=read(root/'manifest.json');rc=rm['command'];graph=str(Path(rc[rc.index('--read_rr_graph')+1]));arch=str(Path(rc[1]));circuit=str(Path(rc[2]));expected=dict(graph=rm['shared_inputs'][graph]['sha256'],architecture=rm['shared_inputs'][arch]['sha256'],circuit=rm['shared_inputs'][circuit]['sha256'],packing=sha(root/'packed.net'),placement=sha(root/'placed.place'));old=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/runs';sources=[D,old]
write(b/'registration.json',dict(status='before_metadata_scan',roots=list(map(str,sources)),expected_physical_input_sha256=expected,question='Were earlier legal guide/parameter candidates excluded by scalar CPD preferences even though their wire/SB/CB tradeoffs merit retention or new current-STA repair?',source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'manifest.json',D/'multiobjective_archive_26/completion.json']},native_calls=0,route_calls=0,qualification='Declared manifest metadata first. Exact raw-file/binary/input seals must be verified before adding a newly found point to the authoritative archive or reusing it. Different configurations, convergence and runs remain separate; no per-circuit history-best algorithm configuration is selected.'))
paths=[]
for source in sources:
 result=subprocess.run(['rg','--files',str(source),'-g','manifest.json','-g','!**/*workspace*/**','-g','!**/src/**','-g','!**/paper_snapshots/**'],capture_output=True,text=True,check=True);paths += [Path(p) for p in result.stdout.splitlines()]
rows=[];failure=[];excluded=collections.Counter();files=[]
def option(cmd,name,default=None):return cmd[cmd.index(name)+1] if name in cmd else default
def matches(m):
 cmd=m['command'];shared=m.get('shared_inputs',{});outputs=m.get('outputs',{});private=m.get('private_input_sha256',{})
 if '--route' not in cmd:return 'not_full_route'
 if '--read_rr_graph' not in cmd:return 'no_declared_graph'
 gp=option(cmd,'--read_rr_graph');ap=cmd[1];cp=cmd[2]
 if any(shared.get(p,{}).get('sha256')!=expected[k] for p,k in [(gp,'graph'),(ap,'architecture'),(cp,'circuit')]):return 'different_graph_architecture_or_circuit'
 for n,k in [('packed.net','packing'),('placed.place','placement')]:
  candidates=[outputs.get(n,{}).get('sha256')]+[h for p,h in private.items() if Path(p).name==n]
  if expected[k] not in candidates:return 'packing_or_placement_unmatched'
 if option(cmd,'--seed','0')!='11' or option(cmd,'--route_chan_width')!='100' or option(cmd,'--clock_modeling','ideal')!='ideal':return 'different_seed_width_clock'
 return None
seen=set()
for path in paths:
 path=path.resolve()
 if path in seen:continue
 seen.add(path)
 try:m=read(path)
 except (ValueError,FileNotFoundError):excluded['transient_or_missing_manifest']+=1;continue
 if not isinstance(m.get('command'),list):excluded['no_command']+=1;continue
 reason=matches(m)
 if reason:excluded[reason]+=1;continue
 row=dict(id=str(path.parent),manifest=str(path),manifest_sha256=sha(path),status=m.get('status'),command=m['command'],environment=m.get('environment'),convergence_max=option(m['command'],'--router_max_convergence_count','1'),reconvergence_threshold=option(m['command'],'--router_reconvergence_cpd_threshold','0.99'),tags=m.get('tags'),whole_route_process_seconds=m.get('wall_seconds'),planning_seconds=None,complete_time_cohort=None)
 audit_path=path.parent/'independent_audit.json'
 if m.get('status')!='completed' or not m.get('metrics',{}).get('native_full_check_passed') or not audit_path.exists():failure.append(row);continue
 try:audit=read(audit_path)
 except ValueError:row['status']='audit_currently_unreadable';failure.append(row);continue
 if not audit.get('audit',{}).get('passed') or not audit.get('physical_metrics'):row['status']='independent_audit_not_passed';failure.append(row);continue
 p=audit['physical_metrics'];value=m['metrics'].get('critical_path_ns')
 if value is None:row['status']='missing_CPD';failure.append(row);continue
 half=10**(math.floor(math.log10(abs(value)))-5)/2;binary=m['command'][0];digest=m.get('shared_inputs',{}).get(binary,{}).get('sha256');route_digest=m['outputs'].get('routed.route',{}).get('sha256')
 row.update(CPD_ns=value,CPD_interval_ns=[value-half,value+half],CPD_precision='Conservative six-significant-digit printed-native interval; full precision not assumed',wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'],binary_sha256=digest,route_sha256=route_digest,route_body_sha256='unverified:'+str(route_digest),audit=str(audit_path),audit_sha256=sha(audit_path),input_files_verified_in_this_scan=False,complete_single_configuration_seconds=m.get('wall_seconds'))
 rows.append(row);files += [path,audit_path]
current=[p for p in read(D/'multiobjective_archive_26/points.json') if p['circuit']=='bnn'];potential=[]
for row in rows:
 row['certainly_dominated_by_collected_quality']=[p['id'] for p in current if dominates(p,row)]
 row['certainly_dominates_collected_quality']=[p['id'] for p in current if dominates(row,p)]
 if not row['certainly_dominated_by_collected_quality']:potential.append(row['id'])
write(b/'records.json',rows);write(b/'matched_failure_or_missing_records.json',failure);write(b/'potential_records.json',potential)
write(b/'completion.json',dict(passed=True,manifest_files_examined=len(seen),metadata_matched_legal_records=len(rows),matched_nonlegal_or_incomplete_records=len(failure),exclusion_counts=dict(excluded),not_certainly_quality_dominated=len(potential),source_sha256={str(p):sha(p) for p in [b/'registration.json',D/'multiobjective_archive_26/points.json',Path(__file__).resolve()]},artifact_sha256={n:sha(b/n) for n in ['records.json','matched_failure_or_missing_records.json','potential_records.json']},native_calls=0,route_calls=0,complete_process_seconds=time.monotonic()-started,qualification='Read-only metadata inventory, not admission or new native measurement. Printed CPD uncertainty retained; raw code/input/route/audit seals must be verified before new evidence is reused. Post-legal repair states and unequal convergence/time cohorts are not silently fused into a run. No configuration chosen by per-circuit historical best.'))
print(dict(examined=len(seen),metadata_matched_legal=len(rows),potential=len(potential),nonlegal_or_missing=len(failure)),flush=True)
