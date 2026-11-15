# 机制归因、跨输入筛选与固定版本接续

公开证据基点仍为 `9734eee`，本次增量继承 `cdcd931`。保留本地 HEAD、索引、已登记版本和全部完成回执；Goal active，不设固定日期、总调用次数或矩阵完成停止条件。

统一方法为：当前 STA 重选组 → 跨层冗余驱动的共享域 → 按网络失败释放 → 容量证书与当前余量驱动的 owner 协调 → 固定根规则下接受完整合法事务 → 重选组与独立终结选点 → 完整时序组合。中间构造状态不要求逐步改善 CPD。完整串行方法已迁入独立 dev03，但实际整流程检查尚在队列中，不能称为已冻结的确认结果。

本次完成[六个历史物理输入的结构筛选](../research/dac_v14_20261112/structural_input_screen_01/completion.json)。每个合法根核验实际路由边、图缓存身份、容量及物理资源；没有重复 native 路由。

| 输入 | 结构共享候选切口 | 支持的完全阻塞源出口证书 | 边界 |
|---|---:|---:|---|
| clstm s21/p0 | 6 | 0 | 尚需当前 STA 与完整匹配执行 |
| reduction s21/p0 | 268 | 0 | 尚需当前 STA 与完整匹配执行 |
| robot s21/p0 | 6 | 2 | 与现代完整实验的初始树正文一致 |
| robot s23/p0 | 3 | 0 | 与 s21 同 packing、实际不同布局 |
| robot s21/p1 | 43 | 30 | packing 和布局均改变，非纯布局对照 |
| attention s11/p0 | — | — | 历史初始路由失败，无合法修复根 |

这些是结构适用性证据，不能作为新的完整算法结果或未见过的留出测试。没有支持的阻塞证书，也不等于没有其他优化机会。相同初始树的不同 seed 仍不计独立起点。

[robot 精确域/容量审计](../research/dac_v14_20261112/robot_release_capacity_cut_01/completion.json)解释了两个实际失败释放网络：同层源出口被事务外 owner 占满，保留域仅允许向外跨层，不能返回源层 sink。在固定外部占用与该域下，合法路径不存在；释放域可解除此限制，但不释放外部 owner。实际 native 和 domain-release 候选在两个网络上均各保留两个跨层资源。另一个仍受域限制的网络节省一个 CB，因此域限制、失败释放和 owner 协调应分别归因。该条件证明不等于全局不可路由，也不替代仍排队的关闭释放 native 消融。

[原通用 owner 选组器](../research/dac_v14_20261112/robot_current_owner_screen_01/completion.json)在真实 robot 路由及 STA 上得到 16 个余量合格联合组；首选为三条目标连接加一条 owner 连接。规则不含电路专属网络编号。这证明存在当前规则可提出的干预，并未证明 native 可实现、可接受或产生收益。下一项归因应匹配同根目标单独修复与加入 owner 的修复，而非继续围绕 BNN 调整少量线长。

[clstm 完整 native/domain 配对](../research/dac_v14_20261112/portable_clstm_pair_01/plan.json)已固定输入与 dev03，追加在独立完整方法检查后。先决检查失败时，两臂保持未执行；成功后两臂从相同物理文件重新路由，核对实际初始树与完整向量，只改变 domain_mode/domain_feedback，owner 均 unrestricted。完整时间覆盖新路由、图索引、资源/时序过程及封存。此实例无明确 SDC，不支持应用时序要求主张；单次顺序两臂也不构成交错计时结论。原 attention 与 robot s23 SDC 配对继续保留其早先登记版本。

捕获时 BNN query-reduction domain 已接受 13 步，actor PID 2219632 与 start ticks 匹配；原 pool 正常轮换到 PID 88947，不应按旧 PID 消失触发恢复。后续仍为线长组合 native 验证、robot no-release、完整 terminal-wire BNN、attention/robot-SDC、独立观测/事务/完整方法检查，最后 clstm 配对。新增 clstm owner PID 286682、start ticks 1955916028，正在等待；所有状态以[实际回执入口](../research/dac_v14_20261112/CURRENT_STATUS.json)为准，不提前计为完成。

完整代价尚无新的匹配结果：原 BNN 两臂 CPD 同为 13.228145690 ns，wire 2059631→2061417，SB 82→43（−47.56%），CB 5062→5060；SB+CB 5144→5103（约−0.797%）。完整时间 7933.245509→9754.312096 s（约+22.95%）；setup 534 改善、803 退化，无新增 hold 违例。节省固定图上的 SB 占用有资源配置意义，不等于芯片面积或功耗减少。工程改进仍须两臂匹配，稳定后同环境交错测量。

[六页正文](../research/dac_v14_20261112/paper_snapshots/current_mechanism_inputs_20261115/build/current_repair_main.pdf)替换了通用选机制与 robot 归因两段，保留 22 行统一主表及所有失败/无收益/退化案例。变更第2/3/4页完成视觉检查，第1/5/6页逐像素一致；原 671 条观测、34 个完整质量配置（33 个完整观察者测量、1 个限定 GNU-time）不变。详细结构筛选和证书留在补充材料，[证据绑定](../research/dac_v14_20261112/mechanism_inputs_paper_binding_04.json)区分条件机制证明与未执行的 native 消融。新增完整算法结果、native 调用均为 0，不新增普遍收益主张。大型原始图、二进制及全部运行数据仍在共享存储，本推送不是完整异地备份。
