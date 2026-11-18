"""Matched cost-only comparison at the first group of the interleaved BNN experiment."""
import fcntl
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from endpoint_timing_policy_streaming_v2 import compare
from multiobjective_acceptance_v2 import decide
from state_resource_assurance import require_publication_proof

out = D/'BNN_first_group_cost_01'
out.mkdir(exist_ok=False)
began = time.monotonic()
base = D/'BNN_interleaved_timing_03'
group = Path('flow/resource_flow/repair/round_000/candidate_00')
native, domain = [base/r/group for r in ('native_0','domain_0')]
reg = read(native/'registration.json')
role = reg['roles']['reuse_off']
guided = read(domain/'registration.json')['roles']['reuse_on']
worker = D/'vertical_cost_baseline_dev_01/run_vertical_cost_seed_analysis.py'
names = {'zero':0.,'half':.5,'two':2.}
request = Path(role['request'])
assert request.read_bytes()==Path(guided['request']).read_bytes()
for k in ['queries','removed_pins','seed_order','objective','original_budget','fixed_resource_limits']:
    assert role[k]==guided[k]
for n in ['routed.route','packed.net','placed.place']:
    # VPR output headers include a different absolute placement filename.
    a,b=[Path(r['source'])/n for r in (role,guided)]
    assert (route_body(a)==route_body(b)) if n=='routed.route' else sha(a)==sha(b)
state=Path(role['state'])
before=read(state/'endpoint_vector.json')
d_before=read(Path(guided['state'])/'endpoint_vector.json')
assert all(before[k]==d_before[k] for k in ['setup','hold','cpd_s','endpoint_ids','constraints_sha256'])
reg['roles']={name:role for name in names}
reg.update(scope='First selected K8 group, first N/D pair, same legal root. Weighted-cost binary is a joint-repair worker; full-flow timing and controller superiority are outside this contrast.',weights=names,zero_gate='candidate route, ordered query work, endpoint vectors, resources and decision',source_domain=str(domain),source_native=str(native))
write(out/'registration.json',reg)
(out/'empty.txt').write_text('0\n0\n0\n')
lock=(D/'critical_scope_runner.lock').open()
fcntl.flock(lock,fcntl.LOCK_EX)
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
stages=[]
def stage(tag,script,*args):
    assert shutil.disk_usage(out).free>=80*1024**3
    cmd=[sys.executable,'-B',str(script),*map(str,args)]
    start=time.monotonic()
    with (out/(tag+'.log')).open('x') as log:
        ret=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=2400)
    stages.append(dict(tag=tag,command=cmd,returncode=ret.returncode,seconds=time.monotonic()-start))
    write(out/'stages.json',stages)
    ret.check_returncode()

common=['--source',role['source'],'--objective',role['objective'],'--seed-order',role['seed_order'],'--candidate-full-sta']
stage('empty',worker,*common,'--native-cases',out/'empty.txt','--batch',out/'control','--vertical-cost-weight',0)
loaded=Path(read(out/'control/candidate_exports.json')['candidate'])/'routed.route'
rows={}
for name,weight in names.items():
    stage(name,worker,*common,'--native-cases',request,'--batch',out/name,'--expected-loaded-source-route',loaded,'--vertical-cost-weight',weight)
    audit=out/(name+'_audit')
    stage(name+'_scope',D/'audit_native_feedback_objective_cached.py','--batch',out,'--role',name,'--cache',reg['audit_cache'],'--output',audit)
    result=read(audit/'analysis.json')
    assert result['passed'] and read(out/name/'completion.json')['passed']
    if not result.get('candidate_route'):
        rows[name]=dict(weight=weight,status='rolled_back',queries=result['queries'])
        write(out/'rows.json',rows)
        assert weight!=0
        continue
    evaluation=out/(name+'_evaluation')
    stage(name+'_physical',D/'materialize_crossing_source_candidate_v1.py','--worker',out/name,'--output',evaluation,'--audited-route',result['candidate_route'],'--full-graph-cache',reg['full_graph_cache'])
    resources=require_publication_proof(evaluation)['resource_axes']
    after=read(evaluation/'endpoint_vector.json')
    old={k:role['original_budget'][k] for k in resources}
    decision=decide('resources_under_timing',before,after,old,resources,cpd_limit_s=role['original_budget']['CPD_s'],resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
    assert decision['endpoint_comparison']['compatible']
    if not weight:
        prior=read(native/'reuse_off_audit/analysis.json')
        assert result['candidate_sha256']==prior['candidate_sha256']
        for q,ref in zip(result['queries'],prior['queries'],strict=True):
            assert all(q[k]==ref[k] for k in ('net','pin','criticality','pushes','pops','feasible'))
        assert decision==read(native/'reuse_off_decisions.json')['resources_under_timing']
        vector=read(native/'reuse_off_evaluation/endpoint_vector.json')
        assert all(vector[k]==after[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    rows[name]=dict(weight=weight,resources=resources,cpd_ns=after['cpd_s']*1e9,decision=decision,queries=result['queries'],audit_sha256=sha(audit/'analysis.json'),worker_sha256=sha(out/name/'completion.json'),physical_sha256=sha(evaluation/'completion.json'))
    write(out/'rows.json',rows)
write(out/'completion.json',dict(passed=True,rows_sha256=sha(out/'rows.json'),stages_sha256=sha(out/'stages.json'),complete_imported_experiment_seconds=time.monotonic()-began,weights=names,route_queries_by_role={k:len(v['queries']) for k,v in rows.items()}))
