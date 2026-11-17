"""Wait for all current confirmation and necessary gates before input prep."""
from pathlib import Path
import os,sys,time,fcntl,json,hashlib,subprocess
from recovery_prefix_v1 import live_identity
from seed_census_analysis_pool_v2 import process_identity
D=Path(__file__).resolve().parent;U=D/'VTR_s38584_input_01';Q=U/'deferred_queue';P=D/'CLMA_IO_postqueue_01/queue'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def main():
 Q.mkdir(exist_ok=False);lock=(Q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);bound={str(p):sha(p) for p in [Path(__file__).resolve(),D/'prepare_s38584_input_01.py',U/'registration.json',P/'registration.json']}
 write(Q/'registration.json',dict(**process_identity(os.getpid()),predecessor=str(P),source_sha256=bound,route_queries=0));prior=read(P/'registration.json');start=time.monotonic();write(Q/'status.json',dict(status='waiting_for_clma_IO_pair_all_raw_and_terminal_decision'))
 while not (P/'completion.json').exists():
  if not live_identity(prior['pid'],prior['start_ticks']):write(Q/'completion.json',dict(passed=False,status='predecessor_missing_without_receipt',route_queries=0));return
  time.sleep(20)
 while live_identity(prior['pid'],prior['start_ticks']):time.sleep(2)
 assert all(sha(p)==h for p,h in bound.items());assert read(P/'completion.json')['passed'],'Preserve unexpected predecessor infrastructure failure; reconcile before new work'
 write(Q/'status.json',dict(status='executing_registered_pack_place_only'));wait=time.monotonic()-start
 with (Q/'prepare.log').open('x') as log:
  child=subprocess.Popen([sys.executable,'-B',str(D/'prepare_s38584_input_01.py')],stdout=log,stderr=subprocess.STDOUT);identity=process_identity(child.pid);write(Q/'active_child.json',dict(**identity,command='prepare_s38584_input_01.py'));code=child.wait()
 write(Q/'completion.json',dict(passed=code==0 and (U/'completion.json').exists() and read(U/'completion.json')['passed'],returncode=code,wait_for_original_required_queue_seconds=wait,wait_plus_preparation_seconds=time.monotonic()-start,route_queries=0,new_full_confirmation_roles=0,automatic_retry=False));write(Q/'status.json',dict(status='terminal'));print(read(Q/'completion.json'),flush=True)
if __name__=='__main__':main()
