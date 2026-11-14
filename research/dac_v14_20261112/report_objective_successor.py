#!/usr/bin/env python3
"""Report successor quality and matched native scope controls without over-attribution."""
import json,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
from current_sta_selector import select

pair=D/'plateau_successor_evaluation_01';completed=read(pair/'completion.json');assert completed['passed'];potential=read(D/'plateau_successor_potential_01/completion.json')
rows=[];sources=[pair/'completion.json',D/'plateau_successor_potential_01/completion.json',D/'native_objective_summary_01.json'];fixed=-5.854659868020917e-9+.2e-9
def describe(state):
 complete=read(state/'completion.json');assert complete['passed'];rd=Path(complete['run']);v=read(state/'endpoint_vector.json')
 finite=[x for x in v['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x)]
 return dict(state=str(state),cpd_ns=v['cpd_s']*1e9,resources=read(rd/'independent_audit.json')['physical_metrics'],current_selection=select(rd/'native_sta_frontier.jsonl'),
  near_fixed_initial_components=sum(x<=fixed for x in finite),near_current_components=sum(x<=min(finite)+.2e-9 for x in finite))
for row in completed['rows']:
 role=row['role'];state=Path(row['evaluated_state']);tx=D/f'plateau_successor_{role}_transaction_01';a=read(tx/'analysis.json');d=read(pair/(role+'_decisions.json'))
 rows.append(dict(**row,candidate=describe(state),transaction=dict(affected_nets=a['affected_nets'],blocker_sinks=a['required_blocker_sink_count'],new_queries=sum(not x.get('reused_query',False) for x in a['queries']),build_process_seconds=a['build_process_seconds']),
  regressions=[x for x in d['strict']['comparison']['changes'] if x['kind']=='setup' and x['delta_s']<0]))
 sources += [tx/'analysis.json',tx/'registration.json',pair/(role+'_decisions.json'),state/'completion.json',state/'endpoint_vector.json']
before=read(pair/'strict/endpoint_vector.json');after=read(pair/'endpoint/endpoint_vector.json');cross=compare(before,after);cross.pop('changes')
nb=D/'successor_native_controls_01';nc=read(nb/'completion.json');assert nc['all_roles_completed'];native=[]
for mode,r in nc['roles'].items():
 state=Path(r['evaluation_state']);vector=read(state/'endpoint_vector.json');cmp=compare(before,vector)
 native.append(dict(mode=mode,**describe(state),decisions=r['decisions'],native_queries=r['native_queries'],native_attempts=r['native_attempts'],native_transaction_seconds=r['native_transaction_seconds'],
  exact_setup_and_hold_same_as_external=vector['setup']==before['setup'] and vector['hold']==before['hold'],timing_comparison={k:v for k,v in cmp.items() if k!='changes'}))
 sources += [state/'completion.json',state/'endpoint_vector.json',nb/(mode+'_decision.json'),nb/(mode+'_audit')/'analysis.json',nb/(mode+'_reference_equivalence.json')]
sources += [nb/'completion.json',nb/'registration.json',nb/'process_costs.json']
original=read(D/'native_endpoint_vector_dev_01/R1/endpoint_vector.json')['cpd_s'];best=before['cpd_s']
result=dict(passed=True,research_complete=False,quality_promoted=False,paired_candidates=rows,endpoint_after_plateaus_vs_strict_candidate=cross,native_controls=native,
 best_local_cpd_ns=best*1e9,improvement_vs_original_strong_R1_percent=(1-best/original)*100,improvement_vs_previous_cpd_percent=(1-best/5.854659868020917e-9)*100,
 timing=dict(paired_potential_seconds=potential['complete_seconds'],transaction_build_seconds=[r['transaction']['build_process_seconds'] for r in rows],paired_FULL_STA_wrapper_seconds=completed['complete_seconds'],native_control_orchestrator_seconds=nc['complete_orchestrator_seconds'],
  limitation='Transaction builder timers omit pre-registration/import time; no enclosing wall timer was captured around the separately launched adaptive phases. Whole adaptive-study end-to-end wall time is unknown. Phase timings can overlap and must not be summed into a formal total. Future unified controller must wrap every child from process start.',
  formal_U_times_used=False),
 conclusions=['Both states have the same relaxed0.185825799ns potential for76p1/48p1 and the same5blockingnets. Both legal successors reach5.832274663ns. Prior endpoint-only steps are not necessary for this CPD gain.',
 'Strict accepts the newCPD; endpoint-Pareto rejects because oneMp[12]setup component worsens0.371651154ns. Endpoint branch retains its own oldstate. All comparisons are exact, with no tolerance drift.',
 'Native sequential recovery with no preset target paths reproduces the CPD under the same releasedscope. This supports currentSTA selection/scope/opportunity attribution; supplied scope still comes from path/conflict discovery.',
 'Native mixed-cost candidate provides a separate accepted strict branch with the sameCPD and full timing vector as external repair, but41SB971CB rather than45SB975CB. Preserve both trajectories; do not pretend a sameCPD swap was a strict-improvement step.'],
 new_work_pushed=False,source_sha256={str(p):sha(p) for p in sources})
write(D/'objective_successor_summary_01.json',result)
print(dict(best_local_cpd_ns=result['best_local_cpd_ns'],R1_gain=result['improvement_vs_original_strong_R1_percent'],native=[(r['mode'],r['resources'],r['exact_setup_and_hold_same_as_external']) for r in native],timing=result['timing']),flush=True)
