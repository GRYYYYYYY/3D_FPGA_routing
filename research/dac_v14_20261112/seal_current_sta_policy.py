#!/usr/bin/env python3
"""Preserve completed research evidence and paper; keep the goal active."""
from pathlib import Path
import re
import shutil
import time
import unicodedata
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
text=re.sub(r'-\s+','-',text)
checks={s:s in text for s in ['13,744','14,032','6.018101129','5.854659868','0.460476435','0.185825799','pressure 10']}
assert all(checks.values()),checks
write(paper/'current_sta_policy_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),
    scope='Successful build and PDF key-text extraction; not visual layout or page-limit certification.',build_log_sha256=sha(paper/'build_current_sta_policy_01.log')))
assert read(paper/'data/evidence_v14_ledger_validation.json')['status']=='passed'
snapshot=D/'paper_snapshots/current_sta_policy_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,paper/'build/main.log',paper/'build_current_sta_policy_01.log',paper/'current_sta_policy_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
    q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',this_snapshot_pushed=False))
closures=[D/n for n in ['current_sta_policy_summary_01.json','current_sta_process_cost_breakdown_01.json','current_sta_execution_accounting_01.json','native_capacity_witness_equivalence_01.json','current_sta_joint_native_experiment_01.json','endpoint_timing_policy_validation_01.json','current_sta_user_steering_20261113.json']]
closures += [D/n/'completion.json' for n in ['native_frontier_native_A0_01','native_frontier_native_R1_01','native_frontier_native_Tf_01','native_endpoint_vector_dev_01','joint_endpoint_diagnostics_01','current_sta_policy_R1_01','current_sta_policy_Tf_01','current_sta_policy_Tf_02','native_current_sta_control_dev_03']]
closures += [D/'native_current_sta_control_dev_01/R1/failure_diagnosis.json',D/'native_current_sta_control_dev_01/R1/input_seal_recovery.json',D/'native_current_sta_control_stage_03/binding.json',snapshot/'snapshot_binding.json',paper/'current_sta_policy_pdf_validation_01.json',paper/'data/evidence_v14_ledger.json',paper/'data/evidence_v14_ledger_validation.json']
closures += [D/n for n in ['current_sta_selector.py','endpoint_timing_policy.py','run_current_sta_policy_loop.py','run_current_sta_policy_loop_v2.py','run_current_endpoint_queries.py','run_current_relaxed_queries.py','run_current_joint_search.py','run_current_sta_transaction.py','run_endpoint_state_analysis.py','run_native_control_state_analysis_v3.py','audit_native_current_sta_control_v3.py','run_native_control_followup.py','report_current_sta_policy.py','seal_current_sta_policy.py']]
write(D/'current_sta_policy_report_binding_01.json',dict(passed=True,status='sealed_automatic_policy_native_control_paper',research_complete=False,quality_promoted=False,
 source_sha256={str(p):sha(p) for p in closures},public_snapshot='f7167bd',new_work_pushed=False,paper_snapshot=str(snapshot),paper_pages=len(reader.pages),
 result='Automatic current-STA Tf strict4steps to6.018101129; endpoint1step to6.203926706. Original strongR1 bothpolicies to5.854659868. Native single-connection paths equivalent after price adjustment; joint-native/scheduling isolation remains.',
 next_registered='current_sta_joint_native_experiment_01.json'))
h=read(D/'live_handoff.json');h.update(research_state='active_current_STA_policy_sealed_joint_native_registered',observed_at=time.time(),runners=[],queued_jobs=[],previous_goal_turn_classification='progress')
h['latest_current_STA_policy']=dict(summary='current_sta_policy_summary_01.json',binding='current_sta_policy_report_binding_01.json',native_control='native_current_sta_control_dev_03',native_equivalence='native_capacity_witness_equivalence_01.json',Tf_strict_cpd_ns=6.018101128546505,Tf_endpoint_cpd_ns=6.203926705694585,R1_cpd_ns=5.854659868020917,public_snapshot='f7167bd',followup_pushed=False)
h['next_actions']=[
 'Implement current_sta_joint_native_experiment_01.json: same compatible target choices/allowed pruned trees, native blocker recovery with stepwise occupancy, then same FULL/STA/strict-or-endpoint gates. Also native sequential same-scope control to isolate joint planning/scheduling.',
 'Native pressure1 improving paths conflicted; pressure10 yielded exactly same full routes as hardcapacity for2R1targets. Do not present single-connection query as a separate quality mechanism.14completed nativeconnectionsearches; inherited wrapper route_search_calls0 means no --route process.',
 'Tf strict4accepted current-selectedsteps reaches6.018101129; endpointbranchrejectssecondstep because PRDATA[7]clk→virtual_IO worsens0.460476435ns despiteCPD gain. Try victim-urgency order and provisional delay budgets within same affected scope; finalexactendpointSTA stillmandatory.',
 'Tf laterjoint5490p5/6590p4 legalCPDregression6.01810→6.20393 rejected. Initial4target/78sinktransaction alsolegalregression6.20812→6.73484. Preserve both; changevictimcost/objective ratherthanrepeatingadjacentquerybudgets.',
 'All completed inputs/results retained. R1/Tfsharedorchestrations125.741/361.208s includeexplicitreuse, notcoldformalmethodruntime. State/auditwrappercostdominates; optimizeafteroracle/scopeisolation. Unknownoldprebindingtime staysunknown; neverreuseUformalruntime.',
 'Policy v2 exhausts only currentoperator/window, notoverallresearch. Future runner timeout should terminate childprocessgroup, preserve failurejournal and count resourcewait separately. No overallstopdate/count/matrix/authorblock.']
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:
    f.write('\nCurrent-STA automatic policy and native control sealed: source-bound originalR1 jointCPD5.854659868ns accepted byboth246setupimproved0regressed. OriginalTf strict accepts5479p36→6587p4 coordinated→7647p56→6583p24, ending6.018101129ns/130SB961CB; endpointbranchonlyfirststep6.203926706 duePRDATA[7]0.460476435ns loss atjoint. Laterjointlegalregressionrejected. Nativeweightedpres10 twoR1paths exactlyequalcapacitypaths, bothendpoints/CPDplateaus; joint-native/schedulingcontrol registered.24nativeprocesses23completed1integrationfailure;14actualconnectionsearches. PaperC79–C82, ledger341sources235links, snapshotcurrent_sta_policy_20261113 localonly. Goalactive, nextcurrent_sta_joint_native_experiment_01.json.\n')
print(dict(pages=len(reader.pages),snapshot=str(snapshot),goal='active'))
