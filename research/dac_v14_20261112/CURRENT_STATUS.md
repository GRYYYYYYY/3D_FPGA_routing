# 当前研究状态（2026-11-15T23:34:56.484269+00:00）

Goal active；公开证据基点为 `9734eee`，统一方法/六页稿/BNN stream 工程对照，以及独立观测与选组迁移、三个已完成分组对照以及完整质量/测量覆盖区分及独立事务入口验证已增量推送至 `00279cf` 并经 GitHub 读回核对，后续本地分析以真实回执接续。无固定日期、总调用或矩阵完成停止条件。[增量发布说明](../../docs/GitHub_unified_method_progress_20261115.md) · [机器状态](CURRENT_STATUS.json)。

[失败释放迁移验证](standalone_release_replay_01/completion.json)重放真实 robot 协议：3454/3438 释放，3140/8785 继续受域限制，全部科学字段与原记录一致；成功后释放、重复释放、错误保留域均被拒绝。该重放不替代 no-release 消融。另有[持久化事务执行检查](standalone_transaction_native_check_01/plan.json)排在原观测检查之后，计划两次 native 调用（源序列化控制＋实际 owner 修复），当前尚未执行，不新增独立输入。

[独立串行资源控制器组件](standalone_resource_controller_component_03.json)已接通新路由输入、原资源/owner 状态机及终结选点。真实无切口控制器执行和 R1 请求生成通过；三个 worker 与新路由入口仅完成启动前检查。该早期资源组件验证保留；当前完整时序组合及外层已迁入新开发包，未冻结确认版本。

[独立完整方法开发包](standalone_unified_method_component_03.json)包含原完整资源/owner/终结选点/时序组合及原整流程核验器，116 个文件逐字节重建一致。工程外真实 eltwise 选组、反馈、组合和事务准备到首次 native 边界通过；容量/放宽查询各复用 5 条、重新求解 0 条。两个时序 worker 准备和四种实际子进程清理测试通过。新 native 调用 0、新独立输入 0；[完整方法实际执行检查](standalone_whole_method_check_01/plan_v2.json)排在现有事务检查之后，使用固定 dev03，不设总方法时间或调用上限。

统一方法以当前 STA 重选事务组，按跨层冗余构造共享域；网络搜索失败时释放其域，容量阻塞时另行协调 owner。完整合法候选按固定时序/资源规则接受，终结选点与中间接受分离。[开发入口](run_complete_unified_method_v1.py)已接通资源、owner 协调、重选组、终结选点和时序阶段；[通用 owner 接口](current_owner_transaction_validation_01/completion.json)重建原两臂 native 参数，无切口 SPMV 实际执行不启动求解。完整分支仍待实际集成结果与独立打包冻结，不能称为已完成跨输入确认。

[当前统一档案](multiobjective_closed_stream_quality_01/verification.json)：**671 条合法观测、34 个完整质量配置，其中 33 个有完整观察者测量，1 个仅有带限定的原 GNU-time**；仍为 5 个成功电路身份、3 个垂直家族，不是独立样本数量。新纳入 stream 流程的 13 个真实状态，包括合法拒绝候选；完整时间仅归属于实际终点，缺失的 PSS/观察者墙钟/CPU 不补写，也不参与匹配计时支配。[当前六页稿](paper_snapshots/current_unified_archive_20261115/build/current_repair_main.pdf) 已同步上述口径，22 行统一主表含 2 个初始失败角色；前五页与上一版逐像素一致，第六页更新测量覆盖范围。历史轨迹、640 条图投影及恢复审计仍保留原范围。

| 已验证完整 BNN 配置 | CPD/ns | wire / SB / CB | 完整秒 |
|---|---:|---:|---:|
| native |13.228145690|2059631 / 82 / 5062|7933.245509|
| domain-first |13.228145690|2061417 / 43 / 5060|9754.312096|
| 单遍索引 native |13.228145690|2059631 / 82 / 5062|7463.174179|
| 索引＋同流程缓存／stream native |13.228145690|2059631 / 82 / 5062|约7247（原 GNU-time，整数秒）|

原匹配两臂：SB 减少 47.56%，SB+CB 总计数减少约 0.797%，wire 增加 1786，完整时间增加约 22.95%；setup 534 改善/803 退化，无新增 hold 违例。占用节省不等于器件面积或功耗下降。单遍索引是同质量的单次工程观察；尚未取得优化后两臂的交错计时结论。

输入证据及无效输入：robot 两臂为 251116/9/653 与 251136/9/652，同 13.354624073 ns，377.71/424.45 s；domain 用 20 wire 与 46.74 s 换 1 CB。conv_layer 两臂初始路由失败（260.10/254.57 s）；SPMV/CB-only 无适用切口；softmax 两臂同质量；SB-only 严格时序下无额外资源收益。seed11/19 相同初始树不算新起点。

归因：五连接 owner 协调的 native/domain 均为 2070653/32/5071，同完整端点向量，收益归于扩大协调范围。两连接结果多 4 wire，保留支配点。budget64 实际查询多重集合不变而事务 18→32，BNN 导入工作流多 46 wire；新分组阈值只是开发假设。robot release 单标志消融仍待执行。

进程恢复：原完整 BNN 已正常终结，[完整质量核验](orphaned_BNN_quality_analysis_02/completion.json)和[实际状态/请求/native 工作/图载荷对照](orphaned_BNN_engineering_comparison_01/completion.json)均通过。原 GNU-time 为 7247 s，较同口径 7933/7463 s 少约 686/216 s；driver 计时 7247.3263 s。原观察者丢失、全程 PSS 缺口及短暂重叠保留，不能称为无干扰或统计加速。[恢复监控](supervision_recovery_20261115_01/completion.json)已按真实终结恢复 query-reduction owner；两个 eltwise 与 BNN native 角色均已完成，BNN domain 按原队列接续，后续恢复链顺序不改。

| 实际存活 owner 或子阶段 | 阶段 | 原登记 owner PID |
|---|---|---:|
| query_reduction_resource_dev_01 | running | 8305 |
| unexecuted_recovery_20261115_01 | waiting_for_registered_predecessor | 404657 |
| unified_input_integration_01 | waiting_for_registered_recovery_chain | 894335 |
| standalone_native_observation_equivalence_01 | waiting_for_registered_unified_input_chain | 2087555 |
| standalone_transaction_native_check_01 | waiting_for_registered_portable_observation | 3385842 |
| standalone_whole_method_check_01 | waiting_for_registered_transaction_interface_check | 4177680 |

[新登记集成配对](unified_input_integration_01/plan.json)：attention native/domain，以及 robot s23/p0 native/domain（同 packing、真实不同布局，明确 clk 20 ns、I/O max1 ns/min0 ns SDC）。两臂只改 domain_mode/domain_feedback，owner 均 unrestricted，所有工程改进一致；这是开发验证，尚无结果，SDC 是声明的基准目标而非外部应用要求。排在现有恢复链之后，独立只读比较 owner 已登记。

[独立运行组件](standalone_native_runtime_dev_01/README.md)已封装为[24 KB 源码与 guard 包](standalone_native_runtime_artifact_01/standalone_native_runtime_component_01.tar.gz)，解包自检通过；迁出工程后，正常/超时/线程拒绝/输入篡改/错误二进制检查通过，实际 tiny 物理审计与原回执相同，错误 switch 被拒绝、失败角色计数保留。新 VPR 调用为 0，不增加独立电路或完整配置计数。选组、事务及完整控制器现已迁入独立开发入口，实际完整运行仍待验证；不能把组件封存当作完整确认版冻结。

时钟审计：原质量核验第一次因 GNU-time 小时格式只显示整数秒、却使用 0.1 s 容差而失败；保留该失败，v2 按实际显示精度核验且原质量 gate 不变。query-reduction native 的父队列等待计时含 SIGSTOP，3133.7414 s 不作为算法耗时；子 actor 实际报告导入工作流 117.8027 s，paired 为 119.8088 s。原值均保留，见[独立计时说明](query_reduction_timing_qualification_01/completion.json)。

[独立观测依赖](standalone_observation_dependencies_validation_02/completion.json)已在工程目录外验证：单遍索引生成、五个缓存载荷与原数据一致，真实缓存物理审计/完整端点向量/接受及拒绝决策保持一致；未完成事务、不同约束、截断 trace、损坏缓存和错误哈希均被拒绝。初次 tuple/list 表示比较失败原样保留，v2 只修正完整向量的 JSON 表示比较，复用已完成索引生成。新 native FULL/STA 接口验证已[登记排队](standalone_native_observation_equivalence_01/plan.json)，工程外持久化输入与依赖已冻结，待现有跨输入队列终结后执行一次；本轮新 native 调用为 0，完整算法仍未独立冻结。

[独立选组迁移](standalone_selection_validation_01/completion.json)已用工程外完整 R1 和 tiny 数据实际执行，禁止 Python 读取旧工程：R1 的 8 个 owner 组、1 个共享切口、完整证书/筛选/排序/请求及 STA 目标与原实现一致；tiny 无切口保留。完整 NativeAnalysisPool 已原字节复制，尚未执行迁移后的池。完整方法仍未冻结。

[新分组的三个已完成角色](query_reduction_completed_comparison_02/completion.json)与各自原 K8 的完整端点向量、路由正文、请求和决策序列一致；提议连接数分别仍为 94/32/70，未减少。BNN native 导入流程 2089.304 s，相比历史 2076.308 s 多 12.996 s；eltwise 两臂分别少 5.950/6.291 s，均不是交错计时或独立输入证据。BNN domain 仍待终结。

[独立事务入口](standalone_transactions_validation_03/README.md)已实现显式输入/二进制/运行库绑定、源序列化控制、范围/域审计、真实候选物化和固定根接受。在工程外重放原 R1 两臂，完整请求/候选/端点/物理字段一致（只排除审计路径和耗时）；五连接 owner 准备与 VPR 调用前检查通过。篡改实际 gate 或换入错误完整树均被拒绝。两次校验失败分别为路径/耗时比较和实际 R1 固定参数未列入白名单，旧失败保留，未重跑 native。新入口尚未实际启动 VPR，不能称为完整方法冻结。

接续重点：独立可执行确认版本、真实不同布局/路由起点、具有明确 SDC 的新实例，以及正文“问题—机制—完整结果—取舍—消融—开销与范围”。历史局部轨迹、恢复时间和审计移到补充材料；负结果用于调整方法。
