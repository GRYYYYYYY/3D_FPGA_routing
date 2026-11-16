"""Short current research entry; detailed component/history records remain linked."""
from pathlib import Path

def render(status,D):
    rows=[]
    for owner in status['owners']:
        if not owner['verified_live'] and not owner.get('flow_active_stage'):continue
        phase=owner.get('effective_wait') or owner['phase_status']
        if owner.get('flow_active_stage'):phase+=' → '+owner['flow_active_stage']['phase']
        rows.append(f"| {owner['batch']} | {phase} | {owner['pid']} |")
    timing_note=''
    if status.get('BNN_timing03_first_complete_arm'):
        timing=status['BNN_timing03_first_complete_arm']
        timing_note=f"当前对称计时首臂：[native_0完整回执](BNN_timing03_native0_receipt_02/completion.json)已在14:12UTC落盘、14:13UTC通过原完整核验。13.228145690ns，2059631wire/82SB/5062CB，{timing['complete_command_seconds']:.2f}s，PSS{timing['sampled_tree_PSS_peak_GiB']:.3f}GiB，缺失内存观察22次，157个测量身份均已终止。首臂后队列自动转入后续角色，当前运行阶段以进程核对表为准；不能沿用旧native_0时序检查点。完整轨迹/请求/图载荷和端点等价核验待原四臂收尾；本次是已知BNN输入的重复计时，没有新独立样本、优化后N/D比值或统计加速结论。\n\n"
    paper=Path(status['paper_pdf']).relative_to(D)
    if status.get('closed_CP1r2_cohort'):
        return f'''# 当前研究状态

观察时间：{status['observed_at']}。Goal active；公开证据基点9734eee，原开发状态、冻结版本与失败回执保留。

统一方法：按当前STA、跨层冗余与容量阻塞选完整连接组；在私有树上执行共享域、按网失败释放及owner协调；经物理/容量/FULL/STA完整检查，在固定根预算下接受或恢复，终结选点独立于中间提交。native享有同等选组、owner和收敛机会。CP1r2独立冻结，不追认旧开发结果为确认。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
{chr(10).join(rows)}

新增确认：[CP1r2四臂终结证据](cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json)。两个预先固定的已知独立电路/实际物理输入中，conv_hls两臂合法，初始树/完整向量匹配，终态同14.351002164ns、84291wire/0SB/37CB、4491setup/hold分量；零提交/提案，505.17/500.90s。18个当前关键连接固定/放宽容量均无物理时序增益。确认一个固定菜单无收益输入，不是普遍收益或全局最优。

TPU_ws两臂均触发原1800s初始执行保护，完整尝试1904.67/1906.23s，PSS2.434/2.433GiB，缺失观察0/0。无合法根/质量/端点比较；不是200迭代拥塞失败或不可路由证明。四角色原回执、实际费用与PID身份均保留，无残留后代，不重跑。

机制：[robot固定25连接/5网三臂消融](robot_union_mechanism_02/verification_v2.json)已只读核验。源251161/10/653；native合法251140/9/654，setup240改善/0退化，却超原CB653上限；domain/no-release精确回滚；domain/release合法251160/9/653，CPD同13.354624073ns，setup240改善/32退化、hold增加0，满足资源预算但不满足端点无退化。共享导入命令194.52s，非各臂独立整流程费用；三个候选未提交原actor。域改变本例取舍，释放使该受限事务可行，owner范围扩大另行归因。

[robot-p1 owner接续审计](robot_owner_reentry_audit_02/completion.json)确认4次自动native owner提交及当前状态重入：231045/47/6677→231113/47/6673，CPD同11.633691344ns，即+68wire/−4CB；一阶段setup退化1。既有reload完整精度CPD/setup/hold/约束/端点ID精确相同，确认旧检查仅误比显示精度。仍是中断开发轨迹，不是完整确认或域收益。precision patch02已暂存，未写入CP1r2。

新增归因核对：[10配置/9个声明物理输入矩阵](mechanism_selection_evidence_01/completion.json)是既有数据分析，不是新增独立确认。4配置初始无共享切口；6配置有切口但其中softmax、严格SB-only无额外垂直节省。SB-only两时序设置同初始树/48条候选/资源上限，CPD cap1.00/1.02下domain相对native多省SB为0/4，通用规则必须包含时序预算。所有实际guided资源角色均已覆盖审计：BNN9角色/0释放、robot3角色/5释放。资源owner依赖可避免跨层冗余与目标/owner余量；时序owner需要同一正延迟见证的容量冲突，不能混用两者。[开发分流原型](mechanism_triage_validation_02/completion.json)未装入冻结版本、无实测节省。

{timing_note}完整费用：历史BNN同13.228145690ns，domain+1786wire换39SB/2CB；SB−47.56%，SB+CB−0.797%，完整时间+22.95%。对称工程改动的domain单次9116.40s，相对9754.31s少6.54%；优化后N/D比值仍待当前N/D/D/N完整交错计时。空查询补丁验证在其后排队，无已测节省。

无效、失败与边界：SPMV/CB-only无切口，Robot SDC无接受收益，conv-layer/attention初始路由失败；TPU为初始执行超时。旧加载错误、5次监督中断及4次保护程序打包失败单列基础设施费用。现有owner联合修复N/D同结果归于协调扩大，不能归于域。

论文：[当前六页PDF]({paper})，主表43行：36终结尝试、2组基础设施失败、5个局部组件。保留六节主线、机制伪代码与路由相关工作；新增完整确认无收益、TPU超时、robot三臂、owner局部接续及主张边界。历史轨迹/恢复与完整审计留补充材料。已公开版本以CURRENT_STATUS.json的latest_incremental_publication回执为准。

新确认协议：[CP1r3三输入/六角色](cp1r3_distinct_input_cohort_01/protocol.json)已登记在robot接续之后，包括LSTM、DLA-like.small和SB-only布局对照。尚未激活实际配置、重建或准入，不能声称确认通过。SB对照与旧主表同声明电路/图/打包，但1883块中1882块实际坐标不同，是新布局而非新电路；其余原始字节/新鲜根仍待核验。协议先绑定来源/规则，实际CP1r3冻结、公开源码重建及检查通过后，先封存配置再运行；现有版本和队列不变。

其余中断阶段：[四臂真实回执清单](interrupted_stage_reconciliation_01/inventory.json)及[串行只读核验登记](interrupted_stage_reconciliation_01/plan.json)已补齐，排在原确认队列之后。CLSTM/native资源阶段已闭合，时序原生与候选审计也已完成；reduction/domain的原生、物理和域审计已完成，两者候选STA目录为空。CLSTM/domain仅原生完成；reduction/native有GNU退出0及269请求完成日志，但worker未封存。只核验旧字节/完整STA，不新增原生调用、改写旧回执或冒认整流程结果；[四臂完整接续入口](interrupted_flow_recovery_01/protocol.json)现已实现并登记在核验之后：CLSTM/native跳过已闭合阶段并保留原时序portfolio/查询，另三臂从原资源检查点继续；31项真实元数据拒绝检查与5项小型流程/20项拒绝检查通过。仍须实际串行核验和逐臂准入，尚无新接续质量或冷启动费用。

后续：保持当前计时规则，完成已登记只读空查询验证；[精度专用CP1r3准备](confirmation_release_cp1r3_01/plan.json)已登记在其后、获取串行锁才打包，不含空查询补丁/新路由，尚未形成新版本执行证据。[robot-p1完整接续](robot_p1_prefix_recovery_01/plan.json)已实现并登记在CP1r3之后，24项元数据负向检查通过，原7步/合法拒绝档案/根预算保留；原生请求与STA复用仍须串行重图/完整轨迹核验，尚无新实验结果或冷启动费用。其余中断输入另行接续，继续真正不同输入/架构及通用机制规则研究。Goal不因批次、推送或普通负结果终止。
'''
    if status.get('execution_reconciliation_20261116'):
        reconciliation=status['execution_reconciliation_20261116']
        attempts='\n'.join(f"| {r['input']}/{r['arm']} | {r['failed_attempt_seconds']:.2f} | {r['sampled_PSS_kib']/1048576:.3f} |" for r in reconciliation['attempts'])
        confirmation_text=''
        if status.get('first_complete_CP1r2_native_arm'):
            c=status['first_complete_CP1r2_native_arm'];r=c['quality']['resources']
            confirmation_text=(f"首个完整CP1r2确认臂已核验：conv_hls/native {c['quality']['CPD_ns']:.9f}ns，{r['wirelength']}wire/{r['SB_pairs']}SB/{r['CB_sources']}CB，{c['complete_seconds']:.2f}s；资源/owner/时序提交均0，时序修复候选0。该已登记独立电路输入在固定菜单中无适用修复；domain配对仍待实际比较。证据：[完整原生臂](cp1r2_cross_circuit_cohort_01/conv_hls_native_evidence_01/evidence.json)。继承development_v1字符串是内部兼容标记，实际外层运行回执绑定CP1r2。")
        if status.get('first_complete_CP1r2_pair'):
            pair=status['first_complete_CP1r2_pair'];n=pair['results']['native'];d=pair['results']['domain']
            confirmation_text=(f"首个完整CP1r2配对已核验：conv_hls两臂初始树/完整向量匹配，终态同14.351002164ns、84291wire/0SB/37CB，4491setup/hold分量均无变化；零提交/零时序提案。完整N/D时间{n['complete_seconds']:.2f}/{d['complete_seconds']:.2f}s，仅单次描述。18个关键连接在固定/放宽容量查询中均零物理增益；7个放宽见证有占用冲突，但无正时序动机。确认一个独立已知电路/实际物理输入的固定菜单无收益，不代表全局最优或算法普遍优势。[配对回执](cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json)。tpu_ws继续按原规则运行。")
        if status.get('CP1r2_tpu_native_timeout'):
            t=status['CP1r2_tpu_native_timeout']
            confirmation_text+=(f"\n\nTPU_ws/native已按真实回执归为初始路由执行超时：原命令1800s保护触发，最后完成190/200迭代，原生命令{t['native_command_seconds']:.2f}s，完整失败尝试{t['failed_attempt_seconds']:.2f}s，采样PSS{t['sampled_PSS_kib']/1048576:.3f}GiB，缺失观察{t['missing_memory_observations']}。无合法根与质量指标；不是200迭代拥塞终态或不可路由证明。9个原测量身份均无存活后代，原队列已转domain，不重跑native。[精确超时证据](cp1r2_cross_circuit_cohort_01/tpu_ws_native_timeout_evidence_01/evidence.json)。")
        return f'''# 当前研究状态

观察时间：{status['observed_at']}。Goal active；公开证据基点9734eee；历史结果与冻结包保留。

统一方法：当前STA/跨层冗余选完整连接组，在私有路由上执行共享域、按网失败释放与容量阻塞owner协调，检查完整组合，按固定根预算接受；终结选点独立于中间提交。native享有同等选组、owner与收敛机会。CP1r2修复Linux进程消失时的监督异常并校验保护程序执行权限，算法/规则不变；[新冻结版本](confirmation_release_cp1r2_01/completion.json)不把既有开发结果追认为确认。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
{chr(10).join(rows)}

[已核对的五次中断](execution_reconciliation_20261116_01/completion.json)均有合法初始路由，但因监督器读取消失的/proc进程触发ProcessLookupError而失去完整流程结果。已按PID+start_ticks核对582个测量身份，无存活身份；原回执不改写。修正版通过注入异常及五类真实进程测试。以下仅为失败尝试费用，无完整质量指标：

| 输入/臂 | 实际时间(s) | 采样PSS(GiB) |
|---|---:|---:|
{attempts}

{confirmation_text}

独立证据：CLSTM两臂、robot-p1/native的修正输入已实际加载并完成合法初始路由；完整方法确认仍缺失。reduction保留native10步/domain4步轨迹，不把不同中断点作N/D因果比较。robot-p1/domain从未执行，原计划与缺口保留，后续单独登记接续。

机制与取舍：BNN完整历史配对同13.228145690ns；domain花1786wire换39SB/2CB。SB减少47.56%，SB+CB减少约0.797%；历史完整时间增加22.95%。新domain工程版9116.40s相对历史9754.31s少6.54%，行为核验精确，但尚无稳定优化后N/D时间比。robot失败释放是原作用域的运行使能；owner范围扩大另有端点/资源交换，不能归因于域。

无效或失败输入继续保留：SPMV/CB-only无切口、Robot SDC无接受收益、conv-layer/attention初始路由失败、历史CLSTM/robot-p1打包解释错误。新五次为基础设施中断，不能混入算法负结果。

论文：[当前六页PDF]({paper})。正文按问题—机制—完整结果—多目标取舍—消融—开销与范围组织；局部轨迹和恢复费用在补充材料。完整CP1r2确认、联合机制效果与对称交错费用仍待实际回执。最新已核验公开提交与回读见CURRENT_STATUS.json的latest_incremental_publication；本轮未发布内容不得视为已公开。

CP1r1四臂因冻结打包误去掉保护程序执行权限而以126终结，均未启动VPR，不算路由失败。原尝试保留在[打包失败回执](CP1r1_packaging_failure_01/completion.json)。CP1r2已通过原生保护测试、固定规则准入及公开源码重建后的同一保护测试。

robot-p1/native中断轨迹另观察到4次owner提交（round3–6），从47SB/6677CB走到47SB/6673CB，线长231045→231113，CPD不变。后续reload出现完整精度manifest与六位显示值比较问题；[只读审计](robot_owner_reentry_audit_02/plan.json)已排队核对固定根预算、状态重入和原有完整向量。审计01在执行前因JSON list/parser tuple格式误判而留据替换为02；修正版仅规范list/tuple，保留顺序和数值精确比较。数值回归拒绝显示精度以下的CPD漂移及setup/hold/端点顺序/身份/约束漂移；实际完整向量复核尚未完成。开发局部轨迹不计完整算法收益或CP1r2确认。

robot联合机制三臂原生工作已结束，原只读校验器错误要求紧凑回执具有额外字段；[独立校验接续](robot_union_verification_recovery_01/plan.json)等待串行锁，只复核原产物，零新原生工作。CP1r2正在执行，BNN03在该复核后等待，旧BNN01/02均未执行。

下一步按实际CP1r2进程、robot只读复核和BNN03队列继续；接续失败开发轨迹时保留原失败和费用口径。不以矩阵、推送、普通负结果或固定调用数终止Goal。
'''
    grouping=status.get('query_reduction_terminal_observation')
    grouping_text='第四个 BNN domain 角色仍需真实终结与封存回执。'
    if grouping:
        res=grouping['final_resources']
        grouping_text=(f"BNN domain 分组开发已终结并封存：{grouping['accepted_steps']}步，"
            f"{res['wirelength']}/{res['SB_pairs']}/{res['CB_sources']}，{grouping['CPD_s']*1e9:.9f} ns，"
            f"完整导入流程 {grouping['imported_workflow_seconds']:.2f} s。相对历史 K8，仅少 {-grouping['K8_wire_delta']} wire，"
            f"同 SB/CB/CPD，历史时间增加 {grouping['historical_time_difference_percent']:.2f}%；不能作为加速证据。"
            "不据此将分组启发式加入已登记 dev03，也不继续优化几个 BNN 线长单位；优先执行既有跨输入与机制验证。"
            "完整四角色端点／工作量比较等待串行空位；此处不是冷启动完整配置费用。")
    terminal_text=''
    handoff=status.get('terminal_wire_actual_handoff_observation')
    if handoff:
        before,after=handoff['before_resources'],handoff['selected_resources']
        terminal_text=(f"当前流程的资源阶段已通过，终结选点实际采用 {after['wirelength']} wire／{after['SB_pairs']} SB／{after['CB_sources']} CB，"
            f"相对主资源终态 wire {after['wirelength']-before['wirelength']:+d}；setup {handoff['setup_improved']}改善／{handoff['setup_regressed']}退化。"
            f"记录阶段为 `{handoff['current_native_phase']}`，进程身份实时核验={handoff['current_native_phase_verified_live']}；"
            f"完整配置最终验证={handoff['complete_configuration_verified']}。这是本次同流程交接观察，最终时序结果和完整费用以终结回执为准。")
    timing=status.get('terminal_wire_current_timing_observation')
    if timing:
        r=timing['current_resources']
        terminal_text+=(f"时序阶段当前接受{timing['accepted_steps']}步，最近检查点为 {timing['current_CPD_s']*1e9:.9f} ns／"
            f"{r['wirelength']} wire／{r['SB_pairs']} SB／{r['CB_sources']} CB。")
        endpoints=timing['last_step_endpoint_summary']
        if endpoints:
            terminal_text+=(f"最近一步相对前态 setup {endpoints['setup_improved']}改善／{endpoints['setup_regressed']}退化，"
                f"新增 hold 违例退化{endpoints['hold_violation_regressions']}项；不是相对完整基线终态的比较。")
    completed_terminal=status.get('completed_terminal_wire_observation')
    terminal_queue_text='原队列当前执行完整 terminal-wire BNN，随后按既有顺序执行'
    terminal_comparison_text='等待实际终结及串行空位'
    terminal_result_text='尚无新完整结果。'
    if completed_terminal:
        r=completed_terminal['resources']
        terminal_queue_text='完整 terminal-wire BNN 已通过配置验证，原恢复队列正常终结；后续队列按既有顺序执行'
        terminal_comparison_text='实际配置已终结并通过核验，基线比较等待串行空位'
        terminal_result_text=''
        terminal_text=(f"本次完整原生 terminal-wire 配置已核验：{completed_terminal['final_CPD_s']*1e9:.9f} ns，"
            f"{r['wirelength']} wire／{r['SB_pairs']} SB／{r['CB_sources']} CB；"
            f"资源接受{completed_terminal['resource_accepted_steps']}步、终结选点{completed_terminal['terminal_wire_commits']}次、时序接受{completed_terminal['timing_accepted_steps']}步。"
            f"同次端到端测量 {completed_terminal['complete_command_wall_seconds']:.2f} s，"
            f"采样 PSS 峰值 {completed_terminal['sampled_tree_PSS_peak_kib']/1048576:.3f} GiB，"
            f"内存缺失观察{completed_terminal['missing_memory_observations']}次，无残留子进程。"
            "这是同一历史 BNN 物理输入上的完整配置，非独立输入，也非统一 dev03 确认。"
            "共同资源前缀等价、相对基线的完整端点变化及同口径费用差，仍以单独比较回执为准；不得由标量相同推断完整等价。")
    qualified=status.get('qualified_terminal_comparison')
    if qualified and qualified.get('passed') and qualified.get('quality_comparison_available'):
        terminal_comparison_text='已完成，匹配共同资源前缀／最终完整端点／同口径 GNU-time'
        terminal_result_text='比较已通过：共同资源前缀状态、请求和原生工作精确一致；相对旧终态少24 wire，setup2改善／0退化，CPD/SB/CB相同。GNU-time7351/7247 s，增加104 s，非加速；旧观察者/PSS缺口及并发限制保留。'
        terminal_text=terminal_text.replace('共同资源前缀等价、相对基线的完整端点变化及同口径费用差，仍以单独比较回执为准；不得由标量相同推断完整等价。','相对自身初始根 setup16改善／17退化；相对旧终态2改善／0退化，两个比较口径分别保留。')
    environment_text=''
    if status.get('measurement_environment_notes'):
        environment_text='[attention-native 测量环境记录](unified_input_integration_01/measurement_environment_note_01.json)：本地同步公开提交触发短暂 Git 自动打包，三个打包进程已核验终止，原实验进程保持不变。保留该实际共享主机重叠，不能称受控交错计时；此前已结束的 BNN 测量不受影响。后续 Git 同步关闭自动打包。'
    input_outcome_text=''
    input_outcome_overview='新登记跨输入配对尚无终结回执。'
    input_outcomes=status.get('unified_input_actual_outcomes')
    if input_outcomes:
        input_outcome_overview=(f"新登记跨输入配对已终结{input_outcomes['terminal_roles']}/{input_outcomes['registered_roles']}臂，"
            f"其中{input_outcomes['verified_legal_roles']}臂通过完整合法验证；失败记录同样保留。")
        input_outcome_text=(f"[跨输入实际回执](unified_input_integration_01/queue/results.json)：登记的{input_outcomes['registered_roles']}个臂中，"
            f"{input_outcomes['terminal_roles']}个已终结，{input_outcomes['verified_legal_roles']}个通过完整合法验证。")
        for name,row in input_outcomes['results'].items():
            input_outcome_text+=f" `{name}`：{row['status']}，完整命令 {row['complete_seconds']:.2f} s。"
        input_outcome_text+='初始路由失败的质量为 None；迭代中的 CPD／线长不作合法质量点。单臂结果不支持配对机制归因，两个臂不算两个独立输入。该批次保持较早登记开发版本，不冒充 dev03 确认。'
    if status.get('attention_initial_failure_pair'):
        input_outcome_text+=' [attention 匹配失败审计](attention_initial_failure_pair_01/completion.json)通过：两臂实际命令除私有路径外相同，已记录物理输入摘要匹配，均执行200轮后剩231个过用节点，未进入资源／时序修复。0次新原生调用；记录摘要与当前文件身份核对不冒充新的大输入重哈希。缺少合法起点属于适用范围证据，不是三种修复机制的收益比较。'
    completed_pairs=status.get('unified_input_complete_comparison')
    if completed_pairs:
        r=completed_pairs['pairs']['robot_s23_SDC']
        input_outcome_text+=(f" [完整配对比较](unified_input_integration_01/comparison.json)通过：robot 两臂起始路由体及完整端点一致，终态端点也一致；CPD {r['native']['CPD_ns']:.9f} ns，250411 wire/2 SB/526 CB，完整费用 {r['native']['complete_wall_seconds']:.2f}/{r['domain']['complete_wall_seconds']:.2f} s。实际布局不同于旧 robot p0；声明的20 ns/IO 1 ns SDC不是外部应用要求。两臂均无资源切口或 owner 提交，三项时序候选均拒绝；较快候选超出固定资源预算。不能据此归因任一机制收益。")
    paper_update_text=''
    if status.get('complete_input_paper_update'):
        paper_update_text='当前版本已更新为[完整输入与比较证据版08](qualified_complete_paper_binding_08.json)：27个完整尝试条目（含4个初始失败）及2个局部组件条目，整合 BNN 完整终结选点费用及相对基线比较、robot-SDC 无收益及 attention 失败；逐项绑定自身初态端点和同次完整费用。下述22行描述为前版06范围，历史档案计数不变。'
    if status.get('owner_contract_paper_update'):
        paper_update_text='当前[六页正文09](owner_contract_paper_binding_09.json)包含31个完整尝试（4个初始路由失败、4个输入加载失败）及2个局部组件条目。新增 robot owner 配对取舍、输入失败分类和 CP1 固定契约；旧批次不追认为确认。下述前版数字均属历史范围。'
    if status.get('complete_tradeoff_paper_update'):
        paper_update_text='当前[六页正文10](complete_tradeoff_paper_binding_10.json)保留31个完整尝试与2个局部条目，主图改为9个完整合法配置配对的资源／线长／CPD／时间变化；9行不等于9个独立输入。八个失败尝试保留，历史BNN局部散点图与原说明转入补充材料。完整BNN费用分解纳入开销节；本次无新增独立实验结果，CP1规则未改。'
    if status.get('BNN_engineering_paper_update'):
        paper_update_text='当前[六页正文11](BNN_engineering_paper_binding_11.json)纳入已闭合的BNN domain工程臂：32个完整尝试与2个局部条目。新臂9116.40秒、11.067GiB采样PSS、28次缺测；与历史同臂图数据、状态、请求、原生修复工作及完整端点向量一致，单次少637.92秒（6.54%）。原22.95%配对费用增幅保留；尚无新的优化后N/D费用比或统计加速结论。新增独立输入为零，CP1未改；原9对完整配置图及失败保留。'
    if status.get('cp1_prospective_cohort'):
        paper_update_text+=' [CP1 首批跨电路确认](cp1_cross_circuit_cohort_01/plan.json)已登记conv_layer_hls和tpu_like.small.ws两输入四臂，单一owner追加在修正robot-p1之后。实际固定入口检查通过；3.32GB物理输入准入待串行槽。历史成功/失败输入同时保留，当前没有新增确认结果；不称未见测试集，不改变正文已证实结论。'
    if status.get('robot_mechanism_composition_screen'):
        paper_update_text+=' [robot 联合机制预筛](robot_mechanism_composition_screen_01/completion.json)：共享与owner候选来自同一根，却重叠同一网络的两连接；共享32个退化端点与owner31个改善端点无交集。不能拼接树或相加标量来宣称组合收益；需要重新构造25连接联合请求并验证完整容量/STA。0次新native调用，CP1不变。'
    if status.get('robot_union_mechanism_plan'):
        paper_update_text+=' [25连接联合机制实验](robot_union_mechanism_01/plan.json)现已登记并排在CP1确认之后：相同联合请求下native、domain-no-release、domain-release三臂；owner网络均不限域。八项开发检查通过，尚无新原生结果，不改CP1。'
    if status.get('complete_BNN_cost_hierarchy'):
        paper_update_text+=' [完整BNN费用分解](complete_BNN_cost_hierarchy_01/completion.json)：原1821.07秒额外时间中1692.84秒处于资源事务，占92.96%；70/1361次连接查询。核心38.23/1207.26秒为嵌套计时，不能与完整时间相加。最终空选择轮27.32秒仅占domain完整时间0.2801%，尚无可归功的提前停止加速；CP1和正在运行的工程臂不变。'
    if status.get('cp1_public_source_restoration'):
        paper_update_text+=' [CP1公开源码重建](cp1_public_source_restoration_01/completion.json)通过：两个固定发行wheel恢复1166依赖文件，1289封存文件全匹配，真实扩展导入/项目外固定入口检查通过；未使用完整运行包或已安装依赖。外部native二进制及物理输入仍需显式提供，0次新native执行。'
    if status.get('portable_whole_method_actual',{}).get('passed'):
        input_outcome_text+=' 项目外观测、已知 R1 非空 owner 事务和 tiny 整方法实际检查均已通过；完整 tiny 耗时101.43 s，零提交，不算新独立样本或正向机制整合收益。后续队列按实际回执接续；正向整合路径和独立确认结果仍待验证。'
    if status.get('clstm_input_compatibility_failure'):
        input_outcome_text+=' [clstm 失败重分类](clstm_input_contract_pair_02/failure_reclassification.json)：两臂在 packed-netlist 读取阶段报$undef不匹配，尚未开始路由；107.00/106.48 s作为失败完整尝试保留。原模板漏带历史--merge_constant_generators off，不能算路由拥塞或机制负结果。新输入契约在两臂继承该选项、复用未改动dev03，追加到reduction之后；[新登记](clstm_input_contract_pair_02/plan.json)不覆盖旧回执，不增独立样本，也不宣称修复已获原生验证。'
    if status.get('robot_p1_input_compatibility_failure'):
        input_outcome_text+=' robot p1两臂同样在路由前报$undef不匹配，102.93/102.90 s保留为输入兼容性失败；[修正配对](robot_p1_input_contract_pair_02/plan.json)追加到修正clstm之后。当前BNN domain工程臂执行，随后reduction、修正clstm、修正robot p1；全部旧规则及回执保留。'
    if status.get('robot_owner_scope_actual'):
        input_outcome_text+=' [robot owner原生消融](robot_owner_scope_pair_01/verification.json)已闭合：target-only251173/10/653，target+owner251185/10/654，同13.354624073 ns；增加12wire/1CB换31setup改善、0退化。资源策略拒绝两者，endpoint规则仅接受owner候选；均未提交原actor。完整导入式配对155.10 s，不是冷启动整算法时间。该晚到局部结果已入补充回执，正文08尚未纳入。'
    engineering_progress_text=''
    engineering=status.get('domain_engineering_actual_progress')
    if engineering:
        engineering_progress_text=(f"实际回执：资源阶段接受{engineering['resource_accepted_steps']}步，资源阶段已核验终结={engineering['resource_phase_verified_terminal']}；"
            f"时序阶段接受{engineering['timing_accepted_steps']}步。")
        if engineering['current_resources']:
            r=engineering['current_resources']
            engineering_progress_text+=(f"最近已接受检查点为{engineering['current_CPD_s']*1e9:.9f} ns／{r['wirelength']} wire／{r['SB_pairs']} SB／{r['CB_sources']} CB。")
        if engineering['whole_case_verified']:
            r=engineering['final_resources']
            engineering_progress_text+=(f"整配置已核验：{engineering['final_CPD_ns']:.9f} ns／{r['wirelength']} wire／{r['SB_pairs']} SB／{r['CB_sources']} CB，"
                f"完整时间{engineering['complete_wall_seconds']:.2f} s；采样PSS峰值{engineering['sampled_tree_PSS_peak_kib']/1048576:.3f} GiB，内存缺失观察{engineering['missing_memory_observations']}次。")
        else:
            engineering_progress_text+='整配置尚未核验终结，不把中间质量或阶段时间当作完整结果。'
        comparison=engineering['full_comparison']
        if comparison:
            if comparison.get('successful_new_roles') and comparison.get('same_role_execution_exact'):
                engineering_progress_text+=(f"完整同角色比较已通过执行等价：相对历史domain完整时间变化{comparison['descriptive_same_role_seconds_difference']:+.2f} s"
                    f"（{comparison['descriptive_same_role_percent_difference']:+.2f}%），仅为单次描述性观测。")
            else:
                engineering_progress_text+='完整比较回执已生成，失败或执行差异按原回执保留，不宣称同等行为的工程加速。'
        else:
            engineering_progress_text+='完整同角色执行等价比较尚待终结。'
        engineering_progress_text+='旧native观察者／PSS缺口及并发限制保留；稳定对称交错计时仍待完成。'
    owner_scope_summary='[已登记 native 范围对照](robot_owner_scope_pair_01/plan.json)固定原通用选组器首选：目标3连接与目标＋owner4连接，两臂均 unrestricted；只改变协调范围，结果以实际终结回执为准。'
    if status.get('robot_owner_scope_actual'):
        owner_scope_summary='[已完成 native 范围对照](robot_owner_scope_pair_01/verification.json)：目标3连接与目标＋owner4连接，两臂均 unrestricted；扩大范围增加12 wire/1 CB，换取31个setup端点改善、0退化，CPD不变。固定资源策略拒绝，均未提交；这是协调范围的取舍证据。'
        input_outcome_text=input_outcome_text.replace('该晚到局部结果已入补充回执，正文08尚未纳入。', '该局部结果已纳入正文09的owner取舍行，完整审计留在补充材料。' if status.get('owner_contract_paper_update') else '该局部结果已入补充回执，正文整合以当前版本证据绑定为准。')
    result=f'''# 当前研究状态（{status['observed_at']}）

Goal active；公开证据基点 `9734eee`，最新增量 `{status['latest_incremental_publication']['commit'][:7]}`。本地实际回执优先；无固定日期、总调用次数或矩阵完成停止条件。[工程缺失臂登记](../../docs/GitHub_domain_engineering_registration_20261116.md) · [跨输入登记](../../docs/GitHub_robot_p1_registration_20261116.md) · [最近完成结果](../../docs/GitHub_native_ablation_progress_20261116.md) · [完整机器状态与证据索引](CURRENT_STATUS.json)。

统一方法：当前 STA 重选事务组 → 跨层共享域 → 按网络失败释放 → 容量证书与当前余量驱动的 owner 协调 → 固定根规则下接受完整合法事务 → 重选与独立终结选点 → 完整时序组合。中间构造不要求逐个改善 CPD。[完整独立开发包 dev03](standalone_unified_method_component_03.json)已迁移原串行控制器；项目外 tiny 整流程已通过；[CP1 确认源码与规则](confirmation_release_cp1_01/completion.json)已冻结并通过23项入口检查及整包移位验证，独立确认结果仍待完成。先前组件、真实请求重放和子进程清理验证只证明对应接口，不证明完整算法收益。

最新机制证据：[robot 精确域/容量审计](robot_release_capacity_cut_01/completion.json)表明两个实际释放网络的原域禁止返回源层，而同层出口被事务外 owner 占满。释放域不释放 owner。[同源无释放原生消融](robot_domain_release_ablation_01/verification.json)现已失败并精确回滚：23连接请求在首连接的9次尝试后失败，源字节及完整端点向量恢复；29.24 s是导入事务成本，没有候选质量。[18 次残余容量路径检查](robot_owner_local_reachability_01/completion.json)中，两次目标单独剪除均无同层路径；16次释放 owner 分支后均可达，无超时。这些路径不包含 owner 重接，不能算16次成功修复。{owner_scope_summary}

跨输入：[结构筛选](structural_input_screen_01/completion.json)保留无切口和失败案例。{input_outcome_overview} 已完成原 clstm／robot p1 输入加载失败和 robot owner 对照；修正输入配对继续等待串行槽。robot p1 同时改变 packing 与实际坐标，非纯布局因果对照；已知历史输入不称未见测试集。同树不同 seed 不增加独立起点。

| 已核验完整 BNN 配置 | CPD/ns | wire / SB / CB | 完整秒 |
|---|---:|---:|---:|
| native |13.228145690|2059631 / 82 / 5062|7933.245509|
| domain-first |13.228145690|2061417 / 43 / 5060|9754.312096|
| 单遍索引 native |13.228145690|2059631 / 82 / 5062|7463.174179|
| 同流程缓存／stream native |13.228145690|2059631 / 82 / 5062|约7247（限定原 GNU-time）|

原匹配两臂：SB −47.56%，SB＋CB 约−0.797%，wire＋1786，完整时间约＋22.95%；setup 534改善/803退化，无新增 hold 违例。占用减少不等于面积或功耗降低。stream 的观察者丢失、全程 PSS 缺口及短暂并发保留，不能称无干扰统计加速；新工程改进须匹配两臂，稳定后交错计时。

[补齐 domain 工程臂](complete_BNN_domain_engineering_01/plan.json)：复用已完成 stream-native 的单遍索引、显式同流程缓存和 streaming-v2，只恢复原 domain 开关，保持原完整 domain 算法规则。原native结果复用，重型输入核验与执行在串行槽内完成。按完整轨迹／请求／原生工作及端点核对同角色等价后，才解释历史完整费用差。{engineering_progress_text}

完整结果边界：robot native/domain 为251116/9/653与251136/9/652，同13.354624073 ns，377.71/424.45 s；20 wire和46.74 s换1 CB。conv_layer 两臂初始失败，SPMV/CB-only无适用切口，softmax同质量，SB-only严格时序无额外收益。R1五连接 owner 两臂均2070653/32/5071、完整端点向量相同，归因于协调范围扩大。R1/Tf原生菜单已闭合，不能重跑。

| 实际存活 owner 或子阶段 | 阶段 | 登记 PID |
|---|---|---:|
{chr(10).join(rows)}

BNN 分组、组合验证、terminal-wire、robot no-release/owner、attention/robot-SDC、项目外接口检查及原 clstm/p1 失败批次已终结。当前 BNN domain 工程臂运行，随后 reduction → 修正 clstm → 修正 robot p1；以表内实时身份和终结回执为准，不重跑已完成批次。

{environment_text}

{input_outcome_text}

[追加 reduction_layer 配对](portable_reduction_pair_01/plan.json)已登记并由单一 owner 等待现有 domain 工程臂终结，同时要求独立整方法检查通过。该已知历史 n125 Hybrid-O 输入有268个共享范围、62个相关网络、0个支持的 owner 切口；当前 STA 资格与新路由机会尚未知。选择依据是已闭合 attention 初始失败及 robot-SDC 当前无资源候选，检验跨电路共享机会，而非继续调 BNN 线长。两臂仍用同一 dev03、seed21、count8/1.01，只改域/释放开关，不指定 net/RR 目标；不是未见输入、确认冻结或新架构族结论。[配置与实现核对](portable_reduction_pair_01/implementation_review.json)通过，0次原生调用。约5.40 GB物理输入的复制、完整摘要验证和独立运行时准入延后到串行槽；不能把登记预检当作实际准入已通过。

[完整 terminal-wire 只读比较](BNN_terminal_wire_qualified_comparison_02/plan.json)已挂接原恢复队列，{terminal_comparison_text}。旧 v1 依赖缺失的观察者完成回执，新入口使用已核验的旧质量回执并保留缺口；比较共同资源前缀、完整端点和 GNU-time 同口径费用，不补造旧 PSS／观察者时间。[15项反例检查](BNN_terminal_wire_qualified_comparison_validation_02.json)通过，0次原生调用；{terminal_result_text}{terminal_text}

[四角色只读终结比较](query_reduction_resource_dev_01/analysis_03/registration.json)已挂接：等待原批次终结及串行空位，复用前三个已核验比较，补齐 BNN domain 的质量、完整端点、实际 QUERY／ATTEMPT 与完整导入流程费用；不重跑原生实验。[比较器验证](query_reduction_terminal_03_validation.json)覆盖既有结果回归、起点规则不匹配、未终结输入与失败查询记账。{grouping_text}

[固定三网络组合](BNN_wire_timing_native_validation_01/verification.json)现已通过原生 FULL/STA、独立物理审计及固定规则：2059607 wire/82 SB/5062 CB，13.228145690 ns，相对源少24 wire，setup 2改善/0退化，无新增 hold 违例；34个延迟预测全部精确匹配。217.95 s是单个导入候选验证费用，不附加旧完整时间，也不作为独立输入。

{paper_update_text}

[当前六页正文]({paper})沿问题—机制—完整结果—取舍—消融—开销与范围组织。前版06主表保留22个完整流程条目，新增2个明确标注范围的组合／消融条目；robot 无释放失败、精确回滚和合法线长组合已整合。[前版证据绑定](native_ablation_paper_binding_06.json)核验页数、主表与视觉；[历史档案](multiobjective_closed_stream_quality_01/verification.json)为671条合法观测、34个完整质量配置，其中33个完整观察者测量、1个限定 GNU-time，均不等于独立样本数。新增五项直接相关工作，明确已有增量路由／多次收敛与本研究贡献的关系，区分历史拥塞价格、导入式修复和未验证 CHANZ；共9条参考文献。新增条目不计入该历史档案的671条记录；历史局部路径、分组和前缀轨迹已移入补充材料。

接续：以真实终结结果决定下一项干预，优先完成确认版本的实际运行、跨输入匹配和三机制归因。普通失败/退化用于调整方向；未执行计划、结构路径和局部时间不替代完整可复现收益。
'''
    if engineering and engineering.get('whole_case_verified'):
        result=result.replace('当前 BNN domain 工程臂运行，随后 reduction → 修正 clstm → 修正 robot p1；', '完整BNN domain工程臂已终结，后继顺序为reduction → 修正clstm → 修正robot p1；')
        result=result.replace('当前BNN domain工程臂执行，随后reduction、修正clstm、修正robot p1；', 'BNN domain工程臂已终结，后继reduction、修正clstm、修正robot p1按实际状态接续；')
        result=result.replace('CP1和正在运行的工程臂不变。', 'CP1和原登记工程配置保持不变。')
        result=result.replace('已登记并由单一 owner 等待现有 domain 工程臂终结，同时要求独立整方法检查通过。', '由原单一owner在domain工程臂正常终结后接续；实际阶段以上表为准，独立整方法检查仍是准入条件。')
        result=result.replace('[最近完成结果](../../docs/GitHub_native_ablation_progress_20261116.md)', '[最近完整工程结果](../../docs/GitHub_BNN_engineering_complete_20261116.md)')
    reduction=status.get('portable_reduction_actual')
    if reduction and reduction['admission_passed']:
        actual=(f"[实际输入准入](portable_reduction_pair_01/admission.json)已通过完整复制、摘要及独立运行时检查，"
            f"准备耗时{reduction['preparation_seconds_outside_measured_arms']:.2f}秒，位于两臂测量命令之外；各臂仍自行承担登记的新路由、索引与修复工作。")
        observed=reduction.get('native_input_observation')
        if observed:
            actual+=(f"[原生输入加载观察](portable_reduction_pair_01/actual_native_input_observation_01.json)于{observed['observed_at']}确认native已通过packed-netlist读取和布局一致性检查，并加载RR graph。"
                "这不是旧CLSTM/p1的加载失败重现；尚不证明合法路由、完整结果或机制收益，未修改原配置。")
        legal=reduction.get('native_initial_legal')
        if legal:
            actual+=(f"后续原生FULL/STA与独立物理审计已确认合法新初态：{legal['CPD_ns']:.9f}ns、{legal['wirelength']}wire/{legal['SB_pairs']}SB/{legal['CB_sources']}CB；"
                "控制器继续资源修复。该初态不等于完整方法结果，仍待两臂终态比较。")
        for arm,progress in reduction.get('resource_progress',{}).items():
            if progress['accepted_steps']:
                res=progress['last_accepted_resources']
                actual+=(f"{arm}资源阶段已接受{progress['accepted_steps']}步，最近检查点{progress['last_accepted_CPD_ns']:.9f}ns、{res['wirelength']}wire/{res['SB_pairs']}SB/{res['CB_sources']}CB。")
        first=reduction.get('first_native_resource_acceptance')
        if first:
            actual+='[首个原生接受事务](portable_reduction_pair_01/first_native_resource_acceptance_01.json)减少32wire与8SB，CPD/CB不变，setup12改善/0退化，hold违反不增加；这是共同选组与不限域原生修复的局部证据，不能归因共享域或失败释放，也不是完整方法收益。'
        result=result.replace('约5.40 GB物理输入的复制、完整摘要验证和独立运行时准入延后到串行槽；不能把登记预检当作实际准入已通过。',actual)
    if status.get('BNN_interleaved_timing_plan'):
        result+='\n[稳定BNN交错计时登记](BNN_interleaved_timing_01/plan.json)：N→D→D→N，固定相同工程、环境设置及完整测量边界；排在robot联合机制批次之后，未挤占跨输入确认。12项配置与记账门槛检查通过，不是原生结果。每次重新生成路由和索引，保留全部失败／差异；旧native缺失测量不能补入。两个配对只支持描述性均值、范围与比值，不作统计加速或独立样本主张；四次尝试不是研究Goal停止条件。\n'
    return result
