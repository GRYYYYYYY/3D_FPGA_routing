"""Verify actual transfer/index metrics and promote a six-page C223 manuscript."""
import re, shutil, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p=D/'paper'; parent=read(D/'transfer_index_paper_binding_01.json')
old=Path(parent['snapshot']); sb=read(old/'snapshot_binding.json')
assert all(sha(old/f)==h for f,h in sb['files'].items())
assert sha(p/'current_repair_main.tex')==sha(old/'current_repair_main.tex')
source=p/'current_repair_C223.tex';pdf=p/'build_budget_owner_01/current_repair_C223.pdf'
log=p/'build_budget_owner_01.log'; text=source.read_text()
# Formatting is inherited unchanged; no font/margin compression to meet the page count.
assert text[:text.index('Legal FPGA routes')]==(old/'current_repair_main.tex').read_text().split('Legal FPGA routes')[0]
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
tokens=['7463.17','7933.25','470.07','5.93%','11.062','21missingreads','251116/251136',
        '13.354624073','260.10/254.57','twooffourrolessucceed','377.71','424.45','2.517','2.509',
        'singleshared-hostobservation','legacystaticmetadatadependenciesremain',
        '2068956','2074388','2070653','13.228146','1786','1821.07','534','803','640','391BNN','232plotted','2070657','2061423','10568.53','7099.32','2722','32versus18','77queriesinto64','14policyrejects','13.58/13.69','13.40/14.19']
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
archive=D/'multiobjective_connection_budget_closed_01';ac=read(archive/'completion.json');av=read(archive/'verification.json')
assert ac['passed'] and av['passed'] and ac['records']==640 and av['added']==48
assert all(sha(archive/f)==h for f,h in ac['artifact_sha256'].items())
assert sum(r['rejected_legal_observations'] for r in av['comparisons'])==14
fragment=D/'budget64_fragmentation_analysis_01/completion.json';fr=read(fragment)
assert fr['passed'] and fr['exact_common_accepted_prefix_rounds']==[0,1,2,3] and fr['query_role_net_pin_multisets_equal']
assert [r['actual_transactions'] for r in fr['trajectories']]==[18,32]
assert [r['actual_queries'] for r in fr['trajectories']]==[2722,2722]
partial=D/'partial_escape_owner_intervention_01/verification.json';pr=read(partial)
assert pr['passed'] and pr['cohort']['legal_native_observations']==3
for r in pr['outcomes'].values():
    assert r['resources']==dict(wirelength=2070657,SB_pairs=32,CB_sources=5071)
    assert r['endpoint_comparison']['changes']==[]
projection=p/'data/joint_quality_projection_binding_34.json';proj=read(projection)
assert proj['observations']==391 and proj['unique_quality_tuples']==232
assert proj['archive']==str(archive)
assert all(sha(p/'data'/f)==h for f,h in proj['artifact_sha256'].items())
extra=[archive/'completion.json',archive/'verification.json',archive/'points.json',fragment,partial,projection]
receipt_checks.update({str(f):sha(f) for f in extra})
snap=D/'paper_snapshots/current_budget_owner_20261115';snap.mkdir(exist_ok=False)
version=p/'data/manuscript_versions/current_repair_C223.tex';assert not version.exists();shutil.copy2(source,version)
claim='\n| C223 | All48budget64legal candidates (14rejects) archived; BNNguided+46wire at equalCPD/SB/CB,2722same-query multiset/32vs18transactions,10568.53vs7099.32s imported. Two-connection owner repairs legal but4wire worse than five-connection. | multiobjective_connection_budget_closed_01/verification.json; budget64_fragmentation_analysis_01/completion.json; partial_escape_owner_intervention_01/verification.json | Figure34:640archive/391BNN/232coordinates; no cold/statistical speedup or independent samples. |\n'
with (p/'claims_evidence.md').open('a') as f:f.write(claim)
shutil.copy2(source,p/'current_repair_main.tex')
files={}
for src,rel in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),
                (p/'IEEEtran.cls','IEEEtran.cls'),(p/'claims_evidence.md','claims_evidence.md'),
                (p/'data/joint_quality_projection_34.pdf','data/joint_quality_projection_34.pdf'),
                (p/'data/joint_quality_projection_binding_34.json','data/joint_quality_projection_binding_34.json')]:
    dst=snap/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);files[rel]=sha(dst)
write(snap/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=files,source_version=str(version)))
sources=[Path(__file__).resolve(),D/'transfer_index_paper_binding_01.json',old/'snapshot_binding.json',
         index_path,transfer_path,mechanism_path,source,version,p/'current_repair_main.tex',p/'claims_evidence.md',pdf,log,*extra,
         snap/'snapshot_binding.json',p/'data/joint_quality_projection_binding_34.json']
binding=dict(passed=True,claims=parent['claims']+['C223'],pages=6,records=640,archive=str(archive),
    projection_observations=391,projection_coordinates=232,pdf=str(snap/'build/current_repair_main.pdf'),snapshot=str(snap),
    numerical_text_checks=checks,source_sha256={str(f):sha(f) for f in sources},verified_case_receipts=receipt_checks,
    qualification='C223 integrates all48budget64legal candidates and14rejects, negative full imported trajectory tradeoff and actual fragmentation mechanism, plus three dominated two-connection owner observations. Figure34 derives from640-record archive/391BNN/232coordinates. Prior robot and index results retained. Native FULL/STA evidence remains bound, no rerouting performed by manuscript checker. Whole cold costs never assigned to imported endpoints; ongoing algorithms have no claimed outcome.',new_work_pushed=False,complete_research=False)
write(D/'budget_owner_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [p/'current_repair_main.tex',version,index_path,transfer_path,mechanism_path,projection,archive/'completion.json']:ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'current_visual_review_C223.json',dict(passed=True,pages=6,source_sha256=sha(source),pdf_sha256=sha(pdf),
    rendered_contact=str(p/'visual_C223/contact.png'),rendered_contact_sha256=sha(p/'visual_C223/contact.png'),
    review='Inspected rendered six-page contact sheet: full figure, expanded quality table, projection34, negative budget trajectory, partial-owner dominance, complete-cost table and references fit; original preamble/font/margins retained. No overfull boxes. Broader research remains active.'))
print(dict(passed=True,pages=6,pdf=binding['pdf'],claims=binding['claims'][-1:]),flush=True)
