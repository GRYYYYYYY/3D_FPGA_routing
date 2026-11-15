"""Verify and snapshot the six-page C188 manuscript against the new archive."""
from pathlib import Path
import re
import shutil
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

from verify_completed_seed_transfer_evidence_01 import verify_evidence
verify_evidence()
p=D/'paper';archive=D/'multiobjective_feedback_successor_candidates_01'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==390
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
projection=read(p/'data/joint_quality_projection_binding_11.json')
assert projection['passed'] and projection['observations']==269 and projection['unique_quality_tuples']==158
assert all(sha(path)==h for path,h in projection['source_sha256'].items())
assert all(sha(p/'data'/n)==h for n,h in projection['artifact_sha256'].items())
pdf=p/'build_feedback_successor_01/current_repair_main.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==6
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
points=read(archive/'points.json')
tokens=['2061293','1.339','390','2070629','217183','2061377','5046.61','7099.32','1721','Archive390','269BNN','158plotted','7.638334','550','799','434.52','450.11','3093.90']
for arm in ['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']:
    point=next(x for x in points if x['arm']==arm)
    assert point['quality_status']=='nondominated_in_collected_population'
    tokens += [format(point['CPD_ns'],'.6f'),str(point['wirelength'])]
checks={t:t in text for t in tokens};assert all(checks.values()),checks
log=p/'build_feedback_successor_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
source=p/'current_repair_main.tex'
assert 'experiment is queued' not in source.read_text()
assert '| C189 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C189.tex';assert not version.exists();shutil.copy2(source,version)
binding=dict(passed=True,claims=['C186','C187','C188','C189'],pages=6,archive=str(archive),records=390,
    projection_observations=269,projection_coordinates=158,numerical_text_checks=checks,
    source_sha256={str(x):sha(x) for x in [Path(__file__).resolve(),D/'verify_completed_seed_transfer_evidence_01.py',D/'feedback_successor_candidates_validation_01/completion.json',source,version,p/'claims_evidence.md',
        archive/'completion.json',archive/'points.json',archive/'transaction_summaries.json',
        p/'data/joint_quality_projection_binding_11.json',D/'completed_seed_transfer_summary_01.json',D/'R1_fixed_seed_resource_mechanism_01.json',pdf,log]},
    qualification='Six-page formal development manuscript, all current figures/tables and text checked against completed evidence. Prior C183/C186 snapshots preserved. Five completed roles on two circuits; R1 native comparator pending. Cold time, native checkpoint recovery, broader policy confirmation, and whole research completion remain outstanding.')
write(p/'feedback_successor_pdf_validation_01.json',binding)
snapshot=D/'paper_snapshots/current_feedback_successor_20261114';snapshot.mkdir(exist_ok=False)
files=[source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'feedback_successor_pdf_validation_01.json',
       p/'data/joint_quality_projection_11.pdf',p/'data/joint_quality_projection_11.png',
       p/'data/joint_quality_projection_11.csv',p/'data/joint_quality_projection_binding_11.json']
payload={}
for f in files:
    rel=f.relative_to(p);target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snapshot/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target)
payload[str(target.relative_to(snapshot))]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snapshot),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'feedback_successor_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',archive/'transaction_summaries.json',p/'data/joint_quality_projection_binding_11.json']:
    ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,pdf=str(target)),flush=True)
