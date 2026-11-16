"""Bind six-page routing positioning to original data and primary-source locators."""
import re,shutil,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';parent_path=D/'mechanism_inputs_paper_binding_04.json';parent=read(parent_path);previous=Path(parent['snapshot'])
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
source=p/'current_repair_routing_position_05.tex';build=p/'build_routing_position_05';pdf=build/'current_repair_routing_position_05.pdf';log=p/'build_routing_position_05.log'
text=source.read_text();old=(previous/'current_repair_main.tex').read_text();refs=D/'routing_related_work_01'
assert sha(source)==read(refs/'final_source_registration.json')['final_source_sha256']
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
assert re.findall(r'\\section\{([^}]+)\}',text)==parent['sections']
assert text.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
rows=read(previous/'data/complete_table_rows.json');assert len(rows)==22
for row in rows:assert next(x for x in text.splitlines() if x.startswith(row['label']+'&'))==next(x for x in old.splitlines() if x.startswith(row['label']+'&'))
for environment in ['table\\*','figure','figure\\*']:
 pattern=r'\\begin\{'+environment+r'\}.*?\\end\{'+environment+r'\}'
 assert re.findall(pattern,text,re.S)==re.findall(pattern,old,re.S),environment
keys=re.findall(r'\\bibitem\{([^}]+)\}',text);assert keys==read(refs/'final_source_registration.json')['citation_first_appearance_order'] and len(keys)==9
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for word in ['671-record','34quality-complete','33havecompleteobservermeasurements','qualifiedGNU-timeonly','22.95%','47.56%','0.797%','LaZagna','CRoute','historicalcongestioncosts','arXiv:2606.06421v3']:
 assert word in flat,word
receipts=parent['verified_case_receipts'].copy();assert all(sha(f)==h for f,h in receipts.items())
snap=D/'paper_snapshots/current_routing_position_20261116';assert not snap.exists();shutil.copytree(previous,snap)
for src,name in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:shutil.copy2(src,snap/name)
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/routing_position_page{i}.png')
shutil.copytree(refs,snap/'supplement/routing_related_work')
claims=read(previous/'claims_evidence.json');claims['related_work']=dict(primary_source_locators='supplement/routing_related_work/sources.json',comparison='supplement/routing_related_work/comparison.md',external_numeric_comparison_reproduced=False,established_ingredients=['current timing','retained trees','incremental rerouting','multiple convergences'],contribution_scope='Conditional vertical domains, failure release, capacity-certified owner scopes and whole-candidate fixed-envelope decisions, supported by local mechanisms and complete costs; full confirmation pending.')
write(snap/'claims_evidence.json',claims)
visual='All six final pages inspected at1.3x; readable columns, full table/figure, all9references; no overflow/clipping. Historical images remain historical; routing_position_page1--6 are current. Fonts/margins/figures/table values unchanged.'
files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'}
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_routing_position_update',files=files,visual_review=visual))
shutil.copy2(source,p/'current_repair_main.tex');ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding={k:v for k,v in parent.items() if k not in ['source_sha256','qualification','visual_review','snapshot','pdf']}
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),references=9,table_rows=22,new_native_calls=0,new_independent_inputs=0,
 source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,refs/'sources.json',refs/'comparison.md',refs/'moved_local_detail.tex',refs/'final_source_registration.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},visual_review=visual,
 qualification='Related work and contribution boundaries revised from5 primary sources, references ordered by appearance. Original22 measured rows, both figures, sections and671/34/33+1 archive counts unchanged. Two local-detail paragraphs retained in supplement. No experimental benefit, external-router superiority, CHANZ validation or confirmation freeze inferred.')
write(D/'routing_position_paper_binding_05.json',binding)
print(dict(passed=True,pages=6,references=9,rows=22,pdf=binding['pdf']))
