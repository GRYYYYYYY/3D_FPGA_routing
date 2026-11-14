#!/usr/bin/env python3
"""Bind immutable accepted transactions while their trajectory can keep running."""
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
from run_native_scope_policy_v4 import run_dir
b=D/'strong_A0_timing_trajectories_01/strict';out=D/'strong_A0_accepted_prefix_01';out.mkdir(exist_ok=False)
steps=read(b/'steps.json');write(out/'steps_snapshot.json',steps)
assert len(steps)==3 and all(x['accepted'] and x['after_CPD_s']<x['before_CPD_s'] for x in steps)
root=Path(read(b/'registration.json')['initial_state']);files=[Path(__file__).resolve(),b/'registration.json',out/'steps_snapshot.json'];rows=[]
def resources(s):
 x=read(run_dir(s)/'independent_audit.json')['physical_metrics'];return dict(wirelength=x['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=x['sb_pairs_used'],CB_sources=x['cb_crossing_output_sources_used'])
for i,step in enumerate(steps):
 state=Path(step['evaluation']);before=Path(step['before_state']);v=read(state/'endpoint_vector.json');bv=read(before/'endpoint_vector.json');c=read(state/'completion.json');r=run_dir(state);assert c['passed'] and read(r/'analysis_gate.json')['passed'] and read(r/'independent_audit.json')['audit']['passed'] and read(r/'manifest.json')['metrics']['native_full_check_passed'];assert v['cpd_s']==step['after_CPD_s'] and bv['cpd_s']==step['before_CPD_s'];assert not (state/'completion.json').read_text().find('requires_final_input_seal')>=0
 diff=compare(bv,v);finite={k:x for k,x in v['setup'].items() if isinstance(x,(float,int)) and math.isfinite(x)};worst=min(finite.values());reg=[x for x in diff['changes'] if x['kind']=='setup' and x['delta_s']<0]
 tx=state.parent;roles=read(tx/'registration.json')['roles'];name=state.name.removesuffix('_evaluation');role=roles[name];assert read(tx/'completion.json')['passed'];assert all(sha(p)==h for p,h in read(tx/'completion.json')['source_sha256'].items());audit=tx/(name+'_audit/analysis.json');assert read(audit)['passed'];cones={}
 for label,folder in [('before',b/f'round_{i:03d}/feedback'),('after',b/f'round_{i+1:03d}/feedback')]:
  f=folder/'cone.json'
  if f.exists():
   x=read(f);assert x['passed'];cones[label]=dict(source_state=x['source_state'],endpoints=[e['identity'] for e in x['selected_endpoints']],connections=[[p['net'],p['pin']] for p in x['routed_connections']]);files.append(f)
 row=dict(step=i+1,proposal=step['proposal'],state=str(state),before_state=str(before),CPD_ns=v['cpd_s']*1e9,CPD_improvement_ps=(bv['cpd_s']-v['cpd_s'])*1e12,resources=resources(state),request_connections=[[q['net'],q['pin']] for q in role['queries']],targets=role.get('targets'),reused_native=step['reused_native'],setup_improved=diff['setup_improved'],setup_regressed=diff['setup_regressed'],hold_violation_regressions=diff['hold_violation_regressions'],closest_regressed_margin_ns=min((finite[x['endpoint_domain']]-worst)*1e9 for x in reg) if reg else None,near_endpoint_counts={str(ns):sum(x<=worst+ns*1e-9 for x in finite.values()) for ns in [.05,.1,.2,.5,1.]},critical_cones=cones)
 if set(cones)=={'before','after'}:row['critical_connections_changed']=cones['before']['connections']!=cones['after']['connections'];row['worst_endpoints_changed']=cones['before']['endpoints']!=cones['after']['endpoints']
 rows.append(row);files += [state/'completion.json',state/'endpoint_vector.json',r/'analysis_gate.json',r/'independent_audit.json',r/'manifest.json',tx/'registration.json',tx/'completion.json',audit,Path(role['request'])]
rootres=resources(root);finalres=rows[-1]['resources'];oldA0=read(D/'A0_strict_portfolio_summary_01.json');oldR1=read(D/'R1_strict_portfolio_summary_02.json');tf=next(x for x in read(D/'critical_exchange_results_summary_01.json')['rows'] if x['role']=='000_expanded_free_weighted');others={'old_A0_fast':oldA0,'old_R1_fast':oldR1,'Tf_fast':tf};comparisons={}
for name,x in others.items():
 assert x['CPD_ns']==rows[-1]['CPD_ns'];rr=x['resources'];d={k:finalres[k]-rr[k] for k in finalres};comparisons[name]=dict(same_exact_CPD=True,resource_delta=d,quality_relation='dominates' if all(v<=0 for v in d.values()) and any(v<0 for v in d.values()) else 'tradeoff')
files += [D/'A0_strict_portfolio_summary_01.json',D/'R1_strict_portfolio_summary_02.json',D/'critical_exchange_results_summary_01.json'];write(out/'completion.json',dict(passed=True,trajectory_still_allowed_to_continue=True,sealed_prefix_steps=len(rows),initial_state=str(root),last_accepted_state=rows[-1]['state'],initial_CPD_ns=read(root/'endpoint_vector.json')['cpd_s']*1e9,CPD_ns=rows[-1]['CPD_ns'],resources=finalres,resource_delta={k:finalres[k]-rootres[k] for k in rootres},comparisons=comparisons,rows=rows,complete_single_configuration_algorithm_seconds=None,source_sha256={str(p):sha(p)for p in files},native_calls=0,route_calls=0,qualification='Only already completed independently sealed native transactions and existing current-STA cones. Original live controller remains untouched; its mutable steps were copied into this immutable prefix. No total workflow time inferred before terminal receipt, no cold complete runtime borrowed, no suite-wide or equal-compute superiority claim.'))
print(dict(CPD_ns=rows[-1]['CPD_ns'],resources=finalres,comparisons=comparisons),flush=True)
