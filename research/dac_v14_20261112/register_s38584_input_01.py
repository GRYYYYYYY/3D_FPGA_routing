"""One distinct sequential input, queued only after all current required gates."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,re,hashlib,subprocess
D=Path(__file__).resolve().parent;U=D/'VTR_s38584_input_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
U.mkdir(exist_ok=False);(U/'inputs').mkdir();old=read(D/'VTR_clma_input_01/registration.json');src=D.parents[1]/'vendor/vtr/vtr_flow/benchmarks/blif/s38584.1.blif';commit=old['source_commit'];data=src.read_bytes();assert data==subprocess.check_output(['git','show',commit+':vtr_flow/benchmarks/blif/s38584.1.blif'],cwd=src.parents[3]);blif=U/'inputs/s38584.blif';blif.write_bytes(data)
text=data.decode().replace('\\\n',' ');ports={kind:next(l for l in text.splitlines() if l.startswith('.'+kind+' ')).split()[1:] for kind in ['inputs','outputs']};assert all(re.fullmatch(r'[A-Za-z0-9_]+',p) for names in ports.values() for p in names)
latches=[l.split() for l in text.splitlines() if l.startswith('.latch ')];assert len(latches)==1260 and all(l[3]=='re' and l[4]=='pclk' for l in latches);assert 'pclk'in ports['inputs'];inputs=[p for p in ports['inputs'] if p!='pclk'];sdc=U/'inputs/s38584.sdc'
sdc.write_text('# Preregistered explicit clock/IO benchmark; not an external application requirement.\ncreate_clock -period 20 [get_ports {pclk}]\n'+''.join(f'set_{kind}_delay -clock pclk -{limit} {val} [get_ports {{'+' '.join(names)+'}]\n' for kind,names in [('input',inputs),('output',ports['outputs'])] for limit,val in [('max',1),('min',0)]))
script=D/'prepare_s38584_input_01.py';assert not script.exists();s=(D/'prepare_clma_input_01.py').read_text().replace('VTR_clma_input_01','VTR_s38584_input_01').replace('inputs/clma.','inputs/s38584.');script.write_text(s)
# Prior registrations searched by top-level experiment plans, not historical filename heuristics.
prior=[]
for folder in D.iterdir():
 if not folder.is_dir() or folder==U:continue
 for name in ['plan.json','registration.json']:
  p=folder/name
  if p.exists() and p.stat().st_size<1000000 and re.search(r's38584',p.read_text(),re.I):prior.append(str(p))
assert not prior,prior
bindings={p:h for p,h in old['source_sha256'].items() if 'VTR_clma_input_01' not in p and not p.endswith('prepare_clma_input_01.py')};bindings.update({str(p):sha(p) for p in [Path(__file__).resolve(),script,src,blif,sdc]})
plan={**old,'registered_at':datetime.now(timezone.utc).isoformat(),'input':'s38584','source_path':'vtr_flow/benchmarks/blif/s38584.1.blif','actual_source_sha256':sha(src),'names':sum(l.startswith('.names') for l in text.splitlines()),'latches':1260,'subckts':sum(l.startswith('.subckt') for l in text.splitlines()),'prior_registered_matches':prior,'IO_delay_constraints':dict(input_max_ns=1,input_min_ns=0,output_max_ns=1,output_min_ns=0,data_input_ports=len(inputs),output_ports=len(ports['outputs'])),'new_to_current_CP1_confirmation':True,'new_architecture_family':False,'selection_reason':'Distinct pinned public sequential benchmark with1260 actual pclk latches, compared to clma33. Tests timing-covered dependencies on a different register-rich circuit. Same fixed20ns+IOmax1/min0 benchmark specification, minimum audited device at80%capacity, one seed21placement, no routing QoR selection. Public known benchmark, not an unseen holdout. Every failure/no-cut/no-gain kept.','execution_after_current_required_queue':str(D/'CLMA_IO_postqueue_01/queue'),'source_sha256':bindings}
write(U/'registration.json',plan);print(dict(registered=True,public_circuit='s38584.1',latches=1260,data_inputs=len(inputs),outputs=len(ports['outputs']),routing_queries_planned=0,upstream_stages=['pack_01','place_01']))
