#!/usr/bin/env python3
"""Actual native resource counters versus existing and fresh independent physical audits."""
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from actual_route_tree_identity import tree_identity
from endpoint_timing_policy_streaming_v2 import load
from run_native_scope_policy_v4 import run_dir

b=D/'native_resource_census_eltwise_02'
b.mkdir(exist_ok=False)
started=time.monotonic()
assert read(D/'repair_seed_order_eltwise_01/completion.json')['passed']
source=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation'
tx=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_001/candidate_00'
reference=D/'repair_seed_order_eltwise_01/delay_rr_id_canonical_independent_LOAD'
assert read(reference/'completion.json')['passed']
files=[Path(__file__).resolve(),D/'run_native_census_analysis.py',D/'native_resource_census_stage_01/binding.json',
    D/'repair_seed_order_eltwise_01/completion.json',source/'completion.json',source/'endpoint_vector.json',
    reference/'completion.json',reference/'endpoint_vector.json',run_dir(reference)/'independent_audit.json',tx/'request.txt',tx/'domain.txt']
bound={str(path):sha(path) for path in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    source_sha256=bound,question='Does opt-in C++ census exactly match independently audited planar wire/SB/CB counts, including per-net occupancies and crossing edge kinds, without changing actual routes/search/STA?',
    fixed='Same source, request, retained-crossing domain and delay/RR-ID seed order; counter flag0/1 only. Source/candidate/restored counts have explicit state kinds and native assurance labels.',
    limits=dict(this_chain_native_VPR_maximum=1,combined_with_BNN_parent_child_maximum=3,child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Recovery reuses two sealed valid native workers after correcting an overstrict full-file comparison of private placement header paths; ordered route bodies must remain exactly equal. Old failed guard and original cost retained, no repair searches repeated. Native counter validation, not a replacement independent audit or a whole-algorithm speedup. Reuse existing physical reference only after exact topology/vector/static input binding. One new independent same-binary candidate LOAD/physical audit is separately charged.'))
records=[]
def invoke(name,counter,repair=True,candidate=None):
    if name in ['counter_off','counter_on']:
        prior=D/'native_resource_census_eltwise_01'
        original=read(prior/'registration.json')
        assert all(sha(path)==digest for path,digest in original['source_sha256'].items())
        state=prior/name
        assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
        rd=run_dir(state);m=read(rd/'manifest.json');r=read(state/'registration.json')
        assert r['native_resource_census'] is counter and r['seed_order']=='delay_rr_id'
        assert m['environment']['VPR_H3D_RESOURCE_CENSUS']==('1' if counter else '0')
        assert sha(m['command'][0])==read(D/'native_resource_census_stage_01/binding.json')['binary_sha256']
        records.append(dict(case=name,reused=True,new_native_calls=0,origin=str(state),historical_creation_time_borrowed=False))
        write(b/'process_costs.json',records)
        return rd
    output=b/name
    command=[sys.executable,str(D/'run_native_census_analysis.py'),'--source',str(run_dir(source)),'--batch',str(output)]
    if repair:command += ['--native-cases',str(tx/'request.txt'),'--crossing-domain',str(tx/'domain.txt'),'--seed-order','delay_rr_id']
    if counter:command += ['--native-census']
    if candidate:command += ['--candidate-route',str(candidate)]
    t=time.monotonic()
    with (b/(name+'.log')).open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(b/'status.json',dict(case=name,pid=process.pid,start_ticks=Path('/proc',str(process.pid),'stat').read_text().split(') ',1)[1].split()[19]))
        code=process.wait()
    records.append(dict(case=name,returncode=code,complete_process_seconds=time.monotonic()-t))
    write(b/'process_costs.json',records)
    assert code==0 and read(output/'completion.json')['passed'],name
    return run_dir(output)

def check(native,kind,state):
    path=native/'native_sta_frontier.jsonl.resources.json'
    data=read(path)
    assert data['schema_version']==1 and data['assurance_kind']=='native_actual_route_tree_census' and data['state_kind']==kind
    expected=read(run_dir(state)/'independent_audit.json')
    assert expected['audit']['passed']
    for key,value in data['physical_metrics'].items():assert value==expected['physical_metrics'][key],(kind,key,value,expected['physical_metrics'].get(key))
    assert all(isinstance(data['physical_metrics'][key],int) and data['physical_metrics'][key]>=0 for key in
        ['planar_wirelength_excluding_sb_half_nodes','sb_pairs_used','sb_pair_net_occupancy','cb_crossing_output_sources_used','cb_crossing_output_source_net_occupancy'])
    return data

off=invoke('counter_off',False)
on=invoke('counter_on',True)
assert not list(off.rglob('*.resources.json'))
for part in ['.','candidate','candidate_restored']:
    for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
        assert sha(off/part/suffix)==sha(on/part/suffix)
    if part!='.':assert route_body(off/part/'routed.route')==route_body(on/part/'routed.route'),'Ordered body differs beyond expected private placement header'
assert (off/'search_cost.log').read_bytes()==(on/'search_cost.log').read_bytes()
assert (off/'actual_seed.log').read_bytes()==(on/'actual_seed.log').read_bytes()
assert tree_identity(on/'candidate/routed.route')==tree_identity(run_dir(reference)/'routed.route')
vector=load(on/'candidate/native_sta_frontier.jsonl')
oldvector=read(reference/'endpoint_vector.json')
assert all(vector[key]==oldvector[key] for key in ['cpd_s','setup','hold','constraints_sha256'])
counts=dict(input=check(on,'input',source),candidate=check(on/'candidate','candidate',reference),
    restored=check(on/'candidate_restored','restored_source',source))
plain=invoke('plain_input_counter',True,repair=False)
counts['plain_input']=check(plain,'input',source)
independent=invoke('independent_actual_candidate_LOAD_and_physical_audit',True,repair=False,candidate=on/'candidate/routed.route')
assert read(independent/'independent_audit.json')['audit']['passed']
for key,value in counts['candidate']['physical_metrics'].items():assert value==read(independent/'independent_audit.json')['physical_metrics'][key]
for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
    assert sha(on/'candidate'/suffix)==sha(independent/suffix)
assert all(sha(path)==digest for path,digest in bound.items())
write(b/'completion.json',dict(passed=True,counter_toggle_routes_actual_seed_trace_sink_costs_FULLSTA_exact=True,
    source_candidate_restored_and_plain_input_counts_match_independent_audit=True,
    all_planar_wire_SB_CB_net_occupancies_and_crossing_kinds_exact=True,independent_same_binary_candidate_LOAD_and_physical_audit_pass=True,
    counts=counts,native_processes=sum(not row.get('reused',False) for row in records),reused_native_processes=sum(row.get('reused',False) for row in records),complete_component_validation_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),b/'registration.json',b/'process_costs.json',independent/'independent_audit.json']},
    qualification='New native resource counts remain explicitly distinct from independent audit. Opt-in counter does not change source/candidate/frontier/search/seed choices in this actual case. Accepted resource metrics may later consume the bound counter, but that faster consumer and end-of-actor independent validation are not implemented by this experiment. No whole-algorithm speed claim.'))
print(dict(passed=True,candidate=counts['candidate']['physical_metrics'],native_processes=len(records)),flush=True)
