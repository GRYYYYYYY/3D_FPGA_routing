#!/usr/bin/env python3
"""Bind native all-pin observer evidence and update the paper without rerouting."""
import csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

b = D / 'native_sta_frontier_dev_03'
v = read(b / 'frontier_validation.json')
m = read(b / 'frontier_mechanism_analysis.json')
c = read(b / 'completion.json')
h = read(b / 'guided_history_identity.json')
assert v['passed'] and m['passed'] and c['passed'] and h['passed']
assert all(sha(p) == expected for p, expected in v['source_sha256'].items())
assert all(sha(p) == expected for p, expected in m['source_sha256'].items())
stage = D / 'native_sta_frontier_stage_03'
binding = read(stage / 'binding.json')
assert all(sha(D / 'src' / p) == expected for p, expected in binding['source_sha256'].items())
old = read(D / 'actual_search_tree_stage_01/binding.json')
assert all(sha(D / 'src' / p) == expected for p, expected in old['source_sha256'].items())
roles = {}
for role, row in v['roles'].items():
    a = m['roles'][role]
    roles[role] = dict(pin_rows=row['pins'], routed_connections=row['routed_connections'],
                       atom_pins=row['unique_routed_atom_pins'], ignored_pin_rows=row['ignored_pin_rows'],
                       global_pin_rows=row['global_pin_rows'], unmapped_pin_rows=row['unmapped_pin_rows'],
                       native_float_mismatches=row['native_float_mismatches'],
                       max_float_vs_double_error_seconds=row['max_float_vs_double_error_s'],
                       exact_float_ties=row['exact_worst_slack_connections'], numerical_ties=len(a['tie_group']),
                       near_within_0p2ns=a['near_within_0p2ns'], raw_criticality_one_misses_ties=a['exact_one_misses_tied'],
                       exact_top10_report_connections=len(row['top10_report_exact_connections']))
summary = dict(passed=True, status='native_all_pin_observer_and_frontier_mechanism_sealed',
               research_complete=False, quality_promoted=False, roles=roles,
               final_stage='native_sta_frontier_stage_03', binary_sha256=binding['binary_sha256'],
               paired_native_analysis_calls=8, all_development_native_analysis_calls=12,
               all_development_status_counts=dict(completed=10, observer_integration_failed=2, timeout=0, missing=0),
               failed_stage_01='Pre-routing pin lookup invalid after native post-routing pin-equivalence sync; replaced with native final-STA remapping-aware atom-sink traversal.',
               failed_stage_02='Analysis-loaded RouteTree lacks routing-only find_by_isink index; replaced with read-only actual-node pin-index traversal.',
               route_search_calls=0, original_route_files_unchanged=True,
               route_algorithm_source_files_unchanged=len(old['source_sha256']),
               final_stage_route_and_STA_neutral=True, physical_connection_checks=sum(r['routed_connections'] for r in roles.values()),
               Tf_tied_connections_guided_history=m['roles']['Tf']['guided_history_overlap'],
               strongest_local_CPD_ns=5.85466, strongest_local_result='joint_coordinated_native_01/runs/eltwise_layer_R',
               next_registered='native_frontier_joint_policy_experiment_01.json',
               limitations='Observer validation does not improve CPD. Four frozen states of one circuit/seed, zeroRC only. All-pin mapping uses native post-sync functions, not independently reimplemented packed traversal. Pin slack is not a CPD derivative; raw criticality is per-domain normalized. Whole-policy A0/R1/Tf comparisons and formal runtime remain pending.',
               public_snapshot='f7167bd1fbeb267d7ffc02766eeb2e5966aec387', this_followup_pushed=False)
write(D / 'native_sta_frontier_summary_01.json', summary)
paper = D / 'paper'
csv_path = paper / 'data/native_sta_frontier_v14.csv'
with csv_path.open('w') as stream:
    writer = csv.writer(stream)
    writer.writerow(['role', 'mode', 'status', 'CPD_ns', 'analysis_process_seconds', 'route_search_calls', 'router_iterations'])
    for r in c['receipts']:
        writer.writerow([r['role'], r['mode'], r['status'], r['cpd_ns'], r['process_seconds'], 0, 'not_applicable'])
fragment = paper / 'data/native_sta_frontier_discussion_v14.tex'
fragment.write_text(r'''A default-disabled, read-only final-analysis exporter now records all native net/pin identifiers, exact atom endpoints, available routing terminals, native floating-point net delays, raw setup/hold slack and criticality, and launch/capture-domain slack tags. It runs after the native timing update and does not alter routing, physical delays, pin synchronization, or STA. The standard timing echo lacks the complete pin-to-route mapping required by this intervention. Two development failures are retained: the routing-time pin lookup does not survive post-routing equivalent-pin synchronization, and analysis-loaded route trees need not contain the router-only sink lookup. The final observer instead uses the remapping-aware atom-sink traversal used by the native delay calculator and reads actual tree-node pin indices, as native net-delay loading does.

On frozen count-two eltwise A0/R1/Tf states and the accepted joint-R1 state, all eight observer-off/on analysis calls pass native FULL checks and preserve input routes and native CPD/setup/hold statistics. Each export contains 36,391 pin rows, including 2,583 ignored and 1,560 global pin rows (overlapping categories), with no unmapped pin rows. All 23,905 routed connections per state have exact route pin/RR identities; their 31,108 mapped atom sink pins are distinct. Across 95,620 routed-connection checks, the native delay equals an independent float-accumulation replay on the verified zero-RC graph. Maximum differences from a double-accumulation model are $2.248202\times10^{-15}$\,s for A0/R1/joint-R1 and $3.358425\times10^{-15}$\,s for Tf; full-precision native values are therefore retained. This validation does not cover nonzero-RC or flat-routing architectures.

Numerical worst-slack groups (within eight float ULPs) contain 5/6/4/2 connections for A0/R1/Tf/joint-R1. Exact float equality alone gives 3/4/4/1 because neighboring path pins can differ by one ULP. The separate descriptive 0.2\,ns near-worst windows contain 12/14/23/51 connections. These windows are not a frozen repair policy or proof that every member requires rerouting. A raw-criticality-equals-one filter misses all A0/R1/Tf worst-slack group members: their raw values are slightly below one, while a different clock-domain path can have criticality one and larger global slack. Native criticality is normalized per timing constraint and cannot directly substitute for a global CPD rank.

All four Tf numerical worst-slack connections are absent from the previously captured 3,809 guided-search contexts. The historic trace and current exported state have identical packing, placement, full route body and RRG. Thus more accurate queries limited to that guided population do not directly evaluate these final critical connections. The observer adds no quality improvement; CPDs remain 6.01810/6.01810/6.20812/5.85466\,ns. The next experiment applies one exact-mapping, current-STA target policy to A0/R1/Tf, separates independent versus joint capacity-compatible selection, and restores displaced networks transactionally. Twelve analysis calls were made during observer development: ten completed and two observer-integration failures; none invoked route search. Final-stage process times are reported separately and are not formal integrated-router overhead.
''')
main = paper / 'main.tex'
text = main.read_text()
tag = r'\input{data/plateau_joint_repair_discussion_v14.tex}'
assert text.count(tag) == 1 and 'native_sta_frontier_discussion_v14' not in text
main.write_text(text.replace(tag, tag + '\n' + r'\input{data/native_sta_frontier_discussion_v14.tex}'))
claims = paper / 'claims_evidence.md'
with claims.open('a') as stream:
    stream.write('\n| C77 | 原生最终STA全连接信息导出及精确端点/延迟验证 | [汇总](../native_sta_frontier_summary_01.json)、[逐连接验证](../native_sta_frontier_dev_03/frontier_validation.json)、[开关对照](../native_sta_frontier_dev_03/completion.json)、[计时](data/native_sta_frontier_v14.csv) | 4状态×23905路由连接，95620次原生float复算与RR映射一致；每状态36391pin行、31108路由atom汇，无未映射pin。8最终开关analysis均FULL/STA不变；开发累计12analysis含2导出集成失败，0route搜索。仅零RC/当前电路验证，不是质量提升或正式开销结论 |\n')
    stream.write('| C78 | 现有guided查询群体遗漏全部Tf当前最差并列连接，raw criticality不能直接代替全局CPD排序 | [机制分析](../native_sta_frontier_dev_03/frontier_mechanism_analysis.json)、[历史状态一致性](../native_sta_frontier_dev_03/guided_history_identity.json)、[下一联合策略实验](../native_frontier_joint_policy_experiment_01.json) | A0/R1/Tf/jointR1数值并列组5/6/4/2，0.2ns描述窗口12/14/23/51；Tf4目标在3809guided contexts中均0次。criticality==1遗漏A0/R1/Tf全部并列成员，需处理浮点及跨时序约束归一化。联合R1仍5.85466；统一策略/跨电路验证待完成 |\n')
status = paper / 'DEVELOPMENT_STATUS.md'
status.write_text('当前进展：默认关闭的原生全连接STA导出已完成4状态开关验证，95620条连接复算/映射一致。Tf全部4条数值并列最差连接未在原guided搜索群体出现；下一重点为统一全连接关键组选择、联合容量决策和事务恢复。观察器不增加质量收益；最强本地仍R1联合修复5.85466ns。研究active，新增仅本地。\n\n' + status.read_text())
ledger_path = paper / 'data/evidence_v14_ledger.json'
ledger = read(ledger_path)
files = [D / 'native_sta_frontier_summary_01.json', D / 'native_frontier_joint_policy_experiment_01.json',
         b / 'completion.json', b / 'frontier_validation.json', b / 'frontier_mechanism_analysis.json', b / 'guided_history_identity.json',
         D / 'native_sta_frontier_dev_01/failure_diagnosis.json', D / 'native_sta_frontier_dev_02/failure_diagnosis.json',
         stage / 'binding.json', csv_path, fragment]
for path in files:
    ledger['sources_sha256'][str(path.relative_to(D))] = sha(path)
ledger['native_sta_frontier'] = dict(status=summary['status'], physical_connection_checks=95620,
                                    paired_analysis_calls=8, total_analysis_calls=12, route_search_calls=0,
                                    Tf_final_ties_without_guided_history=4, next_registered=summary['next_registered'])
write(ledger_path, ledger)
print(dict(status=summary['status'], checks=95620, binary=binding['binary_sha256']))
