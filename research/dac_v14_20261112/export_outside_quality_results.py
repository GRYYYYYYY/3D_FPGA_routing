#!/usr/bin/env python3
import csv,collections,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from analyze_native_reconvergence_v2 import observe
from verify_path_witnesses_v2 import fields,f32
b=D/'outside_native_eltwise_dev_02';reg=read(b/'registration.json');assert read(b/'input_seal.json')['passed'] and read(b/'control_reuse.json')['passed'];dirs={a:Path(p) for a,p in reg['controls'].items()};dirs.update({a:b/'runs'/('eltwise_layer_'+a) for a in ['N2','N1']});assert read(dirs['N1']/'first_legal_prefix_reproduction.json')['passed']
source={str(Path(__file__)):sha(__file__)};reports={}
for a in ['N2','N1']:
 for n in ['outside_tree_'+a+'.json','outside_solver_state_'+a+'.json']:
  p=b/n;assert read(p)['passed'];source[str(p)]=sha(p)
rb=D/'outside_rollback_dev_01';assert read(rb/'input_seal.json')['passed'];rollback={}
for a in ['Xnew','Xret']:
 for n in ['outside_tree_'+a+'.json','outside_solver_state_'+a+'.json']:
  p=rb/n;assert read(p)['passed'];source[str(p)]=sha(p)
 r=read(rb/('outside_solver_state_'+a+'.json'));assert r['summary']['forced_rejections']==r['summary']['outside_rollback_checks']==1;rollback[a]=r['summary']
rows=[];prior_binding=read(D/'bounded_cap_range_eltwise_dev_02/recovery_binding_v2.json')['checks']
for count,rs in reg['references'].items():
 for a,p in rs.items():
  rd=Path(p)
  for n in ['manifest.json','independent_audit.json','stdout.log','routed.route','time.txt','final_guide_audit.json']:
   if (rd/n).exists():assert sha(rd/n)==prior_binding[str(rd/n)]['expected_sha256'];source[str(rd/n)]=sha(rd/n)
  rows.append(dict(observe(rd),arm=a,count=int(count),group='reference',reused=True))
for a,rd in dirs.items():
 r=dict(observe(rd),arm=a,count=1 if a=='N1' else 2,group='outside_quality',reused=a in ['C2','Z2']);assert r['status']=='legal';rows.append(r)
 for n in ['manifest.json','stdout.log','time.txt','independent_audit.json','final_guide_audit.json','h3d_final_guides.csv']:
  source[str(rd/n)]=sha(rd/n)
for a in ['Xnew','Xret']:rows.append(dict(observe(rb/'runs'/('eltwise_layer_'+a)),arm=a,count=2,group='rollback_test_only',reused=False))
comparisons={};control=next(r for r in rows if r['arm']=='C2')
for a,count in [('N2',2),('N1',1)]:
 tr=next(r for r in rows if r['arm']==a)
 for c in ['A0','R1','Tf','A1']:
  cr=next(r for r in rows if r['group']=='reference' and r['arm']==c and r['count']==count);comparisons[f'count{count}:{c}->{a}']=dict(reference_cpd_ns=cr['legal_cpd_ns'],new_cpd_ns=tr['legal_cpd_ns'],cpd_improvement_pct=(1-tr['legal_cpd_ns']/cr['legal_cpd_ns'])*100)
 comparisons[f'Ccurrent->{a}']=dict(cpd_improvement_pct=(1-tr['legal_cpd_ns']/control['legal_cpd_ns'])*100,same_complete_route=route_body(dirs[a]/'routed.route')==route_body(dirs['C2']/'routed.route'))
C=(dirs['C2']/'stdout.log').read_text().splitlines();N=(dirs['N2']/'stdout.log').read_text().splitlines();actual_iter=lambda ls:[l for l in ls if l.startswith('H3D_ITER ')];iters_exact=actual_iter(C)==actual_iter(N)
summary=lambda ls:fields(next(l for l in reversed(ls) if l.startswith('H3D_GUIDE_INFLUENCE_SUMMARY ')))
cs,ns=summary(C),summary(N);domain=[fields(l) for l in C if l.startswith('H3D_SEARCH_DOMAIN ') and 'guide=1' in l];threshold=f32(.7)
P=D/'paper/data';p=P/'outside_quality_v14.csv';assert not p.exists()
with p.open('w') as f:
 w=csv.writer(f);w.writerow(['group','arm','max_convergences','reused','status','CPD_ns','iterations','SB_net_occupancy','CB_source_net_occupancy','planning_seconds','router_seconds','complete_process_seconds'])
 for r in rows:
  pm=r.get('physical_metrics') or {};w.writerow([r['group'],r['arm'],r['count'],r['reused'],r['status'],r.get('legal_cpd_ns'),r.get('iterations'),pm.get('sb_pair_net_occupancy'),pm.get('cb_crossing_output_source_net_occupancy'),r.get('planning_seconds'),r.get('router_seconds'),r.get('process_seconds')])
source[str(p)]=sha(p)
timing=[]
for a,rd in dirs.items():
 m=read(rd/'manifest.json');row=next(r for r in rows if r['arm']==a);l=(rd/'stdout.log').read_text().splitlines();probe=fields(next(x for x in reversed(l) if x.startswith('H3D_RESIDUAL_SUMMARY ')));timing.append(dict(arm=a,full_process_seconds=m['wall_seconds'],router_seconds=m['metrics']['router_seconds'],planning_seconds=row['planning_seconds'],residual_probe_seconds=float(probe['seconds']),outside_router_seconds=m['wall_seconds']-m['metrics']['router_seconds']))
write(D/'outside_quality_timing_01.json',dict(passed=True,rows=timing,build_seconds=read(D/'outside_native_stage_01/build_result.json')['wall_seconds'],quality_process_total_seconds=sum(r['full_process_seconds'] for r in timing),scope='Only instrumented per-process measured wall time, native router time and nested planning/probe timers. Planning and probe are router subitems, not additive to router total. Outside-router subtraction includes loading/setup/output/checks/exit. API probe excludes source collection/dedup/output. Human reasoning and audit/packaging stages lack one unified timer; no invented total research-cycle distribution or formal speedup.'))
result=dict(passed=True,status='sealed_native_outside_quality_and_transaction_tests',source_sha256=source,observations=rows,comparisons=comparisons,rollback=rollback,current_native_iteration_heap_counters_exact_C2_N2=iters_exact,guided_crossing_evaluations_C2_N2=[int(cs['events']),int(ns['events'])],same_beta_firstlegal_prefix=True,quality_promoted=False,actual_below_planning_mincrit=dict(searches=len(domain),threshold=threshold,below=sum(float(r['criticality'])<threshold for r in domain)),qualification='Four quality/control roles complete, two controls strictly reused after comparator-only recovery; two forced transaction roles separate. Same actual final route and native heap iteration counters do not prove full per-node search trajectory equivalence;96 fewer guided crossing evaluations and different plans/queries are retained. New DP removes some soft preferences but does not improve observed CPD/SB/CB/iterations on this seen circuit; inherited current-Tf advantage over legacy R1 is not new outside-method gain. Native original congestion/physicalTdel/STA retained. Ordered costs not formal speedup; no general circuit-coverage claim.')
write(D/'outside_quality_summary_01.json',result);print(dict(passed=True,rows=len(rows),comparisons=comparisons,iteration_heap_exact=iters_exact,guided_crossing_delta=int(ns['events'])-int(cs['events']),below_mincrit=result['actual_below_planning_mincrit']))
