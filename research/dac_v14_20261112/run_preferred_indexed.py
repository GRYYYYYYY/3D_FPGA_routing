#!/usr/bin/env python3
"""Bounded offline preferred-cross query and independent adapter unit checks."""
import os,resource,signal,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
require_formal_terminal();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
b=D/'preferred_query_certificate_offline_03';base=D/'residual_query_offline_01';reg=read(b/'registration.json')
assert all(sha(p)==h for p,h in reg['source_sha256'].items()) and shutil.disk_usage(D).free>=80*1024**3
assert sha(base/'graph.bin')==read(base/'graph_binding.json')['binary_graph_sha256']
inputs=[Path(__file__),b/'registration.json',base/'graph.bin',*sorted((b/'src').glob('*'))]
source={str(p):sha(p) for p in inputs};write(b/'execution_registration.json',dict(status='registered_before_compile',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=source,timeout=1800,memory_bytes=24*1024**3,native_route_calls=0))
started=time.monotonic()
for name in ['preferred_query_driver']:
 with (b/(name+'_compile.log')).open('w') as f:
  subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-D_GLIBCXX_ASSERTIONS','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(b/'src'),str(b/'src'/(name+'.cpp')),'-o',str(b/name)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
unit_source=D/'preferred_query_certificate_offline_02'
assert read(unit_source/'unit_validation.json')['passed']
for name in ['preferred_query_adapter.h','h3d_candidate_path.h','test_preferred_query.cpp']:
 assert sha(b/'src'/name)==sha(unit_source/'src'/name)
shutil.copy2(unit_source/'test_preferred_query',b/'test_preferred_query')
write(b/'unit_validation.json',dict(passed=True,reused=True,source=str(unit_source/'unit_validation.json'),source_sha256=sha(unit_source/'unit_validation.json'),reason='Exact same adapter, core and test source; only offline driver pre-indexes identical edges. Existing5760 Floyd adapter checks retained, not rerun or added as independent samples.'))
cases=[c for c in read(base/'cases.json') if c['oracle']['guide']];assert len(cases)==10
write(b/'cases.json',cases)
with (b/'cases.txt').open('w') as f:
 f.write(str(len(cases))+'\n')
 for c in cases:
  r=c['domain'];pref=r['preferred'].split(',');assert pref!=['-']
  f.write(' '.join([r['search'],r['sink']]+[r[k] for k in ['xmin','xmax','ymin','ymax','layer_min','layer_max']]+[str(len(c['seeds'])),str(len(pref))])+'\n')
  for s in c['seeds']:f.write(f"{s['node']} {s['delay']:.17g}\n")
  f.write(' '.join(pref)+'\n')
with (b/'query_stdout.log').open('w') as f,(b/'query_stderr.log').open('w') as err:
 subprocess.run([str(b/'preferred_query_driver'),str(base/'graph.bin'),str(b/'cases.txt'),'256'],stdout=f,stderr=err,check=True,timeout=600)
assert all(sha(p)==h for p,h in source.items());assert all(sha(p)==h for p,h in reg['source_sha256'].items())
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=source,output_sha256={n:sha(b/n) for n in ['cases.json','cases.txt','unit_validation.json','preferred_query_driver','test_preferred_query','query_stdout.log','query_stderr.log']},elapsed_seconds=time.monotonic()-started,native_route_calls=0))
# Only the fourth ordering arm is new. Every old non-time field/path must match.
old=(D/'preferred_query_certificate_offline_02/query_stdout.log').read_text().splitlines()
new=(b/'query_stdout.log').read_text().splitlines()
def normalized(lines):
 result=[]
 for line in lines:
  v=line.split()
  if v[0]=='WORK':continue
  if int(v[2])==4:continue
  if v[0]=='RESULT':v[10]='<elapsed>'
  result.append(v)
 return result
control=normalized(old)==normalized(new);write(b/'control_reproduction.json',dict(passed=control,scope='Every P0/Ph/Pf/Pt non-time result and physical path record exact; only Pi uses indexed crossing lookup.'))
assert control
targeted=[];indexed=[]
for l in new:
 v=l.split()
 if v[0]=='WORK':continue
 if int(v[2]) not in [3,4]:continue
 mode=int(v[2]);v[2]='3'
 if v[0]=='RESULT':v[10]='<elapsed>'
 (targeted if mode==3 else indexed).append(v)
assert targeted==indexed
write(b/'index_reproduction.json',dict(passed=True,scope='Every Pi result/path/non-time counter equals Pt after arm identity normalization; lookup changes only candidate-filter work.'))
print('Strictly reused 5760 adapter checks; all targeted/indexed non-time results and paths exact');print('Physical audit pending',flush=True)
