# 当前研究状态（2026-11-16T01:02:52.461135+00:00）

Goal active；公开证据基点 `9734eee`，最新增量 `f5fb23d`。本地实际回执优先；无固定日期、总调用次数或矩阵完成停止条件。[本轮说明](../../docs/GitHub_native_ablation_progress_20261116.md) · [完整机器状态与证据索引](CURRENT_STATUS.json)。

统一方法：当前 STA 重选事务组 → 跨层共享域 → 按网络失败释放 → 容量证书与当前余量驱动的 owner 协调 → 固定根规则下接受完整合法事务 → 重选与独立终结选点 → 完整时序组合。中间构造不要求逐个改善 CPD。[完整独立开发包 dev03](standalone_unified_method_component_03.json)已迁移原串行控制器；实际整流程验证仍排队，确认版尚未冻结。先前组件、真实请求重放和子进程清理验证只证明对应接口，不证明完整算法收益。

最新机制证据：[robot 精确域/容量审计](robot_release_capacity_cut_01/completion.json)表明两个实际释放网络的原域禁止返回源层，而同层出口被事务外 owner 占满。释放域不释放 owner。[同源无释放原生消融](robot_domain_release_ablation_01/verification.json)现已失败并精确回滚：23连接请求在首连接的9次尝试后失败，源字节及完整端点向量恢复；29.24 s是导入事务成本，没有候选质量。[18 次残余容量路径检查](robot_owner_local_reachability_01/completion.json)中，两次目标单独剪除均无同层路径；16次释放 owner 分支后均可达，无超时。这些路径不包含 owner 重接，不能算16次成功修复。[已登记 native 范围对照](robot_owner_scope_pair_01/plan.json)固定原通用选组器首选：目标3连接与目标＋owner4连接，两臂均 unrestricted；只改变协调范围，排在 clstm 之后，尚未执行。

跨输入：[结构筛选](structural_input_screen_01/completion.json)保留五个合法历史根和 attention 初始失败。clstm/reduction 有6/268个共享候选切口、均无当前支持的完全阻塞源出口证书；robot 三个实际物理起点有2/0/30个证书，p1同时改变 packing，非纯布局因果对照。新增完整方法结果仍为0。[clstm 固定 dev03 两臂](portable_clstm_pair_01/plan.json)在完整方法检查后从物理输入新路由；实际起点必须匹配，先决检查失败则保持未执行。原 [attention 与 robot s23 SDC 配对](unified_input_integration_01/plan.json)保留先前登记版本；同树不同 seed 不算独立输入。

| 已核验完整 BNN 配置 | CPD/ns | wire / SB / CB | 完整秒 |
|---|---:|---:|---:|
| native |13.228145690|2059631 / 82 / 5062|7933.245509|
| domain-first |13.228145690|2061417 / 43 / 5060|9754.312096|
| 单遍索引 native |13.228145690|2059631 / 82 / 5062|7463.174179|
| 同流程缓存／stream native |13.228145690|2059631 / 82 / 5062|约7247（限定原 GNU-time）|

原匹配两臂：SB −47.56%，SB＋CB 约−0.797%，wire＋1786，完整时间约＋22.95%；setup 534改善/803退化，无新增 hold 违例。占用减少不等于面积或功耗降低。stream 的观察者丢失、全程 PSS 缺口及短暂并发保留，不能称无干扰统计加速；新工程改进须匹配两臂，稳定后交错计时。

完整结果边界：robot native/domain 为251116/9/653与251136/9/652，同13.354624073 ns，377.71/424.45 s；20 wire和46.74 s换1 CB。conv_layer 两臂初始失败，SPMV/CB-only无适用切口，softmax同质量，SB-only严格时序无额外收益。R1五连接 owner 两臂均2070653/32/5071、完整端点向量相同，归因于协调范围扩大。R1/Tf原生菜单已闭合，不能重跑。

| 实际存活 owner 或子阶段 | 阶段 | 登记 PID |
|---|---|---:|
| unexecuted_recovery_20261115_01 | running | 404657 |
| unified_input_integration_01 | waiting_for_registered_recovery_chain | 894335 |
| standalone_native_observation_equivalence_01 | waiting_for_registered_unified_input_chain | 2087555 |
| standalone_transaction_native_check_01 | waiting_for_registered_portable_observation | 3385842 |
| standalone_whole_method_check_01 | waiting_for_registered_transaction_interface_check | 4177680 |
| portable_clstm_pair_01 | waiting_for_portable_whole_method_execution | 286682 |
| robot_owner_scope_pair_01 | waiting_for_registered_clstm_pair | 580012 |

BNN 分组、固定组合 LOAD 和 robot no-release 已终结；原队列当前执行完整 terminal-wire BNN，随后按既有顺序执行 attention/robot-SDC → 独立 native 观测/事务/完整方法检查 → clstm → robot owner 范围对照。PID 必须与 start ticks、终结回执交叉核对；正常 pool 轮换不触发恢复。各批次原规则及已完成结果保持不变。

[四角色只读终结比较](query_reduction_resource_dev_01/analysis_03/registration.json)已挂接：等待原批次终结及串行空位，复用前三个已核验比较，补齐 BNN domain 的质量、完整端点、实际 QUERY／ATTEMPT 与完整导入流程费用；不重跑原生实验。[比较器验证](query_reduction_terminal_03_validation.json)覆盖既有结果回归、起点规则不匹配、未终结输入与失败查询记账。BNN domain 分组开发已终结并封存：16步，2061345/43/5060，13.607436067 ns，完整导入流程 10308.49 s。相对历史 K8，仅少 32 wire，同 SB/CB/CPD，历史时间增加 45.20%；不能作为加速证据。不据此将分组启发式加入已登记 dev03，也不继续优化几个 BNN 线长单位；优先执行既有跨输入与机制验证。完整四角色端点／工作量比较等待串行空位；此处不是冷启动完整配置费用。

[固定三网络组合](BNN_wire_timing_native_validation_01/verification.json)现已通过原生 FULL/STA、独立物理审计及固定规则：2059607 wire/82 SB/5062 CB，13.228145690 ns，相对源少24 wire，setup 2改善/0退化，无新增 hold 违例；34个延迟预测全部精确匹配。217.95 s是单个导入候选验证费用，不附加旧完整时间，也不作为独立输入。

[当前六页正文](paper_snapshots/current_native_ablation_20261116/build/current_repair_main.pdf)沿问题—机制—完整结果—取舍—消融—开销与范围组织，统一主表保留22个完整流程条目，新增2个明确标注范围的组合／消融条目；robot 无释放失败、精确回滚和合法线长组合已整合。[证据绑定](native_ablation_paper_binding_06.json)核验页数、主表与视觉；[档案](multiobjective_closed_stream_quality_01/verification.json)为671条合法观测、34个完整质量配置，其中33个完整观察者测量、1个限定 GNU-time，均不等于独立样本数。新增五项直接相关工作，明确已有增量路由／多次收敛与本研究贡献的关系，区分历史拥塞价格、导入式修复和未验证 CHANZ；共9条参考文献。新增组件不计入该历史档案的671条记录；历史局部路径、分组和前缀轨迹已移入补充材料。

接续：以真实终结结果决定下一项干预，优先完成确认版本的实际运行、跨输入匹配和三机制归因。普通失败/退化用于调整方向；未执行计划、结构路径和局部时间不替代完整可复现收益。
