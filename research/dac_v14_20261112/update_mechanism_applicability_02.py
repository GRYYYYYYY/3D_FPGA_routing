"""Extend the existing descriptive table; no new experiment or scheduler tuning."""
import csv
import time
from retained_prefix_workflow import D, read, write, sha

out=D/'mechanism_selection_evidence_02'
start=time.monotonic();registration=read(out/'registration.json')
assert not (out/'completion.json').exists()
assert all(sha(p)==h for p,h in registration['source_sha256'].items())
old=D/'mechanism_selection_evidence_01';proof=read(old/'completion.json')
assert proof['passed']
for name in ['pairs.json','timing_envelope_counterexample.json']:
    assert sha(old/name)==proof['artifact_sha256'][name]
rows=[]
for pair in read(old/'pairs.json'):
    rows.append(dict(label=pair['label'],scopes=pair['native']['initial_STA_eligible_sharing_scopes'],
        CPD_limit_over_initial=pair['native']['fixed_CPD_headroom_ratio'],
        domain_minus_native=pair['domain_minus_native'],
        observed_release_queries=pair['domain']['observed_released_queries'],
        scope=pair['evidence_kind'],whole_time_comparison='historical configuration only; BNN is original cold pair',
        source=str(old/'pairs.json')))
ld=read(D/'LSTM_domain_whole_admission_03/admission_decision.json')
lm=read(D/'LSTM_admitted_mechanism_synthesis_01/completion.json')
assert ld['complete_pair_admission']=='passed' and lm['passed']
assert ld['domain_minus_native']==lm['complete_domain_minus_native']
assert ld['formal_complete_time_ratio'] is None and lm['missing_matched_LSTM_no_release_control']
rows.append(dict(label='LSTM CP1r3',scopes=lm['initial_features']['initial_eligible_scopes'],
    CPD_limit_over_initial=1.0,domain_minus_native={**ld['domain_minus_native'],'complete_seconds':None},
    observed_release_queries=lm['total_guided_release_events'],
    scope='supplementary admitted complete pair; historical ctime failure not promoted',
    whole_time_comparison='unavailable: external archival interference; raw costs retained',
    source=str(D/'LSTM_domain_whole_admission_03/admission_decision.json')))
td=read(D/'TPU_OS_complete_admission_02/admission_decision.json')
tm=read(D/'TPU_OS_complete_admission_02/mechanism_summary.json')
tc=read(D/'cp1r5_tpu_os_pair_01/native_menu_closure_01.json')
assert td['complete_pair_admission']=='passed' and tm['passed'] and tc['passed']
assert tm['equal_final_full_endpoint_vectors'] and not tm['domain_extra_vertical_gain']
assert all(a['failed_search_release_events']==0 and a['owner_transactions']==0 for a in tm['arms'])
assert tm['arms'][0]['initial']['state']==tc['selector_sequence'][0]['source_state']
times={r['arm']:r['complete_command_seconds'] for r in td['rows']}
rows.append(dict(label='TPU-OS CP1r5',scopes=tc['selector_sequence'][0]['eligible_scopes'],
    CPD_limit_over_initial=1.0,domain_minus_native={**td['domain_minus_native'],
        'complete_seconds':times['domain']-times['native']},observed_release_queries=0,
    scope='admitted matched complete pair; same known TPU family and architecture',
    whole_time_comparison='single N/D descriptive only; not symmetric interleaved',
    source=str(D/'TPU_OS_complete_admission_02/admission_decision.json')))
for row in rows:
    delta=row['domain_minus_native']
    row['vertical_increment']=(delta['SB_pairs']<=0 and delta['CB_sources']<=0 and
                              (delta['SB_pairs']<0 or delta['CB_sources']<0))
by={r['label']:r for r in rows}
assert by['Eltwise']['scopes']==12 and by['Eltwise']['vertical_increment']
assert by['TPU-OS CP1r5']['scopes']==19 and not by['TPU-OS CP1r5']['vertical_increment']
counter=read(old/'timing_envelope_counterexample.json');assert counter['passed']
assert counter['same_initial_STA_screen_and_48_scope_bytes']
write(out/'pairs.json',rows)
with (out/'overview.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['configuration','initial_scopes','CPD_cap_ratio','D_minus_N_wire','SB','CB','CPD_ns','observed_release_queries','vertical_increment','time_qualification'])
    for r in rows:
        v=r['domain_minus_native'];writer.writerow([r['label'],r['scopes'],r['CPD_limit_over_initial'],v['wirelength'],v['SB_pairs'],v['CB_sources'],v['CPD_ns'],r['observed_release_queries'],r['vertical_increment'],r['whole_time_comparison']])
lines=['# 机制适用性：新增已准入LSTM与TPU-OS','',
       '这是既有结果的回顾性整理，不是新确认、调参集或收益预测器；当前CLSTM-SB未终结结果不纳入。不同版本和预算分列，不能把配置数当独立电路数或计算泛化成功率。','',
       '| 配置 | 初始可选切口 | CPD预算/初始 | D−N线长 | SB | CB | 观察到的释放查询 |',
       '|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
    v=r['domain_minus_native'];lines.append(f"| {r['label']} | {r['scopes']} | {r['CPD_limit_over_initial']:.2f} | {v['wirelength']:+d} | {v['SB_pairs']:+d} | {v['CB_sources']:+d} | {r['observed_release_queries']} |")
lines += ['','可检验的设计约束：',
 '- 切口数是可操作性描述，不是增量收益预测。Eltwise的12个切口有垂直收益，TPU-OS的19个没有；不能仅以数量阈值或“越多越值得”替代匹配比较。这是不同配置间的描述性反例，不是控制变量的因果估计。',
 '- 时序预算必须显式进入决策。同一个SB-only输入、同48个切口字节，在严格与102%预算下产生不同取舍；该对照不是独立样本。',
 '- 失败释放依据实际失败查询触发。LSTM观察到34次释放、接受guided分支中12次；既有同源no-release反事实缺失，不能据次数归因必要性。TPU-OS两臂都有18SB改善但没有释放/owner事件，不能将共有改善归给这些机制。',
 '- 合法完成仍需完整预算接受。保留robot四档代价候选的CB策略拒绝、LSTM线长拒绝及原ctime失败；不把操作性失败自动判作全局不可行，也不把释放成功视作预算收益。',
 '- 因此继续保留结构/余量筛选、实际失败释放、阻塞owner协调与整组接受的关系；不安装按电路ID或切口数量调出的新开关。若开发自动选择规则，需独立登记并评估完整资源、端点及费用。',
 '', '费用边界：BNN旧行来自原冷启动配置，当前交错24.91%另有独立证据；LSTM仅照录受归档干扰的两条完整费用，不计算干净差值；TPU-OS只支持单次描述。初始路由失败、超时和未准入案例继续保留于原主表，缺失切口数为未知，不能填0。',
 '', '当前稿件08和运行中的CLSTM-SB规则不变。']
(out/'APPLICABILITY.md').write_text('\n'.join(lines)+'\n')
assert all(sha(p)==h for p,h in registration['source_sha256'].items())
write(out/'completion.json',dict(passed=True,configuration_rows=len(rows),versions_uniform=False,
    new_native_or_STA_calls=0,new_confirmed_inputs=0,running_configuration_changed=False,
    whole_LSTM_time_difference=None,scope_count_is_not_gain_predictor=True,
    full_candidate_budget_acceptance_required=True,complete_metadata_synthesis_seconds=time.monotonic()-start,
    source_sha256={**registration['source_sha256'],str(out/'registration.json'):sha(out/'registration.json'),str(__file__):sha(__file__)},
    artifact_sha256={n:sha(out/n) for n in ['pairs.json','overview.csv','APPLICABILITY.md']},
    qualification='Retrospective descriptive evidence; no learned policy, success probability, new benchmark or causal release claim. Existing scope/budget counterexamples constrain future development, not frozen confirmation.'))
print(dict(passed=True,configuration_rows=len(rows),new_native_or_STA_calls=0))
