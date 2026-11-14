#!/usr/bin/env python3
"""Load one immutable state and reproduce several historical native transactions.

This is an engineering-equivalence diagnostic. Each native transaction rolls back
before the next one. It neither commits routes nor replaces candidate FULL/STA.
"""
import argparse,fcntl,json,os,shutil,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
from native_batch_evidence import transaction
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103';sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
p=argparse.ArgumentParser();p.add_argument('--registration',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args();started=time.monotonic();registration=a.registration.resolve();reg=read(registration)
require_formal_terminal();lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert shutil.disk_usage(D).free>=80*1024**3
assert all(sha(path)==h for path,h in reg['source_sha256'].items())
source=Path(reg['source']);stage=D/'native_batch_stage_02';assert sha(stage/'bin/vpr')==read(stage/'binding.json')['binary_sha256']
m=read(source/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and read(source/'independent_audit.json')['audit']['passed']
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
b=a.batch.resolve();b.mkdir(exist_ok=False);(b/'bin').mkdir();(b/'joint_outputs').mkdir();rd=b/'runs/state';rd.mkdir(parents=True)
shutil.copy2(stage/'bin/vpr',b/'bin/vpr');shutil.copy2(OLD/'runtime_dependency_binding.json',b/'runtime_dependency_binding.json')
for n in ['packed.net','placed.place','routed.route']:shutil.copy2(source/n,rd/n)
manifest=b/'native_batch.txt';manifest.write_text(str(len(reg['requests']))+'\n'+''.join(f'{json.dumps(r["request"])} {json.dumps(str(b/"joint_outputs"/(name+".log")))} {r["objective"]}\n' for name,r in reg['requests'].items()))
files=[Path(__file__).resolve(),D/'native_batch_evidence.py',registration,stage/'binding.json',source/'manifest.json',source/'independent_audit.json',graph,manifest,b/'bin/vpr',source/'native_sta_frontier.jsonl',*list(rd.glob('*'))]
hashes={str(p):sha(p) for p in files};write(b/'execution_registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=hashes,status='before_native',qualification='One shared native-analysis process; independent static-state transactions, zero route commits. Not an accepted-update trajectory.'))
io.BASE=b;io.ADDRESS_SPACE_BYTES=64*1024**3
for path,h in {**hashes,**reg['source_sha256']}.items():io.frozen_hash(path,h)
write(rd/'pair_check.json',dict(passed=True,checks={n:sha(source/n)==sha(rd/n) for n in ['packed.net','placed.place','routed.route']},scope='Same immutable source and exact native inputs for all transactions'))
cmd=list(m['command']);cmd[0]=str(b/'bin/vpr')
if '--route' in cmd:cmd.remove('--route')
assert '--analysis' in cmd
for option,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(option)+1]=str(rd/n)
if '--verify_route_file_switch_id' not in cmd:cmd+=['--verify_route_file_switch_id','on']
else:cmd[cmd.index('--verify_route_file_switch_id')+1]='on'
cmd[cmd.index('--timing_report_npaths')+1]='10'
pre=rd/'native_sta_frontier.jsonl';post=rd/'post_batch_sta.jsonl'
env=dict(VPR_H3D_MODE='off',VPR_JOINT_NATIVE_REQUEST='',VPR_JOINT_NATIVE_OUTPUT='',VPR_JOINT_NATIVE_BATCH=str(manifest),VPR_JOINT_NATIVE_BATCH_POST_STA=str(post),VPR_H3D_FINAL_STA_TRACE=str(pre),VPR_H3D_FINAL_TIMING_ECHO='')
preparation=time.monotonic()-started
result=io.run(rd.name,cmd,environment=env,timeout=1800,frozen=[cmd[0],cmd[1],cmd[2],graph,b/'execution_registration.json'],private_inputs=[rd/n for n in ['packed.net','placed.place','routed.route']],tags=dict(phase='independent_static_native_batch',full_route_flow_calls=0,native_transactions=len(reg['requests'])))
checks=dict(process_completed=result['status']=='completed',original_native_FULL=result['metrics'].get('native_full_check_passed',False),inputs_unchanged=all(sha(rd/n)==sha(source/n) for n in ['packed.net','placed.place','routed.route']),CPD_original=result['metrics'].get('critical_path_ns')==m['metrics']['critical_path_ns'])
checks['pre_post_original_STA_identical']=pre.exists() and post.exists() and sha(pre)==sha(post)==sha(source/'native_sta_frontier.jsonl')
comparisons={}
if checks['process_completed']:
 for name,r in reg['requests'].items():
  actual=transaction(b/'joint_outputs'/(name+'.log'));reference=transaction(r['reference_log']);same=all(actual[k]==reference[k] for k in ['success','finished','planned','normalized_sha256'])
  comparisons[name]=dict(passed=same,actual=actual,reference=reference,reference_native_completion=r['reference_completion'],reference_quality_state=r.get('reference_evaluation'),qualification='Exact complete native tree/search/rollback comparison, elapsed fields excluded. Reference quality belongs to its own old run; no new candidate commit or timing point is created.')
 checks['all_transactions_equal']=all(x['passed'] for x in comparisons.values()) and len(comparisons)==len(reg['requests'])
write(b/'comparisons.json',comparisons);io.seal_inputs(b/'input_seal.json');checks['sealed']=read(b/'input_seal.json')['passed']
write(b/'completion.json',dict(passed=all(checks.values()),checks=checks,native_analysis_calls=1,native_transaction_calls=len(reg['requests']),new_route_commits=0,full_route_flow_calls=0,post_batch_fresh_STA=True,preparation_seconds=preparation,native_process_seconds=result['wall_seconds'],complete_observed_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,source_sha256={str(p):sha(p) for p in [registration,b/'execution_registration.json',b/'comparisons.json',b/'input_seal.json',rd/'manifest.json']},qualification='Engineering static-state equivalence only. Actual batch time includes extra post-batch native STA restoration validation. Older isolated times are not a paired performance cohort; final candidate native FULL/STA and independent physical audits remain separately required. Existing research queues and acceptance rules unchanged.'))
print(dict(passed=all(checks.values()),checks=checks,requests=len(comparisons)),flush=True);assert all(checks.values())
