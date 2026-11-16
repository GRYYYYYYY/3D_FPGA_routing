# 固定 dev03 的 robot p1 完整配对登记

本次在原队列末尾登记 robot p1 的完整 native/domain 开发配对，接在 robot owner 范围对照之后。此前已完成的实验不重跑，现有队列、版本和接受规则不修改；公开证据基点仍为 `9734eee`。

要回答的问题是：同一独立执行的 dev03 统一方法，在另一套真实 packing／placement、且历史上存在容量阻塞的输入上，能否完成合法路由与时序—资源—费用取舍。现有 clstm 历史根没有支持的 owner 阻塞证书，robot owner 范围对照又仅覆盖局部事务；本配对补充完整控制器的不同物理输入验证，不强制触发某个模块，也不要求每个模块或中间状态单独改善 CPD。

输入为 `heldout_robot_rl_s21_hybrid_o_n60_w100_p1_a0`。已实际核对其2468块的归一化块名—坐标映射和packing：均不同于已有现代robot p0输入，电路与架构相同。因此不是相同初始树换seed；但packing与布局同时变化，不能归因于布局单一因素。目录名中的heldout是历史标签，这是已知开发输入，不是未见测试集。未提供明确SDC，不主张应用时序闭合。

两臂使用与clstm配对完全相同的dev03包；仅domain模式与失败释放开关不同。owner协调在两臂均为unrestricted，搜索机会、工程实现、完整接受和终结规则匹配。两臂都重新构建索引并从物理输入执行新路由，不导入旧树或历史候选，不注入目标网络。比较器只在真实新初始树及完整初始端点向量相同后进行最终配对比较；失败、无收益和退化保留。

历史结构筛选有43个共享切口和30个支持的owner阻塞证书。这些数量不是新流程的适用性、可行性或收益保证；实际新路由上的STA、容量和机制触发必须重新观测。该整流程两臂也不能单独归因域、释放或owner的作用，局部消融另行保留。

项目外准入已实际通过，固定包、物理文件和规则均绑定哈希；新增原生调用为0。新队列已确认存活，等待已有robot owner范围对照终结，并要求前序独立完整方法检查通过。核验或执行基础设施异常会保留未执行角色并请求状态核对；普通失败或负结果不是整个研究的停止条件。

- [固定计划](../research/dac_v14_20261112/portable_robot_p1_pair_01/plan.json)
- [实际物理输入核验](../research/dac_v14_20261112/portable_robot_p1_pair_01/physical_identity_check.json)
- [实际队列登记](../research/dac_v14_20261112/portable_robot_p1_pair_01/queue/registration.json)
- [执行入口](../research/dac_v14_20261112/run_portable_robot_p1_pair_01.py)与[比较器](../research/dac_v14_20261112/compare_portable_robot_p1_pair_01.py)
- [当前状态](../research/dac_v14_20261112/CURRENT_STATUS.md)

当前仍在运行完整terminal-wire BNN。本文是前瞻登记，不是新增独立结果；六页正文和既有完整费用结论保持原证据范围。确认版本尚未冻结，Goal继续进行。
