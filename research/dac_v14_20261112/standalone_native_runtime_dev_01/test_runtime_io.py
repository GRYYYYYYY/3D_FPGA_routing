"""Relocatable execution tests; no VPR/routing experiment is launched."""
import argparse,json,os,signal,sys
from pathlib import Path
import runtime_io as io
from runtime_common import write_json,sha256

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['normal','timeout','thread','mutated','wrong_binary'],required=True);p.add_argument('--forbid-prefix');a=p.parse_args()
if a.forbid_prefix:
 forbidden=str(Path(a.forbid_prefix).resolve())
 def guard(event,args):
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
   name=os.fsdecode(args[0])
   if str(Path(name).resolve()).startswith(forbidden+'/'):raise RuntimeError('Historical project read forbidden: '+name)
 sys.addaudithook(guard)
io.configure(a.output,sys.executable)
frozen=a.output/'input.txt';frozen.write_text('fixed\n')
io.frozen_hash(frozen)
if a.mode=='wrong_binary':
 try:io.run('wrong',['/bin/echo','wrong'],frozen=[frozen])
 except AssertionError as e:write_json(a.output/'test.json',dict(passed=True,case=a.mode,rejected=str(e),native_calls=0));raise SystemExit(0)
 raise AssertionError('Mismatched executable accepted')
if a.mode=='mutated':
 frozen.write_text('modified\n')
 try:io.seal_inputs(a.output/'input_seal.json')
 except RuntimeError:
  assert not json.loads((a.output/'input_seal.json').read_text())['passed']
  write_json(a.output/'test.json',dict(passed=True,case=a.mode,mutation_rejected=True,native_calls=0));raise SystemExit(0)
 raise AssertionError('Modified input accepted')
code='import time,os; assert os.environ["OMP_NUM_THREADS"]=="1"; assert "LD_PRELOAD" not in os.environ; time.sleep(.1); print("runtime_probe_ok")'
timeout=3
if a.mode=='thread':code='import threading; t=threading.Thread(target=lambda:None); t.start(); t.join()'
if a.mode=='timeout':code='import time; time.sleep(2)';timeout=.15
os.environ['LD_PRELOAD']='/nonexistent_test_override'
r=io.run('probe',[sys.executable,'-c',code],frozen=[frozen],timeout=timeout)
os.environ.pop('LD_PRELOAD',None)
if a.mode=='normal':assert r['status']=='completed' and r['returncode']==0 and r['process_tree_observation']['samples']>0
if a.mode=='timeout':assert r['status']=='timeout' and r['returncode']!=0
if a.mode=='thread':assert r['status']=='thread_constraint_violated' and r['thread_enforcement']['top_level_sigsys_observed']
assert not r['metrics']['native_full_check_passed'] and not r['metrics']['routing_success_reported']
io.seal_inputs(a.output/'input_seal.json')
write_json(a.output/'test.json',dict(passed=True,case=a.mode,status=r['status'],returncode=r['returncode'],native_calls=0,executable_sha256=sha256(sys.executable),qualification='Generic process-wrapper test, not native FPGA analysis or quality evidence.'))
