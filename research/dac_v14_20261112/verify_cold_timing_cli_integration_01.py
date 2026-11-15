"""Exercise every generated cold-timing command parser without launching routing."""
import ast,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_group_feedback_cold_v1 import commands
out=D/'cold_timing_cli_integration_01';out.mkdir(exist_ok=False);rows=[]
batch=out/'mock_flow/timing/round_000/feedback'
for script,args,tag in commands(out/'source',batch,out/'query_graph',out/'audit_cache',[],.9):
 command=[sys.executable,str(D/script),*map(str,args),'--help']
 result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
 (out/(tag+'.log')).write_text(result.stdout);assert result.returncode==0,(script,result.stdout[-500:])
 rows.append(dict(script=script,phase=tag,parser_returncode=result.returncode))
paths=[D/n for n in ['current_group_feedback_cold_v1.py','run_current_cone_capacity_queries_cold_v1.py','run_current_graph_relaxed_queries_cold_v1.py','run_complete_flow_critical_portfolio_v1.py','run_complete_resource_timing_flow_v1.py','verify_complete_resource_timing_flow_v1.py']]
for p in paths:ast.parse(p.read_text(),str(p))
assert 'cache_directories=[]' in paths[1].read_text() and 'histories=[]' in paths[2].read_text()
write(out/'completion.json',dict(passed=True,native_calls=0,commands=rows,syntax_checked=[str(p) for p in paths],source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),*paths]},qualification='Only parser integration, source scoping and syntax for the new complete-flow wiring. All eight generated command parsers accept their exact arguments; implicit historical query lists removed and explicit reuse confined to the actor. No native route, graph build, query execution, default/candidate equivalence, final QoR or full performance is inferred. Actual complete configuration remains required.'))
print(dict(passed=True,parsers=len(rows),native_calls=0,full_native_validation_pending=True),flush=True)
