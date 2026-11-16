# 完整费用与跨输入结果：2026-11-16

接续公开证据基点 `9734eee` 与增量 `612b764`，保留本地开发状态及原队列。不重跑已完成原生批次；研究 Goal 继续，无日期、调用次数或矩阵完成停止条件。

统一方法是：当前 STA 与树结构选组 → 有共享冗余时限制到保留跨层域 → 搜索失败时仅释放受影响网络的域 → 对容量阻塞建立独立 owner 协调事务 → 完整合法性、物理延迟、FULL/STA 与固定预算验收 → 独立终结选点及当前 STA 反馈。接受的是完整组合，不要求每个中间状态改善 CPD。已经登记的开发批次保持版本和规则不变；项目外整流程在已有小型输入上已通过；完整确认版仍需冻结及正向机制路径的整合验证，不将无提交执行等同于全面确认。

## 新闭合的证据

| 完整尝试 | CPD (ns) | 线长 / SB / CB | 完整时间 (s) | 解释 |
| --- | ---: | --- | --- | --- |
| BNN terminal N | 13.228145690 | 2059607 / 82 / 5062 | 7351.26 | 同一历史 BNN 输入；包含初始路由、索引、终结选点、三次时序提交及拒绝成本 |
| robot-SDC N / D | 12.727250365 / 相同 | 250411 / 2 / 526，完全相同 | 498.00 / 504.09 | 两臂起始路由体和完整端点一致，最终端点也一致；无收益 |
| attention N / D | 无合法结果 | 无合法结果 | 794.67 / 792.69 | 两臂初始路由均在 200 轮后失败，剩余 231 个过用节点，未进入修复 |

robot 使用已知历史电路的实际不同布局，不是同树换 seed；与旧输入相比还加入了 SDC，不能作布局单因素因果比较。固定声明为 20 ns 时钟、最大／最小 I/O 延迟 1／0 ns。两臂各 10972 个实际 setup 与 hold 分量均有限且非负。这是声明的基准要求，不是外部应用时序要求，也不是未见测试集。

当前 robot 树没有合格共享切口或 owner 协调组，三项时序提案均被固定规则拒绝。一个合法候选把 CPD 降至 12.671110383 ns，但增加 8 wire、1 SB、1 CB，超出固定资源上限；没有临时放松规则。两臂质量相同，完整时间差 6.10 s（约 +1.22%）只作共享主机上的描述。一个物理输入的两个臂不算两个独立样本。

[完整配对比较](../research/dac_v14_20261112/unified_input_integration_01/comparison.json) · [attention 匹配失败审计](../research/dac_v14_20261112/attention_initial_failure_pair_01/completion.json) · [物理输入身份](../research/dac_v14_20261112/confirmation_input_inventory_01/completion.json) · [SDC](../research/dac_v14_20261112/unified_input_integration_01/robot_50MHz.sdc)

## 机制与完整费用的边界

此前 BNN 三网线长组合已通过原生 FULL/STA，34 项延迟预测精确匹配；其 217.95 s 是导入候选验证，不能替代上表完整时间。[独立比较器的实际回执](../research/dac_v14_20261112/BNN_terminal_wire_qualified_comparison_02/completion.json)已通过：共同资源前缀的状态、请求与原生工作精确一致，最终比旧 stream 基线少 24 wire、setup 2 改善／0 退化，无新增 hold 违例，CPD/SB/CB 相同。同口径 GNU-time 为 7351／7247 s（整秒显示），增加 104 s，约 1.44%；旧观察者与完整 PSS 缺失、短暂并发限制保留，不能宣称加速。新流程相对自身初始根为 setup 16 改善／17 退化，不能与相对旧终态的 2／0 混用。

robot 同源 no-release 消融实际失败并精确回滚，支持失败释放的操作作用；它不证明整个 FPGA 不可路由，也不证明 owner 协调有收益。已有 R1 owner 联合修复中 native 与 domain 相同，应归于协调范围扩大。当前新增输入没有证明任一机制推进质量取舍。

原始完整 BNN 配对仍是：SB 82→43，减少 **47.56%**；SB＋CB 5144→5103，减少 **0.797%**；完整时间代价 **22.95%**。节省固定器件上的稀缺占用有工程意义，但不等于面积、功耗或普遍可布通率改善。新 terminal N 费用不替换该原始配对费用。匹配 domain 工程臂已排队；稳定版本后仍需同环境交错计时。

新 BNN 采样 PSS 为 11.063 GiB，缺失 24 次内存观察；robot N/D 缺失 5／2 次，采样峰值并非精确最大值。attention-native 存在已记录的短暂 Git 自动打包重叠，进程已终止且原实验未重启；[环境记录](../research/dac_v14_20261112/unified_input_integration_01/measurement_environment_note_01.json)保留，不能宣称受控速度优势。

## 六页正文与接续

[新版六页正文](../research/dac_v14_20261112/paper_snapshots/current_qualified_inputs_20261116/build/current_repair_main.pdf)与[证据绑定](../research/dac_v14_20261112/qualified_complete_paper_binding_08.json)沿“问题—机制—完整结果—多目标取舍—消融—开销与范围”组织。统一主表为 27 个完整尝试（含 4 个初始失败）和 2 个明确限定范围的组件条目；新增完整费用、SDC 无收益与 attention 失败，端点来自各自初态／终态完整向量，不累加局部变化。机制图和九项相关工作保留；局部轨迹、恢复与审计留在补充材料。历史档案的 671 条观测与 34 个完整质量配置计数不冒充已纳入这些新结果。

独立打包的原生观察接口已在项目外实际执行，FULL/STA、原生 trace、完整端点及物理审计精确一致；这是组件执行检查，不是独立输入或整算法收益。已知 R1 非空事务也在项目外通过，请求、路由体、端点及物理审计精确复现（806.16 s 组件费用）。已有 tiny 输入的整方法实际通过，101.43 s，零资源／owner／时序提交；它验证完整可执行路径，不证明正向机制整合收益。随后 clstm 两臂在 packed-netlist 加载时报 `$undef` 不匹配，未进入路由；107.00／106.48 s 是输入兼容性失败成本，不是拥塞或修复负结果。已查明模板遗漏历史 `--merge_constant_generators off`，保留原回执并[单独重分类](../research/dac_v14_20261112/clstm_input_contract_pair_02/failure_reclassification.json)。robot owner-scope 已接续运行，其余原队列保持不变。

[修正输入契约的新 clstm 配对](../research/dac_v14_20261112/clstm_input_contract_pair_02/plan.json)已追加到 reduction 之后：同一 dev03、相同物理输入及算法规则，两臂继承历史常量解释选项，不改旧批次。实际命令继承函数和失败分类检查通过，0 次新原生调用；完整准入与执行仍待串行槽。它不增加独立物理样本，修复尚未获原生结果确认。该输入兼容性发现保留在补充回执中，不冒充当前主表的路由失败。

根据 attention 失败及 robot-SDC 无适用资源切口，已将一个固定 dev03 的 [reduction_layer 配对](../research/dac_v14_20261112/portable_reduction_pair_01/plan.json)追加到原工程臂之后。历史输入有 268 个共享范围、62 个相关网络、无支持的 owner 切口；只用于选择待检输入，不算新算法收益。新的实际路由与 STA 资格未知，约 5.40 GB 输入的完整验证／复制延后到串行槽。没有重新优化单个 BNN 的几个线长单位，也没有改变当前确认候选规则。

[发布时实际进程快照](../research/dac_v14_20261112/CURRENT_STATUS.md)区分运行、等待与终结状态。该 GitHub 增量包含文稿、代码、精选回执和绑定，不是全部大型原始图、路由及端点数据的异地备份。


## 发布后接续回执（04:08 UTC）

robot owner-scope 原生配对现已[验证通过](../research/dac_v14_20261112/robot_owner_scope_pair_01/verification.json)：target-only 为251173 wire/10 SB/653 CB，加入owner为251185/10/654，CPD均13.354624073 ns。相对target-only，新增12wire和1CB换31个setup分量改善、0退化；相对各自源，target-only为0改善/1退化，owner为31改善/0退化。两者均无新增hold违例。固定资源策略拒绝两者，独立endpoint规则接受owner候选；均未提交原actor。完整共享导入式配对155.10 s，不能分摊或冒充冷启动算法时间。域限制与失败释放在两臂均关闭，因此归于协调范围的局部取舍，未减少本例垂直资源。正文08保留其封存时边界，此晚到消融先以补充回执发布，待下一次正文整合。

robot p1两臂也在packed-netlist读取阶段因同一常量网解释选项缺失失败，完整费用102.93/102.90 s，未开始路由；[重分类回执](../research/dac_v14_20261112/robot_p1_input_contract_pair_02/failure_reclassification.json)保留原始失败。[修正robot p1配对](../research/dac_v14_20261112/robot_p1_input_contract_pair_02/plan.json)复用未变dev03和物理输入，在修正clstm之后等待。实际修复结果尚未知，不增加独立样本；当前BNN domain工程臂运行，其后依次是reduction、修正clstm、修正robot p1。旧队列和科学批次不被重启或覆写。
