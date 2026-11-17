"""Read-only native import probe; expected missing route is not legal routing."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,json,sys,time
from retained_prefix_workflow import D,read,write,sha
from measure_process_tree_v1 import measure
P=D/'VTR_diffeq_p1_input_02';B=D/'diffeq_p1_native_import_probe_01'
def main():
 assert not B.exists();B.mkdir();start=time.monotonic();plan=read(P/'registration.json');cap=read(P/'capacity_selection.json');prior=read(P/'queue/completion.json');place=read(P/'place_01/execution_completion.json');assert not prior['passed'] and place['passed']
 fixture=cap['selected_fixture'];binary=plan['binary']['path'];p1net=P/'place_01/packed.net';p1place=P/'place_01/placed.place';blif=P/'inputs/diffeq.blif';sdc=P/'inputs/diffeq.sdc';missing=B/'intentionally_missing.route';assert not missing.exists()
 cmd=[binary,fixture['architecture'],str(blif),'--analysis','--device','fixture','--route_chan_width','100','--num_workers','1','--seed','21','--clock_modeling','ideal','--verify_file_digests','off','--read_rr_graph',fixture['graph'],'--timing_report_npaths','0','--net_file',str(p1net),'--place_file',str(p1place),'--route_file',str(missing),'--merge_constant_generators','off','--sdc_file',str(sdc)]
 files=[Path(__file__).resolve(),P/'registration.json',P/'queue/completion.json',P/'place_01/registration.json',P/'place_01/execution_completion.json',Path(binary),Path(fixture['architecture']),Path(fixture['graph']),p1net,p1place,blif,sdc];bound={str(p):sha(p) for p in files};write(B/'registration.json',dict(registered_at=datetime.now(timezone.utc).isoformat(),command=cmd,source_sha256=bound,purpose='Observe frozen native reader compatibility with real P1 packed/place files; missing route is intentional; cannot establish native FULL or route quality.',new_route_queries_planned=0,automatic_retry=False))
 env=dict(__import__('os').environ);__import__('os').chdir(B)
 try:m=measure(['/usr/bin/prlimit','--as=68719476736','--',*cmd],B/'measurement')
 finally:__import__('os').chdir(D.parents[1])
 assert not m['live_descendants_after_command_exit'];assert all(sha(p)==h for p,h in bound.items());log=(B/'measurement/stdout.log').read_text(errors='replace');write(B/'completion.json',dict(execution_ended=True,command_returncode=m['returncode'],complete_command_seconds=m['complete_command_wall_seconds'],actual_stdout_sha256=sha(B/'measurement/stdout.log'),native_route_FULL_passed=False,route_quality_admitted=False,source_sha256=bound,qualification='Raw native import diagnostic only; classify actual log separately. Deliberately absent route cannot be promoted to a full route or successful confirmation.'))
 print(json.dumps(dict(execution_ended=True,returncode=m['returncode'],seconds=m['complete_command_wall_seconds'],route_quality_admitted=False)))
if __name__=='__main__':
 with (D/'critical_scope_runner.lock').open() as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
