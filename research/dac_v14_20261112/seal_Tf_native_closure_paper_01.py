"""Seal C219 against the complete actual Tf recovery and prior immutable C218."""
import shutil,re,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';parent=read(D/'BNN_cold_pair_paper_binding_02.json');assert parent['passed']
snapshot=Path(parent['snapshot']);sb=read(snapshot/'snapshot_binding.json')
assert all(sha(snapshot/f)==h for f,h in sb['files'].items())
# The current prose/claim files intentionally advance. Their old versions remain exact in snapshot.
mutable={str(p/'current_repair_main.tex'),str(p/'claims_evidence.md')}
assert all(sha(f)==h for f,h in parent['source_sha256'].items() if f not in mutable)
archive=D/'multiobjective_closed_Tf_native_01';c=read(archive/'completion.json');v=read(archive/'verification.json')
assert c['passed'] and v['passed'] and c['records']==574 and v['new_actual_states']==6
assert c['complete_measured_configurations_total']==24
assert all(sha(archive/n)==h for n,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
for rel in ['Tf_closed_own_current_native_pair_01.json','Tf_native_terminal_endpoint_tradeoff_01.json']:
 x=read(D/rel);assert x['passed'] and all(sha(f)==h for f,h in x['source_sha256'].items())
closed=read(D/'native_checkpoint_recovery_02/bnn_Tf_native/completion.json')
assert closed['passed'] and closed['accepted_steps']==11 and closed['attempted_scopes']==14 and closed['native_analysis_children']==6
assert closed['operator_stop']=='no_admissible_move_in_registered_current_rank_windows'
assert closed['final_resources']==dict(wirelength=2074388,SB_pairs=74,CB_sources=5062)
assert format(closed['complete_recovery_segment_seconds'],'.2f')=='1707.77'
projection=read(p/'data/joint_quality_projection_binding_31.json')
assert projection['observations']==344 and projection['unique_quality_tuples']==206
assert all(sha(f)==h for f,h in projection['source_sha256'].items())
assert all(sha(p/'data'/f)==h for f,h in projection['artifact_sha256'].items())
pdf=p/'build_Tf_native_closure_03/current_repair_main.pdf';log=p/'build_Tf_native_closure_03.log'
reader=PdfReader(pdf);assert len(reader.pages)==6
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
text=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
removed={'2068956','2074463','2068928'}
replacements={'568':'574','Archive568':'Archive574','338BNN':'344BNN','200plotted':'206plotted'}
tokens=[replacements.get(t,t) for t in parent['numerical_text_checks'] if t not in removed]
tokens += ['1707.77','2074308','elevencommits','nineteensetupimprovements/fourregressions','Sevenofeightroot/controlrolesaresealed','R1-nativeclosureremainpending']
# Actual text uses plural "remain" for pooled costs + R1 closure.
tokens[-1]='pooledcostsandR1-nativeclosureremainpending'
checks={t:(t in text or (any(c.isalpha() for c in t) and t.replace('-','') in text.replace('-',''))) for t in tokens}
assert all(checks.values()),{t:ok for t,ok in checks.items() if not ok}
source=p/'current_repair_main.tex';assert 'Tf-native closure remains pending' not in source.read_text()
assert '| C219 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C219.tex';assert not version.exists();shutil.copy2(source,version)
files=[Path(__file__).resolve(),D/'BNN_cold_pair_paper_binding_02.json',snapshot/'snapshot_binding.json',archive/'completion.json',archive/'points.json',archive/'verification.json',archive/'Tf_native_closure_summary.json',D/'Tf_closed_own_current_native_pair_01.json',D/'Tf_native_terminal_endpoint_tradeoff_01.json',D/'native_checkpoint_recovery_02/bnn_Tf_native/completion.json',source,version,p/'claims_evidence.md',p/'data/joint_quality_projection_binding_31.json',pdf,log]
binding=dict(passed=True,claims=parent['claims']+['C219'],pages=6,archive=str(archive),records=574,projection_observations=344,projection_coordinates=206,numerical_text_checks=checks,source_sha256={str(f):sha(f) for f in files},qualification='C219 adds actual closed Tf own-current native control:11accepts/14scopes,2074388wire/74SB/5062CB at13.421610489672275ns; matched paired2076038/43/5060 has1650morewire/31fewerSB/2fewerCB. Root/anchor/K8/seed/rank controls match; both trajectories recompute current opportunities, not equal work or one-factor attribution. Recovery1707.7659113295376s is not historical whole time. Six actual candidates,3legal rejects, added to574observations/344BNN/206coords;24whole configurations unchanged. Terminal2074308wire has19setup improvements/4regressions, no increasedhold; original vertical and endpoint-vector rules reject. Four historical checkpoint numbers moved from main paragraph to preserved C218/supplementary evidence. Cold-pair findings and failures remain exact. R1native menu and pooled full cost remain pending. No native execution by this sealer, no time splice or statistical speedup. Research active, local/unpushed.')
write(p/'Tf_native_closure_pdf_validation_01.json',binding)
snap=D/'paper_snapshots/current_Tf_native_closure_20261115';snap.mkdir(exist_ok=False);payload={}
for f in [source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'Tf_native_closure_pdf_validation_01.json',p/'data/joint_quality_projection_31.pdf',p/'data/joint_quality_projection_31.png',p/'data/joint_quality_projection_31.csv',p/'data/joint_quality_projection_binding_31.json']:
 rel=f.relative_to(p);target=snap/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snap/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target);payload[str(target.relative_to(snap))]=sha(target)
write(snap/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snap),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'Tf_native_closure_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',p/'data/joint_quality_projection_binding_31.json']:
 ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,records=574,pdf=str(target)),flush=True)
