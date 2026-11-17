"""Check the separate manuscript against admitted receipts and protected parent."""
from pathlib import Path
import hashlib,json,datetime,sys
from pypdf import PdfReader
D=Path(__file__).resolve().parent;P=D/'submission_narrative_13';O=D/'submission_narrative_12'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
a=(O/'main.tex').read_text();b=(P/'main.tex').read_text()
def rows(s):return s.split('Circuit/role &',1)[1].split('\\hline',1)[1].split('\\hline\\end{tabular}',1)[0].strip().splitlines()
old,new=rows(a),rows(b);assert len(old)==42 and len(new)==44 and new[:42]==old
for start,end in [(r'\section{Introduction}',r'\section{Validation'),(r'\section{Mechanism Attribution',r'\section{Complete Cost')]:assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
assert (O/'data/references.tex').read_bytes()==(P/'data/references.tex').read_bytes();assert (P/'data/references.tex').read_text().count(r'\bibitem')==10
assert len(PdfReader(P/'build/main.pdf').pages)==6
assert 'Overfull' not in (P/'build/main.log').read_text()
assert sha(O/'build/main.pdf')=='4a9e99f49508c379e0578995651062e56c18ee2bed0a63673fbbdb00bd755dc4'
for path,h in read(P/'edit_registration.json')['source_sha256'].items():assert sha(path)==h,path
for path,h in read(D/'CLMA_complete_admission_01/admission_decision.json')['source_sha256'].items():assert sha(path)==h,path
summary='# 完整配对主表（投稿13）\n\n与正文Table I逐行一致。每行属于对应实际输入与完整命令；单次配对、重复测量和不同布局不计独立电路。端点相对各臂根，最终N/D配对见对应PAIR_TABLE。\n\n| 角色 | CPD(ns) | 线长/SB/CB | 完整秒数 | PSS(GiB) | setup改善/退化/新增hold |\n|---|---:|---|---:|---:|---|\n'
for row in new:summary+='| '+' | '.join(t.strip() for t in row.rstrip('\\').split('&'))+' |\n'
summary+='\nBNN交错24.91%与原冷启动22.95%分别保留；LSTM归档干扰不推算无干扰时间。Clma原生共同收益及单次费用不当domain增量或统计加速。失败/未准入质量为空，全部费用保留。\n'
(P/'COMPLETE_PAIR_TABLE.md').write_text(summary)
sys.path.insert(0,'/tmp/peng_pdfium');import pypdfium2 as pdfium
from PIL import Image
R=P/'review';R.mkdir(exist_ok=True);doc=pdfium.PdfDocument(str(P/'build/main.pdf'));contact=Image.new('RGB',(1320,1200),'#ccc')
for i,p in enumerate(doc):
 im=p.render(scale=1.6).to_pil().convert('RGB');im.save(R/f'page{i+1}.png');im.thumbnail((430,570));contact.paste(im,((i%3)*440,(i//3)*600))
contact.save(R/'contact.png')
write(P/'technical_checks.json',dict(passed=True,pages=6,rows=44,all42_previous_rows_unchanged=True,method_prior_art_controls_unchanged=True,parent_PDF_preserved=True,ten_references_preserved=True,clma_pair_passed=True,artifact_sha256={str(p):sha(p) for p in sorted(P.rglob('*')) if p.is_file() and 'review' not in p.parts and p.suffix not in ['.aux','.xdv','.log'] and p.name not in ['technical_checks.json','verification.json']}))
print(dict(passed=True,pages=6,rows=44,visual_review_pending=True))
