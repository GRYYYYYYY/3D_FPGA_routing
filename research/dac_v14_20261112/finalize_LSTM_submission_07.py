"""One manuscript revision from actual terminal admissions, not a verifier framework."""
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D/'LSTM_domain_whole_admission_03'
paper = D/'submission_narrative_07'
parent = D/'submission_narrative_06'
assert not (root/'admission_decision.json').exists()
terminal = read(root/'queue/completion.json')
supp_path = D/'CP1r3_supplemental_verifier_03/cases/lstm/domain/completion.json'
native_path = D/'LSTM_necessary_readonly_02/native_raw/completion.json'
native = read(native_path)
supp = read(supp_path) if supp_path.exists() else {}
raw_path, pair_path = root/'raw/completion.json', root/'pair/completion.json'
raw = read(raw_path) if raw_path.exists() else {}
pair = read(pair_path) if pair_path.exists() else {}
transition = read(root/'state_transition_observation.json')
config = read(root/'configuration_matching.json')
assert native['passed'] and native['quality_admitted']
assert transition['passed'] and config['passed']
assert all(sha(p)==h for p,h in config['source_sha256'].items())
assert all(sha(p)==h for p,h in transition['source_sha256'].items())
admitted = bool(supp.get('passed') and raw.get('passed') and raw.get('quality_admitted'))
matched = bool(admitted and pair.get('passed') and pair.get('matched_complete_quality_pair'))
gaps = []
if not supp.get('passed'):gaps.append(dict(gate='original_checks_with_exact_failed_scope',error=supp.get('error','not executed')))
if not raw.get('passed'):gaps.append(dict(gate='full_raw_evidence',error=raw.get('error','not executed: prerequisite failed')))
if not matched:gaps.append(dict(gate='actual_pair_matching',error=pair.get('error',pair.get('status','not executed: prerequisite failed'))))
sources = [root/'queue/completion.json', native_path, root/'state_transition_observation.json',
           root/'configuration_matching.json', root/'execution_plan.json',
           D/'LSTM_necessary_readonly_02/domain_failed_evaluation/audit.json',
           D/'cp1r3_distinct_input_cohort_01/lstm_results.json', Path(__file__).resolve()]
sources += [p for p in [supp_path,raw_path,pair_path] if p.exists()]
if admitted:
    # Connect the independently observed controller chain to the actual raw
    # audit's byte closure, without repeating completed graph/STA parsing.
    audited_states={s['state']:s for s in read(root/'raw/states.json')}
    sources.append(root/'raw/states.json')
    for t in transition['transitions']:
        assert t['before'] in audited_states and t['after'] in audited_states
        assert not audited_states[t['before']].get('rejected_failed_evaluation_only')
        assert not audited_states[t['after']].get('rejected_failed_evaluation_only')
        for name in ['registration.json','progress.json','completion.json']:
            p=str(Path(t['transaction'])/name)
            assert raw['source_sha256'][p]==transition['source_sha256'][p]
original = read(D/'cp1r3_distinct_input_cohort_01/lstm_results.json')
rows = []
for arm,result in [('native',native),('domain',raw)]:
    passed = bool(result.get('quality_admitted') and result.get('passed'))
    endpoint_path = (D/'LSTM_necessary_readonly_02/native_raw' if arm=='native' else root/'raw')/'own_initial_final_endpoints.json'
    ep = read(endpoint_path) if passed else None
    if ep is not None:sources.append(endpoint_path)
    rows.append(dict(arm=arm,execution_ended=True,admission='passed' if passed else 'not_passed',
        quality=result['quality'] if passed else None,
        own_root_endpoints={k:v for k,v in ep.items() if k!='changes'} if ep else None,
        complete_attempt_seconds=original[arm]['complete_seconds'],
        original_verification_status=original[arm]['status'],
        original_verification_seconds=original[arm]['independent_research_verification_seconds'],
        legal_no_gain=result.get('legal_no_gain'),timeout=False,
        original_ctime_archival_interference=(arm=='domain'),
        unperturbed_time_estimate=None))
decision = dict(decided_at=datetime.now(timezone.utc).isoformat(),
    domain_whole_arm_admission='passed' if admitted else 'not_passed',
    complete_pair_admission='passed' if matched else 'not_passed',
    rows=rows,gaps=gaps,domain_minus_native=pair.get('delta_domain_minus_native') if matched else None,
    paired_final_endpoints=pair.get('final_endpoint_summary') if matched else None,
    actual_source_state_chain_passed=True,original_failed_candidate_remains_failed=True,
    native_fallback_rejection_and_later_accepts_preserved=True,
    original_failure_promoted_to_success=False,formal_complete_time_ratio=None,
    clean_timing_admitted=False,unperturbed_time_estimate=None,
    additional_readonly_stage_costs=terminal.get('stages',[]),
    complete_readonly_queue_seconds=terminal.get('complete_active_queue_seconds',terminal.get('complete_queue_seconds')),
    new_native_or_STA_calls=0,source_sha256={str(p):sha(p) for p in sources},
    qualification='Supplementary whole-arm quality admission is separate from the original failed verifier and ctime-affected complete command. The failed guided candidate remains uncommitted and failed; native fallback and subsequent accepted states retain all original checks. No clean complete-time ratio or corrected time is inferred.')
write(root/'admission_decision.json',decision)
write(paper/'data/LSTM_complete_pair_admission.json',decision)
dest=paper/'supplement/LSTM_whole_admission'
for name,p in [('domain_supplement.json',supp_path),('domain_raw.json',raw_path),('pair_matching.json',pair_path),
               ('native_raw.json',native_path),('state_transitions.json',root/'state_transition_observation.json'),
               ('configuration_matching.json',root/'configuration_matching.json'),('queue_completion.json',root/'queue/completion.json')]:
    if p.exists():(dest/name).write_bytes(p.read_bytes())

text=(paper/'main.tex').read_text()
if matched:
    delta=pair['delta_domain_minus_native']; assert delta==dict(wirelength=2187,SB_pairs=-70,CB_sources=0,CPD_ns=0.0)
    ep=pair['final_endpoint_summary'];own=rows[1]['own_root_endpoints']
    assert own['compatible'] and ep['compatible']
    text=text.replace('SB and total vertical-count reductions are 47.56\\% and 0.797\\%, respectively; endpoint regressions remain explicit.',
        'SB and total vertical-count reductions are 47.56\\% and 0.797\\%, respectively. A supplementary admitted LSTM pair exchanges 2187 wire for 70 SB at equal CPD and CB count; its archival-interference-affected cost is reported without a clean-time ratio. Endpoint regressions remain explicit.')
    text=text.replace('LSTM N has supplementary full admission; its original verification failure and additional audit costs remain supplementary.',
        'Both LSTM roles have supplementary full quality admission. Their original verification failures and audit costs remain supplementary; D includes external archival interference, so its raw full cost supports no clean overhead ratio.')
    text=text.replace('LSTM CP1r3 D (verification fail)&--&--&26657.73&11.498&--',
        f"LSTM CP1r3 D (supp. admitted)&14.600438&2390270/422/8316&26657.73&11.498&{own['setup_improved']}/{own['setup_regressed']}/{own['hold_violation_regressions']}")
    old="LSTM's original independent checks fail in both arms. Subsequent unchanged-check replay and full raw admission validate the native result without rerouting: 104.65/199.30 s of additional research cost, separately from its original command. Domain remains unadmitted, so there is no new complete pair."
    new=("An additionally admitted LSTM pair exchanges 2187 wire for 70 SB (492 to 422) at 14.600438192 ns with 8316 CB unchanged; "
         f"{ep['setup_improved']} final setup components improve and {ep['setup_regressed']} regress versus native, with no increased hold violation. "
         "Actual roots and graph bytes match. Supplementary whole-route and state-transition checks admit the final quality without rerouting or promoting the failed guided attempt; original verification failures and native fallback remain explicit in the supplement. The full 7615.07/26657.73-s commands are retained, but external archival interference in D prevents a clean overhead ratio or an inferred interference-free time. Additional read-only audits are separate research costs.")
    assert old in text;text=text.replace(old+' ','')
    anchor='These observations demonstrate additional resource--timing working points, not uniform improvement of every metric.'
    assert text.count(anchor)==1;text=text.replace(anchor,anchor+'\n\n'+new)
    old="The additional fixed-version attempts supply no admitted complete pair. DLA-small fails initial routing and GEMM times out before legal-root admission. LSTM native has supplementary full admission, but domain and both SB-layout arms remain unadmitted after verification or execution errors. These errors establish neither algorithmic inability nor successful paired transfer. Recovery trajectories are excluded from benefits."
    new="Supplementary full admission adds one matched LSTM quality pair on a different known circuit in the same architecture family, with explicit endpoint and wire costs. Its external archival incident limits timing interpretation, not the verified final quality. DLA-small fails initial routing, GEMM times out before legal-root admission, and both SB-layout arms remain unadmitted after execution errors. Historical recovery trajectories remain supplementary."
    assert old in text;text=text.replace(old,new)
    text=text.replace('The additional fixed-version attempts provide no admitted full-pair replication; they do not extend those benefit claims.',
        'The admitted LSTM pair adds a 70-SB reduction for 2187 wire at equal CPD and CB count on another known circuit; its interfered execution does not establish clean overhead or broader architectural generalization.')
else:
    gap='; '.join(x['gate']+': '+str(x['error']) for x in gaps)
    (dest/'ADMISSION_GAP.txt').write_text(gap+'\n')
    text=text.replace('Domain remains unadmitted, so there is no new complete pair.',
        'The supplementary whole-domain audit does not close all required checks (the precise failing gate is retained in the supplement); domain quality remains unadmitted and no complete pair is claimed.')
    # Failure does not turn a valid route into an inferred algorithmic no-gain.
    assert 'LSTM CP1r3 D (verification fail)&--&--' in text
(paper/'main.tex').write_text(text)
body=text.split('Circuit/role &',1)[1].split('\\hline\\end{tabular}',1)[0]
(paper/'data/current_main_table_rows.tex').write_text(body)

lines=['# LSTM整臂判定与完整配对表','',
       '**整臂准入：'+('通过' if admitted else '未通过')+'；实际配对：'+('通过' if matched else '未通过')+'。**','',
       '| 角色 | 准入 | CPD(ns) | Wire / SB / CB | 自身根setup改善/退化/hold新增 | 完整原命令(s) |',
       '|---|---|---:|---:|---:|---:|']
for row in rows:
    q=row['quality'];e=row['own_root_endpoints'];quality=(f"{q['CPD_ns']:.9f}",'/'.join(str(q['resources'][k]) for k in ['wirelength','SB_pairs','CB_sources'])) if q else ('—','—')
    eps=f"{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}" if e else '—'
    lines.append(f"| {row['arm']} | {row['admission']} | {quality[0]} | {quality[1]} | {eps} | {row['complete_attempt_seconds']:.6f} |")
lines += ['', '原执行结束与原验证失败均保持。上述通过指本次补充整臂准入；没有把失败候选改写为成功。', '',
          'domain完整命令受外部归档ctime干扰。只报告实测26657.726866秒，不推算无干扰时间、不计算正式完整时间比。BNN匹配N/D/D/N的+24.91%完整开销结论保持独立。']
if matched:
    e=pair['final_endpoint_summary'];lines += ['',f"实际配对D−N：wire +2187，SB −70，CB 0，CPD 0；setup {e['setup_improved']}改善/{e['setup_regressed']}退化，hold新增{e['hold_violation_regressions']}。起点树、约束、端点向量及六项图载荷实际匹配，两臂配置仅domain模式/反馈不同。"]
if gaps:lines += ['', '具体缺口：']+[f"- {r['gate']}: `{r['error']}`" for r in gaps]
lines += ['', '本次只读核验实测（与完整算法命令分列）：']
for r in terminal.get('stages',[]):lines.append(f"- {r['stage']}: {r['status']}；{r.get('complete_command_seconds')}秒。")
lines += ['', '原419SB、2390877wire候选超cap402，原策略拒绝保持。ctime失败的另一个419SB、2390832wire候选超357，原FULL_STA_failed保持，自己的CPD/端点已单独核验。后者没有历史成功回执，也未被控制器接受。', '',
          '四档代价对照已完成：0/0.5为251140/9/654，1/2为251125/9/654；全部合法但违反CB≤653。共享域加失败释放给251160/9/653；机制增量仅限该同源固定组，不外推所有权重或输入。CLSTM历史恢复只留补充材料。']
(root/'STATUS.md').write_text('\n'.join(lines)+'\n')
(paper/'LSTM_PAIR_TABLE.md').write_text('\n'.join(lines)+'\n')
impact=f'''# 投稿06修订版07：证据影响与作者审阅

原06完整保留。本版只更新已终结的LSTM整臂判定、表I、摘要、适用性和结论，并把已完成四档代价对照的作用域内增量放进摘要/表II；表III数值不变。问题定义、统一方法、prior-art边界、BNN完整取舍和24.91%费用保持。

| 证据 | 当前判定 | 影响 |
|---|---|---|
| LSTM整臂/实际配对 | {'通过/通过' if matched else '未完全通过；见LSTM_PAIR_TABLE.md具体缺口'} | 表I LSTM行、摘要、§IV-C及§VI适用性/结论；不推出无干扰费用 |
| 四档跨层代价 | 全部完整核验通过，合法但CB策略拒绝 | 已完成机制增量证据；不再列待办，不外推所有权重/输入 |
| BNN N/D/D/N | 已匹配通过 | 原主张与完整费用保持；不再为增加结果量重复局部实验 |
| DLA/TPU/GEMM初始失败或超时、SB-layout执行错误 | 原空质量及具体原因保持 | 表I覆盖和适用范围，不是合法无收益或全局不可行证明 |
| CLSTM/reduction/robot-p1历史恢复 | 仅补充材料 | 不阻塞主稿，也不补充新鲜完整确认或完整时间比 |

本稿无需未来实验结果即可供作者审阅。新增确认只更新对应实验行和范围；不因普通负结果重写方法。LSTM外部归档干扰、原失败、全部核验费与端点退化须保留。未测试权重、架构及应用时序要求没有优势主张。审阅时重点检查资源单位、实验预算与应用SDC的区别，以及配对终点差与自身根变化的区别。
'''
(paper/'EXPERIMENT_IMPACT.md').write_text(impact)
reg=read(paper/'edit_registration.json');reg.update(status='actual_terminal_evidence_integrated_build_pending',
    LSTM_domain_admitted=admitted,LSTM_pair_matched=matched,
    source_sha256={str(root/'admission_decision.json'):sha(root/'admission_decision.json')},
    source_updated_at=datetime.now(timezone.utc).isoformat())
write(paper/'edit_registration.json',reg)
print(dict(domain_admitted=admitted,pair_matched=matched,rows=rows,gaps=gaps))
