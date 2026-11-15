# 统一方法、独立输入与六页稿的增量进展

本增量继承公开证据基点 `9734eee83b62fc012f0bb137f75aba919df514e4`，保持本地 main、索引和正在运行的原实验版本。研究 Goal 继续 active；不以日期、总调用或矩阵完成终止。本文描述发布时点，后续进程变化以本地真实回执为准。

统一方法的[开发入口](../research/dac_v14_20261112/run_complete_unified_method_v1.py)已经接通：新路由与固定根状态 → 当前资源/时序选组 → 跨层共享域与逐网络失败释放 → 资源菜单关闭后诊断并协调阻塞 owner → 接受后重新选择 → 同次执行的端点安全线长终结选点 → 当前 STA 严格时序修复。接受完整事务，保留根状态预算；不要求每个中间状态改善 CPD。两臂的 owner 搜索均 unrestricted；域限制、失败释放和协调范围分别归因。

已有通用 owner 接口在真实 R1 上重建原两臂全部 native 参数，无需历史事务模板；SPMV 无切口路径实际执行且没有启动求解。它们是接口/集成证据，不是新的独立电路收益。[实现状态](../research/dac_v14_20261112/unified_confirmation_candidate_01/implementation_status_01.json)明确保留正向自动 owner 接受后重入、完整集成执行、独立依赖封装和最终确认冻结等未完成项。

[四个新开发角色](../research/dac_v14_20261112/unified_input_integration_01/plan.json)已登记：attention native/domain，以及 robot s23/p0 native/domain。robot 与已有 s21/p0 packing 相同、实际布局坐标不同，并使用明确的 clk 20 ns、输入/输出 max1 ns/min0 ns SDC；这是声明的基准目标，不是外部应用需求，而且布局与 SDC 同时变化，不能归因于单一变量。两臂只改变 domain_mode/domain_feedback。它们排在原恢复链之后，发布时尚无完整结果。相同初始树的不同 seed 不增加独立起点。

[可迁移运行组件](../research/dac_v14_20261112/standalone_native_runtime_dev_01/README.md)已封存为 [24 KB 包](../research/dac_v14_20261112/standalone_native_runtime_artifact_01/standalone_native_runtime_component_01.tar.gz)。禁止读取历史工程目录的迁移检查通过：正常执行、超时、线程拒绝、输入篡改、错误二进制拒绝；真实 tiny 物理审计保持 146 wire/0 SB/13 CB，错误 switch 被拒绝，失败观测保留。解包后的独立自检通过。新 VPR 调用为 0；这是组件工程验证，**不是完整算法的独立可执行确认版**。

完整 BNN 原匹配对照仍为 13.228145690 ns：native 2059631 wire/82 SB/5062 CB、7933.245509 s；domain 2061417/43/5060、9754.312096 s。SB 减少 **47.56%**，SB+CB 总计数减少约 **0.797%**，增加 1786 wire 与约 **22.95%** 完整时间；最终臂间 setup 534 改善/803 退化，无新增 hold 违例。单遍索引 native 7463.174179 s 保持质量与实际工作一致，但尚不能据此替换优化后两臂的完整开销比；对称优化和交错计时仍待完成。

新增完整 BNN 工程对照已正常终结并通过独立质量及逐状态/请求/native 工作/图数据等价核验：CPD 13.228145690 ns、2059631 wire/82 SB/5062 CB，5 次资源接受和 3 次时序接受。原 GNU-time 为 **7247 秒（整数秒精度）**，driver 为 7247.3263 秒；相对同口径 7933/7463 秒约少 **686/216 秒（8.65%/2.89%）**。原观察者丢失且有短暂重叠，全程 PSS 不可恢复，不报告统计加速或优化后 native/domain 新开销比。自身初始到终结 setup 14 改善/17 退化、无新增 hold 违例。新主表用星号区分原 GNU-time 和完整 observer 计时；此新配置尚未并入冻结的 658 条档案。详见[工程等价与计时证据](../research/dac_v14_20261112/orphaned_BNN_engineering_comparison_01/completion.json)。

五连接 owner native/domain 得到相同 2070653 wire/32 SB/5071 CB 与完整端点向量，应归于扩大协调范围；两连接候选多 4 wire。robot 域控制用 20 wire 和 46.74 s 换 1 CB，失败释放单标志消融仍排队。conv_layer 两臂初始失败；SPMV/CB-only 无适用切口；softmax 两臂相同最终质量；SB-only 严格时序下无额外收益。budget64 的负结果保留，不将局部调参改善泛化为完整算法收益。

[当前正文](../research/dac_v14_20261112/paper_snapshots/current_unified_engineering_20261115/build/current_repair_main.pdf)已按“问题—机制—完整结果—多目标取舍—消融—开销与适用范围”重构为六页，包含机制伪代码、路由相关工作和贡献比较。22 行主表包含 20 个合法完整角色及 2 个初始失败角色，列出 CPD、wire/SB/CB、完整时间、PSS 和相对各自初始根的端点变化；历史局部轨迹与恢复审计保留补充材料。[源文、PDF、主表与原始回执绑定](../research/dac_v14_20261112/unified_engineering_paper_binding_02.json)明确哪些主张已有证据，哪些仍属待确认方法。

最新档案实际为 **658 条合法观测、33 个成功完整配置、5 个成功电路身份、3 个垂直家族**。配置数不是独立样本数。继承计数漏掉四个早期配置；640 条档案实际有 30 个，658 条实际有 33 个。旧回执保留，计数纠正在新库存和正文中显式记录。

[进程快照](../research/dac_v14_20261112/CURRENT_STATUS.json)确认原完整 BNN 已结束，独立恢复 owner 已恢复 query-reduction 队列；两个 eltwise 角色已完成，继续已登记的 BNN 角色，之后接续组合 LOAD、robot 消融、terminal-wire 及统一输入开发队列。旧失败/缺失回执不覆盖。只读质量核验 v1 曾因对整数秒 GNU-time 使用 0.1 秒容差而失败；v2 按实际显示精度检查，质量 gates 未变。父队列对 eltwise native 的 3133.7414 秒等待含调度暂停，不作为算法耗时；子 actor 实际导入工作流为 117.8027 秒，paired 为 119.8088 秒。原数值与说明保留在[独立计时审计](../research/dac_v14_20261112/query_reduction_timing_qualification_01/completion.json)。

本次推送是代码、方案、阶段回执、文稿与组件包的增量快照；大型 RRG、route、native 二进制、完整运行日志和外部 Python 依赖仍在共享盘，不是全部原始数据异地备份。绝对来源路径是证据身份，除独立运行组件外，不声明任意目录开箱即跑。发布清单逐文件记录哈希及省略项，运行中的结果不会被当作完成结果。
