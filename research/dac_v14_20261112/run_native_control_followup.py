#!/usr/bin/env python3
"""Pressure-adjusted native witnesses and identical full-precision acceptance."""
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy import decide
b=D/'native_current_sta_control_dev_03';started=time.monotonic();costs=[]
initial=D/'native_endpoint_vector_dev_01/R1';rd=Path(read(initial/'completion.json')['run']);vector=read(initial/'endpoint_vector.json')
def invoke(cmd,tag):
    t=time.monotonic()
    with (b/(tag+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
    costs.append(dict(tag=tag,command=cmd,returncode=r.returncode,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
    assert r.returncode==0,'Preserve failed experiment; diagnose rather than repeat'
cmd=[sys.executable,str(D/'run_native_control_state_analysis_v3.py'),'--source',str(rd),'--batch',str(b/'R1'),'--native-cases',str(b/'R1_cases.txt'),'--pressure-start','10']
invoke(cmd,'native_pressure')
invoke([sys.executable,str(D/'audit_native_current_sta_control_v3.py'),'--native-state',str(b/'R1'),'--queries',str(D/'current_sta_policy_R1_01/queries_000'),'--out',str(b/'R1_witness_audit'),'--native-cases',str(b/'R1_cases.txt')],'witness_audit')
rows=read(D/'native_current_sta_control_dev_02/R1_witness_audit/analysis.json')['rows']+read(b/'R1_witness_audit/analysis.json')['rows']
cache={}
for completion in list((D/'native_endpoint_vector_dev_01').glob('*/completion.json'))+list((D/'current_sta_policy_R1_01').glob('evaluation_*/completion.json')):
    done=read(completion)
    if done['passed'] and done.get('full_precision_cpd_s') is not None:
        source=Path(done['run'])
        if all(sha(source/n)==sha(rd/n) for n in ['packed.net','placed.place']):cache[route_body(source/'routed.route')]=completion.parent
receipts=[]
for r in rows:
    if not r.get('candidate_route'):continue
    body=route_body(r['candidate_route']);state=cache.get(body);reused=bool(state)
    if not state:
        state=b/f'evaluation_{len(receipts):02d}_net{r["net"]}'
        invoke([sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',str(rd),'--batch',str(state),'--candidate-route',r['candidate_route']],state.name)
        cache[body]=state
    decisions={p:decide(p,vector,read(state/'endpoint_vector.json'),read(state/'completion.json')['passed']) for p in ['strict','endpoint_vector']}
    receipts.append(dict(net=r['net'],pin=r['pin'],mode=r['mode'],evaluation=str(state),reused_evaluation=reused,decisions=decisions))
    write(b/'decisions.json',receipts)
    print(r['net'],r['pin'],{p:(v['accepted'],v['reason']) for p,v in decisions.items()},flush=True)
write(b/'completion.json',dict(status='native_pressure_control_terminal',passed=True,results=receipts,
    complete_followup_seconds=time.monotonic()-started,processes=costs,
    qualification='Initial strongR1 single-connection opportunity control. Same current-STA selection/full-device/retained tree/acceptance; native pressure adapts after capacity rejection. Joint-native blocker recovery control still pending.',
    source_sha256={str(p):sha(p) for p in [Path(__file__),b/'registration.json',b/'process_costs.json',b/'decisions.json',b/'R1_witness_audit/analysis.json']}))
