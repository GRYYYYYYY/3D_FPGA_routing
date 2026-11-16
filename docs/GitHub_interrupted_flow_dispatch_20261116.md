# 四臂完整接续入口：2026-11-16

以 `9734eee` 为公开证据基点，保留本地更新和冻结版本。本次完成开发接续程序与真实队列登记，尚未新增独立实验结果、恢复后的最终质量或冷启动整流程费用。研究 Goal 保持 active。

统一方法和固定规则没有变化：当前 STA/跨层冗余选组、共享域、按网失败释放、owner 协调，经完整验证按固定根预算接受，再做终结选点和当前 STA 时序修复。这里补上的是按真实切点继续运行的工程入口。

[四臂协议](../research/dac_v14_20261112/interrupted_flow_recovery_01/protocol.json)已按原顺序固定：CLSTM/native、CLSTM/domain、reduction/native、reduction/domain，排在已登记的[四臂只读阶段核验](../research/dac_v14_20261112/interrupted_stage_reconciliation_01/plan.json)之后。真实 owner 为 PID1905142；启动身份和源码绑定见[队列登记](../research/dac_v14_20261112/interrupted_flow_recovery_01/queue/registration.json)。14:24 UTC 核对共7个登记 owner 存活，BNN 仍占原串行工作链，其他任务保持原依赖顺序。

| 输入臂 | 完整接续方式 |
|---|---|
| CLSTM/native | 已完成资源、终结选点和交接均保留；验证完整合法档案及交接向量，复用原首轮时序 portfolio/查询、原生执行和候选审计，从缺失候选 STA 继续 |
| CLSTM/domain | 保留原根预算、1次已接受资源提交及合法拒绝档案；复用下一事务的已完成原生执行，从缺失审计/STA 继续资源闭合及后续流程 |
| reduction/native | 保留原根和10次资源提交；原生269请求虽有成功日志，worker未封存，必须先通过真实字节/完整STA核验，再写新命名空间的复用回执；原 running manifest 不改写 |
| reduction/domain | 保留原根和4次资源提交；复用原生、候选物理和域审计，从空候选 STA 切点继续，再完成资源及后续流程 |

入口由[整流程驱动](../research/dac_v14_20261112/run_interrupted_full_flow_recovery_v1.py)、[逐臂准入](../research/dac_v14_20261112/admit_interrupted_flow_recovery_01.py)和[阶段复用层](../research/dac_v14_20261112/same_actor_stage_reuse_v1.py)组成。资源/时序事务、控制器改动可逆还原到原源码；固定接受、候选顺序、终结策略及原 robot 登记程序保持原样。旧的原生、物理/域审计只在同一事务角色、输入与规则精确匹配时复用；已有未完成的候选 STA 载荷需另行核对。原先未执行的 optional native 角色和后续新轮次仍由原工作体执行。

准入不会拿元数据测试代替真实核验。串行审计执行后，每臂必须在实际 summary 中有通过记录，绑定实际审计摘要、CP1r3 打包/父版本和未改动算法文件，先封存该臂计划再运行。单臂准入失败保留为未执行；已执行事务若缺终结回执或审计失败，不得晋升为完整恢复结果。残留子进程会阻止继续调度；不自动重试原批次。

验证包括[5项小型流程检查及20项拒绝检查](../research/dac_v14_20261112/interrupted_stage_adapter_01/validation.json)，覆盖原封存/未封存执行复用、旧文件不变、审计复用、空STA后续执行、新轮次及未执行optional角色；另有[4臂真实元数据、源码可逆性和31项拒绝检查](../research/dac_v14_20261112/interrupted_flow_recovery_01/validation.json)，覆盖原角色请求顺序、字节、CPD/资源预算及CLSTM原时序配置。这些检查没有调用VPR，也没有宣称完整行为等价或真实恢复已通过。

每臂将分别测量新接续命令的墙钟、PSS和缺失观察，原失败费用继续单列。恢复结果属于原开发输入，不新增独立样本，不成为CP1r3冻结确认，也不重构冷启动完整费用或N/D时间比。最终端点比较、配对证据和正文结果只有在真实恢复完成并核验后才更新。

现有六页正文、43行主表及已支持主张保持原证据范围：完整BNN资源/计算取舍、robot固定组合的域/释放局部机制、owner范围扩大归因、conv_hls无收益、TPU超时。新增完整跨输入收益、自动机制选择收益和对称工程优化后的完整比值仍待证据；本轮接续工程进入补充材料。
