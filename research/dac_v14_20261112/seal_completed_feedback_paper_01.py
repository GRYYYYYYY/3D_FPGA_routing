"""Verify and snapshot the six-page C186 manuscript against the new archive."""
from pathlib import Path
import re
import shutil
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';archive=D/'multiobjective_completed_feedback_01'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==336
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
projection=read(p/'data/joint_quality_projection_binding_08.json')
assert projection['passed'] and projection['observations']==223 and projection['unique_quality_tuples']==127
assert all(sha(path)==h for path,h in projection['source_sha256'].items())
assert all(sha(p/'data'/n)==h for n,h in projection['artifact_sha256'].items())
pdf=p/'build_completed_feedback_01/current_repair_main.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==6
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
points=read(archive/'points.json')
tokens=['Archive336','223BNN','127plotted','7.638334','550','799','434.52','450.11','3093.90']
for arm in ['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']:
    point=next(x for x in points if x['arm']==arm)
    assert point['quality_status']=='nondominated_in_collected_population'
    tokens += [format(point['CPD_ns'],'.6f'),str(point['wirelength'])]
checks={t:t in text for t in tokens};assert all(checks.values()),checks
log=p/'build_completed_feedback_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
source=p/'current_repair_main.tex'
assert 'experiment is queued' not in source.read_text()
assert '| C186 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C186v2.tex';assert not version.exists();shutil.copy2(source,version)
binding=dict(passed=True,claims=['C186'],pages=6,archive=str(archive),records=336,
    projection_observations=223,projection_coordinates=127,numerical_text_checks=checks,
    source_sha256={str(x):sha(x) for x in [Path(__file__).resolve(),source,version,p/'claims_evidence.md',
        archive/'completion.json',archive/'points.json',archive/'composition_summary.json',
        p/'data/joint_quality_projection_binding_08.json',pdf,log]},
    qualification='Six-page formal development manuscript, all current figures/tables and text checked against completed evidence. Prior C183 snapshot preserved. Cold time, native checkpoint recovery, broader policy confirmation, and whole research completion remain outstanding.')
write(p/'completed_feedback_pdf_validation_01.json',binding)
snapshot=D/'paper_snapshots/current_completed_feedback_20261114';snapshot.mkdir(exist_ok=False)
files=[source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'completed_feedback_pdf_validation_01.json',
       p/'data/joint_quality_projection_08.pdf',p/'data/joint_quality_projection_08.png',
       p/'data/joint_quality_projection_08.csv',p/'data/joint_quality_projection_binding_08.json']
payload={}
for f in files:
    rel=f.relative_to(p);target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snapshot/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target)
payload[str(target.relative_to(snapshot))]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snapshot),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'completed_feedback_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',archive/'composition_summary.json',p/'data/joint_quality_projection_binding_08.json']:
    ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,pdf=str(target)),flush=True)
