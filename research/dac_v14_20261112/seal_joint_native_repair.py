#!/usr/bin/env python3
"""Seal completed native scope controls and register the next failure diagnosis."""
from pathlib import Path
import re,shutil,time,unicodedata
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()));text=re.sub(r'-\s+','-',text)
checks={s:s in text for s in ['329.640','1.681467215','0.849339293','5.854659868','1960/pin 1']};assert all(checks.values()),checks
write(paper/'joint_native_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),build_log_sha256=sha(paper/'build_joint_native_repair_01.log'),scope='Build and PDF text validation only, not visual layout/page-limit certification.'))
assert read(paper/'data/evidence_v14_ledger_validation.json')['status']=='passed'
snapshot=D/'paper_snapshots/joint_native_repair_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,paper/'build/main.log',paper/'build_joint_native_repair_01.log',paper/'joint_native_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
closure=[D/n for n in ['joint_native_repair_summary_01.json','joint_native_execution_accounting_01.json','joint_native_failure_feedback_experiment_01.json','joint_native_victim_timing_diagnostic_01.json','joint_native_repair_stage_01/binding.json','joint_native_repair_dev_01/completion.json','joint_native_feedback_dev_01/completion.json','joint_victim_bound_01/completion.json']]
closure += [D/n for n in ['prepare_joint_native_requests.py','run_joint_native_state_analysis.py','audit_joint_native_repair.py','run_joint_native_comparison.py','run_joint_native_registered.py','diagnose_joint_victim_bound.py','prepare_victim_feedback_scope.py','report_joint_native_repair.py','seal_joint_native_repair.py']]
closure += [snapshot/'snapshot_binding.json',paper/'joint_native_pdf_validation_01.json',paper/'data/evidence_v14_ledger.json',paper/'data/evidence_v14_ledger_validation.json']
write(D/'joint_native_repair_report_binding_01.json',dict(passed=True,research_complete=False,quality_promoted=False,status='sealed_joint_native_controls_bound_and_feedback_failure',
 source_sha256={str(p):sha(p) for p in closure},new_work_pushed=False,public_snapshot='f7167bd',paper_snapshot=str(snapshot),paper_pages=len(reader.pages),
 next_registered='joint_native_failure_feedback_experiment_01.json'))
h=read(D/'live_handoff.json');h.update(research_state='active_joint_native_sealed_failure_state_diagnostic_registered',observed_at=time.time(),runners=[],queued_jobs=[],previous_goal_turn_classification='progress')
h['latest_joint_native']=dict(summary='joint_native_repair_summary_01.json',binding='joint_native_repair_report_binding_01.json',stage='joint_native_repair_stage_01',controls='joint_native_repair_dev_01',feedback_failure='joint_native_feedback_dev_01',local_bound='joint_victim_bound_01',native_search_calls=73,legal_new_candidates=4,partial_transaction_failures=1,new_work_pushed=False)
h['next_actions']=[
 'Implement joint_native_failure_feedback_experiment_01.json. Export partial copied trees and last rejected witness/costs before rollback; do not rerun completed successful control matrix. Failed feedback currentstate snapshot absent, so one diagnostic-mode repeat justified to obtain new decision-relevant data.',
 'Failure: added4nets6sinks from verified shorter victim witness, protects7541p1 first;7541p1,6563p1,6080p1,5996p1 restore,1960p1 fails capacity despite nativefoundpath atpressure1..1e8,criticality0. Check indexedbasecost/overusednodepricing; then exactcapacityqueryonidenticalpartialstate distinguishes nativeprice failure from true fixed-scope infeasibility.',
 'R1 suppliedsame6sinkscope native sequential withoutpresetpaths reproduces5.854659868 and exactsetupvector of fixed-target/native/capacity variants. Maincontributionhereisnotcapacityoracle/CBS; autonomousfail-feedbackscope discovery and extra repair opportunities require isolation.',
 'Tf fixedtargetnative ID/slackorder both6.096180893 strictaccept/endvectorreject. Exactpre-restoration7541min1.681467215vsoriginal1.220990892 provesorderalonecannotfixconnectionlossinthisscope; onlytargetoptimistic0.849339293 showsbackgroundcoupling, notglobalSTA bound.',
 'Nativecore0.165–0.668s vs fourarmwhole329.640s; audits/serialization27.5–27.9s plus candidateevaluation38–40s. State reuse/inprocessverification justified afterfailure/scope mechanics; noformalruntimeorUsubstitution.',
 'Preserve frozen controls, failure and9nativeprocess/73search accounting. PaperC83–C85,353sources245links. Researchactive; nooverallcount/date/matrixstop, noauthorblock.']
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:f.write('\nJoint-native controls sealed: identicalscope R1 fixedpreset andnative-sequential bothlegal5.854659868ns/exactsetupvector, native40SB970CB. Tf ID/slack both6.096180893 strictaccept/endvectorreject. Exactvictim pre-restorationbound1.681467215ns vsoriginal1.220990892, target-onlyrelax0.849339293; feedbackadds4nets6pins butrollsbackon1960p1after4restorations.9nativeprocesses,73actualconnectionsearchcalls,4legalcandidates1partialtransactionfailure. Core0.165–0.668s;4armcomplete329.640s,feedback15.942s. PaperC83–C85 frozenlocal; nextfailurepartialstate+exactcapacity/nativeprice discrimination. Goalactive.\n')
print(dict(pages=len(reader.pages),goal='active',snapshot=str(snapshot)))
