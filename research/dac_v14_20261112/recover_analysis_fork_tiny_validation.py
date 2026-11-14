#!/usr/bin/env python3
"""Reuse all completed native observations after a log-label-only test failure."""
import csv,os,shlex,shutil,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
start=time.monotonic();old=D/'analysis_fork_tiny_regression_01';out=D/'analysis_fork_tiny_regression_02';out.mkdir(exist_ok=False);reg=read(old/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
log=(D/'analysis_fork_validation_queue_01/regression.log').read_text();assert "line.startswith('# Load Packing took')" in log
binding=read(D/'analysis_fork_stage_02/binding.json');binary=D/'analysis_fork_stage_02/bin/vpr';assert sha(binary)==binding['binary_sha256'];fixture=D/'reservation_multisink_regression_01';initial=fixture/'initial';root=D.parents[1]
arch=root/'vendor/lazagna-vtr9-buildfix-src/vtr_flow/arch/timing/k6_N10_mem32K_40nm_fc_abs.xml';circuit=D/'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif';guard=root/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
command=[str(binary),str(arch),str(circuit),'--analysis','--route_chan_width','100','--seed','11','--num_workers','1','--clock_modeling','ideal','--check_route','full','--verify_file_digests','off','--verify_route_file_switch_id','on','--net_file',str(initial/'packed.net'),'--place_file',str(initial/'placed.place'),'--route_file',str(initial/'routed.route')]
rows=list(csv.DictReader((old/'workers.tsv').open(),delimiter='\t'));assert len(rows)==5;assert [int(r['exit_code'])==0 and int(r['signal'])==0 for r in rows]==[True,True,False,True,True]
files=[Path(__file__).resolve(),D/'analysis_fork_validation_queue_01/completion.json',D/'analysis_fork_validation_queue_01/regression.log',old/'registration.json',old/'process_costs.json',old/'sequence.txt',old/'workers.tsv',old/'equivalent_pin.route',old/'rr_graph.xml',D/'analysis_fork_stage_02/binding.json']
for i,reference in [(0,'original'),(1,'alternative'),(3,'alternative'),(4,'original')]:
 directory=old/('sequence_worker_'+str(i));r=old/reference
 for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo']:
  assert sha(directory/name)==sha(r/name),(i,name);files.extend([directory/name,r/name])
 s=(directory/'stdout.log').read_text();assert 'Completed routing consistency check successfully' in s and 'Synchronize the packed netlist to routing optimization' in s;files.append(directory/'stdout.log')
assert sha(old/'original/native_sta_frontier.jsonl')==sha(fixture/'new_off/sta.jsonl')
parent=old/'fork_sequence/stdout.log';assert sum(l.startswith('# Load packing took') for l in parent.read_text().splitlines())==1;assert not(old/'fork_sequence/native_sta_frontier.jsonl').exists();files.append(parent)
import sys
sys.path.insert(0,str(root/'scripts'));from check_route import read_trace
before={n.inode for n in read_trace(initial/'routed.route')[0]['trace'] if n.kind=='IPIN'};after={n.inode for n in read_trace(old/'equivalent_pin.route')[0]['trace'] if n.kind=='IPIN'};assert len(before)==len(after)==1 and not(before&after)
write(out/'registration.json',dict(status='before_remaining_native_checks',reuse=dict(original=str(old),native_observations_reused=3,repeated_native_observations=0,reason='Correct lowercase Load packing timer label; all substantive equality assertions already passed before original test stopped.'),source_sha256={str(p):sha(p) for p in files},command=command))
env={k:v for k,v in os.environ.items() if not k.startswith('VPR_')};env['VPR_H3D_MODE']='off';costs=[]
def run(name,cmd,extra=None):
 directory=out/name;directory.mkdir();assert shutil.disk_usage(out).free>=80*1024**3;t=time.monotonic();e=dict(env);e.update(extra or {})
 with (directory/'stdout.log').open('w') as f:
  proc=subprocess.Popen(['prlimit','--core=0:0','--as='+str(64*1024**3),'--',str(guard),*cmd],cwd=directory,env=e,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=proc.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait();raise
 costs.append(dict(name=name,returncode=code,complete_native_process_seconds=time.monotonic()-t));write(out/'process_costs.json',costs);return code
invalid=list(command);invalid[invalid.index('--route_file')+1]=str(old/'invalid.route');code=run('invalid_standalone',invalid);assert code==-int(rows[2]['signal']),'Malformed-route failure must match same-binary native loader control'
same=out/'duplicate_worker';same.mkdir();manifest=out/'duplicate.txt';manifest.write_text('2\n'+''.join(__import__('json').dumps(str(old/'equivalent_pin.route'))+' '+__import__('json').dumps(str(same))+' 1\n' for i in range(2)))
code=run('duplicate',command,dict(VPR_H3D_ANALYSIS_FORK_MANIFEST=str(manifest),VPR_H3D_ANALYSIS_FORK_RESULTS=str(out/'duplicate.tsv')));assert code!=0 and 'Analysis worker directory must be unique and empty' in (out/'duplicate/stdout.log').read_text();assert not(out/'duplicate.tsv').exists() and not any(same.iterdir())
assert all(sha(p)==h for p,h in reg['source_sha256'].items());assert all(sha(p)==h for p,h in read(out/'registration.json')['source_sha256'].items())
write(out/'completion.json',dict(passed=True,analysis_workers=5,successful_workers=4,reused_completed_native_parent_processes=3,new_native_parent_processes=2,total_native_parent_processes=5,full_precision_STA_and_graph_exact=True,equivalent_pin_changed=dict(net=0,before=sorted(before),after=sorted(after)),invalid_child_followed_by_valid=True,invalid_native_loader_signal=int(rows[2]['signal']),same_binary_invalid_standalone_signal=11,duplicate_directories_rejected=True,original_inputs_unchanged=True,route_search_flow_calls=0,complete_recovery_seconds=time.monotonic()-start,source_sha256={str(p):sha(p) for p in [out/'registration.json',out/'process_costs.json',manifest,Path(__file__).resolve()]},qualification='Actual native tiny FULLSTA/constraints/full graph exact equality after equivalent-IPIN change. Parent loads packing once. Malformed-route loader segfault is reproduced in standalone and isolated worker; subsequent valid worker is unchanged, not graceful in-process rollback. Corrected only a timer-label test assumption; native observations were not rerun. No large-case equivalence or cold algorithm speedup claim.'))
print(dict(passed=True,changed_IPIN=[sorted(before),sorted(after)],reused_native_parents=3,new_checks=2),flush=True)
