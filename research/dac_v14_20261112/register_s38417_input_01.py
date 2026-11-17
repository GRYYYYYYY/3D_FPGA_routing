"""Preregister one different public circuit; no route-dependent selection."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, subprocess

D = Path(__file__).resolve().parent
U = D / 'VTR_s38417_input_01'
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
write = lambda p, v: Path(p).write_text(json.dumps(v, indent=2, ensure_ascii=False)+'\n')
old = read(D / 'VTR_clma_input_01/registration.json')
src = D.parents[1] / 'vendor/vtr/vtr_flow/benchmarks/blif/s38417.blif'
data = src.read_bytes()
assert data == subprocess.check_output(['git','show',old['source_commit']+':vtr_flow/benchmarks/blif/s38417.blif'],cwd=src.parents[3])
text = data.decode().replace('\\\n',' ')
ports = {k: next(l for l in text.splitlines() if l.startswith('.'+k+' ')).split()[1:] for k in ['inputs','outputs']}
assert all(re.fullmatch(r'[A-Za-z0-9_]+',p) for v in ports.values() for p in v)
latches = [l.split() for l in text.splitlines() if l.startswith('.latch ')]
assert len(latches)==1463 and all(l[3]=='re' and l[4]=='pclk' for l in latches)
inputs = [p for p in ports['inputs'] if p!='pclk']; assert len(inputs)+1==len(ports['inputs'])
prior=[]
for folder in D.iterdir():
    if not folder.is_dir(): continue
    for name in ['plan.json','registration.json']:
        p=folder/name
        if p.exists() and p.stat().st_size<1000000 and re.search(r's38417',p.read_text(),re.I): prior.append(str(p))
assert not prior, prior
assert not U.exists()
script = D/'prepare_s38417_input_01.py'; assert not script.exists()
original=(D/'prepare_s38584_input_01.py').read_text()
script.write_text(original.replace('s38584','s38417'))
U.mkdir(); (U/'inputs').mkdir()
blif=U/'inputs/s38417.blif'; blif.write_bytes(data)
sdc=U/'inputs/s38417.sdc'
sdc.write_text('# Explicit benchmark constraint; not an external application requirement.\ncreate_clock -period 20 [get_ports {pclk}]\n'+''.join(f'set_{kind}_delay -clock pclk -{limit} {val} [get_ports {{'+' '.join(names)+'}]\n' for kind,names in [('input',inputs),('output',ports['outputs'])] for limit,val in [('max',1),('min',0)]))
bindings={p:h for p,h in old['source_sha256'].items() if 'VTR_clma_input_01' not in p and not p.endswith('prepare_clma_input_01.py')}
bindings.update({str(p):sha(p) for p in [Path(__file__).resolve(),script,src,blif,sdc]})
plan={**old,'registered_at':datetime.now(timezone.utc).isoformat(),'input':'s38417','source_path':'vtr_flow/benchmarks/blif/s38417.blif','actual_source_sha256':sha(src),'names':sum(l.startswith('.names') for l in text.splitlines()),'latches':len(latches),'subckts':sum(l.startswith('.subckt') for l in text.splitlines()),'prior_registered_matches':prior,'IO_delay_constraints':dict(input_max_ns=1,input_min_ns=0,output_max_ns=1,output_min_ns=0,data_input_ports=len(inputs),output_ports=len(ports['outputs'])),'new_to_current_CP1_confirmation':True,'new_architecture_family':False,'selection_reason':'Different pinned public sequential circuit; 1463 actual pclk registers and 433 nets with >=8 combinational input uses in static source census. These are not evidence of cross-layer sharing or benefit. One actual placement, same Hybrid-O architecture family and fixed benchmark SDC, audited minimum device at 80% logical capacity, no route-QoR selection or reroll. Preserve all failures and no-cut outcomes.','execution_after_current_required_queue':str(D/'S38584_complete_admission_01/queue'),'source_sha256':bindings}
write(U/'registration.json',plan)
print(json.dumps(dict(registered=True,circuit='s38417',latches=len(latches),data_inputs=len(inputs),outputs=len(ports['outputs']),routing_queries=0)))
