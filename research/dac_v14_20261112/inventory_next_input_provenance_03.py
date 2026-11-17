"""Bounded input provenance inventory, without historical QoR-based selection."""
import datetime
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'independent_input_candidates_03';assert not out.exists()
repo=D.parents[1];runs=repo/'results/architecture_flow_20261027/runs'
matrix=D/'mechanism_selection_evidence_01/pairs.json'
cohort=D/'cp1r3_distinct_input_cohort_01/protocol.json'
known={r['native']['declared_physical_identity']['circuit'] for r in read(matrix)}
known.update(r['declared_physical_identity']['circuit_sha256'] for r in read(cohort)['selected_inputs'])
specs=[
 ('gemm_p0','training_gemm_layer_s11_hybrid_o_n200_w100_p0','gemm',
  'Different declared netlist/workload from the matched matrix and current cohort; known historical training source, not unseen.'),
 ('gemm_p1','training_gemm_layer_s11_hybrid_o_n200_w100_p1','gemm',
  'Same-circuit alternate placement candidate; only actual placement/root proof could establish a different start.'),
 ('tpu_os_p0','heldout_tpu_like.small.os_s21_hybrid_o_n60_w100_p0','tpu',
  'Different dataflow/netlist from TPU-WS; retain the same TPU workload-family label. Not a new architecture family.'),
 ('dla_medium_p0','heldout_dla_like.medium_s21_hybrid_o_n200_w100_p0','dla',
  'Scale variant of active DLA-small; not an independent new workload-family or architecture sample.')]
files=[Path(__file__).resolve(),matrix,cohort];rows=[]
for identifier,name,family,scope in specs:
    route=runs/(name+'_a0')/'manifest.json';packing=runs/(name+'_place')/'manifest.json'
    row=dict(id=identifier,source_name=name,workload_family=family,scope=scope,
        source_manifest_exists=route.exists(),packing_manifest_exists=packing.exists(),
        historical_QoR_used_for_selection=False,physical_bytes_verified=False,
        actual_placement_or_root_verified=False,execution_registered=False,
        independent_confirmed_samples_added=0)
    if not route.exists() or not packing.exists():
        row.update(status='missing_source_provenance',reason='Specified p1 source/packing manifests absent; no silent seed or placement substitution.')
        rows.append(row);continue
    assert route.stat().st_size<100_000 and packing.stat().st_size<100_000
    m=read(route);p=read(packing);cmd=m['command']
    copies=dict(architecture=Path(cmd[1]),circuit=Path(cmd[2]),graph=Path(cmd[cmd.index('--read_rr_graph')+1]),
        packed=route.parent/'packed.net',placement=route.parent/'placed.place')
    declared={k:m['shared_inputs'][str(copies[k])]['sha256'] for k in ['architecture','circuit','graph']}
    declared.update(packed=m['outputs']['packed.net']['sha256'],placement=m['outputs']['placed.place']['sha256'])
    assert all(m['outputs'][k]['sha256']==p['outputs'][k]['sha256'] for k in ['packed.net','placed.place'])
    merge=[c['command'][c['command'].index('--merge_constant_generators')+1] for c in [m,p]]
    assert merge==['off','off']
    row.update(status='metadata_consistent_pending_serial_byte_admission',declared_sha256=declared,
        outside_matrix_and_active_cohort_netlist=declared['circuit'] not in known,
        known_historical_input=True,source_packing_metadata_matches=True,
        physical_files={k:dict(path=str(v),exists=v.exists(),bytes=v.stat().st_size if v.exists() else None) for k,v in copies.items()},
        declared_input_bytes=sum(v.stat().st_size for v in copies.values() if v.exists()),
        architecture_family='two_layer_edge_encoded_Hybrid_O',different_size_is_new_architecture=False,
        explicit_SDC='--sdc_file' in cmd,application_timing_claim=False,source_route_will_be_imported=False)
    files.extend([route,packing]);rows.append(row)
assert rows[0]['outside_matrix_and_active_cohort_netlist']
out.mkdir();write(out/'inputs.json',rows)
write(out/'completion.json',dict(passed=True,observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_sha256={str(f):sha(f) for f in files},candidates=len(rows),metadata_consistent=3,missing_provenance=1,
    new_native_or_STA_calls=0,new_independent_results=0,current_queues_changed=False,
    decision='GEMM-p0 is the primary different-netlist candidate; audit large input cost/packing/placement and capacity before any prospective matched release. TPU-OS and DLA-medium remain labeled dataflow/scale variants. GEMM-p1 is unavailable as specified.',
    qualification='Small metadata only, retaining the missing candidate. No raw netlist/graph/packing/placement digest, different initial tree, feasible routing or resource gain is established. No QoR fields used to filter candidates; no new SDC/application requirement. Current CP1r3 and cost-baseline queues retain priority.'))
lines=['# 后续输入来源与独立性','',
 '本清单按来源和物理输入元数据筛选，不读取历史QoR用于选点。当前确认和已登记基线优先，未登记新执行。','',
 '| 候选 | 来源状态 | 输入文件总量(GiB) | 可计入的独立性范围 |','|---|---|---:|---|']
for r in rows:
    size=f"{r['declared_input_bytes']/1024**3:.2f}" if 'declared_input_bytes' in r else '--'
    lines.append('| '+r['id']+' | '+r['status']+' | '+size+' | '+r['scope']+' |')
lines += ['', 'GEMM-p0的声明网表不同于当前匹配矩阵和CP1r3，优先作为后续不同电路候选；其较大输入需要先做串行字节、资源与布局准入。GEMM-p1缺少指定来源，不以同初始树的新seed替代。TPU-OS保留TPU家族标识，DLA-medium保留规模变体标识。以上均未形成新的确认样本，也不增加论文收益或新架构数量。']
(out/'INPUT_SCOPE.md').write_text('\n'.join(lines)+'\n')
print(dict(passed=True,metadata_consistent=3,missing_provenance=1,candidate_input_GiB={r['id']:round(r.get('declared_input_bytes',0)/1024**3,3) for r in rows}))
