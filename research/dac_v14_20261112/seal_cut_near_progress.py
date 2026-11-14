#!/usr/bin/env python3
"""Seal current-STA progress without completing the continuing research goal."""
import re,shutil,time,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

paper=D/'paper';reader=PdfReader(str(paper/'build/main.pdf'))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()));text=re.sub(r'-\s+','-',text)
checks={s:s in text for s in ['85.302','595.235','146.584','1.495641416','218247','7.638']};assert all(checks.values()),checks
assert read(paper/'data/evidence_v14_ledger_validation.json')['status']=='passed'
for name in ['joint_native_cut_feedback_summary_01.json','current_sta_near_selector_summary_01.json']:
 for p,h in read(D/name)['source_sha256'].items():assert sha(p)==h,p
stage=D/'joint_native_repair_stage_02';binding=read(stage/'binding.json')
assert sha(stage/'bin/vpr')==binding['binary_sha256']
for name,h in binding['source_sha256'].items():assert sha(stage/'src'/name)==h==sha(D/'src'/name),name
write(paper/'cut_near_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(paper/'build/main.pdf'),build_log_sha256=sha(paper/'build_cut_near_01.log'),scope='Build and PDF key-text validation; not visual layout or DAC page-limit certification.'))
snapshot=D/'paper_snapshots/current_sta_cut_near_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [paper/'build/main.pdf',paper/'build/main.log',paper/'build_cut_near_01.log',paper/'cut_near_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
scripts=['prepare_joint_native_repair_v2.py','run_joint_native_state_analysis_v2.py','query_native_failure_state.py','prepare_cut_feedback_order.py','diagnose_cut_scope_bound.py','audit_joint_native_repair_v2.py','run_joint_native_registered_v2.py','run_current_endpoint_queries_v2.py','run_current_sta_policy_loop_v3.py','prepare_near_native_controls.py','compare_native_candidate_reference.py','run_near_native_controls.py','report_cut_feedback.py','report_near_selector.py','seal_cut_near_progress.py']
closure=[D/n for n in scripts+['joint_native_cut_feedback_summary_01.json','current_sta_near_selector_summary_01.json','current_sta_cut_near_execution_accounting_01.json','joint_native_repair_stage_02/binding.json','joint_native_failure_state_01/exact_query/completion.json','joint_native_cut_scope_bound_01/completion.json','current_sta_policy_R1_near_01/completion.json','current_sta_near_native_dev_01/completion.json','current_sta_native_objective_experiment_01.json','current_sta_plateau_successor_experiment_01.json','current_sta_state_reuse_experiment_01.json']]
closure += [snapshot/'snapshot_binding.json',paper/'cut_near_pdf_validation_01.json',paper/'data/evidence_v14_ledger.json',paper/'data/evidence_v14_ledger_validation.json']
write(D/'current_sta_cut_near_report_binding_01.json',dict(passed=True,research_complete=False,quality_promoted=False,status='sealed_current_sta_cut_and_near_progress',source_sha256={str(p):sha(p) for p in closure},paper_snapshot=str(snapshot),paper_pages=len(reader.pages),new_work_pushed=False,public_snapshot='f7167bd',next_registered=['current_sta_native_objective_experiment_01.json','current_sta_plateau_successor_experiment_01.json','current_sta_state_reuse_experiment_01.json']))
h=read(D/'live_handoff.json');h.update(observed_at=time.time(),research_state='active_current_STA_cut_near_sealed',previous_goal_turn_classification='progress',runners=[],active_jobs=[],active_owners=[],queued_jobs=[],supervisors=[])
h['latest_cut_feedback']=dict(summary='joint_native_cut_feedback_summary_01.json',binding='current_sta_cut_near_report_binding_01.json',stage='joint_native_repair_stage_02',status='sealed',cpd_ns=6.096180893422343,strict_accept=True,endpoint_accept=False)
h['latest_near_selector']=dict(summary='current_sta_near_selector_summary_01.json',batch='current_sta_policy_R1_near_01',status='sealed',endpoint_steps=4,strict_steps=0,cpd_ns=5.854659868020917,setup_improved=5,setup_regressed=0,near_endpoints=[14,11],resources_after=dict(SB=44,CB=972,wirelength=218247),native_controls='current_sta_near_native_dev_01',exact_native_matches=3,new_work_pushed=False)
h['latest_paper']=dict(pdf='paper/build/main.pdf',validation='paper/cut_near_pdf_validation_01.json',pdf_sha256=sha(paper/'build/main.pdf'),pages=len(reader.pages),snapshot=str(snapshot),claims=['C86','C87','C88','C89'])
h['next_actions']=[
 'Implement current_sta_native_objective_experiment_01:5487p24 nativeweighted differs from physical-minimum capacityrepair; same-objective native hard-occupancy control isolates objective fromengine. Three other nearsteps exactwholephysicaltree match; do notclaimnovelenginequality.',
 'Execute current_sta_plateau_successor_experiment_01 from strict original commonR1state and endpointfour-stepstate with identical successorjoint opportunities. Reuse existing critical-target subsets/queries. CPDstill5.854659868; endpoint5better0worse/near14to11 costs+3SB+1CB+76wire. No proofyetplateausenableCPDgain.',
 'Cut-feedback: diagnostic exactqueryprovesfailedpartialstateunreachable, positiveprice.14positiveentries;13outside-scopeowners,416990scope-conditionallynecessary for1960. Reorder1960p1 before7541p1 giveslegal6.096180893strictaccept/endpointreject2losses. No further order-only sweep: boundvictim1.495641416>original1.220990892. Scope/pathalternativesmustprotectallaffectedendpoints.',
 'current_sta_state_reuse_experiment_01 registered: graphmetadata/audit cache thenconsiderinprocessSTA basedcost. Fullcutflow85.302s vsnative.681s; nearsharedflow595.235s; matchednativeincrement146.584s with3exactFULLSTAreuses. Thesearedevelopment/sharedcachetimes,notformalUorindependentalgorithmcomparison.',
 'PaperC86-C89 sealed;15newnativeanalysisprocessescompleted/53actualnativeconnectionsearchcalls/242newexactofflinemodes/1failedpartialtransactionpreserved. Noactivejobs; do not restart oldterminalhandles. Publicsnapshotstillf7167bd; newworklocalonly; overallresearchactive/no totalcountdateorstopmatrix.']
h['latest_native_pending']=dict(status='none_no_live_or_queued_jobs',registered_not_implemented_not_submitted=['current_sta_native_objective_experiment_01.json','current_sta_plateau_successor_experiment_01.json','current_sta_state_reuse_experiment_01.json'])
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:f.write('\nCurrent-STA cut/near progress: samefailedpartialstate exactcapacityunreachable2expansions;14positiveentries falsifystaticuniquegate,13unchangedowners make416990scope-conditionallyrequired. Derived1960p1-before7541p1 restores16connections legal6.096180893ns,strictaccept/endpointreject2setupregressions; complete85.302s. Exactvictimfloorwithoutgate1.495641416>original1.220990892 forbidsorder-onlyphysicalfix. Near0.2ns/single-only continuation from commonautomaticR1state:strict4reject,endpoint4accept7647p19/32,5487p24/26;5setupbetter0worse,near14→11,CPD5.854659868unchanged,44SB972CB218247wire. Fullsharedflow595.235s. Nativefourmatchedstates3exacttrees/explicitFULLSTAreuse;5487p24nativevectorunchanged,newFULLSTA/dualreject,objectiveconfoundregistered. Incrementalnative146.584s.15nativeprocesses/53connectionsearches/242newofflinequeries,9freshcandidateFULLSTA;onepartialfailurepreserved. PaperC86-C89 snapshotsealed localonly. Nextnativeobjectiveparity,pairedjointsuccessors,statecacheengineering;goalactive,notcompleted.\n')
print(dict(pages=len(reader.pages),snapshot=str(snapshot),research='active',new_work_pushed=False),flush=True)
