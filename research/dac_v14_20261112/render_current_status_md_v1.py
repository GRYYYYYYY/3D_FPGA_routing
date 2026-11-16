"""Short current research entry; detailed component/history records remain linked."""
from pathlib import Path

def render(status,D):
    rows=[]
    for owner in status['owners']:
        if not owner['verified_live'] and not owner.get('flow_active_stage'):continue
        phase=owner.get('effective_wait') or owner['phase_status']
        if owner.get('flow_active_stage'):phase+=' → '+owner['flow_active_stage']['phase']
        rows.append(f"| {owner['batch']} | {phase} | {owner['pid']} |")
    paper=Path(status['paper_pdf']).relative_to(D)
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
    if status.get('cp1_prospective_cohort'):
        paper_update_text+=' [CP1 首批跨电路确认](cp1_cross_circuit_cohort_01/plan.json)已登记conv_layer_hls和tpu_like.small.ws两输入四臂，单一owner追加在修正robot-p1之后。实际固定入口检查通过；3.32GB物理输入准入待串行槽。历史成功/失败输入同时保留，当前没有新增确认结果；不称未见测试集，不改变正文已证实结论。'
    if status.get('robot_mechanism_composition_screen'):
        paper_update_text+=' [robot 联合机制预筛](robot_mechanism_composition_screen_01/completion.json)：共享与owner候选来自同一根，却重叠同一网络的两连接；共享32个退化端点与owner31个改善端点无交集。不能拼接树或相加标量来宣称组合收益；需要重新构造25连接联合请求并验证完整容量/STA。0次新native调用，CP1不变。'
    if status.get('portable_whole_method_actual',{}).get('passed'):
        input_outcome_text+=' 项目外观测、已知 R1 非空 owner 事务和 tiny 整方法实际检查均已通过；完整 tiny 耗时101.43 s，零提交，不算新独立样本或正向机制整合收益。后续队列按实际回执接续；正向整合路径和独立确认结果仍待验证。'
    if status.get('clstm_input_compatibility_failure'):
        input_outcome_text+=' [clstm 失败重分类](clstm_input_contract_pair_02/failure_reclassification.json)：两臂在 packed-netlist 读取阶段报$undef不匹配，尚未开始路由；107.00/106.48 s作为失败完整尝试保留。原模板漏带历史--merge_constant_generators off，不能算路由拥塞或机制负结果。新输入契约在两臂继承该选项、复用未改动dev03，追加到reduction之后；[新登记](clstm_input_contract_pair_02/plan.json)不覆盖旧回执，不增独立样本，也不宣称修复已获原生验证。'
    if status.get('robot_p1_input_compatibility_failure'):
        input_outcome_text+=' robot p1两臂同样在路由前报$undef不匹配，102.93/102.90 s保留为输入兼容性失败；[修正配对](robot_p1_input_contract_pair_02/plan.json)追加到修正clstm之后。当前BNN domain工程臂执行，随后reduction、修正clstm、修正robot p1；全部旧规则及回执保留。'
    if status.get('robot_owner_scope_actual'):
        input_outcome_text+=' [robot owner原生消融](robot_owner_scope_pair_01/verification.json)已闭合：target-only251173/10/653，target+owner251185/10/654，同13.354624073 ns；增加12wire/1CB换31setup改善、0退化。资源策略拒绝两者，endpoint规则仅接受owner候选；均未提交原actor。完整导入式配对155.10 s，不是冷启动整算法时间。该晚到局部结果已入补充回执，正文08尚未纳入。'
    return f'''# 当前研究状态（{status['observed_at']}）

Goal active；公开证据基点 `9734eee`，最新增量 `{status['latest_incremental_publication']['commit'][:7]}`。本地实际回执优先；无固定日期、总调用次数或矩阵完成停止条件。[工程缺失臂登记](../../docs/GitHub_domain_engineering_registration_20261116.md) · [跨输入登记](../../docs/GitHub_robot_p1_registration_20261116.md) · [最近完成结果](../../docs/GitHub_native_ablation_progress_20261116.md) · [完整机器状态与证据索引](CURRENT_STATUS.json)。

统一方法：当前 STA 重选事务组 → 跨层共享域 → 按网络失败释放 → 容量证书与当前余量驱动的 owner 协调 → 固定根规则下接受完整合法事务 → 重选与独立终结选点 → 完整时序组合。中间构造不要求逐个改善 CPD。[完整独立开发包 dev03](standalone_unified_method_component_03.json)已迁移原串行控制器；项目外 tiny 整流程已通过；[CP1 确认源码与规则](confirmation_release_cp1_01/completion.json)已冻结并通过23项入口检查及整包移位验证，独立确认结果仍待完成。先前组件、真实请求重放和子进程清理验证只证明对应接口，不证明完整算法收益。

最新机制证据：[robot 精确域/容量审计](robot_release_capacity_cut_01/completion.json)表明两个实际释放网络的原域禁止返回源层，而同层出口被事务外 owner 占满。释放域不释放 owner。[同源无释放原生消融](robot_domain_release_ablation_01/verification.json)现已失败并精确回滚：23连接请求在首连接的9次尝试后失败，源字节及完整端点向量恢复；29.24 s是导入事务成本，没有候选质量。[18 次残余容量路径检查](robot_owner_local_reachability_01/completion.json)中，两次目标单独剪除均无同层路径；16次释放 owner 分支后均可达，无超时。这些路径不包含 owner 重接，不能算16次成功修复。[已登记 native 范围对照](robot_owner_scope_pair_01/plan.json)固定原通用选组器首选：目标3连接与目标＋owner4连接，两臂均 unrestricted；只改变协调范围，排在 clstm 之后，尚未执行。

跨输入：[结构筛选](structural_input_screen_01/completion.json)保留无切口和失败案例。{input_outcome_overview} 已完成原 clstm／robot p1 输入加载失败和 robot owner 对照；修正输入配对继续等待串行槽。robot p1 同时改变 packing 与实际坐标，非纯布局因果对照；已知历史输入不称未见测试集。同树不同 seed 不增加独立起点。

| 已核验完整 BNN 配置 | CPD/ns | wire / SB / CB | 完整秒 |
|---|---:|---:|---:|
| native |13.228145690|2059631 / 82 / 5062|7933.245509|
| domain-first |13.228145690|2061417 / 43 / 5060|9754.312096|
| 单遍索引 native |13.228145690|2059631 / 82 / 5062|7463.174179|
| 同流程缓存／stream native |13.228145690|2059631 / 82 / 5062|约7247（限定原 GNU-time）|

原匹配两臂：SB −47.56%，SB＋CB 约−0.797%，wire＋1786，完整时间约＋22.95%；setup 534改善/803退化，无新增 hold 违例。占用减少不等于面积或功耗降低。stream 的观察者丢失、全程 PSS 缺口及短暂并发保留，不能称无干扰统计加速；新工程改进须匹配两臂，稳定后交错计时。

[补齐 domain 工程臂](complete_BNN_domain_engineering_01/plan.json)已排在原 robot p1 完整配对之后：复用已完成 stream-native 的单遍索引、显式同流程缓存和 streaming-v2，只恢复原 domain 开关，保持原完整 domain 算法规则。未引入 terminal-wire、owner 或分组新策略；native 不重跑。新结果尚无，重型输入核验在串行槽内执行。按完整轨迹／请求／原生工作及端点核对同角色等价后，才比较历史完整费用；native 观察者缺失的限定保留，稳定交错计时另行开展。

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
