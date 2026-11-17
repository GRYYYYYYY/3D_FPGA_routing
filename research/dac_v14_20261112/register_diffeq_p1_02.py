"""Register a new syntax-compatible P1 attempt, reusing the successful census."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
D=Path(__file__).resolve().parent;old=D/'VTR_diffeq_p1_input_01';new=D/'VTR_diffeq_p1_input_02'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
prior=read(old/'registration.json');failed=read(old/'queue/completion.json');packed=read(old/'pack_01/execution_completion.json');capacity=read(old/'capacity_selection.json');assert not failed['passed'] and packed['passed'] and capacity['passed'];assert all(sha(p)==h for p,h in prior['source_sha256'].items());assert not new.exists();new.mkdir();(new/'inputs').mkdir()
for n in ['diffeq.blif','diffeq.sdc']:shutil.copyfile(old/'inputs'/n,new/'inputs'/n);assert sha(old/'inputs'/n)==sha(new/'inputs'/n)
canonical=(new/'inputs/diffeq.sdc').read_text();assert canonical.count('create_clock -period 20 [get_ports {pclk}]')==1;legacy=canonical.replace('create_clock -period 20 [get_ports {pclk}]','create_clock -period 20 pclk');(new/'inputs/diffeq_p1_legacy.sdc').write_text(legacy)
grammar=D.parents[1]/'vendor/beyond-flatland-src/libs/EXTERNAL/libsdcparse/src/sdc_parser.y';src=grammar.read_text();part=src.split('cmd_create_clock:',1)[1].split('cmd_set_input_delay:',1)[0];assert 'cmd_create_clock string' in part and 'cmd_get_ports' not in part
files=[Path(__file__).resolve(),D/'prepare_diffeq_p1_02.py',old/'registration.json',old/'queue/completion.json',old/'pack_01/execution_completion.json',old/'pack_01/registration.json',old/'pack_01/packed.net',old/'capacity_selection.json',new/'inputs/diffeq.blif',new/'inputs/diffeq.sdc',new/'inputs/diffeq_p1_legacy.sdc',grammar]
bound={**prior['source_sha256'],**{str(p):sha(p) for p in files}}
plan={**prior,'registered_at':datetime.now(timezone.utc).isoformat(),'attempt':'02_after_preserved_legacy_parser_failure','prior_attempt':str(old),'prior_failure_preserved':True,'census_pack_reused':str(old/'pack_01/packed.net'),'capacity_selection_reused':str(old/'capacity_selection.json'),'placement_SDC':str(new/'inputs/diffeq_p1_legacy.sdc'),'confirmation_SDC':str(new/'inputs/diffeq.sdc'),'SDC_syntax_qualification':'Only create_clock collection syntax changes to the old parser supported direct pclk target; the clock period, exact port and all four I/O constraint commands remain identical. Canonical SDC is used for subsequent routing. Actual P1 parser must successfully report the single pclk clock and five commands.','source_sha256':bound}
write(new/'registration.json',plan);print(json.dumps(dict(registered=True,reused_actual_census=True,prior_failure_preserved=True,route_queries=0)))
