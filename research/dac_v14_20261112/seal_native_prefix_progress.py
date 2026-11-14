#!/usr/bin/env python3
"""Seal the new manuscript delta, without replaying the historical full ledger."""
import re,shutil,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';delta=read(p/'data/native_prefix_delta_binding_01.json');assert delta['passed'];assert all(sha(D/n)==h for n,h in delta['sources_sha256'].items());reader=PdfReader(p/'build/main.pdf');text=unicodedata.normalize('NFKC',' '.join(' '.join(a.extract_text() or '' for a in reader.pages).split()));checks={s:s in text for s in ['2068880','2059567','2418.704','285.010','960.935','193','5062','527.395','31.130']};assert all(checks.values()),checks;log=p/'build_native_prefix_01.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text());claims=(p/'claims_evidence.md').read_text();assert all('| '+c+' |' in claims for c in delta['claims']);links=[]
for dest in re.findall(r'\]\(([^)]+)\)',claims[claims.index('| C137 |'):]):
 if '://' not in dest:assert (p/dest).exists();links.append(dest)
write(p/'native_prefix_delta_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,new_claims=delta['claims'],new_links_checked=links,sources_sha256=delta['sources_sha256'],pdf_sha256=sha(p/'build/main.pdf'),scope='New numerical claim/source/link and build/extracted-text checks only. Existing full ledger and native experiments not repeated. No new visual audit or submission-readiness claim.'))
snapshot=D/'paper_snapshots/current_native_prefix_tradeoffs_20261114';snapshot.mkdir(exist_ok=False);files=[a for a in p.rglob('*') if a.is_file() and ((a.parent==p and a.suffix in ['.tex','.md','.cls','.sh']) or (a.is_relative_to(p/'data') and 'ledger_history_20261113' not in a.parts))];files += [p/'build/main.pdf',p/'build/main.log',log,p/'native_prefix_delta_validation_01.json',p/'verify_v14_ledger.py']
for a in files:
 target=snapshot/a.relative_to(p);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(a.relative_to(p)):sha(a) for a in files},public_snapshot='f7167bd',pushed=False));write(D/'native_prefix_paper_binding_01.json',dict(passed=True,snapshot=str(snapshot),pdf=str(snapshot/'build/main.pdf'),pages=len(reader.pages),claims=delta['claims'],new_work_pushed=False,complete_research=False,source_sha256={str(a):sha(a) for a in [snapshot/'snapshot_binding.json',p/'data/native_prefix_delta_binding_01.json',p/'native_prefix_delta_validation_01.json',D/'multiobjective_archive_30/completion.json',D/'shared_crossing_results_summary_01.json',D/'pool_state_evaluator_bnn_01/completion.json']},qualification='Local manuscript update with new-delta validation; prior frozen snapshots preserved. Full cold algorithm time remains unknown.'))
print(dict(sealed=str(snapshot),pages=len(reader.pages),claims=delta['claims']),flush=True)
