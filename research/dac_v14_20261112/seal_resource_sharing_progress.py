#!/usr/bin/env python3
"""Seal the built portfolio evidence without replaying native experiments."""
import re,shutil,unicodedata
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';reader=PdfReader(p/'build/main.pdf');text=unicodedata.normalize('NFKC',' '.join(' '.join(a.extract_text() or '' for a in reader.pages).split()))
checks={s:s in text for s in ['2070781','3909.490','2076392','5103','7.744']}
checks['heading']='anativeendpoint-vectorbridgeandanalysis-state' in ''.join(text.casefold().split())
assert all(checks.values()),checks
log=p/'build_resource_sharing_02.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
v=read(p/'data/evidence_v14_ledger_validation.json');assert v['status']=='passed' and v['ledger_sha256']==sha(p/'data/evidence_v14_ledger.json')
write(p/'resource_sharing_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(p/'build/main.pdf'),sources=v['source_count'],links=v['local_link_count'],scope='Build and extracted numerical-text check; no new visual page audit or submission readiness claim.'))
snapshot=D/'paper_snapshots/current_resource_sharing_20261114';snapshot.mkdir(exist_ok=False)
files=[a for a in p.rglob('*') if a.is_file() and ((a.parent==p and a.suffix in ['.tex','.md','.cls','.sh']) or (a.is_relative_to(p/'data') and 'ledger_history_20261113' not in a.parts))]
files += [p/'build/main.pdf',p/'build/main.log',log,p/'resource_sharing_pdf_validation_01.json',p/'verify_v14_ledger.py',p/'verify_resource_sharing_01.log']
for a in files:
 target=snapshot/a.relative_to(p);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(a.relative_to(p)):sha(a) for a in files},public_snapshot='f7167bd',pushed=False))
write(D/'resource_sharing_paper_binding_01.json',dict(passed=True,snapshot=str(snapshot),pages=len(reader.pages),claims=['C133','C134','C135'],new_work_pushed=False,complete_research=False,source_sha256={str(a):sha(a) for a in [snapshot/'snapshot_binding.json',D/'A0_portfolio_archive_summary_01.json',D/'A0_portfolio_execution_cost_01.json',D/'resource_domain_tiny_regression_02/completion.json',D/'multiobjective_archive_24/completion.json',D/'multiobjective_tradeoff_summary_07.json']}))
print(dict(sealed=str(snapshot),pages=len(reader.pages),sources=v['source_count'],links=v['local_link_count']))
