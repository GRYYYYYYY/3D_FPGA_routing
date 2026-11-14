#!/usr/bin/env python3
"""Focused native reservation/rollback regression on a tiny routed fixture.

Supply a built VPR and a compatible VTR architecture. This directly exercises
the post-route hook, which needs generated route-tree IDs and cannot use a fixed
task-config request. It verifies occupancy restoration, not candidate QoR.
"""
import argparse,hashlib,json,math,os,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--vpr',type=Path,required=True);p.add_argument('--architecture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();start=time.monotonic()
b=a.output.resolve();b.mkdir(exist_ok=False);binary=a.vpr.resolve();arch=a.architecture.resolve();blif=Path(__file__).with_name('fixture.blif').resolve();initial=b/'initial';initial.mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
command=[str(binary),str(arch),str(blif),'--pack','--place','--route','--analysis','--route_chan_width','100','--seed','11','--num_workers','1','--clock_modeling','ideal','--check_route','full','--verify_file_digests','off','--verify_route_file_switch_id','on','--net_file',str(initial/'packed.net'),'--place_file',str(initial/'placed.place'),'--route_file',str(initial/'routed.route')]
base=dict(os.environ,VPR_H3D_MODE='off',VPR_JOINT_NATIVE_REQUEST='',VPR_JOINT_NATIVE_RESERVE_TARGETS='',VPR_JOINT_NATIVE_RESERVE_OUTPUT='')
def run(cmd,env,directory):
 assert shutil.disk_usage(b).free>=80*1024**3
 with (directory/'stdout.log').open('w') as log:r=subprocess.run(['prlimit','--as='+str(8*1024**3),'--',*cmd],cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
 assert r.returncode==0,(directory,r.returncode)
run(command,dict(base,VPR_H3D_FINAL_STA_TRACE=str(initial/'sta.jsonl')),initial)
records=[json.loads(l) for l in (initial/'sta.jsonl').open()];assert records[-1]['type']=='complete';chosen={}
for r in records:
 if r.get('type')=='pin' and not r['driver'] and not r['ignored'] and not r['global'] and r['route_tree_present'] and r['pin']>0 and isinstance(r['setup_criticality_raw'],(int,float)):
  chosen.setdefault(r['net'],r)
targets=list(chosen.values())[:2];assert len(targets)==2
request=b/'request.txt';request.write_text('2\n'+''.join(f"{r['net']} 1 {r['pin']}\n" for r in targets)+'0\n2\n'+''.join(f"{r['net']} {r['pin']} {r['setup_criticality_raw']:.17g}\n" for r in targets))
reserve=b/'targets.txt';reserve.write_text('2\n'+''.join(f"{r['net']} {r['pin']}\n" for r in targets));before={n:sha(initial/n) for n in ['packed.net','placed.place','routed.route']};results={}
for mode in ['off','on']:
 directory=b/mode;directory.mkdir();cmd=[x for x in command if x not in ['--pack','--place','--route']]
 env=dict(base,VPR_H3D_FINAL_STA_TRACE=str(directory/'sta.jsonl'),VPR_JOINT_NATIVE_REQUEST=str(request),VPR_JOINT_NATIVE_OBJECTIVE='physical_capacity',VPR_JOINT_NATIVE_OUTPUT=str(directory/'joint.log'))
 if mode=='on':env.update(VPR_JOINT_NATIVE_RESERVE_TARGETS=str(reserve),VPR_JOINT_NATIVE_RESERVE_OUTPUT=str(directory/'reservations.log'))
 run(cmd,env,directory);assert all(sha(initial/n)==h for n,h in before.items())
 lines=(directory/'joint.log').read_text().splitlines();assert lines[-1].endswith('occupancy_restored');success=bool(int(lines[-1].split()[1]));assert success
 actual=[json.loads(l) for l in (directory/'sta.jsonl').open()];assert actual==records,'Original STA context changed after diagnostic transaction'
 if mode=='on':
  rows=(directory/'reservations.log').read_text().splitlines();held={};holds=releases=0
  for row in rows[:-1]:
   typ,n,r,c,x,y=row.split();key=int(n),int(r);c,x,y=map(int,[c,x,y])
   if typ=='HOLD':assert key not in held and y==x+c;held[key]=c;holds+=1
   else:assert typ=='RELEASE' and held.pop(key)==c and y==x-c;releases+=1
  assert rows[-1]=='COMPLETE 1 reservations_cleared' and not held and holds==releases and holds>0
 else:assert not (directory/'reservations.log').exists()
 results[mode]=dict(native_success=success,original_inputs_unchanged=True,original_STA_identical=True,reservations_cleared=True)
(b/'completion.json').write_text(json.dumps(dict(passed=True,results=results,seconds=time.monotonic()-start,source_sha256={str(p):sha(p) for p in [binary,arch,blif,Path(__file__),request,reserve]},qualification='Tiny actual native off/on bookkeeping regression. Does not establish BNN timing/quality benefit or all-architecture coverage; larger paired experiments remain required.'),indent=2)+'\n');print(results,flush=True)
