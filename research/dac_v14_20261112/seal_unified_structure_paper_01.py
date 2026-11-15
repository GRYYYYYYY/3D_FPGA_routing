"""Seal the reorganized six-page manuscript, preserving historical claim snapshots."""
import shutil,re,sys,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';source=p/'current_repair_unified_structure_01.tex';pdf=p/'build_unified_structure_01/current_repair_unified_structure_01.pdf';log=p/'build_unified_structure_01.log'
parent=read(D/'C223_count_correction_paper_binding_01.json');assert sha(p/'current_repair_main.tex')==sha(Path(parent['snapshot'])/'current_repair_main.tex')
text=source.read_text();sections=re.findall(r'\\section\{([^}]+)\}',text)
assert sections==['Problem and Motivation','Method: Current-State Transactional Repair','Complete Results and Transfer','Multiobjective Tradeoffs','Mechanism Ablations and Attribution','Overhead and Applicability']
assert text[:text.index('\\begin{document}')]==(p/'current_repair_main.tex').read_text().split('\\begin{document}')[0]
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
r=PdfReader(pdf);assert len(r.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in r.pages))
tokens=['47.56%','0.797%','22.95%','534','803','209/32/0','547/820/0','260.10','254.57','198.88','256.54','658','33successful','controller','PathFinder','SDC']
assert all(t in flat for t in tokens),[t for t in tokens if t not in flat]
main=read(D/'unified_main_table_evidence_01/completion.json');assert main['passed'] and main['rows']==21 and main['failed_initial_rows']==2
assert all(sha(f)==h for f,h in main['source_sha256'].items())
assert sha(D/'unified_main_table_evidence_01/rows.json')==main['artifact_sha256']['rows.json']
checks={
 'complete_quality_cost_endpoint_tradeoff':['complete_resource_timing_full_flow_01/comparison.json','unified_main_table_evidence_01/completion.json'],
 'circuit_topology_success_noop_failure':['complete_serial_transfer_dev_01/comparison.json','complete_serial_architecture_transfer_01/comparison.json','complete_serial_additional_circuits_01/comparison.json'],
 'owner_scope_not_extra_domain_benefit':['R1_owner_release_joint_probe_01/verification.json','partial_escape_owner_intervention_01/verification.json'],
 'grouping_negative_complete_trajectory':['budget64_fragmentation_analysis_01/completion.json'],
 'engineering_descriptive_whole_cost':['complete_BNN_joint_index_flow_01/comparison.json','complete_serial_lazy_source_snapshot_01/comparison.json'],
 'terminal_rules_and_pending_composition':['terminal_timing_envelope_policy_01/verification.json','robot_terminal_wire_transfer_01/completion.json','BNN_wire_timing_native_validation_01/plan.json'],
 'confirmation_integration_still_pending':['current_escape_owner_selector_validation_01/completion.json','confirmation_input_inventory_01/completion.json'],
 'archive_counts':['multiobjective_engineering_inventory_01/verification.json']}
receipts={}
for sources in checks.values():
 for name in sources:
  f=D/name;receipt=read(f);assert receipt.get('passed',False) or name=='BNN_wire_timing_native_validation_01/plan.json';receipts[str(f)]=sha(f)
# Render the final, identical layout after the caption-only cleanup.
sys.path.insert(0,str(p/'tools/pdf_review'));import pymupdf
from PIL import Image
visual=p/'visual_unified_structure_01';doc=pymupdf.open(pdf);canvas=Image.new('RGB',(1224,1056),'#ccc')
for i,page in enumerate(doc):
 pix=page.get_pixmap(matrix=pymupdf.Matrix(2/3,2/3));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);canvas.paste(im,((i%3)*408,(i//3)*528));page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(visual/f'page{i+1}.png')
canvas.save(visual/'contact.png')
snap=D/'paper_snapshots/current_unified_structure_20261115';snap.mkdir(exist_ok=False)
files={}
for src,name in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),(p/'IEEEtran.cls','IEEEtran.cls'),(p/'data/joint_quality_projection_34.pdf','data/joint_quality_projection_34.pdf'),(p/'data/joint_quality_projection_binding_34.json','data/joint_quality_projection_binding_34.json'),(visual/'contact.png','visual/contact.png'),(D/'unified_main_table_evidence_01/rows.json','data/complete_table_rows.json'),(p/'claims_evidence.md','supplement/historical_claims_evidence.md'),(p/'supplement_development_history_01/historical_main_C223_corrected.tex','supplement/historical_main_C223_corrected.tex'),(p/'supplement_development_history_01/audit_notes.tex','supplement/audit_notes.tex')]:
 dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);files[name]=sha(dest)
write(snap/'snapshot_binding.json',dict(status='immutable_reorganized_main_and_supplement',files=files))
write(snap/'claims_evidence.json',dict(main_claim_groups=checks,historical_claims_location='supplement/historical_claims_evidence.md',unconfirmed=['integrated automatic confirmation controller','independent frozen-policy cohort','application timing with explicit SDC','symmetric interleaved engineering runtime','robot release ablation','BNN composed candidate FULL_STA']))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=dict(passed=True,pages=6,sections=sections,records=658,complete_configurations=33,figure_archive_records=640,table_rows=21,table_failed_initial_rows=2,snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),main_claim_groups=checks,source_sha256={str(f):sha(f) for f in [source,pdf,log,D/'unified_main_table_evidence_01/completion.json',D/'C223_count_correction_paper_binding_01.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},verified_case_receipts=receipts,visual_review='Six-page contact and full main-table/ablation page inspected; original font and margins retained; no overfull or unresolved references. Final caption cleanup removes obsolete dagger/fused-row wording.',new_independent_native_results=0,new_work_pushed=False,complete_research=False,qualification='Reorganized problem-method-complete results-tradeoffs-ablations-cost/scope main. Table binds own CPD/wire/SB/CB/whole time/PSS/complete endpoint changes; two initial failures retained. Historical local trajectories/recovery/audit retained in supplement. Unified controller explicitly remains integration target. Historical paper snapshots and claim ledger are preserved, not implicitly asserted to appear verbatim in this main.')
write(D/'unified_structure_paper_binding_01.json',binding)
print(dict(passed=True,pages=6,rows=21,pdf=binding['pdf']))
