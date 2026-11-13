#!/usr/bin/env python3
"""Admit neutral traces, bind the exported physical graph, run independent oracle."""
from pathlib import Path
import csv, hashlib, json, math, os, re, resource, shutil, signal, subprocess, time
D=Path(__file__).resolve().parent
B=D/'estimate_trace_dev_01';Q=D/'estimate_diagnostics';G=D/'query_prototype/rrg_spmv'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
assert json.loads((B/'input_seal.json').read_text())['passed']
validation=json.loads((Q/'oracle_validation.json').read_text());assert validation['passed']
for name,digest in validation['sha256'].items():assert sha(Q/name)==digest
assert shutil.disk_usage(D).free>=80*1024**3
out=D/'estimate_oracle_01';out.mkdir(exist_ok=False)
shutil.copy2(__file__,out/'runner.py');shutil.copy2(Q/'exact_distances',out/'exact_distances');shutil.copy2(Q/'exact_distances.cpp',out/'exact_distances.cpp')
reg=json.loads((B/'registration.json').read_text());graph=json.loads((G/'binding.json').read_text())
bindings={str(p):sha(p) for p in [B/'input_seal.json',B/'registration.json',G/'binding.json',Q/'oracle_validation.json',out/'exact_distances',out/'runner.py',out/'exact_distances.cpp']}
for f in ['edges.bin','layers.bin']:
 assert sha(G/f)==graph['export_sha256'][f];bindings[str(G/f)]=graph['export_sha256'][f]
assert sha(graph['graph'])==graph['graph_sha256'];bindings[graph['graph']]=graph['graph_sha256']
fields=['run','phase','net','pin','source','sink','candidate','criticality','source_known','sink_known','source_value','sink_value','source_scale','sink_scale','source_proxy','sink_proxy','opening','branch','unit']
requests=set();counts={};known=0
with (out/'estimates.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
 for c in reg['circuits']:
  for arm in reg['arms']:
   rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text())
   assert m['status']=='completed' and m['metrics']['native_full_check_passed']
   assert json.loads((rd/'independent_audit.json').read_text())['audit']['passed']
   assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
   assert json.loads((rd/'estimate_equivalence.json').read_text())['passed']
   assert m['environment']['VPR_H3D_TRACE_ESTIMATES']=='1'
   graphpath=m['command'][m['command'].index('--read_rr_graph')+1]
   assert m['shared_inputs'][graphpath]['sha256']==graph['graph_sha256']
   for fn in ['manifest.json','stdout.log','independent_audit.json','final_guide_audit.json','estimate_equivalence.json']:bindings[str(rd/fn)]=sha(rd/fn)
   count=0;summary=None;seen=set()
   with (rd/'stdout.log').open() as log:
    for line in log:
     if line.startswith('H3D_ESTIMATE_SUMMARY '):summary=dict(re.findall(r'(\w+)=(\S+)',line))
     if not line.startswith('H3D_ESTIMATE '):continue
     r=dict(re.findall(r'(\w+)=(\S+)',line));r['run']=rd.name
     assert set(r)==set(fields) and r['phase'] in ['pre','source','post','table','selected']
     identity=(r['phase'],r['net'],r['pin'],r['candidate']);assert identity not in seen;seen.add(identity)
     for k in ['criticality','source_value','sink_value','source_scale','sink_scale','source_proxy','sink_proxy','opening','branch','unit']:assert math.isfinite(float(r[k]))
     assert float(r['unit'])>0
     assert math.isclose(float(r['branch']),float(r['sink_value'])*(1+4*float(r['criticality']))+4*float(r['criticality'])*float(r['source_value']),rel_tol=1e-12,abs_tol=1e-10)
     for side,reverse in [('source',0),('sink',1)]:
      assert r[side+'_known'] in ['0','1'];requests.add((int(r[side]),reverse,int(r['candidate'])));known+=int(r[side+'_known'])
     writer.writerow(r);count+=1
   assert summary and int(summary['enabled'])==1 and int(summary['rows'])==count>0
   counts[rd.name]=count
(out/'requests.txt').write_text(''.join(f'{a} {b} {c}\n' for a,b,c in sorted(requests)))
for f in ['estimates.csv','requests.txt']:bindings[str(out/f)]=sha(out/f)
write(out/'registration.json',dict(question='Do calibrated unknown distances underestimate candidate costs and induce score-rank reversals after source measurement? Independent graph-proxy diagnosis, not physical STA or single-event routing causality.',rows=counts,unique_requests=len(requests),logged_measured_sides=known,graph=graph['graph'],bindings=bindings,timeout=1800,memory_bytes=16*1024**3,selection='All candidate records and both sides from admitted spmv/eltwise P/Rq neutral traces, no outcome-based subset',oracle='Independent full Dijkstra with one crossing for reverse; no production search code',pid=os.getpid()))
def protect():resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3))
start=time.monotonic()
with (out/'exact.csv').open('x') as output,(out/'oracle.stderr').open('x') as errors:
 process=subprocess.Popen(['/usr/bin/time','-v','-o',str(out/'time.txt'),str(out/'exact_distances'),str(G),str(out/'requests.txt')],stdout=output,stderr=errors,preexec_fn=protect,start_new_session=True)
 write(out/'oracle_process.json',dict(pid=process.pid,start_ticks=Path(f'/proc/{process.pid}/stat').read_text().split(') ',1)[1].split()[19],scope='Private process group; timeout terminates complete oracle group'))
 try:
  code=process.wait(timeout=1800);status='completed' if code==0 else 'failed'
 except subprocess.TimeoutExpired:
  status='timeout'
  try:os.killpg(process.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:code=process.wait(timeout=5)
  except subprocess.TimeoutExpired:
   try:os.killpg(process.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   code=process.wait()
write(out/'completion.json',dict(status=status,returncode=code,wall_seconds=time.monotonic()-start))
assert status=='completed',status
checks={p:sha(p)==digest for p,digest in bindings.items()}
write(out/'input_seal.json',dict(passed=all(checks.values()),checks=checks));assert all(checks.values())
print(json.dumps(dict(status=status,rows=counts,requests=len(requests))))
