"""Seal C220 against the complete actual Tf recovery and prior immutable C218."""
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
archive=D/'multiobjective_R1_joint_owner_escape_01';c=read(archive/'completion.json');v=read(archive/'verification.json')
assert c['passed'] and v['passed'] and c['records']==576 and v['added']==2 and v['actual_full_vectors_exact_to_source']
assert c['complete_measured_configurations_total']==24
assert all(sha(archive/n)==h for n,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
for rel in ['Tf_closed_own_current_native_pair_01.json','Tf_native_terminal_endpoint_tradeoff_01.json','multiobjective_closed_Tf_native_01/verification.json','R1_owner_release_joint_probe_01/verification.json']:
 x=read(D/rel);assert x['passed'] and all(sha(f)==h for f,h in x['source_sha256'].items())
closed=read(D/'native_checkpoint_recovery_02/bnn_Tf_native/completion.json')
assert closed['passed'] and closed['accepted_steps']==11 and closed['attempted_scopes']==14 and closed['native_analysis_children']==6
assert closed['operator_stop']=='no_admissible_move_in_registered_current_rank_windows'
assert closed['final_resources']==dict(wirelength=2074388,SB_pairs=74,CB_sources=5062)
assert format(closed['complete_recovery_segment_seconds'],'.2f')=='1707.77'
projection=read(p/'data/joint_quality_projection_binding_32.json')
assert projection['observations']==346 and projection['unique_quality_tuples']==207
assert all(sha(f)==h for f,h in projection['source_sha256'].items())
assert all(sha(p/'data'/f)==h for f,h in projection['artifact_sha256'].items())
pdf=p/'build_joint_owner_escape_01/current_repair_main.pdf';log=p/'build_joint_owner_escape_01.log'
reader=PdfReader(pdf);assert len(reader.pages)==6
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
text=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
removed={'2068956','2074463','2068928','101.02','88.87','100.33','88.48','1804.56','1418.13','6307.79','5614.05'}
replacements={'568':'576','Archive568':'Archive576','338BNN':'346BNN','200plotted':'207plotted'}
tokens=[replacements.get(t,t) for t in parent['numerical_text_checks'] if t not in removed]
tokens += ['1707.77','2074308','elevencommits','nineteensetupimprovements/fourregressions','root/controlrolesaresealedontwocircuits','Sevenofeight','2070653','913.07','24morewire','onefewerSB','owner-scopeexpansion','R1-nativeclosureremainpending']
# Actual text uses plural "remain" for pooled costs + R1 closure.
tokens[-1]='pooledcostsandR1-nativeclosureremainpending'
checks={t:(t in text or (any(c.isalpha() for c in t) and t.replace('-','') in text.replace('-',''))) for t in tokens}
assert all(checks.values()),{t:ok for t,ok in checks.items() if not ok}
source=p/'current_repair_main.tex';assert 'Tf-native closure remains pending' not in source.read_text()
assert all(f'| C{x} |' in (p/'claims_evidence.md').read_text() for x in [219,220])
version=p/'data/manuscript_versions/current_repair_C220.tex';assert not version.exists();shutil.copy2(source,version)
files=[Path(__file__).resolve(),D/'BNN_cold_pair_paper_binding_02.json',snapshot/'snapshot_binding.json',archive/'completion.json',archive/'points.json',archive/'verification.json',archive/'joint_owner_summary.json',D/'multiobjective_closed_Tf_native_01/completion.json',D/'multiobjective_closed_Tf_native_01/verification.json',D/'R1_owner_release_joint_probe_01/verification.json',D/'Tf_closed_own_current_native_pair_01.json',D/'Tf_native_terminal_endpoint_tradeoff_01.json',D/'native_checkpoint_recovery_02/bnn_Tf_native/completion.json',source,version,p/'claims_evidence.md',p/'data/joint_quality_projection_binding_32.json',pdf,log]
binding=dict(passed=True,claims=parent['claims']+['C219','C220'],pages=6,archive=str(archive),records=576,projection_observations=346,projection_coordinates=207,numerical_text_checks=checks,source_sha256={str(f):sha(f) for f in files},qualification='C220 integrates actual prospective owner-scope escape plus closed Tf-native control. Joint native and target-CB-domain controls both attain2070653wire/32SB/5071CB at13.421610489672275ns,24morewire/1fewerSB, exact full endpoint vector unchanged; same route, no extra domain benefit. Independently inspected actual RR3507189 ownership transfer from62707 to31767 across the certified saturated single-net cut. Aggregate5103 attains terminal lower bound; new point nondominated. Shared imported two-arm scope913.0741119608283s is not per-arm/whole cost; original actor unchanged. Tf control11commits/14scopes at2074388wire/74SB/5062CB, recovery1707.77s with unknown historical whole; terminal2074308candidate trades19setup improvements/4regressions. Archive576/346BNN/207coords preserves all6Tf+2joint new candidates;24complete configurations unchanged. Historical checkpoint and validation-cost details condensed from main and preserved in prior snapshot/data. Actual cold-pair complete costs and quality remain paired correctly. R1native menu and pooled full costs remain open. Research active, local/unpushed, no statistical speedup, independent-test or one-factor domain claim.')
write(p/'joint_owner_escape_pdf_validation_01.json',binding)
snap=D/'paper_snapshots/current_joint_owner_escape_20261115';snap.mkdir(exist_ok=False);payload={}
for f in [source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'joint_owner_escape_pdf_validation_01.json',p/'data/joint_quality_projection_32.pdf',p/'data/joint_quality_projection_32.png',p/'data/joint_quality_projection_32.csv',p/'data/joint_quality_projection_binding_32.json']:
 rel=f.relative_to(p);target=snap/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snap/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target);payload[str(target.relative_to(snap))]=sha(target)
write(snap/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snap),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'joint_owner_escape_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',p/'data/joint_quality_projection_binding_32.json']:
 ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,records=574,pdf=str(target)),flush=True)
