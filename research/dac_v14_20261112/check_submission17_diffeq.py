"""Verify the new submission's evidence, parent, source and six-page build."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
from pypdf import PdfReader
D=Path(__file__).resolve().parent;P=D/'submission_narrative_17';O=D/'submission_narrative_16'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
a=(O/'main.tex').read_text();b=(P/'main.tex').read_text()
def rows(s):return s.split('Circuit/role &',1)[1].split('\\hline',1)[1].split('\\hline\\end{tabular}',1)[0].strip().splitlines()
old,new=rows(a),rows(b);assert len(old)==50 and len(new)==52 and new[:50]==old
for start,end in [(r'\section{Introduction}',r'\section{Validation'),(r'\section{Mechanism Attribution',r'\section{Complete Cost')]:assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
assert (O/'data/references.tex').read_bytes()==(P/'data/references.tex').read_bytes();assert (P/'data/references.tex').read_text().count(r'\bibitem')==10
pdf=PdfReader(P/'build/main.pdf');assert len(pdf.pages)==6
assert 'Overfull' not in (P/'build/main.log').read_text()
assert sha(O/'build/main.pdf')==read(P/'edit_registration.json')['source_sha256'][str(O/'build/main.pdf')]
for path,h in read(P/'edit_registration.json')['source_sha256'].items():assert sha(path)==h,path
d=read(D/'DIFFEQ_P1FIX_complete_admission_01/admission_decision.json');assert d['complete_pair_admission']=='passed' and not d['gaps'] and d['identical_final_working_point_including_full_vector']
for path,h in d['source_sha256'].items():assert sha(path)==h,path
for r,row in zip(d['rows'],new[-2:]):
 q=r['quality'];v=q['resources'];e=r['own_root_endpoints'];assert f"{q['CPD_ns']:.6f}" in row and f"{v['wirelength']}/{v['SB_pairs']}/{v['CB_sources']}" in row and f"{r['complete_command_seconds']:.2f}" in row and f"{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}" in row
text=' '.join(p.extract_text() for p in pdf.pages);assert 'Diffeq' in text and '56.74' in text and '56.97' in text
summary='# 完整配对主表（投稿17）\n\n与正文 Table I 逐行一致。每行属于对应实际输入与完整命令；单次配对、重复测量和不同布局不计独立电路。端点相对各臂根，N/D 最终配对见对应 PAIR_TABLE。\n\n| 角色 | CPD(ns) | 线长/SB/CB | 完整秒数 | PSS(GiB) | setup改善/退化/新增hold |\n|---|---:|---|---:|---:|---|\n'
for row in new:summary+='| '+' | '.join(t.strip() for t in row.rstrip('\\').split('&'))+' |\n'
summary+='\nBNN交错24.91%与冷启动22.95%分列；LSTM归档干扰不推算无干扰时间。diffeq原生和域最终向量相同，单次费用不当统计加速。失败或未准入质量为空。\n'
(P/'COMPLETE_PAIR_TABLE.md').write_text(summary)
sys.path.insert(0,'/tmp/peng_pdfium');import pypdfium2 as pdfium
from PIL import Image
R=P/'review';R.mkdir(exist_ok=False);doc=pdfium.PdfDocument(str(P/'build/main.pdf'));contact=Image.new('RGB',(1320,1200),'#ccc')
for i,page in enumerate(doc):
 im=page.render(scale=1.6).to_pil().convert('RGB');im.save(R/f'page{i+1}.png');im.thumbnail((430,570));contact.paste(im,((i%3)*440,(i//3)*600))
contact.save(R/'contact.png')
write(P/'technical_checks.json',dict(passed=True,checked_at=datetime.now(timezone.utc).isoformat(),pages=6,rows=52,all50_previous_rows_unchanged=True,method_prior_art_controls_unchanged=True,parent_PDF_preserved=True,ten_references_preserved=True,diffeq_pair_passed=True,visual_review_pending=True,artifact_sha256={str(p):sha(p) for p in sorted(P.rglob('*')) if p.is_file() and 'review' not in p.parts and p.suffix not in ['.aux','.xdv','.log'] and p.name not in ['technical_checks.json','verification.json']}))
print(dict(passed=True,pages=6,rows=52,visual_review_pending=True))
