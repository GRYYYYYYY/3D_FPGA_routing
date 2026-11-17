"""Terminal-event successor; no new route/STA calls, no confirmation edits."""
from pathlib import Path
import os,sys,time,json,hashlib,fcntl
from measure_process_tree_v1 import measure
from recovery_prefix_v1 import live_identity
from seed_census_analysis_pool_v2 import process_identity
D=Path(__file__).resolve().parent;B=D/'S38584_postqueue_01';PRE=D/'S38584_complete_admission_01/queue'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def main():
 Q=B/'queue';Q.mkdir(parents=True,exist_ok=False);lock=(Q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files=[Path(__file__).resolve(),D/'finalize_s38584_admission_01.py',D/'S38584_complete_admission_01/plan.json',D/'cp1r6_s38584_pair_01/plan.json']
 bound={str(p):sha(p) for p in files};write(Q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,predecessor=str(PRE),new_native_or_STA_calls=0));write(Q/'status.json',dict(status='waiting_for_original_pair_and_three_admission_gates'))
 predecessor=read(PRE/'registration.json');start=time.monotonic()
 while not (PRE/'completion.json').exists():
  if not live_identity(predecessor['pid'],predecessor['start_ticks']):
   write(Q/'completion.json',dict(passed=False,status='predecessor_missing_without_terminal',new_native_or_STA_calls=0));return
  time.sleep(20)
 while live_identity(predecessor['pid'],predecessor['start_ticks']):time.sleep(2)
 assert all(sha(p)==h for p,h in bound.items());rows=[]
 for name,script in [('decision','finalize_s38584_admission_01.py')]:
  if name=='initial_scope_diagnosis' and read(D/'S38584_complete_admission_01/admission_decision.json')['complete_pair_admission']!='passed':
   rows.append(dict(stage=name,status='not_executed_pair_not_admitted'));break
  write(Q/'status.json',dict(status='running_readonly_terminal_followup',stage=name))
  m=measure([sys.executable,'-B',str(D/script)],B/name);rows.append(dict(stage=name,passed=m['passed'],complete_command_seconds=m['complete_command_wall_seconds'],native_or_STA_calls_new=0));write(B/'stages.json',rows)
  if not m['passed']:break
 write(Q/'completion.json',dict(passed=all(r.get('passed',True) for r in rows),stages=rows,wait_plus_queue_seconds=time.monotonic()-start,new_native_or_STA_calls=0,original_batches_unchanged=True));write(Q/'status.json',dict(status='terminal'));print(read(Q/'completion.json'),flush=True)
if __name__=='__main__':main()
