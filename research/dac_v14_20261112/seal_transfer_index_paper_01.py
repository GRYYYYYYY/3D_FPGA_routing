"""Verify actual transfer/index metrics and promote a six-page C222 manuscript."""
import re, shutil, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p=D/'paper'; parent=read(D/'R1_native_closure_paper_binding_01.json')
old=Path(parent['snapshot']); sb=read(old/'snapshot_binding.json')
assert all(sha(old/f)==h for f,h in sb['files'].items())
assert sha(p/'current_repair_main.tex')==sha(old/'current_repair_main.tex')
source=p/'current_repair_C222.tex';pdf=p/'build_transfer_index_01/current_repair_C222.pdf'
log=p/'build_transfer_index_01.log'; text=source.read_text()
# Formatting is inherited unchanged; no font/margin compression to meet the page count.
assert text[:text.index('Legal FPGA routes')]==(old/'current_repair_main.tex').read_text().split('Legal FPGA routes')[0]
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
tokens=['7463.17','7933.25','470.07','5.93%','11.062','21missingreads','251116/251136',
        '13.354624073','260.10/254.57','twooffourrolessucceed','377.71','424.45','2.517','2.509',
        'singleshared-hostobservation','legacystaticmetadatadependenciesremain',
        '2068956','2074388','2070653','13.228146','1786','1821.07','534','803','578','348BNN','208plotted']
checks={t:t.replace('-','') in flat.replace('-','') for t in tokens};assert all(checks.values()),checks
index_path=D/'complete_BNN_joint_index_flow_01/comparison.json'; index=read(index_path)
transfer_path=D/'complete_serial_additional_circuits_01/comparison.json';transfer=read(transfer_path)
mechanism_path=D/'robot_domain_first_scope_analysis_02/completion.json'
assert index['passed'] and index['same_downstream_execution'] and all(x['byte_exact'] for x in index['graph_payloads'])
assert index['actual_resources']==dict(wirelength=2059631,SB_pairs=82,CB_sources=5062)
assert format(index['actual_complete_seconds'],'.2f')=='7463.17'
assert format(-index['descriptive_seconds_difference'],'.2f')=='470.07'
assert format(-index['descriptive_seconds_difference']/index['reference_complete_seconds']*100,'.2f')=='5.93'
assert transfer['passed'] and transfer['registered_roles']==4 and transfer['successful_legal_roles']==2
assert read(mechanism_path)['passed']
for role,wire,cb,time,pss in [('native',251116,653,'377.71','2.517'),('domain',251136,652,'424.45','2.509')]:
    row=transfer['results']['robot_rl_'+role]
    assert row['resources']==dict(wirelength=wire,SB_pairs=9,CB_sources=cb)
    assert format(row['CPD_ns'],'.9f')=='13.354624073'
    assert format(row['complete_wall_seconds'],'.2f')==time
    assert format(row['sampled_tree_PSS_peak_kib']/1048576,'.3f')==pss
for role,time in [('native','260.10'),('domain','254.57')]:
    row=transfer['results']['conv_layer_'+role];assert row['quality'] is None
    assert format(row['actual_failed_seconds'],'.2f')==time
# Confirm each cited comparison still names the exact completed case receipts.
receipt_checks={}
for report in [index,transfer,read(mechanism_path)]:
    for name,digest in report['source_sha256'].items():
        f=Path(name)
        if f.name in ['completion.json','comparison.json','results.json','registration.json','plan.json']:
            assert sha(f)==digest;receipt_checks[name]=digest
snap=D/'paper_snapshots/current_transfer_index_20261115';snap.mkdir(exist_ok=False)
version=p/'data/manuscript_versions/current_repair_C222.tex';assert not version.exists();shutil.copy2(source,version)
claim='\n| C222 | Known-circuit robot transfer spends20wire/46.74s for1CB; conv_layer2/2initial routing failures retained. Single-pass BNN indexes preserve graph payloads/downstream work and final quality at7463.17s vs7933.25s (5.93% single descriptive observation). | complete_serial_additional_circuits_01/comparison.json; robot_domain_first_scope_analysis_02/completion.json; complete_BNN_joint_index_flow_01/comparison.json | No unseen-test, isolated-release, statistical-speedup or pooled-cost claim; original578-record projection retained. |\n'
with (p/'claims_evidence.md').open('a') as f:f.write(claim)
shutil.copy2(source,p/'current_repair_main.tex')
files={}
for src,rel in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),
                (p/'IEEEtran.cls','IEEEtran.cls'),(p/'claims_evidence.md','claims_evidence.md'),
                (p/'data/joint_quality_projection_33.pdf','data/joint_quality_projection_33.pdf'),
                (p/'data/joint_quality_projection_binding_33.json','data/joint_quality_projection_binding_33.json')]:
    dst=snap/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);files[rel]=sha(dst)
write(snap/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=files,source_version=str(version)))
sources=[Path(__file__).resolve(),D/'R1_native_closure_paper_binding_01.json',old/'snapshot_binding.json',
         index_path,transfer_path,mechanism_path,source,version,p/'current_repair_main.tex',p/'claims_evidence.md',pdf,log,
         snap/'snapshot_binding.json',p/'data/joint_quality_projection_binding_33.json']
binding=dict(passed=True,claims=parent['claims']+['C222'],pages=6,records=578,archive=parent['archive'],
    projection_observations=348,projection_coordinates=208,pdf=str(snap/'build/current_repair_main.pdf'),snapshot=str(snap),
    numerical_text_checks=checks,source_sha256={str(f):sha(f) for f in sources},verified_case_receipts=receipt_checks,
    qualification='C222 integrates actual robot transfer and both initial-routing failures, first-scope combined-domain interpretation, and actual single-pass-index full BNN cost with exact downstream execution. Figure remains the named578-record archive; no inferred global count or independent-sample claim. Original C221 retained. Complete native/raw reexecution was not performed by manuscript checker. Single shared-host observations; legacy metadata dependencies remain; broader confirmation and pooled complete costs pending.',new_work_pushed=False,complete_research=False)
write(D/'transfer_index_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [p/'current_repair_main.tex',version,index_path,transfer_path,mechanism_path]:ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'current_visual_review_C222.json',dict(passed=True,pages=6,source_sha256=sha(source),pdf_sha256=sha(pdf),
    rendered_contact=str(p/'visual_C222/contact.png'),rendered_contact_sha256=sha(p/'visual_C222/contact.png'),
    review='Inspected rendered six-page contact sheet: full figure, three new complete-cost rows, robot failure qualification and references fit; original preamble/font/margins retained. No overfull boxes. Broader research remains active.'))
print(dict(passed=True,pages=6,pdf=binding['pdf'],claims=binding['claims'][-1:]),flush=True)
