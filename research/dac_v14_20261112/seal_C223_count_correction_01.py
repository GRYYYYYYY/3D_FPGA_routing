"""Correct one inherited aggregate count without changing any scientific observation."""
import shutil
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';parent=read(D/'budget_owner_paper_binding_01.json');old=Path(parent['snapshot'])/'current_repair_main.tex'
source=p/'current_repair_C223_count_correction.tex';pdf=p/'build_C223_count_correction_01/current_repair_C223_count_correction.pdf'
assert source.read_text()==old.read_text().replace('preserves 26 successful complete configurations','preserves 30 successful complete configurations')
assert sha(p/'current_repair_main.tex')==sha(old)
assert len(PdfReader(pdf).pages)==6
inventory=read(D/'multiobjective_engineering_inventory_01/completion.json');assert inventory['passed']
log=p/'build_C223_count_correction_01.log';assert 'Overfull' not in log.read_text()
snap=D/'paper_snapshots/current_C223_count_correction_20261115';snap.mkdir(exist_ok=False)
files={}
for src,name in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),(p/'data/joint_quality_projection_34.pdf','data/joint_quality_projection_34.pdf'),(p/'IEEEtran.cls','IEEEtran.cls'),(p/'visual_C223_count_correction_01/contact.png','visual/contact.png')]:
 dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);files[name]=sha(dest)
write(snap/'snapshot_binding.json',dict(status='immutable_count_correction_snapshot',files=files))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
write(D/'C223_count_correction_paper_binding_01.json',dict(passed=True,claims=parent['claims'],pages=6,records=640,complete_configurations=30,latest_inventory_configurations=33,snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),parent_binding=str(D/'budget_owner_paper_binding_01.json'),source_sha256={str(f):sha(f) for f in [source,pdf,log,D/'multiobjective_engineering_inventory_01/complete_configuration_inventory.json',D/'multiobjective_engineering_inventory_01/verification.json',snap/'snapshot_binding.json']},visual_review='Six-page contact inspected: all tables, projection and references retained; only 26 to30 text correction. No overfull boxes.',qualification='Corrected aggregate only. Old snapshots/bindings preserved; old checker comparing mutable current to old snapshot is historical. No route/time/endpoint values changed.',new_work_pushed=False))
print(dict(passed=True,pages=6,archive640_complete_configurations=30))
