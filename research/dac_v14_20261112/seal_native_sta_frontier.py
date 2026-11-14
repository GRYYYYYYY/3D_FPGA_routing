#!/usr/bin/env python3
"""Seal the already completed observer, paper and next research registration."""
from pathlib import Path
import re
import shutil
import time
import unicodedata
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

paper = D / 'paper'
pdf = paper / 'build/main.pdf'
reader = PdfReader(str(pdf))
text = unicodedata.normalize('NFKC', ' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
text = re.sub(r'-\s+', '-', text)
checks = dict(all_pin_claim='36,391' in text, total_checks='95,620' in text,
              native_float='floating-point net delays' in text, frontier_neutrality='observer-off/on' in text,
              joint_result='5.85466' in text)
assert all(checks.values()), checks
validation = dict(passed=True, pages=len(reader.pages), checks=checks, pdf_sha256=sha(pdf),
                  main_tex_sha256=sha(paper / 'main.tex'), build_log_sha256=sha(paper / 'build_native_sta_frontier_01.log'),
                  scope='Successful TeX build and PDF key-text extraction with ligature/line-hyphen normalization, not visual layout or final page-limit certification.',
                  warnings_preserved='Underfull/overfull details retained in build log; no claim of submission readiness.')
write(paper / 'native_sta_frontier_pdf_validation_01.json', validation)
ledger = read(paper / 'data/evidence_v14_ledger_validation.json')
assert ledger['status'] == 'passed'
snapshot = D / 'paper_snapshots/native_sta_frontier_20261113'
snapshot.mkdir(exist_ok=False)
files = [p for p in paper.rglob('*') if p.is_file() and (
    (p.parent == paper and p.suffix in ['.tex', '.md', '.cls', '.sh'])
    or (p.is_relative_to(paper / 'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf, paper / 'build/main.log', paper / 'build_native_sta_frontier_01.log',
          paper / 'native_sta_frontier_pdf_validation_01.json', paper / 'verify_v14_ledger.py']
for p in files:
    q = snapshot / p.relative_to(paper)
    q.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, q)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_paper_evidence_snapshot',
      files={str(p.relative_to(paper)): sha(p) for p in files}, pages=len(reader.pages), public_snapshot='f7167bd', pushed=False))
closures = [D / 'native_sta_frontier_dev_03' / n for n in [
    'completion.json', 'input_seal.json', 'frontier_validation.json', 'frontier_mechanism_analysis.json', 'guided_history_identity.json']]
closures += [D / n / f for n in ['native_sta_frontier_dev_01', 'native_sta_frontier_dev_02']
             for f in ['failure_diagnosis.json', 'input_seal.json']]
closures += [D / 'native_sta_frontier_summary_01.json', D / 'native_sta_frontier_stage_03/binding.json',
             D / 'native_frontier_joint_policy_experiment_01.json', D / 'research_strategy_update_native_frontier_20261113.json',
             paper / 'data/evidence_v14_ledger.json', paper / 'data/evidence_v14_ledger_validation.json',
             paper / 'native_sta_frontier_pdf_validation_01.json', snapshot / 'snapshot_binding.json']
closures += [D / n for n in ['run_native_sta_frontier_v3.py', 'audit_native_sta_frontier_v3.py', 'analyze_native_sta_frontier.py',
                            'report_native_sta_frontier.py', 'prepare_native_sta_frontier_v3.py', 'seal_native_sta_frontier.py']]
owners = []
for n in ['native_sta_frontier_dev_01', 'native_sta_frontier_dev_02', 'native_sta_frontier_dev_03']:
    r = read(D / n / 'registration.json')
    proc = Path('/proc') / str(r['pid']) / 'stat'
    alive = proc.exists() and proc.read_text().split(') ', 1)[1].split()[19] == r['start_ticks']
    assert not alive and read(D / n / 'input_seal.json')['passed']
    owners.append(dict(batch=n, terminal=True, pid=r['pid']))
write(D / 'native_sta_frontier_report_binding_01.json', dict(passed=True, status='sealed_observer_frontier_paper',
      research_complete=False, quality_promoted=False, source_sha256={str(p): sha(p) for p in closures}, owners=owners,
      native_analysis_calls=12, route_search_calls=0, final_paired_analysis_calls=8, paper_pages=len(reader.pages),
      paper_snapshot=str(snapshot), next_registered='native_frontier_joint_policy_experiment_01.json',
      public_snapshot='f7167bd', this_followup_pushed=False))
handoff = read(D / 'live_handoff.json')
handoff.update(research_state='active_native_STA_frontier_sealed_joint_policy_registered', observed_at=time.time(),
               previous_goal_turn_classification='progress', runners=[], queued_jobs=[])
handoff['latest_native_STA_frontier'] = dict(summary='native_sta_frontier_summary_01.json',
    binding='native_sta_frontier_report_binding_01.json', stage='native_sta_frontier_stage_03', batch='native_sta_frontier_dev_03',
    total_analysis_calls=12, observer_integration_failures=2, final_paired_passed=8, route_search_calls=0,
    checked_connections=95620, Tf_tied_targets_unguided=4, next_registered='native_frontier_joint_policy_experiment_01.json')
handoff['next_actions'] = [
    'Implement native_frontier_joint_policy_experiment_01.json on frozen matched count2 A0/R1/Tf using exact all-pin exports; same entire repair opportunity. Do not reroute to rebuild observer information.',
    'Current tied/nearcritical groups require domain-aware CPD/slack and numeric tolerance. rawcriticality==1 is unsuitable, not an existing-policy bug. Tf4 worstties absentguidedhistory. EightULP groups5/6/4/2 and near0.2ns12/14/23/51 are diagnostics, not permanent limits.',
    'Compare independent and joint compatible path choices with transactional blocker restoration; reuse queries only after exact graph/prefix/occupancy/capacity/model matching. StrongestR1joint5.85466 remains one development intervention, not general method promotion.',
    'Stage03 uses native post-sync find_pb_route_clb_input_net_pin and actualtree net_pin_index. Preserve stage01/stage02 integration failures. Final8FULL/STA-neutral analyses;41sourcefilesbound,39routefilesunchanged.',
    'PaperC77/C78 built and ledger/PDFkeytext checked; immutablepaper_snapshots/native_sta_frontier_20261113. Newworklocalonly. Keep prelegal failure/scope/success branch; integrated/fullruntime and nonzeroRC unknown. No overall date/count/matrix stop.']
handoff['latest_strategy_review'] = 'research_strategy_update_native_frontier_20261113.json'
write(D / 'live_handoff.json', handoff)
with (D / 'RESEARCH_LOG.md').open('a') as stream:
    stream.write('\nNative STA frontier stage03: 4 frozen states,8off/on FULL/STA-neutral analyses;4x23905 exactfloat/RR checks. Each36391pinrows/31108routedatompins,0unmapped.39routefiles unchanged, newbaseAPI+header. Stage01 pre-sync lookup andstage02 optionalisink index failed; retainedrecords,12totalanalysis(10completed2observerfailures),0route. Numericalties5/6/4/2; near0.2ns12/14/23/51. Tf4worstties allabsentguidedhistory; rawcriticality==1 unsuitable duefloat/perconstraintnormalization. BestlocalR1joint5.85466 unchanged. Unifiedjointpolicyregisterednext; nooverallstops. PaperthroughC78 built/keytext/ledgerchecked, immutable snapshot, localonly.\n')
print(dict(pages=len(reader.pages), snapshot_files=len(files), ledger_sources=ledger['source_count'],
           links=ledger['local_link_count'], checks=checks, state=handoff['research_state']))
