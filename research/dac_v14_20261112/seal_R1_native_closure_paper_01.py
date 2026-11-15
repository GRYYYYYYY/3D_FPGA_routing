"""Seal C221 against completed R1 own-current native controls and immutable C220."""
import shutil,re,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';parent=read(D/'joint_owner_escape_paper_binding_01.json');assert parent['passed']
snapshot=Path(parent['snapshot']);sb=read(snapshot/'snapshot_binding.json')
assert all(sha(snapshot/f)==h for f,h in sb['files'].items())
# The current prose/claim files intentionally advance. Their old versions remain exact in snapshot.
mutable={str(p/'current_repair_main.tex'),str(p/'claims_evidence.md')}
assert all(sha(f)==h for f,h in parent['source_sha256'].items() if f not in mutable)
archive=D/'multiobjective_closed_R1_native_01';c=read(archive/'completion.json');v=read(archive/'verification.json')
assert c['passed'] and v['passed'] and c['records']==578 and v['new_materialized_states']==2 and v['terminal_checkpoint_not_duplicated']
assert c['complete_measured_configurations_total']==24
assert all(sha(archive/n)==h for n,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
for rel in ['Tf_closed_own_current_native_pair_01.json','Tf_native_terminal_endpoint_tradeoff_01.json','multiobjective_closed_Tf_native_01/verification.json','R1_owner_release_joint_probe_01/verification.json','closed_seed_transfer_eight_roles_01.json']:
 x=read(D/rel);assert x['passed'] and all(sha(f)==h for f,h in x['source_sha256'].items())
closed=read(D/'native_checkpoint_recovery_03/bnn_R1_native/completion.json')
assert closed['passed'] and closed['accepted_steps']==4 and closed['attempted_scopes']==7 and closed['native_analysis_children']==1
assert closed['operator_stop']=='no_admissible_move_in_registered_current_rank_windows'
assert closed['final_resources']==dict(wirelength=2068956,SB_pairs=71,CB_sources=5072)
assert format(closed['complete_recovery_segment_seconds'],'.2f')=='548.22'
projection=read(p/'data/joint_quality_projection_binding_33.json')
assert projection['observations']==348 and projection['unique_quality_tuples']==208
assert all(sha(f)==h for f,h in projection['source_sha256'].items())
assert all(sha(p/'data'/f)==h for f,h in projection['artifact_sha256'].items())
pdf=p/'build_R1_native_closure_01/current_repair_main.pdf';log=p/'build_R1_native_closure_01.log'
reader=PdfReader(pdf);assert len(reader.pages)==6
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
text=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
removed={'Sevenofeight','root/controlrolesaresealedontwocircuits','pooledcostsandR1-nativeclosureremainpending'}
replacements={'576':'578','Archive576':'Archive578','346BNN':'348BNN','207plotted':'208plotted'}
tokens=[replacements.get(t,t) for t in parent['numerical_text_checks'] if t not in removed]
tokens += ['548.22','2068956','1673','38fewerSB/onefewerCB','Alleight','root/controlmenusareclosedontwocircuits','R1nativeseedK8','TfnativeseedK8']
checks={t:(t in text or (any(c.isalpha() for c in t) and t.replace('-','') in text.replace('-',''))) for t in tokens}
assert all(checks.values()),{t:ok for t,ok in checks.items() if not ok}
source=p/'current_repair_main.tex';assert 'Tf-native closure remains pending' not in source.read_text()
assert 'R1-native closure remain pending' not in source.read_text()
assert 'native menu remains checkpointed' not in source.read_text()
assert all(f'| C{x} |' in (p/'claims_evidence.md').read_text() for x in [221])
version=p/'data/manuscript_versions/current_repair_C221.tex';assert not version.exists();shutil.copy2(source,version)
files=[Path(__file__).resolve(),D/'joint_owner_escape_paper_binding_01.json',snapshot/'snapshot_binding.json',archive/'completion.json',archive/'points.json',archive/'verification.json',archive/'R1_native_closure_summary.json',D/'closed_seed_transfer_eight_roles_01.json',D/'native_checkpoint_recovery_03/queue/completion.json',D/'native_checkpoint_recovery_03/bnn_R1_native/completion.json',D/'multiobjective_R1_joint_owner_escape_01/verification.json',D/'multiobjective_closed_Tf_native_01/completion.json',D/'multiobjective_closed_Tf_native_01/verification.json',D/'R1_owner_release_joint_probe_01/verification.json',D/'Tf_closed_own_current_native_pair_01.json',D/'Tf_native_terminal_endpoint_tradeoff_01.json',D/'native_checkpoint_recovery_02/bnn_Tf_native/completion.json',source,version,p/'claims_evidence.md',p/'data/joint_quality_projection_binding_33.json',pdf,log]
binding=dict(passed=True,claims=parent['claims']+['C221'],pages=6,archive=str(archive),records=578,projection_observations=348,projection_coordinates=208,numerical_text_checks=checks,source_sha256={str(f):sha(f) for f in files},qualification='C221 closes all8original root/control menus with exact own-current native/paired root/anchor/K8/rank/seed checks. R1native ends2068956wire/71SB/5072CB/13.421610489672275ns after4commits/7scopes; paired2070629/33/5071spends1673wire for38SB/1CB. Recovery548.2221115380526s is partial, not historical whole. Two newly materialized legal rejected candidates add2observations: one completed historical worker plus one new native worker, both fresh independent physics audits, exact raw candidate FULL/freshSTA vectors. Terminal references existing checkpoint; no duplicate state. Archive578/348BNN/208coords,24complete configurations unchanged. Actual joint32SB nondominated escape and actual cold complete costs remain as inC220; Tf own-current closure remains. No inherited creation-time splice, missing old pool seal fabrication, statistical speedup, independent root samples or one-factor attribution. Research active, local/unpushed.')
write(p/'R1_native_closure_pdf_validation_01.json',binding)
snap=D/'paper_snapshots/current_R1_native_closure_20261115';snap.mkdir(exist_ok=False);payload={}
for f in [source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'R1_native_closure_pdf_validation_01.json',p/'data/joint_quality_projection_33.pdf',p/'data/joint_quality_projection_33.png',p/'data/joint_quality_projection_33.csv',p/'data/joint_quality_projection_binding_33.json']:
 rel=f.relative_to(p);target=snap/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snap/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target);payload[str(target.relative_to(snap))]=sha(target)
write(snap/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snap),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'R1_native_closure_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',p/'data/joint_quality_projection_binding_33.json']:
 ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,records=578,pdf=str(target)),flush=True)
