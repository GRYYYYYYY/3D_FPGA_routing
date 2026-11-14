#!/usr/bin/env python3
"""Seal completed scope evidence without interrupting the independent Tf run."""
import re,shutil,time,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf));text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()));text=re.sub(r'-\s+','-',text)
checks={s:s in text for s in ['5.832274663220005','631.358','249.654','102.544','82116','1387','218245']};assert all(checks.values()),checks
log=paper/'build_native_scope_01.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
for name in ['native_scope_policy_summary_02.json','protected_native_scope_summary_01.json']:
 for path,h in read(D/name)['source_sha256'].items():assert sha(path)==h,path
stage=D/'native_objective_stage_01';binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
for name,h in binding['source_sha256'].items():assert sha(stage/'src'/name)==h==sha(D/'src'/name),name
validation=read(paper/'data/evidence_v14_ledger_validation.json');assert validation['status']=='passed' and validation['ledger_sha256']==sha(paper/'data/evidence_v14_ledger.json')
write(paper/'native_scope_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),build_log_sha256=sha(log),scope='Build and PDF text checks; not visual layout or DAC page-limit certification.'))
snapshot=D/'paper_snapshots/current_sta_native_scope_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,paper/'build/main.log',log,paper/'native_scope_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
names=['seal_native_scope_progress.py','native_scope_policy_summary_02.json','protected_native_scope_summary_01.json','native_timing_budget_scope_experiment_01.json','native_scope_request_validation_01/validation.json','current_sta_policy_native_continue_01/completion.json','current_sta_policy_native_R1_01/completion.json','current_sta_policy_native_target_only_01/failure.json','current_sta_policy_native_target_only_02/completion.json','protected_native_scope_dev_01/completion.json','protected_joint_scope_search_02/completion.json','run_native_scope_policy_v3.py','diagnose_protected_critical_prefix_v2.py','run_protected_joint_search.py','native_objective_stage_01/binding.json']
paths=[D/n for n in names]+[snapshot/'snapshot_binding.json',paper/'native_scope_pdf_validation_01.json',paper/'data/evidence_v14_ledger.json',paper/'data/evidence_v14_ledger_validation.json']
write(D/'native_scope_progress_binding_01.json',dict(passed=True,research_complete=False,quality_promoted=False,status='sealed_completed_native_scope_and_protected_prefix_studies',source_sha256={str(p):sha(p) for p in paths},paper_snapshot=str(snapshot),paper_pages=len(reader.pages),public_snapshot='f7167bd',new_work_pushed=False,
 pending_study='current_sta_policy_native_Tf_01; not included in the immutable completed-study claims. Keep its existing process running.',next_registered='native_timing_budget_scope_experiment_01.json'))
h=read(D/'live_handoff.json');h.update(observed_at=time.time(),research_state='active_pristine_Tf_after_sealed_R1_scope_progress',previous_goal_turn_classification='progress')
h['latest_paper']=dict(pdf='paper/build/main.pdf',validation='paper/native_scope_pdf_validation_01.json',pdf_sha256=sha(pdf),pages=len(reader.pages),snapshot=str(snapshot),claims=['C93','C94','C95','C96'])
h['latest_native_scope']=dict(summary='native_scope_policy_summary_02.json',protected_summary='protected_native_scope_summary_01.json',binding='native_scope_progress_binding_01.json',pristine_R1_strict_state='current_sta_policy_native_R1_01/attempt_003/evaluation',pristine_R1_endpoint_state='current_sta_policy_native_R1_01/attempt_002/evaluation',best_local_cpd_ns=5.832274663220005,native_resources=dict(SB=40,CB=970,wirelength=218245),shared_R1_controller_seconds=631.3579910583794,target_only_seconds=102.54398719593883,new_work_pushed=False)
h['git_publication']['snapshot_pushed']=True;h['git_publication']['new_results_pushed']=False;h['git_publication']['new_results_scope']='Post-f7167bd local research changes'
h['next_actions']=[
 'Continue existing pristine Tf controller current_sta_policy_native_Tf_01/session38508. Never restart a live owner; inspect terminal completion before reusing results. Its accepted states/decisions are not included in the completed R1/protected paper snapshot.',
 'Current R1 native automatic conflict-scope trajectory has2strict accepts6.018101129→5.854659868→5.832274663,40SB970CB218245wire; endpoint acceptsfirstonly246better0worse. Target-only sameSTA/full-device/opportunities nofirstgain. Do not claim unique engine benefit.',
 'Execute native_timing_budget_scope_experiment_01: protect-current-frontier reference gives capacity1 IPIN82116 conditional bottleneck for2targets with8non-targetprefixes fixed. Firstvictim-only protection preserved6589p4 butmovescriticalityto6592p4 andbothgatesreject6.285112431. Budgeted equal-delay victim alternatives/retained-scope changes remain open; no globaloptimality claim.',
 'Prototype overhead: shared R1 maincontroller631.358s, audits249.654/FULLSTAwrappers196.460/nativewrappers72.494; nativecore1.979nested. Target-only102.544withexactreuse, notspeedratio. Optimize immutablegraphmetadata with measured cold/warm validation; noUtiming.',
 'Retain v2 target-only failed identity assertion (0native) and corrected v3. Explicit historical native reuse checks source state/request/nativeconfig/objective andallactualinputs, excludes onlybatchregistration provenance notpassedtoVPR. Two single native attempts and jointscope reused; changedscope ranfresh.',
 'PaperC93-C96 sealed with422sources; new snapshotcurrent_sta_native_scope_20261113. Allnewworklocal; publicf7167bdunchanged. Goalactive,nooverallcount/date/matrixstop.']
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:
 f.write('\nNative current-STA progress sealed: pristineR1 automatic strict2accepts6.018101128546505→5.854659868020917→5.832274663220005ns,254setupbetter1worse40SB970CB218245wire; endpoint onlyfirst246better0worse. Matched target-only sameSTA/full-device/nativeobjective/opportunities gets0accepts. Complete sharedR1 controller631.358s vsnativecore1.979nested; target-only102.544incremental with2native/fullSTA andjointscope exactreuses,notindependenttimingratio. v2 metadataidentity assertion0native preserved;v3corrects provenance-onlyregistration handling. Continuation candidate6.285112431rejected. Protecting6589p4 retains7.639ps targetpotential andlegalreplacement,butmovesworstto6592p4 andstill6.285112431/1387setupregressions;87.245scomplete. FullSTA ruleprotects8non-targetprefixes;exact2forbidden queries showcapacity1IPIN82116necessaryforbothlocalimprovements,sojointgainscannotcoexistwiththoseprefixesfixed. NotglobalSTAoptimum;nextbudgetedvictimalternatives/retainedscope. PaperC93-C96/422sources sealedlocal snapshot. PristineTf controlleralreadyrunning,keepcurrenthandle;notincludedincompletedstudyseal. Goalactive.\n')
print(dict(pages=len(reader.pages),sources=validation['source_count'],links=validation['local_link_count'],snapshot=str(snapshot),research='active',Tf='independent study remains running or pending terminal observation'),flush=True)
