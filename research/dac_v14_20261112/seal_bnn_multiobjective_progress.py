#!/usr/bin/env python3
"""Seal completed direct-repair evidence independently of the live joint batch."""
import re,shutil,time,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
checks={s:s in text for s in ['2074301','2074313','885.791','185.825799']}
checks['section_heading']='bnncurrent-stateresourceandcapacityevidence' in ''.join(text.casefold().split())
assert all(checks.values()),checks
log=paper/'build_bnn_multiobjective_progress_02.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error|error:',log.read_text())
v=read(paper/'data/evidence_v14_ledger_validation.json');assert v['status']=='passed' and v['ledger_sha256']==sha(paper/'data/evidence_v14_ledger.json')
validation=paper/'bnn_multiobjective_pdf_validation_01.json'
write(validation,dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),scope='Development manuscript build and key-number checks, not submission length readiness.',recovered_build='bnn_build_recovery_01.json'))
snapshot=D/'paper_snapshots/current_bnn_multiobjective_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,validation,log,paper/'bnn_build_recovery_01.json',paper/'build_bnn_multiobjective_progress_01.log',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
paths=[Path(__file__).resolve(),D/'bnn_multiobjective_progress_summary_01.json',D/'multiobjective_archive_02/completion.json',D/'bnn_direct_repair_dev_01/completion.json',D/'bnn_baseline_capacity_screens_01/completion.json',D/'bnn_slack_release_screen_01/protected_critical/completion.json',D/'current_query_case_cache_validation_01/completion.json',D/'bnn_release_joint_dev_01/registration.json',snapshot/'snapshot_binding.json',snapshot/validation.name,snapshot/'data/evidence_v14_ledger.json']
write(D/'bnn_multiobjective_progress_binding_01.json',dict(passed=True,source_sha256={str(p):sha(p) for p in paths},new_work_pushed=False,research_complete=False,archive_records=90,claims=['C110','C111'],joint_batch_outcomes='Not included; separate live experiment'))
for name in ['CONTINUATION.json','live_handoff.json']:
 h=read(D/name);h['latest_paper']=dict(snapshot=str(snapshot),pages=len(reader.pages),claims=['C110','C111'],new_work_pushed=False)
 h['latest_multiobjective']=dict(binding='bnn_multiobjective_progress_binding_01.json',archive='multiobjective_archive_02',points=90,non_dominated_records=44,uncertain_records=12,dominated_records=34,complete_standalone_repair_time='unknown',new_native_candidates=2,resource_accepted_candidates=2)
 h['previous_goal_turn_classification']='progress';h['updated_at']=time.time();write(D/name,h)
with (D/'RESEARCH_LOG.md').open('a') as f:
 f.write('\nBNN multiobjective direct progress sealed C110–C111: exactCPD13.421610489672275ns unchanged, both full endpoint vectors unchanged; automatic73897p1 shortens7.639ps and leaves currentmaximum-arrivalcone(13→12). Weightednativewire2074301 dominatesphysicalcapacity2074313 atSB105CB5062, both belowinitial2074317. Strict/endpointreject; fixedbudgetresourceaccept. Sharedtwoarm885.791s, core.164/.202s, completealgorithmunknown. Archive90actualrecords44nondominated12precisionuncertain34dominated, includesstrongbaselines. A0/R1directscreens0/2positive. Two noncritical-owner releasewitnesses survivecriticalprotection; largest185.826psgapdoesnot. Querycase13actual+96edgeconditions equivalence checked. Nextindependent8armcombined/target-only/owner-only+R1 nativepair launched with immutable registration; no outcomes folded into thisseal. Paper45pages564sources327links, localonly; oldpublicf7167bd unchanged. Goalactivewithoutdate/count/matrixstop.\n')
print(dict(pages=len(reader.pages),sources=v['source_count'],links=v['local_link_count'],sealed=True))
