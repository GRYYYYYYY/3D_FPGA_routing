#!/usr/bin/env python3
"""Bounded offline preferred-cross query and independent adapter unit checks."""
import os,resource,signal,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
require_formal_terminal();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
b=D/'preferred_query_certificate_offline_01';base=D/'residual_query_offline_01';reg=read(b/'registration.json')
assert all(sha(p)==h for p,h in reg['source_sha256'].items()) and shutil.disk_usage(D).free>=80*1024**3
assert sha(base/'graph.bin')==read(base/'graph_binding.json')['binary_graph_sha256']
inputs=[Path(__file__),b/'registration.json',base/'graph.bin',*sorted((b/'src').glob('*'))]
source={str(p):sha(p) for p in inputs};write(b/'execution_registration.json',dict(status='registered_before_compile',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=source,timeout=1800,memory_bytes=24*1024**3,native_route_calls=0))
started=time.monotonic()
for name in ['test_preferred_query','preferred_query_driver']:
 with (b/(name+'_compile.log')).open('w') as f:
  subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-D_GLIBCXX_ASSERTIONS','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(b/'src'),str(b/'src'/(name+'.cpp')),'-o',str(b/name)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
unit=subprocess.run([str(b/'test_preferred_query')],text=True,capture_output=True,timeout=120)
(b/'unit_stdout.log').write_text(unit.stdout);(b/'unit_stderr.log').write_text(unit.stderr)
write(b/'unit_validation.json',dict(passed=unit.returncode==0,returncode=unit.returncode,stdout=unit.stdout,stderr=unit.stderr,source_sha256=source,qualification='240 random two-layer directed graphs, zero cycles, duplicate/missing seeds, BB rejection, disconnected preferred crossings, arbitrary inadmissible order heuristic; independent forward two-phase Floyd. Three modes x three work caps x two storage caps. No external graph facts assumed.'))
assert unit.returncode==0,unit.stderr
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
print(unit.stdout.strip());print('Physical audit pending',flush=True)
