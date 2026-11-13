#!/usr/bin/env python3
"""Read-only contract reconciliation; no graph parsing, solver, or experiment writes."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, math

P=Path(__file__).resolve().parent
ROOT=P.parents[1]
A=ROOT/'results/architecture_flow_20261027'
B=A/'serial_strict_reexecution_20261103'
bindings={};cache={};coords_cache={};checks=[]
def read_bytes(path):
    p=Path(path).resolve();s=p.stat();before=(s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    raw=p.read_bytes();s=p.stat();assert before==(s.st_size,s.st_mtime_ns,s.st_ctime_ns),str(p)
    bindings[str(p)]=hashlib.sha256(raw).hexdigest()
    return raw
def read(path):
    key=str(Path(path).resolve())
    if key not in cache:cache[key]=json.loads(read_bytes(path))
    return cache[key]
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
def coordinates(path):
    key=str(Path(path).resolve())
    if key not in coords_cache:
        rows={}
        for line in read_bytes(path).decode().splitlines():
            if not line.strip() or line.startswith(('#','Netlist','Array')):continue
            f=line.split('#')[0].split();assert len(f)==5 and f[0] not in rows
            rows[f[0]]=tuple(map(int,f[1:]))
        assert rows
        coords_cache[key]=(len(rows),hashlib.sha256(json.dumps(sorted(rows.items()),separators=(',',':')).encode()).hexdigest())
    return coords_cache[key]

models=[]
for path in sorted((A/'benchmark_models').glob('*/manifest.json')):
    model=read(path);label=path.parent.name;size=model['size'];span=size-2
    slots=dict(clb=2*span*span-2*span*(len(range(2,size-1,8))+len(range(4,size-1,8))),complex_dsp=2*span*len(range(2,size-1,8)),spram=2*span*len(range(4,size-1,8)),io=64*span)
    check('model_ready:'+label,model['status']=='ready' and set(model['fixtures'])=={'sb','cb_o','hybrid_o','matched_2d'})
    audits={};rows=[]
    for family,fixture in model['fixtures'].items():
        audit=read(fixture['physical_audit']);audits[family]=audit;conv=fixture['conversion']
        check('model_binding:'+label+'/'+family,audit['graph_sha256']==conv['source_graph_sha256'] and audit['architecture_sha256']==conv['source_architecture_sha256'] and audit['graph']==fixture['original_graph'])
        check('model_capacities:'+label+'/'+family,audit['logical_slots']==model['logical_slots']==slots)
        check('model_zero_rc_pairs:'+label+'/'+family,audit['schema_version']==2 and audit['unpaired_sb_nodes']==0 and audit['nonzero_node_RC_count']==0 and audit['sb_pair_nodes']==2*audit['sb_pair_count'])
        switches={v['name']:v for v in audit['switches'].values()}
        check('full_sb_delay_sum:'+label+'/'+family,all(math.isclose(sum(float(switches[n]['timing'].get('Tdel',0)) for n in row['switch_names']),row['seconds'],rel_tol=1e-12) for row in audit['sb_full_transition_delay_histogram']))
        schema_count=fixture.get('native_schema_exact_records',fixture.get('native_schema_check',{}).get('exact_compared_lines',0))
        schema_unit='records' if 'native_schema_exact_records' in fixture else 'lines'
        check('schema_receipt:'+label+'/'+family,schema_count>audit['total_nodes']+audit['total_edges'] and fixture.get('native_schema_check',{}).get('passed',True))
        rows.append(dict(family=family,sb_pairs=audit['sb_pair_count'],cb_output_sources=audit['cb_crossing_source_rr_nodes'],cross_layer_edges=audit['cross_layer_edges'],planar_wire_capacity=audit['wire_resources']['total_planar_wire_unit_capacity'],full_sb_delay_ns=sorted({r['seconds']*1e9 for r in audit['sb_full_transition_delay_histogram']}),cb_switch_delay_ns=sorted({float(audit['switches'][str(r['switch'])]['timing'].get('Tdel',0))*1e9 for r in audit['crossing_delay_histogram'] if r['edge_type'].startswith('OPIN')}),zero_indegree_clock_ipins=audit['zero_indegree_clock_ipins'],schema_comparison_count=schema_count,schema_comparison_unit=schema_unit))
    check('common_plane_inventory:'+label,model['same_plane_exact'] and audits['sb']['wire_resources']==audits['cb_o']['wire_resources']==audits['hybrid_o']['wire_resources'])
    check('crossing_inventory:'+label,audits['sb']['sb_pair_count']==audits['hybrid_o']['sb_pair_count'] and audits['cb_o']['cb_crossing_source_rr_nodes']==audits['hybrid_o']['cb_crossing_source_rr_nodes'] and audits['cb_o']['sb_pair_count']==0 and audits['sb']['cb_crossing_source_rr_nodes']==0 and not audits['matched_2d']['cross_layer_edges'])
    ratio=audits['matched_2d']['wire_resources']['total_planar_wire_unit_capacity']/audits['sb']['wire_resources']['total_planar_wire_unit_capacity']
    check('2d_inventory_ratio:'+label,math.isclose(ratio,model['planar_wire_2d_over_3d'],rel_tol=1e-12))
    models.append(dict(model=label,size=size,width=model['width'],logical_slots=slots,planar_2d_over_3d=ratio,rows=rows))

protocol=read(B/'benchmark_protocol.json');capacity=read(B/'capacity_selection.json')
observations=read(B/'evaluation_analysis/role_observations.json')['rows']
unique={r['run']:r for r in observations if r['run'] and r['status']=='legal'}
pairs=[]
for name,row in unique.items():
    d=B/'runs'/name;m=read(d/'manifest.json');pair=read(d/'pair_check.json');source=Path(pair['source'])
    placement=read(source/'manifest.json');pc=read(source/'placement_check.json');tags=m['tags'];command=m['command']
    model=read(B/'benchmark_models'/f"n{tags['size']}_w{tags['width']}"/'manifest.json')
    fixture=model['fixtures'][tags['family']];conv=fixture['conversion'];legacy=tags['router']=='B2'
    graph=fixture['original_graph'] if legacy else conv['graph'];arch=fixture['architecture'] if legacy else conv['architecture']
    graph_hash=conv['source_graph_sha256'] if legacy else conv['graph_sha256'];arch_hash=conv['source_architecture_sha256'] if legacy else conv['architecture_sha256']
    binary=protocol['binaries'][tags['router']]
    # Input packed-file bytes remain part of the explicit large-file audit gap.
    packed=m['outputs']['packed.net']['sha256']
    coordinate_equal=coordinates(d/'placed.place')==coordinates(source/'placed.place')
    conditions=dict(pair_receipt=pair['passed'] and all(pair['checks'].values()),packed_binding=packed==placement['outputs']['packed.net']['sha256']==m['private_input_sha256'][str(d.resolve()/'packed.net')]==m['shared_inputs'][str(source/'packed.net')]['sha256'],placement_coordinates=coordinate_equal,placement_digest=bindings[str((d/'placed.place').resolve())]==m['outputs']['placed.place']['sha256'],placement_semantics=pc['passed'] and pc['packed_semantic']['semantic_sha256']==capacity['circuits'][tags['circuit']]['semantic_sha256'],graph_choice=command[command.index('--read_rr_graph')+1]==graph and m['shared_inputs'][graph]['sha256']==graph_hash==row['graph_sha256'],architecture_choice=command[1]==arch and m['shared_inputs'][arch]['sha256']==arch_hash,binary_choice=command[0]==binary['path'] and m['shared_inputs'][binary['path']]['sha256']==binary['sha256'],source_graph_binding=row['original_graph_sha256']==conv['source_graph_sha256'])
    check('legal_pair_contract:'+name,all(conditions.values()),conditions)
    pairs.append(dict(run=name,router=tags['router'],source=str(source),conditions=conditions))

serial=read(B/'serial_analysis/summary.json');registration=read(B/'serial_protocol.json')
serial_names=set();serial_guards=[]
for case in serial['cases']:
    repeat_coordinates=[]
    for repeat in case['repeats']:
        serial_names.add(repeat['setup']['run'])
        if repeat['setup']['status']=='completed':repeat_coordinates.append(coordinates(B/'runs'/repeat['setup']['run']/'placed.place'))
        serial_names.update(r['run'] for r in repeat['routes'].values())
    check('serial_repeat_coordinates:'+str((case['circuit'],case['family'],case['flow'])),len(set(repeat_coordinates))==1 and len(repeat_coordinates)==3)
for name in sorted(serial_names):
    d=B/'runs'/name;m=read(d/'manifest.json');e=m['thread_enforcement'];launch=m['launch_command'];o=m['process_tree_observation']
    conditions=dict(method=e['method']=='seccomp_guard_no_ptrace' and 'thread_syscall_trace' not in m,guard=e['guard']['sha256']==registration['guard_sha256'] and not e['top_level_sigsys_observed'],runner=m['runner_sha256']==registration['timing_runner_sha256'],launch=launch[4:8]==['/usr/bin/prlimit','--as=68719476736:68719476736','--core=0:0','--'] and launch[8]==str(B.resolve()/'execution_scripts/seccomp_thread_guard') and launch[9:]==m['command'],observation=o['samples']>0 and bool(o['processes']) and o['peak_threads']<=1 and not o['violation_observed'])
    check('serial_execution_contract:'+name,all(conditions.values()),conditions)
    serial_guards.append(dict(run=name,conditions=conditions))
serial_intervals=[(datetime.fromisoformat(read(B/'runs'/n/'manifest.json')['start_utc']),datetime.fromisoformat(read(B/'runs'/n/'manifest.json')['finish_utc']),n) for n in serial_names]
lo=min(x[0] for x in serial_intervals);hi=max(x[1] for x in serial_intervals)
intervals=[];examined=0
# Exclude manifests whose own start is after the whole serial window. These
# may belong to the ongoing queue and are neither bound nor treated as closed.
for path in (B/'runs').glob('*/manifest.json'):
    m=json.loads(path.read_text());examined+=1
    if not m.get('start_utc'):continue
    start=datetime.fromisoformat(m['start_utc'])
    if start>=hi:continue
    if m.get('finish_utc'):
        end=datetime.fromisoformat(m['finish_utc'])
        if end<=lo:continue
    else:end=hi
    m=read(path);intervals.append((start,end,m['name']))
overlaps=[]
for start,end,name in serial_intervals:
    for a,z,other in intervals:
        if name!=other and max(start,a)<min(end,z):overlaps.append((name,other))
check('serial_no_registered_overlap',not overlaps,overlaps)
check('serial_process_count',len(serial_names)==180==serial['isolation']['checked_serial_processes'])
proof=read(B/'seccomp_full_workload_validation.json')
check('serial_guard_receipt',proof['status']=='passed' and set(proof['covered_workloads'])>={'A0','R1','B2','P1'} and bindings[str((B/'seccomp_full_workload_validation.json').resolve())]==registration['guard_validation_sha256'])
for path in [__file__,ROOT/'scripts/validate_flatland_pilots.py',ROOT/'scripts/audit_flatland_graphs.py',B/'execution_scripts/analyze_flatland_evaluation.py',B/'execution_scripts/analyze_flatland_serial_candidate.py']:
    read_bytes(path)
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='passed_with_explicit_scope_limits' if all(c['passed'] for c in checks) else 'issues_found',checks=checks,models=models,legal_pair_count=len(pairs),legal_pair_by_router=dict(Counter(x['router'] for x in pairs)),legal_pairs=pairs,serial=dict(process_count=len(serial_names),examined_manifest_count=examined,overlaps=overlaps,window_utc=[lo.isoformat(),hi.isoformat()],guards=serial_guards),source_sha256=bindings,limitations=['Physical inventory is reconciled from saved per-graph audits; full graph equality and packed-file bytes await large-file integrity closure.','Exact common-plane and native-schema comparisons are archived preparation receipts, not newly rerun graph comparisons.','The physical audits provide crossing-output inventories and examples, not exhaustive per-pin exit or layer-direction histograms.','No exclusive-host or unrecorded-process isolation claim; serial isolation covers registered study process intervals only.','No solver execution and no mutation of frozen experiment files.'])
(P/'data/comparison_contract_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'],'checks',len(checks),'models',len(models),'legal pairs',len(pairs),'serial processes',len(serial_names),'source files',len(bindings),flush=True)
for c in checks:
    if not c['passed']:print('FAILED',c,flush=True)
raise SystemExit(0 if result['status']!='issues_found' else 1)
