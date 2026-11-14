#!/usr/bin/env python3
"""Read-only current-STA timing opportunity after stronger native resource convergence."""
import os,resource,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_group_feedback import commands
b=D/'strong_native_A0_timing_screen_01';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));state=D/'native_extra_opportunity_bnn_01/A0_observation';assert read(state/'completion.json')['passed'];feedback=b/'feedback';feedback.mkdir();old=D/'portfolio_execution_dev_01';reuse=[*old.glob('A0_*/round_*/feedback/capacity'),*old.glob('R1_*/round_*/feedback/capacity')];old_relaxed=[*old.glob('A0_*/round_*/feedback/relaxed'),*old.glob('R1_*/round_*/feedback/relaxed')];work=commands(state,feedback,D/'bnn_physical_query_graph_01',D/'rr_audit_cache_bnn_01',reuse,.9);prepared=[]
for script,args,tag in work:
 if script=='run_current_graph_relaxed_queries.py':
  script='run_current_graph_relaxed_queries_v2.py'
  for path in old_relaxed:args+=['--reuse-batch',path]
 prepared.append((script,args,tag))
files=[Path(__file__).resolve(),state/'completion.json',state/'endpoint_vector.json',D/'native_extra_opportunity_bnn_01/completion.json',D/'current_group_feedback.py',*[D/script for script,_,_ in prepared],D/'query_critical_owner_exchange.py',D/'expand_critical_owner_scope.py'];bound={str(p):sha(p) for p in files};write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_state=str(state),source_sha256=bound,question='Does the stronger native A0 low-wire/vertical state retain current-STA timing opportunities, and can native critical-owner closure combine the known timing mechanism with native convergence resource savings?',current_root=dict(CPD_ns=13.607436066820355,wirelength=2059567,SB_pairs=94,CB_sources=5062),cache_reuse_capacity=list(map(str,reuse)),cache_reuse_relaxed=list(map(str,old_relaxed)),native_calls=0,route_calls=0,qualification='New source state with changed actual routing/occupancy; reuse exact matching query fingerprints and graph/core seals. Read-only mechanism screen, no final native replacement or assumed combination benefit. Existing quality/large-backend/bundle queues unchanged. Per-child query/CPU/memory protection, no overall research stopping condition.'))
costs=[]
def run(script,args,tag):
 t=time.monotonic();cmd=[sys.executable,str(D/script),*map(str,args)]
 with (b/(tag+'.log')).open('w') as out:
  proc=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(pid=proc.pid,start_ticks=Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19],tag=tag,command=cmd))
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);write(b/'progress.json',dict(last_terminal_stage=tag,returncode=code));assert code==0,tag
for script,args,tag in prepared:run(script,args,tag)
run('query_critical_owner_exchange.py',['--feedback',feedback,'--output',b/'critical_exchange','--audit-cache',D/'rr_audit_cache_bnn_01','--query-graph',D/'bnn_physical_query_graph_01'],'critical_owner_exchange')
exchange=read(b/'critical_exchange/completion.json')
if exchange['rows']:run('expand_critical_owner_scope.py',['--diagnostic',b/'critical_exchange','--feedback',feedback,'--output',b/'exchange_expansion','--audit-cache',D/'rr_audit_cache_bnn_01'],'critical_owner_closure')
assert all(sha(p)==h for p,h in bound.items());write(b/'completion.json',dict(passed=True,source_state=str(state),direct_group_plan=str(feedback/'proposal/plan.json'),critical_exchange=str(b/'critical_exchange/completion.json'),expanded_closure=str(b/'exchange_expansion/completion.json') if exchange['rows'] else None,native_calls=0,route_calls=0,complete_offline_screen_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',feedback/'cone.json',feedback/'capacity/analysis.json',feedback/'relaxed/analysis.json',feedback/'owners/completion.json',feedback/'protected/completion.json',feedback/'proposal/plan.json',b/'critical_exchange/completion.json',*([b/'exchange_expansion/completion.json'] if exchange['rows'] else [])]},qualification='Current-state optimistic timing/closure diagnostics only. No candidate accepted, actual combination benefit or complete-configuration speedup inferred. Fixed old result code/inputs and active queues remain untouched.'))
print(dict(passed=True,plan=read(feedback/'proposal/plan.json')['selection'],critical_exchange_rows=len(exchange['rows'])),flush=True)
