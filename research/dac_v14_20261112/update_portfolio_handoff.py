#!/usr/bin/env python3
"""Reconcile actual queue ownership and completed evidence without changing jobs."""
import shutil,time
from datetime import datetime,timezone
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('portfolio_'+str(time.time_ns()));history.mkdir(parents=True)
q=D/'portfolio_execution_dev_01';reg=read(q/'queue/registration.json');phase=read(q/'queue/status.json')
def alive(pid,ticks=None):
 try:
  f=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1].split();return f[0]!='Z' and (ticks is None or f[19]==ticks)
 except FileNotFoundError:return False
owner=dict(batch=q.name,pid=reg['pid'],start_ticks=reg['start_ticks'],verified_live=alive(reg['pid'],reg['start_ticks']),tool_session=66557,receipt=str(q/'queue/registration.json'),phase=phase,completion_exists=(q/'completion.json').exists())
assert owner['verified_live'] or owner['completion_exists'],'Investigate owner loss; do not fabricate a completed cohort'
terminal=['pending_reservation_dev_02','native_batch_equivalence_dev_01','critical_owner_exchange_dev_01','reservation_prune_recovery_dev_01']
completed={n:dict(passed=read(D/n/'completion.json')['passed'],completion=str(D/n/'completion.json')) for n in terminal}
a=read(D/'multiobjective_archive_22/completion.json');paper=read(D/'portfolio_paper_binding_01.json');portfolio_sources={p:sha(p) for p in read(q/'registration.json')['source_sha256']};assert portfolio_sources==read(q/'registration.json')['source_sha256']
stage=D/'portfolio_stage_03'
if not stage.exists():
 stage.mkdir()
 for source in portfolio_sources:
  path=Path(source)
  if path.parent==D and path.suffix=='.py':shutil.copy2(path,stage/path.name)
 write(stage/'binding.json',dict(passed=True,status='registered_native_cohort_frozen',controller='run_automatic_portfolio_repair_v3.py',source_sha256=portfolio_sources,cohort=str(q),old_batches_unchanged=True,policy='Fixed primary/combined/target/owner menu; lazy dependency closure; target-first then owner-first; exact immutable root limits; own-current selection after every acceptance',scope='BNN development. Root-specific zero-headroom bounds are not common absolute A0/R1/Tf bounds. No new native search primitive or cold algorithm speedup claim.'))
next_actions=['Finish the unchanged v3 A0 endpoint/strict, R1 strict and resumed Tf zero-resource native actors; each selects on its own current accepted state. Preserve failures and rejections, and do not skip uncached proposals to cherry-pick later results.', 'Append newly terminal legal candidates with actual version/objective/order, final FULLSTA and resource counts; preserve cross-method archive and reject vs final retention distinction.', 'Use the completed free/preset identical-route control to attribute gains to dependency closure and schedule over the native kernel; do not present it as a superior connection-search primitive.', 'Develop disabled-by-default state-loading reuse in an independent serial pre-route-load fork workspace. Every child must reload its route, synchronize pin equivalence and compute native FULLSTA from fresh private state; compare entire precision traces to same-binary standalone jobs, including failure followed by success.', 'Then define common absolute resource/time design envelopes and one uniform candidate policy for matched A0/R1/Tf starts and additional circuits. Current root-specific budgets and warm replay times do not establish cross-method superiority.', 'Maintain manuscript problem/mechanism/whole outcome/Pareto/ablation/cost structure; cold single-configuration timing remains unknown and historical U formal times are never assigned to repair.']
for name in ['CONTINUATION.json','live_handoff.json']:
 p=D/name;shutil.copy2(p,history/name);x=read(p);active=[owner] if owner['verified_live'] else []
 x.update(updated_at=now,observed_at=now,research_state='active',current_goal_state='active',old_caps_revoked=True,research_blockers=[],author_metadata_blocks_research=False,previous_goal_turn_classification='progress',running_jobs=active,active_jobs=active,active_owners=active,runners=active,supervisors=active,queued_jobs=[],next_actions=next_actions,current_terminal_cohorts=completed)
 x['latest_native_pending']=dict(status='registered_portfolio_actors_running' if active else 'portfolio_terminal_pending_analysis',cohort=q.name,owner=owner)
 x['active_current_sta_batch']=dict(batch=q.name,version='run_automatic_portfolio_repair_v3.py',role_states=phase,from_pristine_strong_starts=True,resource_continuation='portfolio_Tf_zero_resource_replay_dev_01',old_batches_unchanged=True)
 x['latest_multiobjective']=dict(archive='multiobjective_archive_22',points=a['records'],quality_counts=a['quality_counts'],retention_counts=a['retention_counts'],summary='multiobjective_tradeoff_summary_05.json',new_work_pushed=False,full_single_configuration_time=None,record_count_is_not_configuration_count=True)
 x['latest_critical_owner_exchange']=dict(summary='critical_exchange_results_summary_01.json',batch='critical_owner_exchange_dev_01',passed=True,fast_CPD_ns=13.228145689936355,fast_wire=2074313,owner_first_CPD_ns=13.413972155262854,owner_first_wire=2074277,SB=105,CB=5062,free_native_identical_to_preset=True,fast_setup_regressions=2,closest_regressed_endpoint_margin_ns=2.114957098342529)
 x['latest_automatic_workflow']=dict(stage='portfolio_stage_03/binding.json',batch=q.name,version='run_automatic_portfolio_repair_v3.py',replays='portfolio_zero_bounds_summary_01.json',zero_resource_root_timing_replay_accepted=2,zero_timing_root_resource_replay_accepted=2,query_and_native_reuse_exact=True,policy_divergence_on_current_states=True,cold_configuration_seconds=None)
 x['latest_static_native_batch']=dict(stage='native_batch_stage_02/binding.json',passed=True,large_equivalence='native_batch_equivalence_dev_01/completion.json',native_processes=2,transactions=10,summary='static_batch_reservation_summary_01.json',matched_speedup=None)
 x['latest_pending_target_reservations']=dict(old_batch='pending_reservation_dev_02',old_passed=False,old_on_failures=4,class_of_failure='implementation_assertion_before_candidate',new_stage='native_reservation_stage_04/binding.json',recovery='reservation_prune_recovery_dev_01/completion.json',recovery_passed=True,quality='Prevents physical-cost starvation regression, matches earlier weighted target-only control; no advantage over stronger native control.')
 x['latest_reservation_prune_recovery']=x['latest_pending_target_reservations'];x['latest_paper']=dict(snapshot=paper['snapshot'],pdf=str(Path(paper['snapshot'])/'build/main.pdf'),pages=paper['pages'],claims=paper['claims'],new_work_pushed=False)
 x['latest_automatic_group_planner'].update(workflow_integrated=True,independent_native_trajectories=q.name,qualification='Current portfolio and dependency closure integrated. Exact archived native outcomes reused for pristine Tf automatic trajectories; new strong-start transfer actors running.')
 x['multiobjective_policy'].update(archive='multiobjective_archive_22',not_solely_CPD=True,intermediate_transactions='Mechanism-backed release/joint moves allowed only in private transaction; final native FULLSTA legality and fixed design requirements govern acceptance',budget_anchor='immutable root; zero_headroom mode adds no rolling tolerance',root_relative_is_not_common_absolute_envelope=True,no_overall_stop=True)
 x['git_publication']['new_work_pushed']=False;write(p,x)
write(history/'update_binding.json',dict(updated_at=now,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'portfolio_paper_binding_01.json',D/'multiobjective_archive_22/completion.json',q/'registration.json',q/'queue/registration.json']},new_artifact_sha256={n:sha(D/n) for n in ['CONTINUATION.json','live_handoff.json']},new_native_calls=0))
print(dict(owner=owner['pid'],verified_live=owner['verified_live'],actor=phase.get('actor'),archive_records=a['records'],paper_pages=paper['pages']))
