#!/usr/bin/env python3
"""Seal completed studies and leave the independent cross-circuit work running."""
import re, shutil, time, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
checks={s:s in text for s in ['778.355','6.018101128546505','7.638778499','327377','327383','327448','228453','0.460476435']}
assert all(checks.values()),checks
log=paper/'build_budget_scope_01.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
report=read(D/'budget_scope_progress_summary_01.json')
for p,h in report['source_sha256'].items():assert sha(p)==h,p
stage=D/'native_objective_stage_01';binding=read(stage/'binding.json')
assert sha(stage/'bin/vpr')==binding['binary_sha256']
for name,h in binding['source_sha256'].items():assert sha(stage/'src'/name)==h==sha(D/'src'/name),name
validation=read(paper/'data/evidence_v14_ledger_validation.json')
assert validation['status']=='passed' and validation['ledger_sha256']==sha(paper/'data/evidence_v14_ledger.json')
write(paper/'budget_scope_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),build_log_sha256=sha(log),scope='Build and PDF text checks; not visual layout or DAC page-limit certification.'))
snapshot=D/'paper_snapshots/current_sta_budget_scope_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,paper/'build/main.log',log,paper/'budget_scope_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
paths=[D/'seal_budget_scope_progress.py',D/'budget_scope_progress_summary_01.json',D/'native_objective_stage_01/binding.json',snapshot/'snapshot_binding.json',snapshot/'budget_scope_pdf_validation_01.json',snapshot/'data/evidence_v14_ledger.json',snapshot/'data/evidence_v14_ledger_validation.json']
write(D/'budget_scope_progress_binding_01.json',dict(passed=True,research_complete=False,quality_promoted=False,status='sealed_completed_Tf_and_budget_potential_studies',source_sha256={str(p):sha(p) for p in paths},paper_snapshot=str(snapshot),paper_pages=len(reader.pages),public_snapshot='f7167bd',new_work_pushed=False,next_registered='current_sta_cross_circuit_spmv_experiment_01.json',pending_study='current_sta_policy_native_spmv_R1_01; ongoing results are not included in this completed-study seal'))
h=read(D/'live_handoff.json');h.update(observed_at=time.time(),research_state='active_cross_circuit_after_Tf_and_source_budget_certificate',previous_goal_turn_classification='progress')
h['latest_paper']=dict(pdf='paper/build/main.pdf',validation='paper/budget_scope_pdf_validation_01.json',pdf_sha256=sha(pdf),pages=len(reader.pages),snapshot=str(snapshot),claims=['C97','C98','C99','C100'])
h['latest_budget_scope']=dict(summary='budget_scope_progress_summary_01.json',binding='budget_scope_progress_binding_01.json',Tf_strict_state='current_sta_policy_native_Tf_01/attempt_003/evaluation',Tf_endpoint_state='current_sta_policy_native_Tf_01/attempt_000/evaluation',Tf_strict_cpd_ns=6.018101128546505,Tf_endpoint_cpd_ns=6.203926705694585,Tf_shared_controller_seconds=778.3553300350904,source_only_capacity_cut='source_budget_cut_certificate_01',new_work_pushed=False)
h['current_STA_progress']['Tf_active']=None;h['current_STA_progress']['Tf_native_completed']='current_sta_policy_native_Tf_01/completion.json'
h['next_actions']=[
 'Inspect the existing SPMV R1 controller current_sta_policy_native_spmv_R1_01/session48473 by its registration PID/start ticks; do not restart a live owner. This is a newly registered cross-circuit study, not a research stopping matrix.',
 'After R1 terminal, run the same two-policy controller from native_endpoint_spmv_dev_01/A0. R1 and Tf have identical physical routes but conservative normalized native configurations differ; do not claim exact reuse without checking actual runtime inputs. The three initial endpoint observations were all fresh; 37.988s total, zero routing calls.',
 'Completed native Tf: pristine start strict4accepts to6.018101128546505ns,256setupbetter1worse,124SB961CB228453wire; endpoint onlyfirst to6.203926705694585 because PRDATA[7] loses0.460476435ns. Fullsharedflow778.355s vsnativecore1.418s nested;6transactions47searches. Two subsequent strict candidates tie/regress and are rejected.',
 'Local bestR1 cone: IPINassignment gives7.638778499ps optimistic gain with10wholepathconflicts. CBS256limit is unresolved; finitepool failures are not graph infeasibility. Two3pin extra-prune references retain no complete legal candidate. Source-only exact cut:5490/6589/6591/6592 require channels327377/327383/327448 totalcapacity3 for simultaneous strictproxybudgets, even all retainedbranches relaxed. Four other serial targets alreadyatSOURCE-onlyphysicalminimum. Not fullSTAglobaloptimality; shift from this cone to othercases/runtime.',
 'Optimize immutable graphmetadata/audit preparation under current_sta_state_reuse_experiment_01, validating against sealed physical audits and bad-edge/capacity controls; no reroutes merely to fill documentation. Sourcegraph must be SHA-bound; softmax/bnn have differentRRG from eltwise/SPMV.',
 'PaperC97-C100/452sources snapshotcurrent_sta_budget_scope_20261113 sealed. Newworklocalonly afterpublicf7167bd. Nativeobjective C++ binary and45sourcebindingsunchanged. Goalactive; nooveralltime/call/matrixstop.']
reg=read(D/'current_sta_policy_native_spmv_R1_01/registration.json')
h['active_current_sta_batch']=dict(batch='current_sta_policy_native_spmv_R1_01',session_id=48473,pid=reg['pid'],start_ticks=reg['start_ticks'],terminal=(D/'current_sta_policy_native_spmv_R1_01/completion.json').exists(),observed_at=time.time())
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:
 f.write('\nCompleted native Tf and budget-potential progress: pristineTf strict4accepts6.208121572→6.018101129ns; endpoint acceptsfirstonly6.203926706, rejectsPRDATA[7] loss0.460476435ns. Legal strict124SB961CB228453wire,256setupbetter1worse, fixedinitialnear5→2. Shared778.355s/core1.418s nested,6transactions47searches; tie/regressive successors rolledback. CurrentbestR1 unchanged5.832274663ns. Slackbudget IPIN assignment6x40 finds optimistic7.638778499ps but10conflicts; CBS256limit0new57reused unresolved. Finitepool/retainedcut followedby3pin6589/6592 extra-prunes,40new200reuseeach,no compatible completewitness. SOURCE-only8queries certify4agents/3capacity fast-entrycut and4serialtargetswithzerophysicalpotential;notglobalSTAoptimality. Total330newdistancequeries457reuseevents;800small independent exhaustivealgorithmtests passed. PaperC97-C100 sealed; 452sources. RegisteredSPMV independentfrompristineA0/R1/Tf;3freshinitialSTAobservations37.988s,zero routing. R1 automaticcontroller session48473 continues. No completedexperiment repeated for reporting; nativeC++unchanged;newworkunpublished;goalactive.\n')
print(dict(pages=len(reader.pages),sources=validation['source_count'],links=validation['local_link_count'],snapshot=str(snapshot),research='active',SPMV=h['active_current_sta_batch']))
