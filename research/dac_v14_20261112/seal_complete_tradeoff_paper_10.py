"""Seal the reviewed complete-pair figure and unchanged result table."""
import re, shutil, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper'; e=D/'complete_tradeoff_paper_evidence_10'
parent_path=D/'owner_contract_paper_binding_09.json'; parent=read(parent_path)
previous=Path(parent['snapshot']); source=p/'current_repair_complete_tradeoffs_10.tex'
build=p/'build_complete_tradeoffs_10'; pdf=build/'current_repair_complete_tradeoffs_10.pdf'
log=build/'current_repair_complete_tradeoffs_10.log'
binding_path=D/'complete_tradeoff_paper_binding_10.json'
assert not binding_path.exists()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json')
assert all(sha(f)==h for f,h in reg['source_sha256'].items())
t=source.read_text(); old=(previous/'current_repair_main.tex').read_text()
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',t,re.S)==re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',old,re.S)
assert re.findall(r'\\begin\{figure\}.*?\\end\{figure\}',t,re.S)==re.findall(r'\\begin\{figure\}.*?\\end\{figure\}',old,re.S)
assert 'joint_quality_projection_34.pdf' not in t
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf); assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for token in ['7351.26','47.56%','0.797%','22.95%','155.10','107.00','102.90','1692.84','92.96%','1361','CP1']:
    assert token in flat,token
pairs=read(e/'paired_complete_deltas.json');assert len(pairs)==9
for row in pairs:
    n,d=row['native'],row['domain'];nq,dq=n['quality'],d['quality']
    assert row['delta']=={k:dq[k]-nq[k] for k in nq}
    assert row['percent']['vertical']==100*((dq['SB_pairs']+dq['CB_sources'])/(nq['SB_pairs']+nq['CB_sources'])-1) or abs(row['percent']['vertical']-100*((dq['SB_pairs']+dq['CB_sources'])/(nq['SB_pairs']+nq['CB_sources'])-1))<1e-12
    assert row['percent']['time']==100*(d['seconds']/n['seconds']-1)
assert len(read(e/'failed_complete_attempts.json'))==8
cost=read(D/'complete_BNN_cost_hierarchy_01/completion.json');assert cost['passed']
assert round(cost['resource_transaction_delta_seconds'],2)==1692.84
assert round(100*cost['transaction_delta_fraction_of_whole_delta'],2)==92.96
assert [cost['arms'][x]['native_query_count'] for x in ['bnn_native','bnn_domain']]==[70,1361]
assert [round(cost['arms'][x]['nested_native_core_seconds'],2) for x in ['bnn_native','bnn_domain']]==[38.23,1207.26]
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
receipts=parent['verified_case_receipts'].copy();receipts.update(reg['source_sha256'])
assert all(sha(f)==h for f,h in receipts.items())
completion=dict(passed=True,pages=6,complete_attempt_rows=31,scoped_rows=2,
                unchanged_table_rows=33,initial_routing_failures=4,input_loading_failures=4,
                legal_configuration_pairs_in_figure=9,independent_new_results=0,
                historical_projection_moved_to_supplement=True,new_native_calls=0,
                source_sha256=reg['source_sha256'])
write(e/'completion.json',completion)
snap=D/'paper_snapshots/current_complete_tradeoffs_20261116';assert not snap.exists()
shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),
                 (p/'data/complete_paired_tradeoffs_10.pdf','data/complete_paired_tradeoffs_10.pdf')]:
    shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/complete_tradeoffs')
for n in ['paired_complete_deltas','failed_complete_attempts']:
    shutil.copy2(e/f'{n}.json',snap/f'data/{n}.json')
history=snap/'supplement/historical_BNN_projection';history.mkdir()
shutil.copy2(previous/'data/joint_quality_projection_34.pdf',history/'joint_quality_projection_34.pdf')
shutil.copy2(e/'historical_figure.tex',history/'original_main_figure.tex')
write(history/'provenance.json',dict(previous_snapshot=str(previous),archive_records=640,
    BNN_observations_on_one_input=391,plotted_coordinates=232,
    pdf_sha256=sha(history/'joint_quality_projection_34.pdf'),
    qualification='Preserved historical figure and original caption. Counts belong to that archive, not the current complete-pair figure or independent input count.'))
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims=read(previous/'claims_evidence.json')
claims['complete_pair_figure_update']=dict(legal_configuration_pairs=9,failed_attempts_retained=8,
    independence='Configurations are not independent circuits/placements; no aggregate success rate or statistical speedup.',
    metric_denominator='100*(domain-native)/native separately per metric and matched pair; SB/CB count deltas shown separately.',
    time_scope='Same complete measured outputs as main table; never substituting active engineering or imported-scope costs.',
    overhead_evidence='complete_BNN_cost_hierarchy_01/completion.json',historical_projection='supplement/historical_BNN_projection',
    new_independent_results=0,CP1_changed=False)
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_complete_tradeoff_update',
    files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source)
ledger['sources_sha256']['paper/data/complete_paired_tradeoffs_10.pdf']=sha(p/'data/complete_paired_tradeoffs_10.pdf');write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),
    figure_archive_records=None,historical_figure_archive_records=640,figure_legal_configuration_pairs=9,
    table_failed_initial_rows=4,table_initial_failure_rows=4,table_input_loading_failure_rows=4,
    new_native_calls_during_paper_update=0,new_complete_attempt_rows=0,
    verified_case_receipts=receipts,visual_review=review,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    qualification='Complete paired tradeoff figure replaces main-text historical BNN projection. Table/rules unchanged. No new independent results, statistical timing claims or CP1 changes. Original whole22.95% and nested-cost boundaries remain.')
write(binding_path,binding)
print(dict(passed=True,pages=6,table_rows=33,figure_pairs=9,pdf=binding['pdf']))
