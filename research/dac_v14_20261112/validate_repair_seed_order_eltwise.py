#!/usr/bin/env python3
"""Cross source representation with explicit seed order and independently observe all candidates."""
import collections
import hashlib
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from actual_route_tree_identity import tree_identity
from endpoint_timing_policy_streaming_v2 import load,compare
from run_native_scope_policy_v4 import run_dir

b=D/'repair_seed_order_eltwise_01'
b.mkdir(exist_ok=False)
started=time.monotonic()
assert read(D/'repair_seed_order_tiny_01/completion.json')['passed']
sources=dict(canonical=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation',
             native=D/'fused_resource_development_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation')
source_trees={key:tree_identity(run_dir(state)/'routed.route') for key,state in sources.items()}
assert source_trees['canonical']==source_trees['native']
tx=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_001/candidate_00'
request,domain=tx/'request.txt',tx/'domain.txt'
files=[Path(__file__).resolve(),D/'run_seed_policy_native_analysis.py',D/'actual_route_tree_identity.py',
    D/'repair_seed_order_stage_01/binding.json',D/'repair_seed_order_tiny_01/completion.json',
    D/'serialization_order_diagnostic_02/completion.json',request,domain]
for state in sources.values():files += [state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'routed.route',run_dir(state)/'manifest.json']
bound={str(path):sha(path) for path in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bound,
    question='Does changing only per-query native seed insertion order remove the already causal source-serialization sensitivity? Do real finite native sink cost labels support equal-cost choice versus changed primary search quality?',
    policies=['native','rr_id','delay_rr_id'],sources={key:str(value) for key,value in sources.items()},
    fixed='Same binary, physical graph/net/packing/placement/SDC, source topology/full vector, pruned sinks, criticalities, query order, retained-crossing domain and release rule. Only explicit seed insertion policy and source representation vary.',
    limits=dict(this_chain_native_processes_at_once=1,combined_with_running_BNN_parent_child_maximum=3,child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Independent six-arm mechanism intervention after tiny regression; not a full algorithm configuration or a per-circuit best-policy choice. Additional independent candidate LOAD/physical audits are validation-only and separately timed. Existing running cohort untouched.'))
costs=[];results={}
def invoke(args,tag):
    t=time.monotonic()
    with (b/(tag+'.log')).open('w') as log:
        process=subprocess.Popen([sys.executable,str(D/'run_seed_policy_native_analysis.py'),*map(str,args)],stdout=log,stderr=subprocess.STDOUT)
        write(b/'status.json',dict(tag=tag,pid=process.pid,start_ticks=Path('/proc',str(process.pid),'stat').read_text().split(') ',1)[1].split()[19]))
        code=process.wait()
    costs.append(dict(tag=tag,returncode=code,complete_process_seconds=time.monotonic()-t))
    write(b/'process_costs.json',costs)
    assert code==0,tag

def parse_costs(path):
    rows=[]
    for line in path.read_text().splitlines():
        row=line.split();assert len(row)==12 and row[0]=='COST'
        found=bool(int(row[6]));feasible=bool(int(row[7]))
        path_cost,backward=map(float,row[8:10])
        assert not found or (math.isfinite(path_cost) and math.isfinite(backward))
        assert float(row[11])==0.,'Registered native repair uses Dijkstra, not positive-A* lookahead'
        rows.append(dict(net=int(row[1]),pin=int(row[2]),order=int(row[3]),pass_index=int(row[4]),pressure=float(row[5]),
            found=found,feasible=feasible,native_total_cost=path_cost if found else None,
            native_backward_cost=backward if found else None,criticality=float(row[10]),astar_fac=float(row[11])))
    return rows

for policy in ['native','rr_id','delay_rr_id']:
    for label,source in sources.items():
        assert all(sha(path)==digest for path,digest in bound.items())
        key=policy+'_'+label
        output=b/key
        invoke(['--source',run_dir(source),'--batch',output,'--native-cases',request,'--crossing-domain',domain,
                '--objective','weighted_soft','--seed-order',policy],key)
        c=read(output/'completion.json');assert c['passed']
        native=run_dir(output);actual=native/'candidate'
        assert (actual/'native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
        assert (native/'candidate_restored/native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
        for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
            assert sha(native/suffix)==sha(native/'candidate_restored'/suffix)
        actual_tree=tree_identity(actual/'routed.route')
        actual_vector=load(actual/'native_sta_frontier.jsonl')
        independent=b/(key+'_independent_LOAD')
        invoke(['--source',run_dir(source),'--batch',independent,'--candidate-route',actual/'routed.route'],key+'_validation_only_independent_LOAD_and_physical_audit')
        independent_c=read(independent/'completion.json');assert independent_c['passed']
        rd=run_dir(independent)
        for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
            assert sha(actual/suffix)==sha(rd/suffix)
        physical=read(rd/'independent_audit.json');assert physical['audit']['passed']
        resources=physical['physical_metrics']
        cpdcosts=parse_costs(native/'search_cost.log')
        seeds=(native/'actual_seed.log').read_text().splitlines()
        blocks=collections.defaultdict(list)
        for line in seeds:
            row=line.split();assert row[0]=='SEED' and len(row)==9
            blocks[(int(row[1]),int(row[2]),float(row[4]))].append((int(row[5]),float(row[6]),float(row[7]),float(row[8])))
        normalized_costs=[{k:v for k,v in row.items() if k!='order'} for row in cpdcosts]
        tree_digest=hashlib.sha256(str(sorted(actual_tree.items())).encode()).hexdigest()
        results[key]=dict(policy=policy,source_kind=label,native_source_observation=str(output),
            actual_candidate=str(actual/'routed.route'),independent_candidate_state=str(independent),
            actual_tree_identity_sha256=tree_digest,CPD_ns=actual_vector['cpd_s']*1e9,
            resources=dict(wirelength=resources['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=resources['sb_pairs_used'],CB_sources=resources['cb_crossing_output_sources_used']),
            native_costs=normalized_costs,seed_rows_count=len(seeds),
            net6719_seed_blocks={str(group):value for group,value in blocks.items() if group[0]==6719},
            complete_endpoint_vector_comparison_to_source=compare(read(source/'endpoint_vector.json'),read(independent/'endpoint_vector.json')),
            native_artifact_sha256={str(path):sha(path) for path in [actual/'routed.route',actual/'native_sta_frontier.jsonl',native/'joint_native.log',native/'search_cost.log',native/'actual_seed.log',actual/'native_state_gate.txt',rd/'independent_audit.json']})
        write(b/'results.json',results)
invariance={}
for policy in ['native','rr_id','delay_rr_id']:
    left,right=(results[policy+'_'+label] for label in ['canonical','native'])
    lv,rv=(read(Path(row['independent_candidate_state'])/'endpoint_vector.json') for row in [left,right])
    invariance[policy]=dict(actual_candidate_topology_same=left['actual_tree_identity_sha256']==right['actual_tree_identity_sha256'],
        complete_endpoint_vectors_same=all(lv[k]==rv[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']),
        real_native_cost_rows_same=left['native_costs']==right['native_costs'],
        net6719_actual_seed_blocks_same=left['net6719_seed_blocks']==right['net6719_seed_blocks'],
        resources_same=left['resources']==right['resources'])
assert all(sha(path)==digest for path,digest in bound.items())
write(b/'completion.json',dict(passed=True,invariance=invariance,results=results,actual_native_workers=6,
    validation_only_independent_candidate_LOAD_calls=6,complete_mechanism_validation_seconds=time.monotonic()-started,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),b/'registration.json',b/'results.json',b/'process_costs.json']},
    complete_single_configuration_algorithm_seconds=None,
    qualification='Actual six-arm source-by-policy experiment and six independent candidate LOAD/FULLSTA/physical audits. Invariance results are observed, not forced to pass. Costs come from real rr_node_route_inf sink labels before reset, never uninitialized RTExploredNode cost fields. Stable seed policy is a determinism/control intervention, not yet a broadly beneficial resource heuristic. No extrapolation to arbitrary RCV/flat routing or full cold timings.'))
print(dict(passed=True,invariance=invariance,resources={key:row['resources'] for key,row in results.items()}),flush=True)
